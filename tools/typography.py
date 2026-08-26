#!/usr/bin/env python3
"""Normalize typography across the site's HTML.

Two jobs:
  1. Straight quotes -> curly ('  ->  ’ , "..."  ->  “...”) in prose and in the
     human-readable meta tags, never in markup, attributes, or code.
  2. Em dashes -> wrapped in <span class="nobr">word<span class="emdash">&mdash;</span></span>
     so the CSS can lengthen them (Newsreader draws its em dash at 0.66em) and
     the dash can never be orphaned to the start of a line.

Safe to run repeatedly: both passes are idempotent.

  python3 tools/typography.py            fix files in place
  python3 tools/typography.py --check    report only, exit 1 if work is needed
"""

import glob
import os
import re
import sys

# Meta tags whose content a reader actually sees (search results, share cards).
META_READABLE = (
    "description", "og:description", "twitter:description",
    "og:title", "twitter:title", "og:image:alt",
)

OPENERS = set(' \t\n\r([{<—–>')  # what can precede an opening double quote


def smart_double_quotes(text: str, prev_char: str) -> str:
    """Straight double quotes -> curly, decided by context rather than by
    alternating state, so the result does not depend on what ran before."""
    out = []
    for ch in text:
        if ch == '"':
            out.append('“' if (prev_char == '' or prev_char in OPENERS) else '”')
        else:
            out.append(ch)
        prev_char = ch
    return ''.join(out)


def fix_prose(body: str) -> tuple[str, int, int]:
    """Convert quotes in text nodes only. Tags, attributes, <script> and <style>
    are left alone."""
    stash = []

    def keep(m):
        stash.append(m.group(0))
        return f'@@STASH{len(stash) - 1}@@'

    body = re.sub(r'<(script|style)\b.*?</\1>', keep, body, flags=re.S)

    parts = re.split(r'(<[^>]+>)', body)
    n_apos = n_quote = 0
    prev_char = ''
    for i, part in enumerate(parts):
        if part.startswith('<') or '@@STASH' in part:
            if part.startswith('<'):
                prev_char = '>'
            continue
        n_apos += part.count("'")
        n_quote += part.count('"')
        part = part.replace("'", '’')
        part = smart_double_quotes(part, prev_char)
        if part:
            prev_char = part[-1]
        parts[i] = part
    body = ''.join(parts)

    # Prose rendered from JS string literals is user-visible too. Only touch
    # apostrophes inside double-quoted literals, which cannot terminate them.
    for i, block in enumerate(stash):
        fixed = re.sub(r'"[^"\n]*"', lambda m: m.group(0).replace("'", '’'), block)
        n_apos += block.count("'") - fixed.count("'")
        body = body.replace(f'@@STASH{i}@@', fixed)

    return body, n_apos, n_quote


def fix_meta(head: str) -> tuple[str, int]:
    n = 0

    def fix_attr(m):
        nonlocal n
        value = m.group(2)
        n += value.count("'")
        return m.group(1) + value.replace("'", '’') + m.group(3)

    names = '|'.join(re.escape(x) for x in META_READABLE)
    head = re.sub(
        rf'(<meta[^>]*?(?:name|property)="(?:{names})"[^>]*?content=")([^"]*)(")',
        fix_attr, head)
    head = re.sub(r'(<title>)([^<]*)(</title>)', fix_attr, head)
    return head, n


def fix_dashes(body: str) -> tuple[str, int]:
    """Wrap each em dash with the word before it.

    Already-wrapped dashes are preceded by '>', which [^\\s<>]+ cannot match,
    so re-running this is a no-op. <script>/<style> are skipped: em dashes in
    code comments are never rendered.
    """
    stash = []

    def keep(m):
        stash.append(m.group(0))
        return f'@@STASH{len(stash) - 1}@@'

    body = re.sub(r'<(script|style)\b.*?</\1>', keep, body, flags=re.S)

    body, n = re.subn(
        r'([^\s<>]+)(?:&mdash;|—)',
        r'<span class="nobr">\1<span class="emdash">&mdash;</span></span>',
        body)

    for i, block in enumerate(stash):
        body = body.replace(f'@@STASH{i}@@', block)
    return body, n


def process(path: str, check_only: bool) -> tuple[bool, str]:
    src = open(path, encoding='utf-8').read()
    if '<body' not in src:
        return False, ''

    head, rest = src.split('<body', 1)
    body = '<body' + rest

    head, n_meta = fix_meta(head)
    body, n_apos, n_quote = fix_prose(body)
    body, n_dash = fix_dashes(body)

    new = head + body
    if new == src:
        return False, ''

    bits = []
    if n_apos or n_meta:
        bits.append(f"{n_apos + n_meta} apostrophe{'s' if n_apos + n_meta != 1 else ''}")
    if n_quote:
        bits.append(f'{n_quote} double quote{"s" if n_quote != 1 else ""}')
    if n_dash:
        bits.append(f'{n_dash} em dash{"es" if n_dash != 1 else ""}')

    if not check_only:
        open(path, 'w', encoding='utf-8').write(new)
    return True, ', '.join(bits)


def main() -> int:
    check_only = '--check' in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    targets = sorted(set(glob.glob('*.html') + glob.glob('essays/*.html')))
    changed = []
    for path in targets:
        did, summary = process(path, check_only)
        if did:
            changed.append((path, summary))

    if not changed:
        print(f'typography: clean ({len(targets)} files)')
        return 0

    verb = 'needs' if check_only else 'fixed'
    for path, summary in changed:
        print(f'typography: {path} {verb} {summary}')
    if check_only:
        print('\nRun: python3 tools/typography.py')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
