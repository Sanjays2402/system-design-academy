from html import escape

FEATURED = [
    ('url-shortener', 'Start with scale', 'URL Shortener', 'IDs, cache-aside reads, partitioning, and asynchronous analytics.'),
    ('rate-limiter', 'Protect the edge', 'Rate Limiter', 'Distributed counters, failure policy, atomic updates, and tenant fairness.'),
    ('message-queue', 'Reason about order', 'Message Queue', 'Partitions, durability, replication, consumer groups, and replay.'),
    ('payment-system', 'Protect the invariant', 'Payment System', 'Idempotency, state machines, double-entry ledgers, and reconciliation.'),
]


def landing_html(Q, HEAD):
    categories = sorted(set(q[2] for q in Q))
    category_filters = ''.join(
        f'<button class="filter-chip" data-filter="{escape(category)}" aria-pressed="false">{escape(category)}</button>'
        for category in categories
    )
    cards = []
    for index, q in enumerate(Q):
        title, slug, category, tagline, scale, components, focuses, followups = q
        cards.append(f'''<a class="design-card" data-category="{escape(category)}" href="designs/{slug}.html">
          <div class="card-top"><span class="n">{index+1:02d} / {len(Q)}</span><span class="card-arrow" aria-hidden="true">↗</span></div>
          <div class="card-graph" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
          <h2>{escape(title)}</h2><p>{escape(tagline)}</p>
          <div class="card-meta"><span class="category">{escape(category)}</span><span class="card-depth">3K words · 2 diagrams</span></div>
        </a>''')
    path = ''.join(
        f'''<a class="path-step" href="designs/{slug}.html"><span class="step-no">0{index+1} · {escape(kicker)}</span><span class="path-line" aria-hidden="true"></span><h3>{escape(title)}</h3><p>{escape(copy)}</p></a>'''
        for index,(slug,kicker,title,copy) in enumerate(FEATURED)
    )
    ticker_terms = ['Requirements','Capacity math','API contracts','Partition keys','Consistency','Cache policy','Failure matrix','Multi-region','Security','Observability']
    ticker = ''.join(f'<span class="signal-pill">{escape(x)}</span>' for x in ticker_terms*2)
    return f'''<!doctype html><html lang="en"><head>{HEAD}<title>System Design Academy · {len(Q)} SDE2 Deep Dives</title><meta name="description" content="{len(Q)} interview-ready SDE2 system and low-level design deep dives with animated architecture, diagrams, and follow-up answers."><link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet"><link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/landing.css"></head>
<body class="landing-page"><header class="topbar"><a class="brand" href="index.html"><b>SD</b>System Design Academy</a><div class="crumb">A field guide for systems that survive the follow-up</div><button class="theme-toggle" data-theme-toggle aria-label="Toggle black and white theme">Dark page</button></header>
<main class="landing-wrap"><section class="hero-stage" aria-labelledby="landing-title"><div class="hero-copy"><div class="hero-kicker"><i class="live-dot"></i>40 interview systems · continuously deployable</div><h1 id="landing-title">Design the system.<span>Defend every choice.</span></h1><p class="hero-lede">An animated, long-form SDE2 curriculum for learning the invariants, bottlenecks, failure modes, and follow-ups behind production systems.</p><div class="hero-actions"><a class="hero-cta" href="designs/url-shortener.html">Start the curriculum <span class="arrow">→</span></a><a class="hero-cta secondary" href="#curriculum">Explore all systems</a></div><div class="hero-metrics"><div class="hero-metric"><b data-count="40">0</b><span>deep dives</span></div><div class="hero-metric"><b data-count="120">0</b><span>thousand words</span></div><div class="hero-metric"><b data-count="80">0</b><span>architecture diagrams</span></div></div></div>
<div class="topology-wrap" aria-label="Animated system topology"><div class="topology-shell"><div class="topology-label">LIVE ARCHITECTURE · REQUEST FLOW</div><canvas data-topology aria-hidden="true"></canvas><div class="topology-status"><i></i> packets flowing · no dependencies</div></div></div></section>
<div class="signal-strip" aria-hidden="true"><span class="signal-label">Every chapter</span><div class="signal-track">{ticker}</div></div>
<section class="path-section"><div class="section-heading"><div><span class="eyebrow">Recommended path</span><h2>Build the mental model in four moves.</h2></div><p>Start with a compact read-heavy service, add distributed enforcement, learn ordered logs, then finish with a correctness-critical transaction system.</p></div><div class="learning-path">{path}</div></section>
<section class="curriculum-section" id="curriculum"><div class="section-heading"><div><span class="eyebrow">The curriculum</span><h2>Forty systems. No hand-waving.</h2></div><p>Filter by architecture family or search for a concept. Every design includes roughly 3,000 words, diagrams, failure analysis, and answer guidance.</p></div>
<div class="curriculum-tools"><div class="tool-row"><div class="search-shell"><input class="search" type="search" data-curriculum-search placeholder="Search systems, categories, or concepts…" aria-label="Search the design curriculum"></div><span class="visible-count" data-visible-count>{len(Q)} of {len(Q)} chapters</span></div><div class="category-rail" aria-label="Filter by category"><button class="filter-chip active" data-filter="all" aria-pressed="true">All systems</button>{category_filters}</div></div>
<div class="catalog">{''.join(cards)}</div><div class="empty">No system matches that filter. Try a broader concept.</div></section>
<footer class="landing-footer"><p>Original interview-learning artifact · 40 systems · 122K+ words · 80 custom diagrams.</p><p><a href="https://github.com/Sanjays2402/system-design-academy">Source on GitHub ↗</a></p></footer></main><script src="assets/site.js"></script><script src="assets/landing.js"></script></body></html>'''
