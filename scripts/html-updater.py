#!/usr/bin/env python3
"""
HTML Updater for Section-based Content Rewriting
Replaces content by matching sections (heading + paragraphs).
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("ERROR: beautifulsoup4 required. Install: pip install beautifulsoup4")
    sys.exit(1)


def find_heading_element(soup, heading_text: str, heading_tag: str):
    """Find heading element by matching text content."""
    if not heading_tag or heading_text == "[Intro]":
        return None

    normalized_target = ' '.join(heading_text.split())

    for element in soup.find_all(heading_tag):
        element_text = element.get_text(strip=True)
        normalized_element = ' '.join(element_text.split())

        # Exact match
        if normalized_element == normalized_target:
            return element

        # Partial match for long headings
        if len(normalized_target) > 30 and len(normalized_element) > 30:
            if normalized_element[:30] == normalized_target[:30]:
                return element

        # Contained match (for nested span structures)
        if normalized_target in normalized_element or normalized_element in normalized_target:
            shorter = min(len(normalized_target), len(normalized_element))
            longer = max(len(normalized_target), len(normalized_element))
            if shorter / longer > 0.8:
                return element

    return None


def get_section_paragraphs(heading_element, next_heading_tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
    """Get all paragraphs between this heading and the next heading."""
    paragraphs = []
    if not heading_element:
        return paragraphs

    # Walk through siblings after the heading
    current = heading_element.find_next_sibling()
    while current:
        # Stop if we hit another heading
        if current.name in next_heading_tags:
            break
        # Collect paragraphs
        if current.name == 'p':
            paragraphs.append(current)
        # Also check for paragraphs inside divs/sections
        elif current.name in ['div', 'section', 'article']:
            for p in current.find_all('p', recursive=True):
                paragraphs.append(p)
                # Only get paragraphs until next heading inside
                if current.find(next_heading_tags):
                    break
        current = current.find_next_sibling()

    return paragraphs


def find_paragraph_by_text(paragraphs, target_text: str):
    """Find paragraph by fuzzy text matching."""
    normalized_target = ' '.join(target_text.split())[:100]  # First 100 chars

    for p in paragraphs:
        p_text = ' '.join(p.get_text(strip=True).split())[:100]
        # Fuzzy match: check if significant overlap
        if normalized_target[:50] == p_text[:50]:
            return p
        # Also try contains match for shorter texts
        if len(normalized_target) > 20 and normalized_target[:30] in p_text:
            return p
    return None


def replace_element_text(element, new_text: str) -> bool:
    """Replace text content while preserving structure."""
    if not element:
        return False

    # Simple text replacement if no children
    if not element.find_all():
        element.string = new_text
        return True

    # Look for text-containing spans
    text_span = element.find('span', class_=lambda x: x and any(
        c in str(x).lower() for c in ['title', 'main', 'text', 'content']
    ))
    if text_span:
        if text_span.string:
            text_span.string = new_text
            return True
        # Clear and add new text
        text_span.clear()
        text_span.append(new_text)
        return True

    # Try any span with substantial text
    for child in element.find_all(['span', 'a']):
        if child.string and len(child.string.strip()) > 10:
            child.string = new_text
            return True

    # Replace first text node
    for child in element.children:
        if isinstance(child, NavigableString) and child.strip():
            child.replace_with(new_text)
            return True

    # Last resort: clear and add text
    element.clear()
    element.append(new_text)
    return True


def find_first_content_paragraph(soup):
    """Find the first main content paragraph (intro paragraph)."""
    # Strategy 1: Look for main content container with text class
    text_container = soup.find('div', class_=lambda x: x and 'text' in str(x).lower())
    if text_container:
        first_p = text_container.find('p')
        if first_p:
            return first_p

    # Strategy 2: Look for j-scrollbox or similar content container
    scrollbox = soup.find('div', class_='j-scrollbox')
    if scrollbox:
        first_p = scrollbox.find('p')
        if first_p:
            return first_p

    # Strategy 3: Find first paragraph in main/article/body
    main = soup.find(['main', 'article']) or soup.find('body')
    if main:
        # Skip paragraphs that are likely navigation or header content
        for p in main.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Substantial content
                return p

    return None


def update_section(soup, section: dict) -> dict:
    """Update a single section in the HTML."""
    stats = {"heading": False, "paragraphs": 0}

    heading_text = section.get('heading_text', '')
    heading_tag = section.get('heading_tag')
    rewritten_heading = section.get('rewritten_heading', heading_text)
    rewritten_content = section.get('rewritten_content', '')
    section_index = section.get('index', -1)

    if not rewritten_content:
        return stats

    # Find and update heading
    heading_element = None
    if heading_tag and heading_text != "[Intro]":
        heading_element = find_heading_element(soup, heading_text, heading_tag)
        if heading_element and rewritten_heading != heading_text:
            if replace_element_text(heading_element, rewritten_heading):
                stats["heading"] = True

    # Split rewritten content into paragraphs
    rewritten_paragraphs = [p.strip() for p in rewritten_content.split('\n\n') if p.strip()]

    if not rewritten_paragraphs:
        return stats

    # Get original paragraph info for matching
    original_paragraphs = section.get('paragraphs', [])

    # Strategy 0: For first section (index 0), find intro paragraph directly
    if section_index == 0 and rewritten_paragraphs:
        first_para = find_first_content_paragraph(soup)
        if first_para:
            # Clear the paragraph and rebuild with simple structure
            first_para.clear()
            first_para.string = rewritten_paragraphs[0]
            stats["paragraphs"] += 1
            # Handle remaining paragraphs if any
            rewritten_paragraphs = rewritten_paragraphs[1:]

    # Strategy 1: Try to find section paragraphs by position (for main content)
    if heading_element:
        section_paras = get_section_paragraphs(heading_element)

        # Match original paragraphs to section paragraphs by text
        for i, orig_para in enumerate(original_paragraphs):
            if i >= len(rewritten_paragraphs):
                break

            # Try fuzzy match in section paragraphs
            para_element = find_paragraph_by_text(section_paras, orig_para['text'])
            if para_element:
                if replace_element_text(para_element, rewritten_paragraphs[i]):
                    stats["paragraphs"] += 1
                    # Remove from list to avoid re-matching
                    section_paras.remove(para_element)
            # Fallback: replace by position if same count
            elif i < len(section_paras):
                if replace_element_text(section_paras[i], rewritten_paragraphs[i]):
                    stats["paragraphs"] += 1

    # Strategy 2: For blog excerpts (h5), find by class
    if heading_tag == 'h5' and heading_element:
        # Look for excerpt paragraph near the heading
        parent = heading_element.find_parent(['div', 'article', 'section'])
        if parent:
            excerpt = parent.find('p', class_=lambda x: x and 'excerpt' in str(x).lower())
            if excerpt and rewritten_paragraphs:
                if replace_element_text(excerpt, rewritten_paragraphs[0]):
                    stats["paragraphs"] += 1

    return stats


def update_html(html_path: str, metadata: dict) -> dict:
    """Update HTML with rewritten content."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    stats = {
        "title": False,
        "description": False,
        "sections": 0,
        "headings": 0,
        "paragraphs": 0
    }

    # Update title
    if metadata.get('rewritten_title'):
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = metadata['rewritten_title']
            stats["title"] = True

    # Update meta description
    if metadata.get('rewritten_description'):
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_desc['content'] = metadata['rewritten_description']
            stats["description"] = True

    # Update sections
    for section in metadata.get('sections', []):
        if not section.get('rewritten_content'):
            continue

        section_stats = update_section(soup, section)
        if section_stats["heading"] or section_stats["paragraphs"] > 0:
            stats["sections"] += 1
            stats["headings"] += 1 if section_stats["heading"] else 0
            stats["paragraphs"] += section_stats["paragraphs"]

    # Add responsible gaming notice
    existing_notice = soup.find(class_='responsible-gaming-notice')
    if existing_notice:
        existing_notice.decompose()

    body = soup.find('body')
    if body:
        notice = soup.new_tag('div', attrs={'class': 'responsible-gaming-notice'})
        notice['style'] = 'position:fixed;bottom:0;left:0;right:0;padding:10px 15px;background:#1a1a1a;border-top:3px solid #e74c3c;color:#fff;font-size:12px;z-index:9999;text-align:center;'

        notice_text = soup.new_tag('span')
        notice_text.string = '⚠️ Chỉ dành cho người từ 18 tuổi trở lên | Chơi có trách nhiệm | Đặt giới hạn thời gian và tiền bạc'
        notice.append(notice_text)

        body.append(notice)

    # Save HTML (minimal formatting to preserve original structure)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    return stats


