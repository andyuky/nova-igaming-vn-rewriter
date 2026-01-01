#!/usr/bin/env python3
"""
Batch Processor for HTML Content Rewriting
Processes all HTML files in a folder and subfolders through the Nova i-Gaming rewriting pipeline.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    print("ERROR: beautifulsoup4 required. Install: pip install beautifulsoup4")
    sys.exit(1)


def find_html_files(folder: str, pattern: str = "*.html") -> list:
    """Find all HTML files in folder and subfolders (recursive by default)."""
    folder_path = Path(folder)
    if not folder_path.exists():
        return []
    # Always recursive
    return sorted(folder_path.rglob(pattern))


def create_batch_manifest(folder: str, output_dir: str, files: list) -> dict:
    """Create manifest tracking all files to process."""
    manifest = {
        "source_folder": str(Path(folder).resolve()),
        "output_dir": str(Path(output_dir).resolve()),
        "created_at": datetime.now().isoformat(),
        "total_files": len(files),
        "status": "pending",
        "files": []
    }

    for html_file in files:
        # Preserve relative path structure
        rel_path = html_file.relative_to(folder)
        manifest["files"].append({
            "source": str(html_file.resolve()),
            "relative_path": str(rel_path),
            "name": html_file.name,
            "meta_file": None,
            "status": "pending",
            "sections": 0,
            "error": None
        })

    return manifest


def save_manifest(manifest: dict, manifest_path: str):
    """Save manifest to JSON file."""
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def load_manifest(manifest_path: str) -> dict:
    """Load existing manifest."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_html_file(html_path: Path, output_dir: Path, preserve_structure: bool = True) -> dict:
    """Parse a single HTML file and extract sections."""
    # Determine output location
    if preserve_structure:
        # Keep same folder structure
        rel_parent = html_path.parent.name
        meta_dir = output_dir / rel_parent
    else:
        meta_dir = output_dir

    meta_dir.mkdir(parents=True, exist_ok=True)

    # Create backup in source folder
    backup_dir = html_path.parent / ".nova-backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"{html_path.stem}_{timestamp}.html.bak"
    backup_path = backup_dir / backup_name
    shutil.copy2(html_path, backup_path)

    # Parse HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract meta
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
    for tag in content_soup(['script', 'style', 'nav', 'footer', 'aside', 'noscript', 'iframe', 'header']):
        tag.decompose()

    body = content_soup.find('body')
    sections = []

    if body:
        main_content = (
            body.find('main') or
            body.find('article') or
            body.find(class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'entry', 'post'])) or
            body
        )

        current_section = None
        section_index = 0

        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            tag_name = element.name
            text = element.get_text(strip=True)

            if not text or len(text) < 10:
                continue

            heading_level = 0
            if tag_name and tag_name.startswith('h') and len(tag_name) == 2:
                try:
                    heading_level = int(tag_name[1])
                except ValueError:
                    pass

            if heading_level > 0:
                if current_section and current_section['paragraphs']:
                    sections.append(current_section)
                    section_index += 1

                current_section = {
                    "index": section_index,
                    "heading_tag": tag_name,
                    "heading_level": heading_level,
                    "heading_text": text,
                    "heading_classes": element.get('class', []),
                    "paragraphs": []
                }
            elif current_section:
                current_section['paragraphs'].append({
                    "text": text,
                    "classes": element.get('class', [])
                })
            else:
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

        if current_section and current_section['paragraphs']:
            sections.append(current_section)

    # Save metadata
    meta_path = meta_dir / f"{html_path.stem}_meta.json"
    metadata = {
        "source_file": str(html_path.resolve()),
        "backup_path": str(backup_path),
        "original_title": title,
        "original_description": description,
        "sections": sections,
        "total_sections": len(sections),
        "extracted_at": datetime.now().isoformat(),
        "status": "pending_rewrite"
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        "meta_file": str(meta_path),
        "sections": len(sections),
        "backup": str(backup_path)
    }


def process_folder(folder: str, output_dir: str = None, resume: str = None) -> dict:
    """Process all HTML files in folder and subfolders."""
    folder_path = Path(folder).resolve()
    output_path = Path(output_dir).resolve() if output_dir else folder_path / ".nova-meta"
    output_path.mkdir(parents=True, exist_ok=True)

    manifest_path = output_path / "batch_manifest.json"

    # Resume from existing manifest or create new
    if resume and Path(resume).exists():
        manifest = load_manifest(resume)
        print(f"📂 Resuming from: {resume}")
    else:
        html_files = find_html_files(folder)
        if not html_files:
            print(f"❌ No HTML files found in: {folder}")
            return {"error": "No HTML files found"}

        manifest = create_batch_manifest(str(folder_path), str(output_path), html_files)
        save_manifest(manifest, str(manifest_path))
        print(f"📂 Source: {folder_path}")
        print(f"📁 Output: {output_path}")
        print(f"📋 Manifest: {manifest_path}")

    # Count by status
    stats = {"pending": 0, "parsed": 0, "rewritten": 0, "updated": 0, "failed": 0}
    for f in manifest["files"]:
        status = f.get("status", "pending")
        stats[status] = stats.get(status, 0) + 1

    print(f"\n📊 Files: {manifest['total_files']} total, {stats['pending']} pending")

    # Process pending files
    results = {"parsed": 0, "failed": 0, "skipped": manifest['total_files'] - stats['pending']}

    for i, file_info in enumerate(manifest["files"]):
        if file_info["status"] != "pending":
            continue

        source = Path(file_info["source"])
        rel_path = file_info.get("relative_path", source.name)
        print(f"\n[{i+1}/{manifest['total_files']}] {rel_path}")

        try:
            result = parse_html_file(source, output_path, preserve_structure=True)
            file_info["meta_file"] = result["meta_file"]
            file_info["sections"] = result["sections"]
            file_info["status"] = "parsed"
            results["parsed"] += 1
            print(f"  ✓ {result['sections']} sections → {Path(result['meta_file']).name}")
        except Exception as e:
            file_info["status"] = "failed"
            file_info["error"] = str(e)
            results["failed"] += 1
            print(f"  ✗ Error: {e}")

        # Save progress after each file
        save_manifest(manifest, str(manifest_path))

    # Update manifest status
    if results["failed"] == 0 and stats["pending"] > 0:
        manifest["status"] = "parsed"
    elif results["failed"] > 0:
        manifest["status"] = "partial"
    manifest["completed_at"] = datetime.now().isoformat()
    save_manifest(manifest, str(manifest_path))

    return {
        "manifest": str(manifest_path),
        "output_dir": str(output_path),
        "results": results
    }


