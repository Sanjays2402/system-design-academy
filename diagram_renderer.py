from html import escape
import math

EDGE_LABELS = [
    "request", "authenticate", "route", "validate", "read / reserve",
    "commit", "publish", "consume", "project", "observe", "repair",
    "reconcile", "invalidate", "acknowledge"
]


def _lines(text, limit=19):
    words = text.replace(" / ", "/").split()
    if not words:
        return [""]
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return lines[:2]


def _role(name):
    n = name.lower()
    rules = [
        (("client", "app", "buyer", "driver", "rider", "merchant", "operator", "player", "user", "panel", "keypad"), "interaction boundary"),
        (("edge", "gateway", "front door", "api", "endpoint", "kiosk"), "protocol · auth · quota"),
        (("cache", "redis", "index", "fst", "trie", "snapshot"), "low-latency read path"),
        (("queue", "stream", "kafka", "log", "journal", "outbox"), "durable ordered events"),
        (("worker", "pipeline", "fanout", "transcode", "parser", "compactor", "repair"), "asynchronous execution"),
        (("store", "db", "ledger", "table", "wal", "sstable", "inventory"), "authoritative durable state"),
        (("policy", "auth", "risk", "rules", "strategy", "engine", "coordinator", "orchestrator"), "decision & coordination"),
        (("metric", "audit", "monitor", "observ", "reconcil", "history", "case"), "evidence & operations"),
        (("router", "discovery", "directory", "membership", "placement"), "routing & ownership"),
    ]
    for needles, role in rules:
        if any(x in n for x in needles):
            return role
    return "domain subsystem"


def architecture_svg(title, spec):
    nodes = spec["nodes"]
    count = len(nodes)
    cols = 5
    box_w, box_h = 216, 106
    gap_x, gap_y = 24, 74
    left, top = 42, 116
    positions = []
    for i in range(count):
        row, col = divmod(i, cols)
        row_count = min(cols, count - row * cols)
        row_width = row_count * box_w + (row_count - 1) * gap_x
        row_left = (1280 - row_width) / 2
        positions.append((row_left + col * (box_w + gap_x), top + row * (box_h + gap_y)))

    layer_names = ["01 · REQUEST & CONTROL", "02 · DOMAIN & COORDINATION", "03 · DATA, ASYNC & OPERATIONS"]
    layer_colors = ["#22d3ee", "#c4b5fd", "#fb923c"]
    layer_fills = ["#0d2631", "#231b3b", "#302014"]
    layer_labels = "".join(
        f'<text x="42" y="{87 + r*(box_h+gap_y)}" class="layer-label" fill="{layer_colors[r]}">{layer_names[r]}</text>'
        for r in range(math.ceil(count/cols))
    )

    edges = []
    for i in range(count - 1):
        x1, y1 = positions[i]; x2, y2 = positions[i + 1]
        if y1 == y2:
            sx, sy, ex, ey = x1 + box_w, y1 + box_h / 2, x2 - 10, y2 + box_h / 2
            path = f"M{sx:.0f} {sy:.0f} H{ex:.0f}"
            tx, ty = (sx + ex) / 2, sy - 8
        else:
            sx, sy = x1 + box_w / 2, y1 + box_h
            ex, ey = x2 + box_w / 2, y2 - 10
            bend = (sy + ey) / 2
            path = f"M{sx:.0f} {sy:.0f} V{bend:.0f} H{ex:.0f} V{ey:.0f}"
            tx, ty = (sx + ex) / 2, bend - 7
        label = EDGE_LABELS[i % len(EDGE_LABELS)]
        edges.append(f'<path d="{path}" class="arch-edge" marker-end="url(#arch-arrow)"/><text x="{tx:.0f}" y="{ty:.0f}" text-anchor="middle" class="edge-label">{escape(label)}</text>')

    # Cross-layer paths communicate cache/read shortcuts and asynchronous repair.
    if count >= 12:
        for source, target, label, cls in [(1, 6, "policy snapshot", "arch-control"), (3, 10, "event stream", "arch-async"), (8, count-1, "telemetry", "arch-async")]:
            if target >= count: continue
            x1,y1=positions[source];x2,y2=positions[target]
            sx,sy=x1+box_w/2,y1+box_h;ex,ey=x2+box_w/2,y2-8
            edges.append(f'<path d="M{sx:.0f} {sy:.0f} C{sx:.0f} {(sy+ey)/2:.0f},{ex:.0f} {(sy+ey)/2:.0f},{ex:.0f} {ey:.0f}" class="{cls}" marker-end="url(#arch-arrow-warm)"/><text x="{(sx+ex)/2:.0f}" y="{(sy+ey)/2-8:.0f}" text-anchor="middle" class="edge-label warm">{escape(label)}</text>')

    boxes = []
    for i, (name, (x, y)) in enumerate(zip(nodes, positions)):
        row = i // cols
        color, fill = layer_colors[row], layer_fills[row]
        text_lines = _lines(name)
        name_text = ''.join(f'<tspan x="{x+box_w/2:.0f}" dy="{0 if j==0 else 17}">{escape(line)}</tspan>' for j,line in enumerate(text_lines))
        boxes.append(f'''<g class="arch-node" data-component="{escape(name)}">
          <rect x="{x:.0f}" y="{y:.0f}" width="{box_w}" height="{box_h}" rx="12" fill="{fill}" stroke="{color}"/>
          <rect x="{x+12:.0f}" y="{y+12:.0f}" width="30" height="20" rx="10" fill="{color}"/>
          <text x="{x+27:.0f}" y="{y+26:.0f}" text-anchor="middle" class="step">{i+1:02d}</text>
          <text x="{x+box_w-13:.0f}" y="{y+25:.0f}" text-anchor="end" class="node-kind">{escape(['EDGE','CORE','DATA'][row])}</text>
          <text x="{x+box_w/2:.0f}" y="{y+51:.0f}" text-anchor="middle" class="node arch-name">{name_text}</text>
          <text x="{x+box_w/2:.0f}" y="{y+91:.0f}" text-anchor="middle" class="node-sub">{escape(_role(name))}</text>
        </g>''')

    height = top + math.ceil(count/cols) * (box_h + gap_y) + 35
    return f'''<svg viewBox="0 0 1280 {height}" role="img" data-component-count="{count}" aria-label="{escape(title)} detailed production architecture">
      <defs><marker id="arch-arrow" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#64748b"/></marker><marker id="arch-arrow-warm" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#fb923c"/></marker><pattern id="arch-grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#1e293b" stroke-width=".5"/></pattern></defs>
      <rect width="1280" height="{height}" fill="#07101f"/><rect width="1280" height="{height}" fill="url(#arch-grid)"/>
      <text x="42" y="35" class="diagram-title">{escape(title.upper())} · PRODUCTION TOPOLOGY</text>
      <text x="42" y="57" class="diagram-note">{count} named components · solid = request/data dependency · warm curve = control, event, or repair path</text>
      <text x="1238" y="35" text-anchor="end" class="diagram-note">MULTI-ZONE · VERSIONED · REPLAYABLE</text>
      {layer_labels}{''.join(edges)}{''.join(boxes)}
    </svg>'''


