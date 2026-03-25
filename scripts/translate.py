#!/usr/bin/env python
"""
Translate untranslated nodes from English to Russian using Claude API.

Usage:
    python scripts/translate.py [--budget 5.0]

Reads nodes where title_ru IS NULL from the database, translates them with
Claude Haiku (cheapest model), and writes results back immediately after each
node so progress is never lost.

Stops gracefully when the budget limit is reached.

Requires: ANTHROPIC_API_KEY environment variable.
"""
import os
import sys
import argparse
from pathlib import Path

# Bootstrap Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proofly.settings')

import django
django.setup()

import anthropic
from graph.models import Node  # noqa: E402

# Claude Haiku 4.5 pricing (USD per token)
INPUT_COST_PER_TOKEN  = 1.00 / 1_000_000
OUTPUT_COST_PER_TOKEN = 5.00 / 1_000_000

SYSTEM_PROMPT = """\
You are a professional mathematical translator specializing in translating \
formal mathematics from English to Russian.

Rules:
- Translate natural language text to Russian
- Keep all LaTeX expressions EXACTLY as-is: $...$, $$...$$, \\command, etc.
- Use standard Russian mathematical terminology:
  group → группа, ring → кольцо, field → поле, theorem → теорема,
  axiom → аксиома, proof → доказательство, lemma → лемма,
  subgroup → подгруппа, identity → единичный элемент, etc.
- Keep the same Markdown structure (##, **, lists)
- Do NOT add explanations or commentary — only the translation
"""


def estimate_cost(text: str) -> float:
    """Rough input token cost estimate: ~4 chars per token."""
    tokens = len(text) / 4
    return tokens * INPUT_COST_PER_TOKEN


def translate_text(client: anthropic.Anthropic, text: str) -> tuple[str, float]:
    """
    Translate text and return (translated_text, actual_cost_usd).
    """
    response = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': text}],
    )
    translated = response.content[0].text
    cost = (
        response.usage.input_tokens  * INPUT_COST_PER_TOKEN +
        response.usage.output_tokens * OUTPUT_COST_PER_TOKEN
    )
    return translated, cost


def main():
    parser = argparse.ArgumentParser(description='Translate nodes to Russian via Claude API')
    parser.add_argument('--budget', type=float, default=5.0,
                        help='Maximum USD to spend (default: $5.00)')
    args = parser.parse_args()

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('Error: ANTHROPIC_API_KEY environment variable is not set.')
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    nodes = list(Node.objects.filter(title_ru__isnull=True).exclude(title_en__isnull=True))
    total = len(nodes)

    if not total:
        print('All nodes already have Russian translations.')
        return

    print(f'Found {total} node(s) to translate. Budget: ${args.budget:.2f}')
    print()

    spent   = 0.0
    done    = 0
    skipped = 0

    for i, node in enumerate(nodes, 1):
        # Pre-check: will this likely exceed budget?
        estimated = estimate_cost((node.title_en or '') + (node.description_en or ''))
        if spent + estimated > args.budget:
            print(f'Budget limit reached after {done} translations '
                  f'(${spent:.4f} spent). {total - done} node(s) remaining.')
            break

        print(f'[{i}/{total}] {node.slug} … ', end='', flush=True)

        try:
            # Translate title
            title_ru, cost_title = translate_text(client, node.title_en or node.slug)
            spent += cost_title

            # Translate description
            description_ru, cost_desc = translate_text(
                client, node.description_en or ''
            )
            spent += cost_desc

            # Save immediately — don't lose progress
            node.title_ru       = title_ru.strip()
            node.description_ru = description_ru.strip()
            node.save(update_fields=['title_ru', 'description_ru'])

            done += 1
            print(f'done (${cost_title + cost_desc:.4f}, total ${spent:.4f})')

        except anthropic.APIError as e:
            skipped += 1
            print(f'ERROR: {e}')
            continue

    print()
    print(f'Translated: {done}, skipped: {skipped}, total spent: ${spent:.4f}')
    remaining = Node.objects.filter(title_ru__isnull=True).exclude(title_en__isnull=True).count()
    if remaining:
        print(f'{remaining} node(s) still need translation. Run again to continue.')


if __name__ == '__main__':
    main()
