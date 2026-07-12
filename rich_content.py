"""Long-form, category-aware chapter expansion for System Design Academy."""
from html import escape

# These profiles supply the technical substrate shared by related systems. The
# per-design title/components/deep-dives/follow-ups still make each chapter unique.
PROFILES = {
    "Foundations": {
        "invariant": "A client-visible identifier or admission decision must be unique, deterministic for the same committed input, and safe to retry.",
        "partition": "Hash the stable lookup key, use virtual nodes or a shard map, and move ranges gradually while serving from both old and new owners.",
        "storage": "Use a strongly consistent metadata store for ownership and policy, an in-memory layer for the hot path, and an append-only stream for audit and analytics.",
        "algorithm": "Keep the online decision O(1): normalize the request, derive a stable key, consult local state, then perform one conditional durable operation only on a miss or mutation.",
        "security": "Rate-limit enumeration, authenticate mutations, validate all externally supplied destinations or keys, and avoid leaking sequential volume through public identifiers.",
    },
    "Product Systems": {
        "invariant": "A user action is accepted once, appears in the correct audience, and remains compatible with privacy, preference, and moderation policy.",
        "partition": "Partition durable content by immutable object ID and graph/timeline work by owner or audience key; isolate celebrity or bulk fan-out paths.",
        "storage": "Keep canonical objects in a durable record store, relationships in an adjacency-oriented store, hot views in caches, and delivery work in replayable queues.",
        "algorithm": "Separate object creation from audience expansion. Commit the source object first, emit an event, derive materialized views asynchronously, and repair them from the event log.",
        "security": "Enforce audience policy at both write and read time, propagate deletes rapidly, scan untrusted media, and retain moderation decisions with auditability.",
    },
    "Storage": {
        "invariant": "A committed object or file version is never silently corrupted, partially published, or returned under the wrong owner/version.",
        "partition": "Partition metadata by object or namespace key; place data chunks independently across racks/zones using replication or erasure coding.",
        "storage": "Use a transactional metadata plane plus immutable blobs/chunks, checksummed manifests, background replication, lifecycle tiers, and continuous scrubbing.",
        "algorithm": "Upload parts independently, verify checksums, write an immutable manifest, and atomically switch the visible version pointer only after every required fragment is durable.",
        "security": "Authorize every namespace/object operation, issue short-lived signed URLs, encrypt per tenant or bucket, and block path traversal and confused-deputy access.",
    },
    "Realtime": {
        "invariant": "Within one conversation or session, accepted events have a stable order, survive reconnects, and are not shown as delivered before durable acceptance.",
        "partition": "Route all events for a conversation/session to the same logical partition while distributing connections across stateless gateway fleets.",
        "storage": "Use an append-only ordered log for durable events, snapshots/materialized inboxes for fast sync, and an ephemeral store for presence and connection routing.",
        "algorithm": "Assign a server sequence after durable append, acknowledge the sender, fan out to online devices, and let offline devices resume from their last acknowledged cursor.",
        "security": "Authenticate each socket, re-authorize membership on sensitive changes, rate-limit fan-out, and separate transport encryption from optional end-to-end encryption.",
    },
    "Media": {
        "invariant": "A published asset references a complete, immutable set of playable renditions; viewers never observe a half-transcoded release.",
        "partition": "Partition control-plane metadata by media ID and distribute immutable segments through object storage and CDN cache keys.",
        "storage": "Keep source media and renditions in object storage, metadata/manifests in a durable database, and transcode jobs/results in a replayable pipeline.",
        "algorithm": "Accept resumable parts, verify the source, fan out transcode tasks, validate every rendition, then atomically publish the playback manifest.",
        "security": "Use signed upload/playback URLs, scan uploads, enforce codec and size limits, protect premium manifests, and watermark or encrypt when required.",
    },
    "Geo & Realtime": {
        "invariant": "A scarce moving resource is assigned to at most one active workflow, and every trip/location transition is monotonic and auditable.",
        "partition": "Index ephemeral positions by geospatial cell; partition durable workflows by trip/resource ID and use leases for short-lived assignment claims.",
        "storage": "Keep recent locations in memory, durable trip state in a transactional store, and raw location/events in a stream for replay and analytics.",
        "algorithm": "Search the nearest cell, expand rings until enough candidates exist, score them, reserve the winner with a short lease, and confirm through a versioned state transition.",
        "security": "Minimize precise-location retention, isolate rider/driver identities, detect spoofed GPS, and audit support or operator access to live locations.",
    },
    "Transactions": {
        "invariant": "Money, inventory, or another scarce entitlement is never created twice, lost after acknowledgment, or committed without an auditable state transition.",
        "partition": "Partition by transaction/order/resource ID, keep each aggregate's mutations serializable, and route cross-service work through a saga rather than a distributed lockstep commit.",
        "storage": "Use a transactional source of truth, immutable ledger/event entries, idempotency records, and queues for partner calls and compensating work.",
        "algorithm": "Create an intent, reserve the scarce resource, perform the external operation, then confirm; on failure execute an idempotent compensation and reconcile later.",
        "security": "Tokenize sensitive data, sign partner callbacks, enforce least privilege, separate duties, and preserve immutable audit evidence for every financial or inventory mutation.",
    },
    "Infrastructure": {
        "invariant": "The data plane remains bounded and predictable when dependencies or control-plane updates fail; policy is never partially applied within one decision.",
        "partition": "Shard by stable client/resource key using consistent hashing; distribute versioned configuration snapshots independently from request traffic.",
        "storage": "Keep hot state in memory, authoritative policy/membership in a consensus-backed store, and operational events in durable telemetry pipelines.",
        "algorithm": "Resolve a versioned policy snapshot locally, route by a stable hash, execute with a deadline, and apply bounded retries or fallback only when semantics permit.",
        "security": "Authenticate control-plane writers, sign snapshots, isolate tenants, protect admin paths, and treat dynamic configuration as production code.",
    },
    "Data Platforms": {
        "invariant": "Each work item is processed according to policy without unbounded duplication, starvation, or loss, and can be replayed from durable state.",
        "partition": "Partition frontier/work queues by fairness or locality key, then independently shard parsing, dedupe, and output storage.",
        "storage": "Use durable queues, a seen/dedupe index, immutable raw storage, parsed/indexed outputs, and checkpointed worker progress.",
        "algorithm": "Claim a bounded batch with a lease, process idempotently, commit output and checkpoint, then acknowledge; expired leases return work to the queue.",
        "security": "Sandbox parsers, limit fetched payloads, enforce egress policy, validate content types, and prevent tenant or domain starvation attacks.",
    },
    "Search": {
        "invariant": "Results are generated from a known index version, respect filtering/safety policy, and return within the interactive latency budget.",
        "partition": "Shard terms or prefixes by normalized key range, replicate hot shards, and merge top-k candidates rather than full result sets.",
        "storage": "Serve immutable compact index snapshots from memory, overlay recent updates, and retain query/click events for ranking and rebuilds.",
        "algorithm": "Normalize input, retrieve bounded candidates, apply safety and locale filters, score with frequency/recency/context, then return top-k with a stable version.",
        "security": "Remove unsafe suggestions quickly, resist poisoning and enumeration, minimize personalized signals, and enforce query-log retention controls.",
    },
    "Observability": {
        "invariant": "Telemetry must not take down the observed system, cross tenant boundaries, or silently disappear without a measurable loss signal.",
        "partition": "Partition by tenant plus time/series fingerprint, cap cardinality, and separate recent interactive storage from compressed archival tiers.",
        "storage": "Buffer in a durable log, write recent data to indexed/TSDB shards, compact and downsample older data, and archive raw segments in object storage.",
        "algorithm": "Batch and compress at agents, apply quotas at collectors, route by tenant/key, build indexes or rollups asynchronously, and evaluate alerts from durable windows.",
        "security": "Redact secrets before persistence, encrypt tenant data, constrain query scope, audit access, and protect alert/webhook destinations from SSRF.",
    },
    "Distributed Data": {
        "invariant": "Replicas converge without acknowledging data that cannot survive the configured failure model; ordering is scoped and explicit.",
        "partition": "Use hash/range partitions with replicas across failure domains; a controller or gossip membership layer assigns ownership and rebalances incrementally.",
        "storage": "Append sequentially to WAL/segments, maintain indexes and offsets, replicate before acknowledgment, compact safely, and archive cold segments.",
        "algorithm": "Route to the partition leader/coordinator, append with an epoch and sequence, replicate to quorum, acknowledge, then repair lagging replicas in the background.",
        "security": "Authenticate cluster peers and clients, authorize topics/keyspaces, encrypt replication, enforce quotas, and audit administrative reconfiguration.",
    },
    "Collaboration": {
        "invariant": "Concurrent edits converge to one deterministic document state while preserving authorship, permissions, and recoverable history.",
        "partition": "Keep one document/session on one ordered collaboration shard while distributing presence and read snapshots separately.",
        "storage": "Persist an operation log and periodic snapshots; keep cursors/presence ephemeral and store permissions in a strongly consistent service.",
        "algorithm": "Apply locally for instant feedback, transform or merge remote operations by version/vector, append the canonical operation, and broadcast the resulting cursor.",
        "security": "Re-authorize participants as sharing changes, protect document encryption keys, bound operation size/rate, and audit exports and permission mutations.",
    },
    "Control Planes": {
        "invariant": "Clients evaluate one complete, validated configuration version and retain a known-good version through control-plane outages.",
        "partition": "Partition configuration by project/tenant, distribute immutable signed snapshots through relay trees, and isolate update traffic from evaluation.",
        "storage": "Store immutable versions plus atomic environment pointers, audit events, rollout state, and client acknowledgments or observed versions.",
        "algorithm": "Validate and persist a version, canary it to a cohort, watch health, advance rollout stages, then atomically promote or roll back the pointer.",
        "security": "Require reviewed writes, sign artifacts, separate secrets, audit every change, and provide emergency kill paths with tighter authorization.",
    },
    "ML Systems": {
        "invariant": "An online decision is reproducible from logged feature/model versions and stays within latency, safety, and freshness budgets.",
        "partition": "Partition online features by entity ID, candidate indexes by embedding shard, and event/training data by time plus subject key.",
        "storage": "Use an offline lake/warehouse, point-in-time feature store, model registry, online feature cache, vector/candidate index, and exposure/decision log.",
        "algorithm": "Fetch bounded candidates/features in parallel, score with a pinned model, apply rules and diversity/safety constraints, return, then log the full decision context asynchronously.",
        "security": "Minimize sensitive features, enforce purpose-based access, detect poisoning and drift, sign model artifacts, and retain explanations for consequential decisions.",
    },
    "Coordination": {
        "invariant": "At most one valid owner may mutate the protected resource for a lease generation; stale owners are rejected even if they keep running.",
        "partition": "Store coordination state in a small consensus group and partition independent lock namespaces only after proving one group is insufficient.",
        "storage": "Use a replicated consensus log, lease/session records, monotonic fencing counters, and watches derived from committed state.",
        "algorithm": "Acquire through consensus, return a lease and fencing token, renew before expiry, and require the protected resource to reject older tokens.",
        "security": "Authenticate lock namespaces, authorize protected resources, cap lease counts, and audit forced releases or operator intervention.",
    },
    "Platform": {
        "invariant": "A request can access only its authenticated tenant's resources, and one tenant cannot exhaust or observe another tenant's capacity or data.",
        "partition": "Route by trusted tenant context to pooled, partitioned, or dedicated placements; maintain a control-plane mapping for migrations.",
        "storage": "Use tenant-scoped keys/indexes, per-tenant quotas and encryption metadata, immutable usage events, and explicit placement records.",
        "algorithm": "Authenticate, derive tenant context, resolve placement/policy, enforce quota, execute with tenant-scoped credentials, and meter asynchronously.",
        "security": "Test isolation continuously, never trust tenant IDs from payloads, use per-tenant keys where required, and tightly audit support impersonation.",
    },
    "Low-Level Design": {
        "invariant": "Every object transition is legal, atomic at the aggregate boundary, and expressible through small interfaces that are independently testable.",
        "partition": "Keep one aggregate's mutable state behind one concurrency boundary; scale by aggregate ID rather than sharing mutable singleton state.",
        "storage": "Represent current aggregate state, immutable transition/audit records, and external-device/service ports behind repositories and adapters.",
        "algorithm": "Validate a command against current state, choose a strategy, apply one state transition, persist with a version check, then publish side effects.",
        "security": "Validate actors at the use-case boundary, hide privileged transitions behind capabilities, sanitize device/input data, and audit overrides.",
    },
}