def sequence_svg(title, spec):
    nodes, steps = spec["nodes"], spec["steps"]
    actor_count = 7
    indices = sorted(set(round(i*(len(nodes)-1)/(actor_count-1)) for i in range(actor_count)))
    actors = [nodes[i] for i in indices]
    cols = [70 + i * 188 for i in range(len(actors))]
    heads = []
    for i,(x,name) in enumerate(zip(cols,actors)):
        lines=_lines(name,15)
        label=''.join(f'<tspan x="{x}" dy="{0 if j==0 else 14}">{escape(line)}</tspan>' for j,line in enumerate(lines))
        heads.append(f'<g class="sequence-actor"><rect x="{x-73}" y="54" width="146" height="62" rx="9" class="seq-head"/><text x="{x}" y="78" text-anchor="middle" class="node seq-name">{label}</text><text x="{x}" y="105" text-anchor="middle" class="node-sub">ACTOR {i+1:02d}</text><line x1="{x}" y1="116" x2="{x}" y2="555" class="life"/></g>')
    messages=[]
    for i,step in enumerate(steps):
        y=155+i*66
        source=i%6;target=source+1
        x1,x2=cols[source],cols[target]
        chunks=_lines(step,48)
        label=' / '.join(chunks)
        messages.append(f'<rect x="{min(x1,x2)+18}" y="{y-28}" width="{abs(x2-x1)-36}" height="19" rx="9" class="message-badge"/><text x="{(x1+x2)/2}" y="{y-15}" text-anchor="middle" class="message-step">STEP {i+1:02d}</text><path d="M{x1} {y} H{x2-9}" class="seq-arrow" marker-end="url(#seq-arrow)"/><text x="{(x1+x2)/2}" y="{y-3}" text-anchor="middle" class="sequence-label">{escape(label)}</text>')
    # Acknowledge and explicit failure/retry path.
    y=155+len(steps)*66
    messages.append(f'<path d="M{cols[-1]} {y} H{cols[0]+9}" class="seq-return" marker-end="url(#seq-arrow)"/><text x="{(cols[0]+cols[-1])/2}" y="{y-9}" text-anchor="middle" class="sequence-label">stable result / cursor / version</text>')
    messages.append(f'<path d="M{cols[4]} {y+55} C{cols[4]} {y+95},{cols[2]} {y+95},{cols[2]} {y+55}" class="seq-failure" marker-end="url(#seq-warm)"/><text x="{(cols[2]+cols[4])/2}" y="{y+93}" text-anchor="middle" class="edge-label warm">timeout → same identity → reconcile committed truth</text>')
    height=y+130
    return f'''<svg viewBox="0 0 1280 {height}" role="img" aria-label="{escape(title)} detailed critical sequence">
      <defs><marker id="seq-arrow" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#94a3b8"/></marker><marker id="seq-warm" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#fb923c"/></marker><pattern id="seq-grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#1e293b" stroke-width=".5"/></pattern></defs>
      <rect width="1280" height="{height}" fill="#07101f"/><rect width="1280" height="{height}" fill="url(#seq-grid)"/>
      <text x="28" y="28" class="diagram-title">{escape(title.upper())} · CRITICAL SEQUENCE</text><text x="1252" y="28" text-anchor="end" class="diagram-note">HAPPY PATH + UNCERTAIN OUTCOME RECOVERY</text>
      {''.join(heads)}{''.join(messages)}
    </svg>'''
