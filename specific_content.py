from html import escape


def specific_html(item, spec):
    title, slug, category, tagline, scale, components, focuses, followups = item
    e=escape
    api=''.join(f'<li><code>{e(x.split(" — ")[0])}</code><span>{e(x.split(" — ",1)[1] if " — " in x else "")}</span></li>' for x in spec['api'])
    records='\n\n'.join(spec['records'])
    steps=''.join(f'<div class="flow-item"><div><b>{i+1:02d} · {e(step.split(".",1)[0])}</b><p>{e(step)}</p></div></div>' for i,step in enumerate(spec['steps']))
    failures=''.join(f'<tr><td><strong>{e(f)}</strong></td><td>{e(_failure_behavior(f))}</td><td>{e(_failure_signal(f))}</td></tr>' for f in spec['failures'])
    nodes=''.join(f'<tr><td><code>{i+1:02d}</code></td><td><strong>{e(n)}</strong></td><td>{e(_component_job(n))}</td><td>{e(_component_state(n))}</td></tr>' for i,n in enumerate(spec['nodes']))
    answers=''.join(f'''<details class="specific-answer" {"open" if i==0 else ""}><summary>{e(q)}</summary><div class="answer-grid"><p><strong>Position.</strong> {e(_answer_position(slug,q,i,focuses))}</p><p><strong>Mechanism.</strong> {e(spec['steps'][i%len(spec['steps'])])}</p><p><strong>Failure test.</strong> {e(spec['failures'][i%len(spec['failures'])])}; explain the retry identity, durable checkpoint, and reconciliation signal.</p><p><strong>Trade-off.</strong> {e(_answer_tradeoff(slug,q,i))}</p></div></details>''' for i,q in enumerate(followups))
    return f'''
<section class="section system-specific" id="system-contract"><h2><span class="section-no">03C · SPECIFIC CONTRACT</span>{e(title)} API surface</h2><p>These operations are intentionally specific to this design. They replace the generic “create/get status” contract with the commands and reads an interviewer expects you to reason about.</p><ul class="api-list">{api}</ul><div class="callout"><strong>Retry contract</strong><p>Mutation identities are stable across client retries. If the response is lost after commit, return the recorded result or reconcile the named state—never repeat the business effect blindly.</p></div></section>
<section class="section system-specific" id="system-schema"><h2><span class="section-no">03D · SPECIFIC DATA MODEL</span>Tables, streams, and indexes</h2><pre>{e(records)}</pre><p>The first record is the authoritative aggregate or lookup. Remaining records represent deduplication, ordered history, derived state, or operational evidence. State which writes share a transaction and which projections can lag.</p></section>
<section class="section system-specific" id="component-map"><h2><span class="section-no">04C · COMPONENT MAP</span>{len(spec['nodes'])} named production components</h2><div class="table-wrap"><table><thead><tr><th>#</th><th>Component</th><th>Owns</th><th>State boundary</th></tr></thead><tbody>{nodes}</tbody></table></div></section>
<section class="section system-specific" id="system-algorithm"><h2><span class="section-no">05C · EXACT FLOW</span>{e(title)} lifecycle</h2><div class="flow">{steps}</div><div class="callout"><strong>Narration rule</strong><p>For each step, say what identity is stable, what state becomes durable, whether the call is synchronous, and what happens when the caller sees a timeout.</p></div></section>
<section class="section system-specific" id="specific-failures"><h2><span class="section-no">08F · NAMED FAILURES</span>Failure drills for this system</h2><div class="table-wrap"><table><thead><tr><th>Scenario</th><th>Runtime behavior</th><th>Proof of recovery</th></tr></thead><tbody>{failures}</tbody></table></div></section>
<section class="section system-specific" id="specific-answers"><h2><span class="section-no">09C · ANSWER DEPTH</span>Follow-up answers, not prompts</h2>{answers}</section>
'''


def _component_job(name):
    n=name.lower()
    if any(x in n for x in ['client','app','panel','keypad','merchant','buyer','driver','rider']): return 'User/device protocol, request identity, local retry and resume behavior.'
    if any(x in n for x in ['edge','gateway','api','front door','kiosk']): return 'Authentication, validation, quotas, deadlines, routing, and bounded payload handling.'
    if any(x in n for x in ['cache','redis','index','fst','trie']): return 'Latency-sensitive lookup or candidate state; disposable and rebuildable.'
    if any(x in n for x in ['queue','stream','kafka','log','journal','outbox']): return 'Durable order, replay, backpressure boundary, and consumer checkpoint.'
    if any(x in n for x in ['worker','pipeline','fanout','transcode','repair','compactor']): return 'Idempotent asynchronous work with leases, retries, and DLQ/reconciliation.'
    if any(x in n for x in ['db','store','ledger','inventory','wal','sstable','table']): return 'Authoritative durable record, version, uniqueness, or immutable evidence.'
    if any(x in n for x in ['policy','engine','strategy','orchestrator','coordinator','router']): return 'Business decision, ownership, ordering, allocation, or state-machine transition.'
    if any(x in n for x in ['audit','metric','monitor','reconcil','history','case']): return 'Operations, correctness proof, incident diagnosis, and controlled repair.'
    return 'A bounded domain capability with explicit inputs, outputs, and failure behavior.'


