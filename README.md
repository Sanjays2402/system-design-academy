# System Design Academy

A searchable, offline-friendly SDE2 interview curriculum with **40 dedicated design chapters**.

**Live site:** https://sanjays2402.github.io/system-design-academy/

## Curriculum

- 30 system-design questions
- 10 low-level / machine-coding design questions
- Requirements, scale, API/data model, architecture, critical flow, deep dives, trade-offs, reliability, security, observability, and an interview plan on every page
- Five tailored follow-up questions per design
- Two custom SVG diagrams per design
- Persistent black/white reading mode with safe storage fallbacks
- Responsive navigation, search, and print styles

## Run locally

Open `site/index.html` directly, or serve the generated site:

```bash
python3 -m http.server 8765 --directory site
```

Then visit `http://127.0.0.1:8765/`.

## Regenerate and validate

```bash
python3 generate_site.py
python3 validate_site.py
```

The validator checks page counts, internal links, required sections, diagram counts, follow-up counts, responsive/theme assets, and storage-safe theme handling.

## Deployment

Every push to `main` regenerates, validates, and deploys `site/` to GitHub Pages using `.github/workflows/pages.yml`.
