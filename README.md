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

## Terms & Disclaimer

By using this project you agree to the following.

- **No warranty.** This software is provided "as is", without warranty of any kind, express or implied, including merchantability, fitness for a particular purpose, and non-infringement.
- **No liability.** To the maximum extent permitted by law, the author and contributors are not liable for any claim, loss, or damage (direct, indirect, incidental, or consequential, including lost data or profits) arising from its use.
- **Your responsibility.** You use it at your own risk and are responsible for complying with the laws that apply to you.
- **Educational content.** The material reflects the author's understanding and may be incomplete or outdated; it is not professional engineering advice. Company and product names are trademarks of their owners.
- **Third parties.** Names, logos, APIs, and services of others belong to their owners and are used for identification only; no affiliation or endorsement is implied.
- **Your statutory rights.** Nothing here limits rights that cannot be waived by agreement, including under consumer-protection laws in the USA, Canada (including Quebec), and India (Consumer Protection Act, 2019).
- **License.** No open-source license is granted. All rights reserved; you may view and fork this repository only as GitHub's Terms of Service allow.

## Content, Assets & Fair Use

- **Original work.** Unless noted otherwise (including below), the code, text, design, and images in this repository were created by the author.
- **Libraries, fonts, and icons.** Third-party libraries, fonts (for example Google Fonts), and icon sets belong to their creators and are used under their own licenses; see the dependency manifests and each source for terms.
- **Logos, brands, and screenshots.** Third-party names, logos, and screenshots appear only to identify or describe their products (nominative use). They remain the property of their owners and do not imply affiliation or endorsement.
- **Ideas and inspiration.** Where this project is inspired by another product, game, or idea, it is an independent implementation. It borrows only general ideas, mechanics, or styles, which are not anyone's exclusive property, and is meant to contain no third-party code or artwork used without permission.
- **Fair use and fair dealing.** Any third-party material is used in limited ways for purposes such as education, research, review, commentary, or identification, relying on fair use in the USA (17 U.S.C. § 107), fair dealing in Canada (Copyright Act, ss. 29–29.2), and fair dealing in India (Copyright Act, 1957, s. 52), where they apply.
- **Concerns and takedown requests.** If you own rights in something here and believe it is used improperly, [open an issue](https://github.com/Sanjays2402/system-design-academy/issues) or contact the author through their GitHub profile with a link to the material and your claim. It will be reviewed promptly and credited, changed, or removed as appropriate. You may also use GitHub's DMCA process.
- **Contributions.** By contributing, you confirm you have the right to submit your contribution and agree it is licensed under this repository's license.
- **Website.** The project site has its own [Terms](https://sanjays2402.github.io/system-design-academy/terms.html) and [Fair Use](https://sanjays2402.github.io/system-design-academy/fair-use.html) pages.
