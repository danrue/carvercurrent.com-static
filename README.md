# carvercurrent.com-static

The Carver Current archive: every issue of the *Carver Gazette* / *Villager Tower*
community newsletter (Carver, Minnesota, 1983–2024) and local history documents.

- **`pub/`**: the original files, unmodified. This repo is the source of truth.
  `pub/history/Historic_Carver.pdf` is in Git LFS (it's over GitHub's 100 MB limit).
- **archive.org** serves the PDFs: one item per newsletter issue, with the
  identifier being the filename lowercased with `_` → `-`
  (`Villager_Tower_376_2021-September-October.pdf` →
  `archive.org/details/villager-tower-376-2021-september-october`).
- **GitHub Pages** serves a small front end (~4 MB) that links to archive.org.
  Old `/pub/...` URLs from the nginx site redirect to archive.org via `404.html`.

## Build and preview

```
python3 tools/build_site.py
python3 -m http.server -d _site
```

Pushing to `main` deploys via `.github/workflows/pages.yml` (Settings → Pages →
Source: GitHub Actions). The PDFs are never part of the published site.

## Uploading issues to archive.org

```
brew install internetarchive && ia configure
python3 tools/mk_ia_manifest.py > villager_tower_ia.csv
ia upload --spreadsheet=villager_tower_ia.csv --retries 5
```

Adding a new issue: drop the PDF in `pub/villager_tower/` using the existing
naming pattern, upload it, and push.