def _component_state(name):
    n=name.lower()
    if any(x in n for x in ['client','gateway','api','edge','worker']): return 'Prefer stateless; carry identity/version in request or durable queue.'
    if any(x in n for x in ['cache','presence','index']): return 'Ephemeral projection with TTL/version and authoritative fallback.'
    if any(x in n for x in ['queue','stream','log','journal']): return 'Append-only durable offsets; consumers checkpoint independently.'
    if any(x in n for x in ['db','store','ledger','inventory','table']): return 'Authoritative, partitioned, replicated, backed up, and reconciled.'
    if any(x in n for x in ['policy','config','registry','directory']): return 'Versioned control-plane snapshot with last-known-good fallback.'
    return 'State is scoped to one aggregate/partition and protected by version or lease.'


def _failure_behavior(failure):
    f=failure.lower()
    if any(x in f for x in ['timeout','unknown','uncertain']): return 'Retry or query using the same operation identity; do not issue a new effect until committed state is known.'
    if any(x in f for x in ['hot','overload','spike','starve','backlog']): return 'Isolate the key/tenant/class, apply admission control, and preserve priority work plus durable backlog.'
    if any(x in f for x in ['race','two','duplicate','twice','overlap','conflict']): return 'Resolve with uniqueness, expected version, lease generation, or monotonic cursor at the authoritative boundary.'
    if any(x in f for x in ['stale','lag','miss','out of order','differ']): return 'Reject older versions, serve explicit stale mode only when safe, and rebuild projection from durable history.'
    if any(x in f for x in ['unavailable','outage','dies','fails','loss','power']): return 'Trip the dependency, fail open/closed by invariant, route to healthy ownership, and recover from durable checkpoint.'
    return 'Stop unsafe progress, preserve evidence, retry idempotently where allowed, and move ambiguous work to reconciliation.'


def _failure_signal(failure):
    f=failure.lower()
    if any(x in f for x in ['queue','backlog','lag']): return 'Oldest-item age returns to SLO and replay reaches the durable high-watermark.'
    if any(x in f for x in ['cache','stale']): return 'Version mismatch and fallback rates return to baseline; sampled reads match source of truth.'
    if any(x in f for x in ['duplicate','twice','race','conflict']): return 'Duplicate suppression/conflict counters stop and reconciliation finds zero invariant violations.'
    if any(x in f for x in ['payment','debit','ledger','settlement','refund']): return 'Processor/bank totals equal balanced internal ledger and every uncertain attempt is classified.'
    return 'Error budget recovers, replicas/consumers converge, and a business-level reconciliation query reports zero gaps.'


def _answer_position(slug, question, i, focuses):
    q=question.lower()
    if 'region' in q: return 'Assign one write owner per aggregate or partition first; add regional reads and asynchronous projections before accepting multi-writer conflict cost.'
    if any(x in q for x in ['duplicate','exactly-once','twice']): return 'Do not promise exactly-once transport. Build an exactly-once business effect from stable identities, conditional state, and deduplicated replay.'
    if any(x in q for x in ['cache','hot key','celebrity']): return 'Treat cache as a projection, detect skew per key, coalesce misses, replicate hot reads, and retain an authoritative fallback.'
    if any(x in q for x in ['unavailable','fails','failure','outage']): return 'Name fail-open versus fail-closed from the invariant, bound retries, preserve durable work, and expose explicit degraded behavior.'
    if any(x in q for x in ['order','ordering']): return 'Guarantee order only within the natural aggregate or partition; carry sequence/epoch and reject stale writes or cursors.'
    return focuses[i%len(focuses)]


def _answer_tradeoff(slug, question, i):
    choices=[
      'The stronger coordination choice protects the invariant but adds latency and lowers availability during partitions; keep derived reads asynchronous.',
      'The materialized/proactive path improves read latency but costs write amplification, repair tooling, and lag monitoring.',
      'The simpler centralized design is an excellent first version; partition only when measured throughput, isolation, or failure-domain needs justify it.',
      'More aggressive caching or batching improves throughput but increases staleness and uncertain work; version every projection and bound the window.',
      'Operational simplicity is a feature: prefer one explicit ownership model over clever multi-writer behavior unless product requirements demand it.'
    ]
    return choices[i%len(choices)]