def show_status(manifest_path: str):
    """Show detailed status of batch processing."""
    manifest = load_manifest(manifest_path)

    stats = {"pending": 0, "parsed": 0, "rewritten": 0, "updated": 0, "failed": 0}
    total_sections = 0

    for f in manifest["files"]:
        status = f.get("status", "pending")
        stats[status] = stats.get(status, 0) + 1
        total_sections += f.get("sections", 0)

    print(f"\n📊 Batch Status: {manifest['status'].upper()}")
    print(f"   Source: {manifest['source_folder']}")
    print(f"   Output: {manifest['output_dir']}")
    print(f"\n   Total files: {manifest['total_files']}")
    print(f"   Total sections: {total_sections}")
    print(f"\n   ⏳ Pending: {stats['pending']}")
    print(f"   📄 Parsed: {stats['parsed']}")
    print(f"   ✍️  Rewritten: {stats['rewritten']}")
    print(f"   ✅ Updated: {stats['updated']}")
    print(f"   ❌ Failed: {stats['failed']}")

    if stats['failed'] > 0:
        print("\n❌ Failed files:")
        for f in manifest["files"]:
            if f.get("status") == "failed":
                print(f"   - {f['relative_path']}: {f.get('error', 'Unknown')}")

    # Show next steps
    if stats['parsed'] > 0 and stats['rewritten'] == 0:
        print(f"\n📝 Next: Rewrite content using html-rewriter.py on meta files")
        print(f"   Example: python html-rewriter.py {manifest['output_dir']}/<name>_meta.json")


def list_files(manifest_path: str, status_filter: str = None):
    """List files in manifest with optional status filter."""
    manifest = load_manifest(manifest_path)

    print(f"\n📋 Files in batch ({manifest['total_files']} total):\n")

    for f in manifest["files"]:
        file_status = f.get("status", "pending")
        if status_filter and file_status != status_filter:
            continue

        icon = {"pending": "⏳", "parsed": "📄", "rewritten": "✍️", "updated": "✅", "failed": "❌"}.get(file_status, "?")
        sections = f.get("sections", 0)
        print(f"  {icon} [{file_status:10}] {f['relative_path']} ({sections} sections)")


def main():
    parser = argparse.ArgumentParser(
        description='Batch process all HTML files in a folder (recursive)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse all HTML files in folder and subfolders
  python batch-processor.py /path/to/html/folder

  # Custom output directory
  python batch-processor.py /path/to/folder -o /output/dir

  # Resume from manifest
  python batch-processor.py --resume /output/batch_manifest.json

  # Check status
  python batch-processor.py --status /output/batch_manifest.json

  # List parsed files
  python batch-processor.py --list /output/batch_manifest.json --filter parsed
        """
    )
    parser.add_argument('folder', nargs='?', help='Folder containing HTML files (processes all subfolders)')
    parser.add_argument('-o', '--output', help='Output directory for metadata (default: <folder>/.nova-meta)')
    parser.add_argument('--resume', help='Resume from existing manifest')
    parser.add_argument('--status', help='Show status of batch manifest')
    parser.add_argument('--list', help='List files in manifest')
    parser.add_argument('--filter', help='Filter by status (pending/parsed/rewritten/updated/failed)')

    args = parser.parse_args()

    # Status command
    if args.status:
        show_status(args.status)
        return

    # List command
    if args.list:
        list_files(args.list, args.filter)
        return

    # Process command
    if not args.folder and not args.resume:
        parser.print_help()
        sys.exit(1)

    folder = args.folder or str(Path(args.resume).parent.parent)

    result = process_folder(
        folder=folder,
        output_dir=args.output,
        resume=args.resume
    )

    if "error" in result:
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"✅ Batch parsing complete!")
    print(f"   Parsed: {result['results']['parsed']}")
    print(f"   Failed: {result['results']['failed']}")
    print(f"   Skipped: {result['results']['skipped']}")
    print(f"\n📋 Manifest: {result['manifest']}")
    print(f"\n📝 Next: Run html-rewriter.py on meta files, then html-updater.py")


if __name__ == "__main__":
    main()
