# System Design Academy

A searchable, offline-friendly SDE2 interview curriculum with **40 dedicated design chapters**.

**Live site:** https://sanjays2402.github.io/system-design-academy/

## Curriculum

- 30 system-design questions
- 10 low-level / machine-coding design questions
- Requirements, estimation math, APIs, concrete records/indexes, architecture, critical flows, algorithms, caching/backpressure, trade-offs, failure matrices, multi-region evolution, security, observability, and interview plans on every page
- Dark-first, diagram-first chapters modeled as one coherent technical walkthrough
- Exactly 11 focused tutorial chapters per design, with sticky navigation
- 12–15 semantically colored, system-specific architecture components per design
- Separate mutation/commit and online/read/recovery sequence views
- Interactive call-flow explorer on every architecture:
  - mutation/commit, online/read, and failure/recovery routes
  - play/pause, previous/next, restart, clickable steps, and keyboard controls
  - animated route packets, active components, and synchronized plain-English narration
  - static numbered fallback and reduced-motion manual stepping
- Four concrete API operations, four records/indexes, exact lifecycle steps, and named failure drills
- At least six focused decision tables and five concrete code/data blocks per chapter
- Follow-up prompts with structured answer guidance
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
