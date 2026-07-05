#!/usr/bin/env python3
"""
Accredited Sponsors Pipeline: PDF → JSON → data/versions.js

Usage:
    python3 extract.py <pdf_path> [options]

Options:
    --date   YYYY-MM-DD   Date of the list (auto-detected from filename if omitted)
    --foi    "FA 25/..."  FOI reference number printed on the document
    --dpi    INT          OCR resolution (default: 150, higher = slower + more accurate)
    --output DIR          Data directory (default: ./data)

Examples:
    python3 extract.py ~/Downloads/"Accredited Sponsors List Jan 15 2025.pdf"
    python3 extract.py ~/Downloads/sponsors_jul_2025.pdf --date 2025-07-01 --foi "FA 25/07/00001"
    python3 extract.py ~/Downloads/sponsors.pdf --dpi 200  # better OCR quality

After running, open index.html in your browser.
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Step 1: Date detection
# ---------------------------------------------------------------------------

_MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def parse_date_from_filename(filename):
    name = filename.lower()
    # ISO: 2025-01-15
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # "Jan 15 2025" or "January 15 2025"
    for mon, num in _MONTHS.items():
        m = re.search(rf'{mon}\w*\s+(\d{{1,2}})\s+(\d{{4}})', name)
        if m:
            return f"{m.group(2)}-{num:02d}-{int(m.group(1)):02d}"
    # "15 Jan 2025"
    for mon, num in _MONTHS.items():
        m = re.search(rf'(\d{{1,2}})\s+{mon}\w*\s+(\d{{4}})', name)
        if m:
            return f"{m.group(2)}-{num:02d}-{int(m.group(1)):02d}"
    return None


def format_label(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%-d %B %Y')
    except Exception:
        return date_str


# ---------------------------------------------------------------------------
# Step 2: OCR extraction
# ---------------------------------------------------------------------------

def _find_poppler():
    for p in ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin']:
        if os.path.exists(os.path.join(p, 'pdftoppm')):
            return p
    return None


def extract_text_from_pdf(pdf_path, dpi=150):
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        sys.exit(
            "ERROR: Missing packages.\n"
            "  pip3 install pdf2image pytesseract Pillow\n"
            "  brew install poppler tesseract"
        )

    poppler_path = _find_poppler()
    if not poppler_path:
        sys.exit(
            "ERROR: poppler not found.\n"
            "  brew install poppler"
        )

    print(f"  Converting PDF pages at {dpi} DPI…")
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    print(f"  {len(pages)} pages found")

    texts = []
    for i, page in enumerate(pages):
        texts.append(pytesseract.image_to_string(page))
        if (i + 1) % 10 == 0 or (i + 1) == len(pages):
            print(f"  OCR: {i+1}/{len(pages)} pages", end='\r')
    print()
    return texts


# ---------------------------------------------------------------------------
# Step 3: Cleaning
# ---------------------------------------------------------------------------

_SKIP_PATTERNS = [
    re.compile(p, re.I) for p in [
        r'^australian\s+gov',
        r'^department\s+of\s+(home|immigration)',
        r'^freedom\s+of\s+information',
        r'^list\s+of\s+accred',
        r'^released\s+by',
        r'^under\s+the\s+freedom',
        r'^source\s*:',
        r'^\d+\.\s+(source|affairs|home|department)',
        r'^act\s+\d{4}',
        r'^\d{3,}[\s,]*$',
        r'^(foi|fa)\s*\d',
    ]
]


def _clean_line(line):
    # Strip leading OCR noise: smart quotes, dashes, brackets, regular quotes
    line = line.lstrip('‘’“”—–•\'"\\-([{ \t')
    return line.strip()


def _is_valid(name):
    if not name or len(name) < 3:
        return False
    # Must contain at least 3 alpha chars
    if len(re.findall(r'[A-Za-z]', name)) < 3:
        return False
    # Skip numeric/punctuation-only lines
    if re.match(r'^[\d\s.,=\-]+$', name):
        return False
    for pat in _SKIP_PATTERNS:
        if pat.match(name):
            return False
    return True


def clean_sponsors(raw_pages):
    seen = {}
    for page_text in raw_pages:
        for line in page_text.split('\n'):
            line = _clean_line(line.strip())
            if not _is_valid(line):
                continue
            key = line.lower()
            # Keep whichever version is longer (usually cleaner)
            if key not in seen or len(line) > len(seen[key]):
                seen[key] = line

    return sorted(seen.values(), key=lambda x: x.lower())


# ---------------------------------------------------------------------------
# Step 4: Save canonical JSON
# ---------------------------------------------------------------------------

def save_version_json(sponsors, version_date, foi_ref, output_dir):
    payload = {
        "version": version_date,
        "label": format_label(version_date),
        "generated_at": date.today().isoformat(),
        "source": {
            "agency": "Department of Home Affairs",
            "document": "List of Accredited Temporary Resident (Skilled Employment) Sponsors",
            "foi_reference": foi_ref,
            "foi_act": "Freedom of Information Act 1982 (Cth)",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "license_url": "https://creativecommons.org/licenses/by/4.0/"
        },
        "total": len(sponsors),
        "sponsors": sponsors
    }

    json_path = Path(output_dir) / f"sponsors_{version_date}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {json_path}")
    return json_path


# ---------------------------------------------------------------------------
# Step 4b: Rebuild versions.json (loaded directly by the frontend)
# ---------------------------------------------------------------------------

def rebuild_versions_json(output_dir):
    output_dir = Path(output_dir)
    json_files = sorted(output_dir.glob('sponsors_*.json'), reverse=True)

    versions = []
    for jf in json_files:
        with open(jf, encoding='utf-8') as f:
            d = json.load(f)
        versions.append({
            "date": d['version'],
            "label": d.get('label', format_label(d['version'])),
            "foi":   d['source'].get('foi_reference', ''),
            "total": d['total'],
        })

    out = output_dir / 'versions.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)

    print(f"  Updated: {out}  ({len(versions)} version(s))")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Extract accredited sponsors from a PDF into versioned JSON.'
    )
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--date', help='Version date YYYY-MM-DD (auto-detected if omitted)')
    parser.add_argument('--foi', default='', help='FOI reference on the document')
    parser.add_argument('--dpi', type=int, default=150, help='OCR DPI (default: 150)')
    parser.add_argument('--output', default='public/data', help='Output directory (default: ./public/data)')
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        sys.exit(f"ERROR: File not found: {pdf_path}")

    version_date = (
        args.date
        or parse_date_from_filename(pdf_path.name)
        or date.today().isoformat()
    )

    print(f"\n{'='*50}")
    print(f"PDF     : {pdf_path.name}")
    print(f"Version : {version_date}  ({format_label(version_date)})")
    print(f"FOI ref : {args.foi or '(not specified)'}")
    print(f"Output  : {args.output}/")
    print(f"{'='*50}\n")

    Path(args.output).mkdir(exist_ok=True)

    print("Step 1/3 — OCR extraction")
    raw_pages = extract_text_from_pdf(str(pdf_path), dpi=args.dpi)

    print("\nStep 2/3 — Cleaning data")
    sponsors = clean_sponsors(raw_pages)
    print(f"  {len(sponsors)} unique sponsors")

    print("\nStep 3/3 — Saving")
    save_version_json(sponsors, version_date, args.foi, args.output)
    rebuild_versions_json(args.output)

    print(f"\nDone. Commit public/data/ and redeploy — the new version appears in the dropdown.")


if __name__ == '__main__':
    main()