FAILURES = [
    ("Primary store unavailable", "Serve only safe cached/read-only paths, reject correctness-sensitive mutations, trip a circuit breaker, and alert on replica health."),
    ("Queue or stream backlog", "Apply admission control, preserve durable work, scale consumers by lag, and expose oldest-item age rather than only queue depth."),
    ("Hot partition or tenant", "Detect skew, isolate the key, add replicas or key salting where ordering permits, and enforce per-tenant budgets."),
    ("Partial timeout after commit", "Retry with the same idempotency key and return the previously committed result instead of repeating the business effect."),
    ("Regional outage", "Route to a healthy region, preserve the chosen write-ownership model, and reconcile divergent asynchronous projections after recovery."),
]

def profile(category):
    return PROFILES.get(category, PROFILES["Infrastructure"])

def rich_html(item, primary_key):
    title, slug, category, tagline, scale, components, focuses, followups = item
    p = profile(category)
    e = escape
    clarifiers = [
        f"What is the smallest useful scope for {title.lower()} in this interview?",
        "Which operation has the strictest correctness requirement, and what may be eventually consistent?",
        f"How should the system behave when the authoritative dependency is unavailable?",
        "Are multi-region writes required now, or is active-passive mutation acceptable initially?",
        "What abuse, privacy, retention, or compliance constraints change the design?",
        "Which metrics will prove the system is healthy from a user's point of view?",
    ]
    clarify = ''.join(f'<li>{e(x)}</li>' for x in clarifiers)
    comp_rows = ''.join(
        f'<tr><td><strong>{e(name)}</strong></td><td>{e(desc)}</td><td>{e(owner)}</td></tr>'
        for name, desc, owner in zip(components,
            ["Terminates the client protocol, validates shape, and propagates identity and deadlines.",
             "Owns the synchronous use case and keeps request handling stateless where possible.",
             "Applies policy, ordering, allocation, ranking, or coordination decisions.",
             "Stores the authoritative record or ordered durable history.",
             "Buffers side effects and decouples bursty producers from workers.",
             "Serves read models, operations, analytics, repair, or downstream integration."],
            ["Edge team","Core service","Domain/control team","Data team","Platform team","Operations/product team"])
    )
    failure_rows = ''.join(f'<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>Alert, trace, and reconcile from durable truth.</td></tr>' for a,b in FAILURES)
    focus_details = ''.join(
        f'<details class="followup" open><summary>{e(["Correctness: protect the invariant","Scale: remove the bottleneck","Operations: recover without guessing"][i])}</summary>'
        f'<p>{e(text)} Begin with the normal path, identify the race or saturation point, then show the exact conditional write, partition key, lease, queue, or cache rule that contains it.</p>'
        f'<p><strong>What to measure:</strong> latency percentiles, retries, rejected conflicts, per-key skew, dependency saturation, and the age of unreconciled work.</p></details>'
        for i,text in enumerate(focuses)
    )
    answer_details = ''.join(
        f'<details class="followup" {"open" if i==0 else ""}><summary>{e(q)}</summary>'
        f'<p><strong>Answer structure:</strong> Start from this invariant: {e(p["invariant"])} Then use the relevant mechanism—{e(focuses[i%3])}</p>'
        f'<p>Explain the happy path, one concurrency or failure case, how retry/recovery stays idempotent, the operational signal you would monitor, and why the simpler alternative stops working at the stated scale.</p></details>'
        for i,q in enumerate(followups)
    )
    return f'''
<section class="section" id="clarify"><h2><span class="section-no">01B · SCOPE</span>Clarifying questions that change the architecture</h2><p>Ask these before committing to a database or drawing a global deployment. A strong design answer narrows ambiguity and names the primary invariant.</p><div class="grid2"><div class="card"><h3>Product and correctness</h3><ul>{clarify}</ul></div><div class="card"><h3>Explicit invariant</h3><p>{e(p['invariant'])}</p><h3>Out of scope unless requested</h3><p>Advanced billing, every administrative workflow, custom reporting, and speculative machine learning should not distract from the critical path. Name extensions, but design the agreed core first.</p></div></div></section>
<section class="section" id="estimation-math"><h2><span class="section-no">02B · CAPACITY MATH</span>Turn estimates into design decisions</h2><div class="table-wrap"><table><thead><tr><th>Calculation</th><th>Interview approximation</th><th>Decision it drives</th></tr></thead><tbody><tr><td>Average throughput</td><td>daily operations ÷ 86,400</td><td>Baseline fleet and partition count.</td></tr><tr><td>Peak throughput</td><td>average × 5–10</td><td>Autoscaling headroom, queue admission, and cache capacity.</td></tr><tr><td>Stored records</td><td>write rate × retention × record bytes</td><td>Shard count, indexes, compaction, and archival tier.</td></tr><tr><td>Network</td><td>peak operations × payload bytes</td><td>Regional placement, batching, compression, and CDN/edge use.</td></tr><tr><td>Availability budget</td><td>99.99% ≈ 52 min/year</td><td>Multi-zone design, automated failover, and dependency budgets.</td></tr></tbody></table></div><p>For this problem, anchor the calculation to <strong>{e(scale)}</strong>. State whether that figure describes average or peak load, then size the first version with at least 2× headroom and a documented scale-out trigger. Numbers are valuable only when they justify a component or trade-off.</p><div class="callout"><strong>Capacity conversation</strong><p>Estimate the dominant read/write path, payload size, retention window, and hot-key factor. Then say which estimate is uncertain and how production telemetry would refine it.</p></div></section>
<section class="section" id="data-model-deep"><h2><span class="section-no">03B · DATA</span>Records, indexes, and consistency boundaries</h2><pre>{e(primary_key)}  // partition or primary key
owner_id / tenant_id
state + version
created_at + updated_at
idempotency_key
policy / configuration

INDEX(owner_id, updated_at)
UNIQUE(idempotency_key, owner_id)
CONDITIONAL UPDATE ... WHERE version = expected_version</pre><div class="grid2"><div class="card"><h3>Authoritative state</h3><p>{e(p['storage'])}</p><p>Keep the record narrow on the hot path. Large payloads, histories, and analytics belong in systems designed for sequential writes or object storage.</p></div><div class="card"><h3>Partition and consistency</h3><p>{e(p['partition'])}</p><p>Use strong or conditional consistency for ownership and state transitions. Read models, dashboards, and derived search/index views may lag if the UI communicates freshness.</p></div></div><h3>Index discipline</h3><ul><li>Every index must correspond to a concrete query; extra indexes multiply write cost and migration risk.</li><li>Cursor pagination should encode a stable sort key plus unique ID; offsets become slow and unstable as data changes.</li><li>Tombstones preserve delete/disable semantics during replication and cache invalidation; purge later under retention policy.</li><li>Store schema/event versions so rolling deployments and replays can understand old records.</li></ul></section>
<section class="section" id="components"><h2><span class="section-no">04B · RESPONSIBILITIES</span>What every component owns</h2><div class="table-wrap"><table><thead><tr><th>Component</th><th>Responsibility</th><th>Operational owner</th></tr></thead><tbody>{comp_rows}</tbody></table></div><p>Keep boundaries honest: services should own a business capability and its data contract, not exist merely because a diagram looks more “microservice-like.” Begin with fewer deployables and split when scale, isolation, or ownership requires it.</p></section>
<section class="section" id="algorithm"><h2><span class="section-no">05B · ALGORITHM</span>Online decision and idempotent mutation</h2><p>{e(p['algorithm'])}</p><pre>handle(command):
    identity = authenticate(command.credentials)
    validate(command.payload)
    prior = idempotency_store.get(identity, command.key)
    if prior: return prior.result

    route = partition_map.owner(command.{e(primary_key)})
    current = authoritative_store.read(route)
    next_state, side_effects = domain.apply(current, command)
    authoritative_store.compare_and_set(current.version, next_state)
    idempotency_store.commit(command.key, next_state.result)
    event_log.append(side_effects)
    return next_state.result</pre><div class="callout"><strong>Exactly-once business effect</strong><p>Networks only give retries and uncertainty. Combine idempotency records, conditional writes, immutable event IDs, and reconciliation to make the user-visible effect occur once.</p></div></section>
<section class="section" id="caching"><h2><span class="section-no">06B · PERFORMANCE</span>Caching, hot keys, and backpressure</h2><div class="grid3"><div class="card"><h3>Cache policy</h3><p>Use cache-aside for read-heavy immutable or slowly changing records. Version keys or publish invalidations after commit. Add TTL jitter and short negative caching.</p></div><div class="card"><h3>Hot-key defense</h3><p>Detect per-key skew, add process-local and replicated reads, coalesce misses, salt only where ordering permits, and isolate abusive tenants.</p></div><div class="card"><h3>Backpressure</h3><p>Bound every queue and buffer. Shed low-priority work, return retry timing, and scale from lag/oldest-item age—not CPU alone.</p></div></div><p>A cache is not a correctness layer. The authoritative store and version rules determine truth; cached entries are disposable projections that must be rebuildable.</p></section>
<section class="section" id="deep-dive-expanded"><h2><span class="section-no">07B · DEEP DIVE</span>Reason through the hard parts</h2>{focus_details}</section>
<section class="section" id="failure-matrix"><h2><span class="section-no">08B · FAILURE MATRIX</span>Degrade intentionally</h2><div class="table-wrap"><table><thead><tr><th>Failure</th><th>Runtime behavior</th><th>Recovery</th></tr></thead><tbody>{failure_rows}</tbody></table></div><p>For every dependency, name its timeout, retry budget, circuit-breaker policy, and whether the endpoint fails open, fails closed, or serves stale data. “Highly available” is not an answer until degraded behavior is explicit.</p></section>
<section class="section" id="regions"><h2><span class="section-no">08C · EVOLUTION</span>Multi-region, migrations, and rollout</h2><div class="flow"><div class="flow-item"><div><b>Start with multi-zone</b><p>Replicate within one region, automate failover, and prove backups and reconciliation before accepting cross-region write complexity.</p></div></div><div class="flow-item"><div><b>Add global reads or stateless edges</b><p>Route latency-sensitive reads near users while retaining one mutation owner when correctness coordination is expensive.</p></div></div><div class="flow-item"><div><b>Introduce regional ownership</b><p>Assign each aggregate or partition a home region. Move ownership through an epoch/fencing transition rather than simultaneous writers.</p></div></div><div class="flow-item"><div><b>Migrate safely</b><p>Use expand/contract schemas, dual-read verification, backfills with checkpoints, shadow traffic, canaries, and reversible cutovers.</p></div></div></div></section>
<section class="section" id="security-deep"><h2><span class="section-no">08D · SECURITY</span>Threat model and abuse controls</h2><p>{e(p['security'])}</p><div class="grid2"><div class="card"><h3>Trust boundaries</h3><ul><li>External client to edge: authentication, validation, rate limits, payload caps.</li><li>Service to service: workload identity, least privilege, encryption, deadline propagation.</li><li>Control plane to data plane: signed/versioned configuration and audited writers.</li><li>Operator access: just-in-time privilege and immutable audit logs.</li></ul></div><div class="card"><h3>Abuse and privacy</h3><ul><li>Quotas by tenant, actor, resource, and network—not one spoofable dimension.</li><li>Minimize retained personal data and enforce deletion/retention workflows.</li><li>Scan or sandbox untrusted content and prevent SSRF in fetch/preview features.</li><li>Alert on enumeration, anomalous fan-out, repeated conflicts, and privilege changes.</li></ul></div></div></section>
<section class="section" id="observability-deep"><h2><span class="section-no">08E · OPERATIONS</span>Dashboards, alerts, and reconciliation</h2><div class="table-wrap"><table><thead><tr><th>Signal</th><th>Examples</th><th>Alert when</th></tr></thead><tbody><tr><td>User experience</td><td>success rate, p50/p95/p99 latency, freshness</td><td>SLO burn rate exceeds fast or slow window budget.</td></tr><tr><td>Dependencies</td><td>timeouts, circuit state, replica lag, cache hit ratio</td><td>Fallback load threatens the source of truth.</td></tr><tr><td>Async pipeline</td><td>consumer lag, oldest age, retries, DLQ growth</td><td>Business freshness or retention window is at risk.</td></tr><tr><td>Correctness</td><td>conflicts, duplicate suppression, reconciliation mismatch</td><td>Invariant violations are non-zero or trending upward.</td></tr><tr><td>Capacity</td><td>shard skew, queue saturation, storage growth</td><td>Forecasted exhaustion enters the change lead-time window.</td></tr></tbody></table></div><p>Carry a trace ID through synchronous calls and include event/aggregate IDs in asynchronous spans. Metrics detect, traces localize, structured logs explain, and reconciliation proves business correctness.</p></section>
<section class="section" id="followup-answers"><h2><span class="section-no">09B · ANSWER GUIDE</span>How to answer the follow-ups</h2>{answer_details}</section>
<section class="section" id="checklist"><h2><span class="section-no">10B · CHECKLIST</span>Before you say “done”</h2><div class="grid2"><div class="card"><h3>Design completeness</h3><ul><li>I stated the invariant and partition key.</li><li>I showed normal and retry paths.</li><li>I separated authoritative state from derived views.</li><li>I explained consistency per operation.</li><li>I covered one hot-key and one backlog scenario.</li></ul></div><div class="card"><h3>Production completeness</h3><ul><li>I named timeouts and degraded behavior.</li><li>I addressed abuse and tenant isolation.</li><li>I identified SLOs and correctness metrics.</li><li>I explained regional evolution and migration.</li><li>I summarized the most important trade-off.</li></ul></div></div></section>
'''
