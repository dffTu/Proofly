#!/usr/bin/env python
"""
Fetch algebra theorems from Metamath's set.mm and load them into the DB.

Usage:
    python scripts/fetch_metamath.py [--file path/to/set.mm] [--no-clear]

Without --file, downloads set.mm from GitHub (raw, ~50 MB).
Writes nodes and edges directly to the database via Django ORM.

By default, clears all existing nodes/edges before importing.
"""
import os
import sys
import re
import argparse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proofly.settings')

import django
django.setup()

from graph.models import Node, Edge  # noqa: E402

SET_MM_URL = (
    'https://raw.githubusercontent.com/metamath/set.mm/master/set.mm'
)

ALGEBRA_PREFIXES = (
    'grp', 'abelgrp', 'ring', 'field', 'subgrp', 'nsg',
    'cring', 'drng', 'slmd', 'lmod', 'lvec',
    'mnd', 'cmn',
)

SEED_THEOREMS = 100


def iter_statements(text):
    """
    Yield (label, kind, comment, proof_refs) for real mathematical statements only.

    In Metamath, $a and $p can be:
      - Syntax/notation: $a class X  or  $a wff X  (skip these)
      - Real math:       $a |- ...   or  $p |- ...  (keep these)

    kind: 'axiom' | 'theorem'
    """
    pattern = re.compile(
        r'(?:\$\((.*?)\$\)\s*)?'
        r'(\w+)\s+\$(a|p)\s+'
        r'(.*?)\$[=.]',
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        comment = (m.group(1) or '').strip()
        label   = m.group(2)
        kind    = 'axiom' if m.group(3) == 'a' else 'theorem'
        body    = m.group(4).strip()

        if not body.startswith('|-'):
            continue

        proof_refs = []
        if kind == 'theorem':
            eq_pos  = text.find('$=', m.end(4))
            dot_pos = text.find('$.', eq_pos) if eq_pos != -1 else -1
            if eq_pos != -1 and dot_pos != -1:
                proof_text = text[eq_pos + 2: dot_pos]
                proof_refs = re.findall(r'\b(\w+)\b', proof_text)

        yield label, kind, comment, proof_refs


def is_algebra(label):
    """
    Check if a label belongs to algebra (group/ring/field theory).
    The 'cmn' prefix also matches unrelated labels like 'cmntrcld' (topology).
    We reject labels that clearly belong to other domains by checking for
    known non-algebra suffixes after the algebra prefix.
    """
    low = label.lower()
    if not low.startswith(ALGEBRA_PREFIXES):
        return False
    NON_ALGEBRA_SUBSTRINGS = ('top', 'trcl', 'cls', 'open', 'clsd', 'cont', 'met')
    for s in NON_ALGEBRA_SUBSTRINGS:
        if low[3:].startswith(s):
            return False
    return True


def label_to_slug(label):
    return label.replace('.', '-').replace('_', '-').lower()


def is_section_header(comment):
    """Section-header comments contain long separator lines like =-=-= or -.-."""
    return bool(re.search(r'[=\-]{10,}', comment))


def extract_title(label, comment):
    """
    Extract a human-readable English title from the Metamath comment.

    Comments typically look like:
      "A commutative monoid is commutative. (Contributed by Mario Carneiro, ...)"
    We take the first sentence (up to the first period or parenthesis).
    """
    if not comment or is_section_header(comment):
        return label

    text = re.sub(r'\s+', ' ', comment).strip()
    text = re.sub(r'~\s*\w+', '', text)
    text = re.sub(r'`\s*(.*?)\s*`', r'\1', text)
    text = text.strip()

    m = re.match(r'^(.*?)(?:\.\s+|\s+\()', text)
    if m:
        title = m.group(1).strip().rstrip('.')
        if len(title) > 8:
            return title[:200]

    short = text[:80].rstrip(' .,')
    return short if short else label


def comment_to_description(label, kind, comment):
    """Convert a raw Metamath comment to Markdown."""
    if not comment or is_section_header(comment):
        return f'## {label}\n\n*(No description available.)*'

    text = re.sub(r'\s+', ' ', comment).strip()
    text = re.sub(r'`\s*(.*?)\s*`', r'$\1$', text)
    text = re.sub(r'~\s*(\w+)', r'[\1](#\1)', text)

    type_label = 'Axiom' if kind == 'axiom' else 'Theorem'
    return f'## {type_label}: {label}\n\n{text}'


def load_set_mm(path):
    print(f'Reading {path} …')
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def download_set_mm():
    cache = Path('/tmp/set.mm')
    if cache.exists():
        print(f'Using cached {cache}')
        return load_set_mm(cache)
    print(f'Downloading set.mm from GitHub (~50 MB) …')
    urllib.request.urlretrieve(SET_MM_URL, cache)
    print('Download complete.')
    return load_set_mm(cache)


def assign_roots_and_levels(nodes_dict, edges):
    """
    Nodes with no incoming edges are 'axioms' (level 0).
    Levels are computed as the longest path from any root using
    topological sort + DP — correct for DAGs.
    Returns (node_types dict, levels dict).
    """
    in_degree  = {slug: 0 for slug in nodes_dict}
    successors = {slug: [] for slug in nodes_dict}
    for from_slug, to_slug in edges:
        successors[from_slug].append(to_slug)
        in_degree[to_slug] += 1

    node_types = {}
    for slug, info in nodes_dict.items():
        node_types[slug] = 'axiom' if in_degree[slug] == 0 else info['node_type']

    from collections import deque
    levels = {slug: 0 for slug in nodes_dict}
    queue  = deque(slug for slug in nodes_dict if in_degree[slug] == 0)
    remaining = dict(in_degree)

    while queue:
        slug = queue.popleft()
        for succ in successors[slug]:
            if levels[slug] + 1 > levels[succ]:
                levels[succ] = levels[slug] + 1
            remaining[succ] -= 1
            if remaining[succ] == 0:
                queue.append(succ)

    for slug in nodes_dict:
        if levels[slug] == 0 and in_degree[slug] > 0:
            levels[slug] = 1

    return node_types, levels


def run(set_mm_text, clear=True):
    if clear:
        print('Clearing existing nodes and edges …')
        Edge.objects.all().delete()
        Node.objects.all().delete()
        print('  Done.')

    all_algebra = {}
    label_to_slug_map = {}

    for label, kind, comment, proof_refs in iter_statements(set_mm_text):
        if not is_algebra(label):
            continue
        slug = label_to_slug(label)
        all_algebra[slug] = {
            'label':      label,
            'node_type':  kind,
            'comment':    comment,
            'proof_refs': proof_refs,
        }
        label_to_slug_map[label] = slug

    print(f'Total algebra statements found in set.mm: {len(all_algebra)}')

    algebra_deps = {}
    for slug, info in all_algebra.items():
        deps = []
        for ref_label in info['proof_refs']:
            ref_slug = label_to_slug_map.get(ref_label)
            if ref_slug and ref_slug in all_algebra and ref_slug != slug:
                deps.append(ref_slug)
        algebra_deps[slug] = deps

    candidates = [
        slug for slug, info in all_algebra.items()
        if len(info['comment']) > 30
    ]

    included = set()
    for slug in candidates:
        if len(included) >= SEED_THEOREMS:
            break
        if slug in included:
            continue
        queue = [slug]
        while queue:
            s = queue.pop()
            if s in included:
                continue
            included.add(s)
            for dep_slug in algebra_deps.get(s, []):
                if dep_slug not in included:
                    queue.append(dep_slug)

    algebra = {slug: all_algebra[slug] for slug in included}
    print(f'Total nodes (seeds + their deps, soft limit {SEED_THEOREMS}): {len(algebra)}')

    edges = []
    for slug in algebra:
        for dep_slug in algebra_deps.get(slug, []):
            if dep_slug in algebra:
                edges.append((dep_slug, slug))
    edges = list(set(edges))

    node_types, levels = assign_roots_and_levels(algebra, edges)

    print('Writing nodes to database …')
    created = updated = 0
    for slug, info in algebra.items():
        title_en       = extract_title(info['label'], info['comment'])
        description_en = comment_to_description(info['label'], node_types[slug], info['comment'])
        _, was_created = Node.objects.update_or_create(
            slug=slug,
            defaults={
                'title_en':       title_en,
                'node_type':      node_types[slug],
                'level':          levels.get(slug, 1),
                'description_en': description_en,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    print(f'  Nodes: {created} created, {updated} updated')

    print('Writing edges to database …')
    edge_created = edge_skipped = 0
    for from_slug, to_slug in edges:
        try:
            from_node = Node.objects.get(slug=from_slug)
            to_node   = Node.objects.get(slug=to_slug)
        except Node.DoesNotExist:
            edge_skipped += 1
            continue
        _, was_created = Edge.objects.get_or_create(from_node=from_node, to_node=to_node)
        if was_created:
            edge_created += 1
        else:
            edge_skipped += 1
    print(f'  Edges: {edge_created} created, {edge_skipped} skipped')

    print('Done.')


def main():
    parser = argparse.ArgumentParser(description='Import Metamath algebra theorems into Proofly DB')
    parser.add_argument('--file',     help='Path to set.mm (downloads from GitHub if omitted)')
    parser.add_argument('--no-clear', action='store_true',
                        help='Do not delete existing data before importing')
    args = parser.parse_args()

    text = load_set_mm(args.file) if args.file else download_set_mm()
    run(text, clear=not args.no_clear)


if __name__ == '__main__':
    main()
