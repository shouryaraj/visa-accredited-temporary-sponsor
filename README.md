# Accredited Sponsors Viewer

A web app to browse and search the Australian Government's list of Accredited Temporary Resident (Skilled Employment) Sponsors, released via FOI by the Department of Home Affairs.

---

## How It Works

### Pipeline: PDF → JSON → Web

```
PDF (scanned image)
  └─► extract.py          OCR each page using Tesseract
        └─► data/sponsors_YYYY-MM-DD.json    Canonical versioned data
              └─► NestJS API (/api/versions, /api/sponsors/:version)
                    └─► index.html           Version selector + search + pagination
```

**Step 1 — OCR extraction** (`extract.py`)
The PDFs released by Home Affairs are scanned images, not selectable text. The script converts each page to an image using `poppler`, then runs `tesseract` OCR on it to extract raw text line by line.

**Step 2 — Cleaning**
Raw OCR output contains noise: page numbers, header fragments, smart-quote artifacts. The script strips these using regex rules and deduplicates entries case-insensitively.

**Step 3 — Save as JSON**
Each version is saved as a structured JSON file in `data/` with metadata (version date, FOI reference, source attribution, license).

**Step 4 — Serve via NestJS**
The API reads JSON files from `data/` at runtime:
- `GET /api/versions` — lists all available versions with metadata
- `GET /api/sponsors/:version` — returns the full sponsor list for that version

The frontend fetches these endpoints and renders a paginated, searchable table.

---

## Adding a New Version

When a new PDF is released by Home Affairs:

**1. Download the PDF**
Get the latest FOI release from the Home Affairs FOI disclosure log.

**2. Run the pipeline**
```bash
python3 extract.py ~/Downloads/"Accredited Sponsors List Jul 2025.pdf"
```

The script auto-detects the date from the filename. If it can't, pass it manually:
```bash
python3 extract.py ~/Downloads/sponsors.pdf --date 2025-07-01 --foi "FA 25/07/00001"
```

Options:
| Flag | Default | Description |
|---|---|---|
| `--date` | auto from filename | Version date `YYYY-MM-DD` |
| `--foi` | *(empty)* | FOI reference printed on the document |
| `--dpi` | `150` | OCR resolution — increase to `200` for better accuracy on low-quality scans |
| `--output` | `./data` | Output directory |

**3. Rebuild and restart**
```bash
npm run build
npm run start:prod
```

The new version appears automatically in the version dropdown — no code changes needed.

---

## Running Locally

**Prerequisites**
```bash
brew install poppler tesseract
pip3 install pdf2image pytesseract Pillow
npm install
```

**Start the server**
```bash
npm run build
npm run start:prod
```

Open [http://localhost:3000](http://localhost:3000).

For development with auto-reload:
```bash
npm run start:dev
```

---

## Project Structure

```
visa-list/
├── extract.py                    # Pipeline: PDF → JSON
├── src/
│   ├── main.ts                   # NestJS bootstrap, serves static files on :3000
│   ├── app.module.ts
│   └── sponsors/
│       ├── sponsors.controller.ts  # API route handlers
│       ├── sponsors.service.ts     # Reads JSON from data/
│       ├── sponsors.module.ts
│       └── sponsors.types.ts       # Shared TypeScript interfaces
├── public/
│   └── index.html                # Frontend — version selector, search, pagination
├── data/
│   └── sponsors_YYYY-MM-DD.json  # One file per version (add more by running extract.py)
├── package.json
└── tsconfig.json
```

---

## Deploying to Railway

The setup mirrors the `badminton-rotation` project — same Dockerfile strategy, same `railway.toml` structure.

**First deploy**
1. Push the repo to GitHub
2. Create a new project on [railway.app](https://railway.app) → Deploy from GitHub repo
3. Railway picks up `railway.toml` automatically and builds via Dockerfile

**Adding a new sponsor version**
```bash
python3 extract.py ~/Downloads/"Accredited Sponsors List Jul 2025.pdf"
git add data/sponsors_2025-07-01.json
git commit -m "Add July 2025 sponsor list"
git push
```
Railway redeploys automatically. The new version appears in the dropdown.

**No database required** — unlike `badminton-rotation` which uses MongoDB, all data here is JSON files committed to git and baked into the Docker image at build time.

---

## Data & Compliance

- **Source**: Department of Home Affairs, released under the *Freedom of Information Act 1982 (Cth)*
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution**: Credit "Department of Home Affairs" and include the FOI reference when republishing
- **Accuracy**: Data reflects accreditation status as at the document date — not a live register
- **Not affiliated** with the Australian Government
