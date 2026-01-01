#!/usr/bin/env python3
"""
HTML Parser for i-Gaming Content Rewriting (Section-based)
Extracts content as sections (heading + paragraphs) for batch rewriting.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 required. Install: pip install beautifulsoup4")
    sys.exit(1)


def create_backup(html_path: str) -> str:
    """Create backup of original HTML for rollback."""
    backup_dir = Path(html_path).parent / ".nova-backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"{Path(html_path).stem}_{timestamp}.html.bak"
    backup_path = backup_dir / backup_name

    shutil.copy2(html_path, backup_path)
    return str(backup_path)


def get_heading_level(tag_name: str) -> int:
    """Get heading level from tag name (h1=1, h2=2, etc.)"""
    if tag_name and tag_name.startswith('h') and len(tag_name) == 2:
        try:
            return int(tag_name[1])
        except ValueError:
            pass
    return 0


def extract_sections(html_path: str) -> dict:
    """Extract content as sections (heading + following content)."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract meta info
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)

    description = ""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        description = meta_desc.get('content', '')

    # Create working copy for extraction
    content_soup = BeautifulSoup(str(soup), 'html.parser')

    # Remove non-content elements
    for tag in content_soup(['script', 'style', 'nav', 'footer', 'aside', 'noscript', 'iframe', 'header']):
        tag.decompose()

    body = content_soup.find('body')
    if not body:
        return {"sections": [], "title": title, "description": description}

    # Find main content area
    main_content = (
        body.find('main') or
        body.find('article') or
        body.find(class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'entry', 'post'])) or
        body
    )

    sections = []
    current_section = None
    section_index = 0

    # Iterate through all elements to build sections
    for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        tag_name = element.name
        text = element.get_text(strip=True)

        # Skip empty or very short text
        if not text or len(text) < 10:
            continue

        heading_level = get_heading_level(tag_name)

        if heading_level > 0:
            # Save previous section if exists
            if current_section and current_section['paragraphs']:
                sections.append(current_section)
                section_index += 1

            # Start new section
            current_section = {
                "index": section_index,
                "heading_tag": tag_name,
                "heading_level": heading_level,
                "heading_text": text,
                "heading_classes": element.get('class', []),
                "paragraphs": []
            }
        elif current_section:
            # Add paragraph to current section
            current_section['paragraphs'].append({
                "text": text,
                "classes": element.get('class', [])
            })
        else:
            # Paragraph before any heading - create intro section
            if not sections or sections[0].get('heading_text') != '[Intro]':
                current_section = {
                    "index": section_index,
                    "heading_tag": None,
                    "heading_level": 0,
                    "heading_text": "[Intro]",
                    "heading_classes": [],
                    "paragraphs": []
                }
            current_section['paragraphs'].append({
                "text": text,
                "classes": element.get('class', [])
            })

    # Don't forget last section
    if current_section and current_section['paragraphs']:
        sections.append(current_section)

    return {
        "source_file": html_path,
        "title": title,
        "description": description,
        "sections": sections,
        "extracted_at": datetime.now().isoformat()
    }


def save_metadata(data: dict, backup_path: str, meta_path: str):
    """Save metadata including sections for rewriter."""
    metadata = {
        "source_file": data['source_file'],
        "backup_path": backup_path,
        "original_title": data['title'],
        "original_description": data['description'],
        "sections": data['sections'],
        "total_sections": len(data['sections']),
        "extracted_at": data['extracted_at'],
        "status": "pending_rewrite"
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def print_sections_summary(sections: list):
    """Print summary of extracted sections."""
    print(f"\n📋 Extracted {len(sections)} sections:")
    for sec in sections[:10]:  # Show first 10
        para_count = len(sec['paragraphs'])
        heading = sec['heading_text'][:50] + "..." if len(sec['heading_text']) > 50 else sec['heading_text']
        print(f"  [{sec['index']}] {sec['heading_tag'] or 'intro'}: {heading} ({para_count} paragraphs)")
    if len(sections) > 10:
        print(f"  ... and {len(sections) - 10} more sections")


def main():
    parser = argparse.ArgumentParser(description='Parse HTML into sections for i-Gaming content rewriting')
    parser.add_argument('html_file', help='Path to HTML file to parse')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    args = parser.parse_args()

    html_path = Path(args.html_file).resolve()
    if not html_path.exists():
        print(f"ERROR: File not found: {html_path}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else html_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = html_path.stem
    meta_path = output_dir / f"{base_name}_meta.json"

    print(f"Đang phân tích: {html_path}")

    # Create backup
    backup_path = create_backup(str(html_path))
    print(f"Đã tạo bản sao lưu: {backup_path}")

    # Extract sections
    data = extract_sections(str(html_path))
    print(f"Đã trích xuất: {len(data['sections'])} sections")

    # Print summary
    print_sections_summary(data['sections'])

    # Save metadata
    save_metadata(data, backup_path, str(meta_path))
    print(f"\nĐã lưu metadata: {meta_path}")

    print("\n✅ Hoàn tất! Tiếp theo:")
    print(f"   python html-rewriter.py {meta_path}")


if __name__ == "__main__":
    main()
