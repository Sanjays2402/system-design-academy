# System Design Academy

A searchable, offline-friendly architecture curriculum with **60 dedicated design chapters**.

**Live site:** https://sanjays2402.github.io/system-design-academy/

## Curriculum

- 47 system-design questions
- 13 low-level / machine-coding design questions
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
- Every component explains its owned responsibility, why it is separated, the rejected alternative, operational cost, and scale/evolution trigger
- Three architecture-rationale deep dives per chapter: simpler-monolith boundary, correctness-versus-availability, and operational evolution
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

The validator checks the 60-route manifest, internal links, required sections, diagram/call-flow behavior, complete per-design specifications, component-level rejected alternatives and evolution triggers, rationale deep dives, responsive/theme assets, storage-safe theme handling, and the `sitemap.xml` / `robots.txt` discovery files (all 61 routes listed, sitemap referenced from robots).

## SEO / discovery

`generate_site.py` emits `site/sitemap.xml` (landing page + all 60 design chapters) and `site/robots.txt` (referencing the sitemap) so search engines can discover every chapter of the public curriculum.

## Deployment

Every push to `main` regenerates, validates, and deploys `site/` to GitHub Pages using `.github/workflows/pages.yml`.