def rollback(meta_path: str) -> bool:
    """Rollback to original HTML from backup."""
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    backup_path = Path(metadata['backup_path'])
    source_path = Path(metadata['source_file'])

    if not backup_path.exists():
        print(f"ERROR: Backup not found: {backup_path}")
        return False

    shutil.copy2(backup_path, source_path)
    return True


def update_metadata(meta_path: str, status: str, stats: dict = None):
    """Update metadata status."""
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    metadata['status'] = status
    metadata['updated_at'] = datetime.now().isoformat()
    if stats:
        metadata['update_stats'] = stats

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Update HTML with rewritten i-gaming content')
    parser.add_argument('meta_file', help='Path to metadata JSON file')
    parser.add_argument('--rollback', action='store_true', help='Rollback to original HTML')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    meta_path = Path(args.meta_file).resolve()
    if not meta_path.exists():
        print(f"ERROR: Metadata file not found: {meta_path}")
        sys.exit(1)

    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Rollback mode
    if args.rollback:
        print(f"Đang khôi phục: {metadata['source_file']}")
        if rollback(str(meta_path)):
            update_metadata(str(meta_path), 'rolled_back')
            print("✅ Đã khôi phục thành công!")
        else:
            print("❌ Khôi phục thất bại!")
            sys.exit(1)
        return

    # Check if content was rewritten
    if metadata.get('status') != 'rewritten':
        print("⚠️ Content not yet rewritten. Run html-rewriter.py first.")
        sys.exit(1)

    # Count rewritten sections
    rewritten_sections = [s for s in metadata.get('sections', []) if s.get('rewritten_content')]

    # Dry run
    if args.dry_run:
        print("\n📋 Xem trước thay đổi:")
        print(f"  Tiêu đề: {metadata.get('rewritten_title', '(không đổi)')[:50]}...")
        print(f"  Mô tả: {metadata.get('rewritten_description', '(không đổi)')[:60]}...")
        print(f"  Sections: {len(rewritten_sections)}/{len(metadata.get('sections', []))}")

        for sec in rewritten_sections[:5]:
            heading = sec['heading_text'][:40] + "..." if len(sec['heading_text']) > 40 else sec['heading_text']
            new_heading = sec.get('rewritten_heading', heading)[:40]
            print(f"    [{sec['index']}] {heading} → {new_heading}")
        if len(rewritten_sections) > 5:
            print(f"    ... và {len(rewritten_sections) - 5} sections khác")
        return

    # Update HTML
    print(f"Đang cập nhật: {metadata['source_file']}")
    try:
        stats = update_html(metadata['source_file'], metadata)
        update_metadata(str(meta_path), 'updated', stats)

        print("✅ Cập nhật thành công!")
        print(f"   Tiêu đề: {'✓' if stats['title'] else '✗'}")
        print(f"   Mô tả: {'✓' if stats['description'] else '✗'}")
        print(f"   Sections: {stats['sections']}")
        print(f"   Headings: {stats['headings']}")
        print(f"   Paragraphs: {stats['paragraphs']}")
        print(f"\n🔄 Để khôi phục: python html-updater.py {meta_path} --rollback")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("Đang tự động khôi phục...")
        if rollback(str(meta_path)):
            update_metadata(str(meta_path), 'update_failed_rolled_back')
            print("✅ Đã khôi phục thành công!")
        sys.exit(1)


if __name__ == "__main__":
    main()
