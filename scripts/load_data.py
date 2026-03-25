#!/usr/bin/env python
"""
Load all theorem JSON files from data/ into the database, then recalculate
levels so that level = max(dependency levels) + 1.

Usage:
    python scripts/load_data.py

Idempotent — safe to run on every container start.
"""
import os
import sys
import json
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proofly.settings')

import django
django.setup()

from graph.models import Node, Edge  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def load_json(data_file: Path):
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    print(f'Loading {len(nodes)} nodes and {len(edges)} edges from {data_file.name} …')

    created = updated = 0
    for n in nodes:
        _, was_created = Node.objects.update_or_create(
            slug=n['slug'],
            defaults={
                'title_ru':       n.get('title_ru'),
                'title_en':       n.get('title_en'),
                'node_type':      n['node_type'],
                'level':          n.get('level', 0),
                'description_ru': n.get('description_ru'),
                'description_en': n.get('description_en'),
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    print(f'  Nodes: {created} created, {updated} updated')

    edge_created = edge_skipped = 0
    for e in edges:
        try:
            from_node = Node.objects.get(slug=e['from'])
            to_node   = Node.objects.get(slug=e['to'])
        except Node.DoesNotExist as exc:
            print(f'  WARN: skipping edge {e["from"]} → {e["to"]}: {exc}')
            edge_skipped += 1
            continue
        _, was_created = Edge.objects.get_or_create(from_node=from_node, to_node=to_node)
        if was_created:
            edge_created += 1
        else:
            edge_skipped += 1
    print(f'  Edges: {edge_created} created, {edge_skipped} skipped/existing')


def recalc_levels():
    """Topological sort + longest-path DP: level = max(dep levels) + 1."""
    nodes = {n.slug: n for n in Node.objects.all()}
    edges = Edge.objects.select_related('from_node', 'to_node').all()

    in_degree  = {slug: 0 for slug in nodes}
    successors = {slug: [] for slug in nodes}
    for e in edges:
        successors[e.from_node.slug].append(e.to_node.slug)
        in_degree[e.to_node.slug] += 1

    levels = {slug: 0 for slug in nodes}
    queue  = deque(s for s in nodes if in_degree[s] == 0)
    remaining = dict(in_degree)

    while queue:
        slug = queue.popleft()
        for succ in successors[slug]:
            if levels[slug] + 1 > levels[succ]:
                levels[succ] = levels[slug] + 1
            remaining[succ] -= 1
            if remaining[succ] == 0:
                queue.append(succ)

    changed = 0
    for slug, node in nodes.items():
        new_level = levels[slug]
        new_type  = 'axiom' if new_level == 0 else 'theorem'
        if node.level != new_level or node.node_type != new_type:
            node.level     = new_level
            node.node_type = new_type
            node.save(update_fields=['level', 'node_type'])
            changed += 1

    print(f'Levels recalculated: {changed} node(s) updated')


def main():
    json_files = sorted(DATA_DIR.glob('*.json'))
    if not json_files:
        print(f'No JSON files found in {DATA_DIR}')
        return

    for f in json_files:
        load_json(f)

    recalc_levels()
    print('All data loaded.')


if __name__ == '__main__':
    main()
