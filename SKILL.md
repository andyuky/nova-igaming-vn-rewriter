---
name: nova-igaming-vn-rewriter
description: Rewrite Vietnamese i-gaming content (casino, sports betting, promotions, VIP) using Nova v8.1.8.1 operators. Optimizes for AIO/SGE visibility, SERP rankings, with mandatory responsible gaming safeguards. Supports formal/casual tone, offshore/licensed operator differentiation. Includes HTML parsing, rewriting, and rollback capabilities.
---

# Nova i-Gaming Vietnamese Rewriter

Rewrite i-gaming content for Vietnamese market with SEO optimization and ethical compliance.

## When to Use

- Rewriting casino/slots game descriptions
- Sports betting content (odds, handicap, match previews)
- Promotional copy (bonuses, welcome offers, VIP programs)
- Responsible gaming disclaimers
- Content localization for Vietnamese audience
- **HTML page rewriting with rollback support**

## Core Pipeline

```
INPUT → Δ(extract) → Σ(segment) → Ω(structure) → ⊗(de-cliché) → NAE(archetype) → VN_MAP → EGM(ethics) → SEO → OUTPUT
```

## Quick Reference

| Operator | Purpose |
|----------|---------|
| Δ | Extract core meaning, strip marketing noise |
| Σ | Segment by player journey (discover→decide→act) |
| Ω | Structure as flowing prose (no bullet dumps) |
| ⊗ | Remove clichés ("free spins", "instant win") |
| NAE | Apply narrative archetype (Hero, Problem-Solution) |
| ⊕TITLE_DOM | Craft SEO-optimized Vietnamese titles |
| **P1_SEO** | First paragraph with keywords, entities, LSIs, semantic triples |

## Ethical Firewall (Mandatory)

Three-layer guard for gambling content:
1. **CITADEL**: Block manipulative CTAs
2. **ERC**: Soften absolutes, no fear-based framing
3. **ΞETHIC**: Hard-stop on 🔴 violations

All odds/claims require E (Evidence) operator validation.

## Tone Selection

| Context | Tone | Use |
|---------|------|-----|
| Regulatory/age gates | Formal | "Chỉ dành cho người 18 tuổi trở lên" |
| Promotions/games | Casual | Friendly, excitement-driven |
| Responsible gaming | Formal | Official warnings, support links |

## Operator Type

| Type | Messaging Focus |
|------|-----------------|
| Licensed | Emphasize regulatory badges, government approval |
| Offshore | Trust signals, player reviews, security features |

## References

Load as needed:
- `references/nova-operators.md` - Full operator definitions + pipeline
- `references/vietnamese-glossary.md` - Gaming terminology + cultural mapping
- `references/ethical-guidelines.md` - Three-layer firewall + safeguards
- `references/seo-patterns.md` - AIO/SGE optimization patterns
- `references/content-pipeline.md` - Detailed rewrite workflow

## Workflow

See `workflows/rewrite-workflow.md` for step-by-step process.

## Output Formats

| Format | Length | Use Case |
|--------|--------|----------|
| EXP-LITE | 120-150w | Standard promo copy |
| MICRO_EXP | <60w | AIO snippets, mobile |
| EXP | 300-400w | Detailed game reviews |

**CRITICAL: All output must be 100% Vietnamese.** Only brand names (e.g., "Liverpool", "Man United") remain in original form. Headers, labels, metadata, CTAs - all Vietnamese.

## Quality Checks

Before output:
- [ ] ΣLINT: No prohibited phrases ("guaranteed", "risk-free")
- [ ] EGM: Ethics gradient 🟢 (or justify 🟡)
- [ ] E: All odds/claims have source citations
- [ ] VN_MAP: Cultural nuances applied (lucky numbers, colors)
- [ ] SEO: Title + meta optimized for Vietnamese SERP

## HTML Rewriting (Scripts)

**Requires:** `pip install beautifulsoup4`

### Single File Processing

#### Step 1: Parse HTML
```bash
python scripts/html-parser.py path/to/page.html
```
Creates: `page_meta.json` + backup

#### Step 2: Rewrite Content
Use AI to rewrite sections in metadata file.

#### Step 3: Update HTML
```bash
python scripts/html-updater.py path/to/page_meta.json
```

#### Rollback (if failed)
```bash
python scripts/html-updater.py path/to/page_meta.json --rollback
```

### Batch Processing (Folder + Subfolders)

Process all HTML files in a folder and all subfolders:

```bash
# Parse all HTML files (recursive)
python scripts/batch-processor.py /path/to/html/folder

# Custom output directory
python scripts/batch-processor.py /path/to/folder -o /output/dir

# Check status
python scripts/batch-processor.py --status /output/batch_manifest.json

# Resume interrupted batch
python scripts/batch-processor.py --resume /output/batch_manifest.json

# List files by status
python scripts/batch-processor.py --list /output/batch_manifest.json --filter parsed
```

**Output structure:**
```
<folder>/.nova-meta/
├── batch_manifest.json    # Tracks all files
├── page1_meta.json        # Individual metadata
├── page2_meta.json
└── subfolder/
    └── page3_meta.json
```

See `workflows/html-rewrite-workflow.md` for detailed process.
