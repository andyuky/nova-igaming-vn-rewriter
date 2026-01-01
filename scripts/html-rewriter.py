#!/usr/bin/env python3
"""
HTML Rewriter - Prepares sections for Claude Code rewriting
Creates a template file that Claude Code can process directly.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Prepare sections for Claude Code rewriting')
    parser.add_argument('meta_file', help='Path to metadata JSON from html-parser.py')
    parser.add_argument('--sections', type=str, help='Comma-separated section indices (e.g., "0,1,2")')
    args = parser.parse_args()

    meta_path = Path(args.meta_file).resolve()
    if not meta_path.exists():
        print(f"ERROR: Metadata file not found: {meta_path}")
        sys.exit(1)

    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    sections = metadata.get('sections', [])

    # Parse section filter
    section_filter = None
    if args.sections:
        section_filter = set(int(x.strip()) for x in args.sections.split(','))

    print(f"📄 Loaded {len(sections)} sections")
    print("\n" + "="*60)
    print("Hãy sử dụng Claude Code để viết lại các sections sau:")
    print("="*60)

    for sec in sections:
        if section_filter and sec['index'] not in section_filter:
            continue

        print(f"\n### Section [{sec['index']}] - {sec.get('heading_tag', 'intro')}")
        print(f"**Heading:** {sec['heading_text']}")
        print("**Content:**")
        for para in sec.get('paragraphs', []):
            print(f"  - {para['text'][:100]}..." if len(para['text']) > 100 else f"  - {para['text']}")

    print("\n" + "="*60)
    print("Sau khi viết lại, lưu vào metadata với format:")
    print('  section["rewritten_heading"] = "..."')
    print('  section["rewritten_content"] = "..."')
    print("="*60)


if __name__ == "__main__":
    main()
