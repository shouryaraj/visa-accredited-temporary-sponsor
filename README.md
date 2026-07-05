# Accredited Sponsors Viewer

A web app to browse and search the Australian Government's list of Accredited Temporary Resident (Skilled Employment) Sponsors, released via FOI by the Department of Home Affairs.

---

## Architecture

```
PDF (scanned image)
  └─► extract.py              OCR via Tesseract, cleans noise
        └─► public/data/
              ├── sponsors_YYYY-MM-DD.json   versioned sponsor list
              └── versions.json              index of all versions
                    └─► server.js            plain Node.js static server
                          └─► index.html     fetches JSON directly, no API layer
```

**No API layer.** The frontend fetches JSON files directly as static assets:
- `GET /data/versions.json` — list of available versions
- `GET /data/sponsors_YYYY-MM-DD.json` — sponsor list for selected version

`server.js` is a zero-dependency Node.js HTTP server. No framework, no build step — Railway deploys it from a 4-line Dockerfile.

> `src/` contains NestJS source kept for future background pipeline work (e.g. scheduled PDF ingestion) but is not part of the serving path.

---

## How the Pipeline Works

**Step 1 — OCR extraction** (`extract.py`)
Home Affairs PDFs are scanned images, not selectable text. The script converts each page to an image via `poppler`, then runs `tesseract` OCR line by line.

**Step 2 — Cleaning**
Raw OCR output has noise: page numbers, header fragments, smart-quote artifacts. Stripped using regex rules, deduplicated case-insensitively.

**Step 3 — Save JSON**
Each version is saved as `public/data/sponsors_YYYY-MM-DD.json` with metadata (FOI reference, license, source). `versions.json` is regenerated to index all available versions.

---

## Adding a New Version

When a new PDF is released by Home Affairs:

**1. Run the pipeline**
```bash
python3 extract.py ~/Downloads/"Accredited Sponsors List Jul 2025.pdf"
```

Date is auto-detected from the filename. Override if needed:
```bash
python3 extract.py ~/Downloads/sponsors.pdf --date 2025-07-01 --foi "FA 25/07/00001"
```

| Flag | Default | Description |
|---|---|---|
| `--date` | auto from filename | Version date `YYYY-MM-DD` |
| `--foi` | *(empty)* | FOI reference printed on the document |
| `--dpi` | `150` | OCR resolution — raise to `200` for low-quality scans |
| `--output` | `./public/data` | Output directory |

**2. Commit and push**
```bash
git add public/data/
git commit -m "Add July 2025 sponsor list"
git push
```

Railway redeploys automatically. The new version appears in the dropdown — no code changes needed.

---

## Running Locally

**Prerequisites (for extract.py)**
```bash
brew install poppler tesseract
pip3 install pdf2image pytesseract Pillow
```

**Start the server**
```bash
node server.js
```

Open [http://localhost:3000](http://localhost:3000).

---

## Project Structure

```
visa-list/
├── extract.py                     # Pipeline: PDF → public/data/
├── server.js                      # Zero-dependency static file server
├── public/
│   ├── index.html                 # Frontend — version selector, search, pagination
│   └── data/
│       ├── versions.json          # Auto-generated index of all versions
│       └── sponsors_YYYY-MM-DD.json  # One file per FOI release
├── src/                           # NestJS (future background pipeline)
│   ├── main.ts
│   ├── app.module.ts
│   └── sponsors/
├── Dockerfile                     # node:20-alpine, copy + run — no build step
├── railway.toml
└── package.json
```

---

## Deployment (Railway)

Dockerfile is intentionally minimal — no build step, no npm install:

```dockerfile
FROM node:20-alpine
COPY server.js ./
COPY public/ ./public/
CMD ["node", "server.js"]
```

Push to GitHub → Railway auto-deploys. To add a new sponsor version: run `extract.py`, commit `public/data/`, push.

---

## Data & Compliance

- **Source**: Department of Home Affairs, released under the *Freedom of Information Act 1982 (Cth)*
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution**: Credit "Department of Home Affairs" and include the FOI reference when republishing
- **Accuracy**: Data reflects accreditation status as at the document date — not a live register
- **Not affiliated** with the Australian Government
