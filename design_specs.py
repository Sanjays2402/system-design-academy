"""System-specific architecture and implementation specifications.

Every design intentionally names its own services, stores, flows, API verbs,
and correctness risks. These are not category-level filler.
"""

def S(nodes, api, records, steps, failures):
    return {"nodes": nodes, "api": api, "records": records, "steps": steps, "failures": failures}

SPECS = {
"url-shortener": S(
 ["Browser / SDK","Anycast DNS","CDN / Edge","Redirect API","URL Create API","Redis Cache","Short-Code Router","Metadata Shards","Range ID Allocator","Kafka Click Stream","Analytics Workers","OLAP Store","Abuse Scanner","Config / SLOs"],
 ["POST /v1/links — create alias with idempotency key","GET /{code} — cache-first 301/302 redirect","PATCH /v1/links/{code} — versioned destination edit","GET /v1/links/{code}/stats — aggregated clicks"],
 ["links(code PK, long_url, owner_id, redirect_type, version, expires_at)","idempotency(owner_id, key UNIQUE, code, response)","click_event(event_id, code, occurred_at, region, referrer_hash)","INDEX links(owner_id, created_at DESC)"],
 ["Validate and canonicalize the destination; run synchronous deny-list checks.","Reserve a numeric ID range locally, allocate one ID, and Base62 encode it.","Conditionally insert code→URL; custom aliases use a uniqueness constraint.","On redirect, read edge/process cache, then Redis, then the owning metadata shard.","Return redirect immediately and publish a sampled/deduplicated click event asynchronously."],
 ["Viral code overloads one cache shard","Client times out after alias commit","Editable destination races with cached redirect","ID worker loses its range lease","Analytics lag grows without affecting redirects"]),
"rate-limiter": S(
 ["API Client","Global Edge","Gateway Worker","Local Token Cache","Limiter Library","Key Normalizer","Redis Cluster","Lua / Atomic Counter","Policy Service","Policy Snapshot CDN","Decision Metrics","Quota Audit Log"],
 ["POST /v1/policies — publish versioned quota","GET /v1/policies/{id} — inspect effective policy","CHECK tenant:user:route — internal allow/deny decision","GET /v1/usage/{key} — bounded usage view"],
 ["policy(policy_id PK, scope, algorithm, capacity, refill_rate, version)","counter(limit_key, window, used, expires_at)","decision(event_id, key_hash, policy_version, allowed, remaining)","INDEX policy(scope, active_version)"],
 ["Normalize tenant, identity, route, and cost into one stable limit key.","Evaluate a signed local policy snapshot before touching remote state.","Spend a small local token lease when available; otherwise execute one atomic Redis script.","Return allowed, remaining, reset, and retry-after without blocking on metrics.","Stream decisions for billing, anomaly detection, and lease reconciliation."],
 ["Redis unavailable forces explicit fail-open/closed policy","Hot enterprise tenant saturates one counter shard","Clock boundary creates fixed-window burst","Policy versions differ across gateways","Retries consume quota twice without request identity"]),
"notification-system": S(
 ["Product Service","Notification API","Preference Service","Template Renderer","Schedule Store","Priority Router","Kafka Topics","Email Worker","Push Worker","SMS Worker","Provider Adapters","Delivery Ledger","DLQ / Replay","Webhook Ingest"],
 ["POST /v1/notifications — accept one idempotent send","POST /v1/campaigns — enqueue fan-out campaign","DELETE /v1/notifications/{id} — cancel if not claimed","GET /v1/notifications/{id} — delivery status"],
 ["notification(id PK, user_id, template_id, priority, schedule_at, state)","delivery(notification_id, channel, attempt, provider_id, status)","preference(user_id, channel, topic, enabled, quiet_hours)","UNIQUE producer_id,idempotency_key"],
 ["Resolve recipient identity, consent, quiet hours, and required channels.","Render a versioned template and persist the notification before acknowledgment.","Route by priority and channel to replayable partitions.","A channel worker claims a delivery lease, applies provider rate limits, and sends.","Verify provider callbacks, dedupe by provider event ID, and update the ledger."],
 ["Provider returns success after worker timeout","Bulk campaign starves password resets","Preference changes after scheduling","Poison template repeatedly fails rendering","Provider outage fills retry queues"]),
"file-storage": S(
 ["Desktop / Web Client","Global API","Auth / Sharing","Metadata Service","Upload Coordinator","Chunk Hash Service","Multipart Session Store","Object Blob Store","Version Manifest DB","Change Journal","Sync Cursor Service","Virus Scanner","Thumbnail Workers","CDN / Download"],
 ["POST /v1/uploads — create resumable session","PUT /v1/uploads/{id}/parts/{n} — checksum part","POST /v1/uploads/{id}/commit — publish manifest","GET /v1/changes?cursor= — incremental sync"],
 ["file(file_id PK, parent_id, owner_id, current_version, etag)","version(file_id, version, manifest_uri, size, content_hash)","upload(upload_id, expected_parts, received_bitmap, expires_at)","journal(owner_id, sequence, change_type, file_id)"],
 ["Create an upload session and return signed part URLs.","Upload chunks independently; verify length and checksum at the storage edge.","Build an immutable ordered manifest only when all required parts exist.","Atomically advance current_version and append one change-journal entry.","Sync clients resume from a monotonic cursor and resolve divergent edits as versions."],
 ["Commit arrives before final part replication","Two devices update the same base version","Shared-link permission is revoked while cached","Chunk dedupe leaks cross-tenant existence","Journal cursor points to compacted history"]),
"chat-system": S(
 ["Mobile / Web","Anycast Edge","WebSocket Gateway","Session Directory","Auth / Membership","Conversation Router","Message Sequencer","Partitioned Message Log","Inbox Fanout","Push Service","Presence Store","Receipt Aggregator","Media Store","Offline Sync API"],
 ["WS SEND_MESSAGE(client_msg_id, conversation_id, body)","GET /v1/sync?cursor= — resume missed events","POST /v1/conversations — create membership","PUT /v1/receipts/{conversation_id} — advance read cursor"],
 ["message(conversation_id, sequence, message_id, sender_id, body_ref)","device_cursor(user_id, device_id, partition, sequence)","membership(conversation_id, user_id, role, version)","receipt(conversation_id, user_id, delivered_seq, read_seq)"],
 ["Authenticate the socket and resolve its gateway in the session directory.","Route a send to the conversation partition and recheck membership version.","Deduplicate client_msg_id, assign the next partition sequence, and durably append.","Acknowledge the sender, then fan out to online gateways and offline inboxes.","Devices resume from cursors; receipt updates coalesce to monotonic sequence advances."],
 ["Gateway dies after log append before acknowledgment","Large group fan-out overwhelms online delivery","Membership revoked during an in-flight send","Two devices race receipt cursors","Regional partition owner becomes unavailable"]),
"news-feed": S(
 ["Mobile Client","Feed API","Auth / Policy","Candidate Service","Social Graph","Post Store","Fanout Router","Timeline Workers","Timeline Cache","Celebrity Pull Path","Ranking Service","Feature Store","Ads Mixer","Impression Stream"],
 ["POST /v1/posts — commit source post","GET /v1/feed?cursor= — ranked page","DELETE /v1/posts/{id} — tombstone and invalidate","POST /v1/impressions — batched exposure events"],
 ["post(post_id PK, author_id, body_ref, visibility, created_at)","timeline(user_id, rank_key, post_id, source, inserted_at)","follow(follower_id, followee_id, state)","cursor(snapshot_time, rank_key, post_id)"],
 ["Commit the post and emit one immutable post-created event.","Fan out ordinary authors into follower timeline partitions; mark celebrities pull-on-read.","At read, merge materialized timeline, celebrity candidates, and eligible ads.","Filter privacy/deletes, fetch features, rank a bounded candidate set, and paginate by cursor.","Log impressions asynchronously with model and candidate-set versions."],
 ["Celebrity post creates billion-edge fan-out","Feed cursor sees inserts between pages","Deleted private post remains cached","Ranking service exceeds latency budget","Fanout lag causes stale timelines"]),
"social-post-service": S(
 ["Creator App","Media Upload Edge","Post API","Auth / Privacy","Media Scanner","Transcode Workers","Object Storage","Post Metadata DB","Social Graph","Timeline Event Bus","Fanout Service","Search Indexer","Moderation Service","CDN"],
 ["POST /v1/media/uploads — signed multipart upload","POST /v1/posts — publish media references","PATCH /v1/posts/{id} — versioned edit policy","DELETE /v1/posts/{id} — tombstone and propagate"],
 ["post(post_id PK, author_id, visibility, text, version, state)","media(media_id PK, owner_id, source_uri, rendition_manifest, scan_state)","follow(follower_id, followee_id, state, version)","moderation(object_id, decision, reason, policy_version)"],
 ["Upload media directly, checksum it, scan it, and generate renditions.","Validate ownership of ready media and commit immutable post identity plus version.","Publish post-created to timeline, search, notification, and moderation consumers.","Serve text/metadata from post storage and immutable renditions through CDN.","Edits create a new version; deletes create a tombstone that invalidates projections."],
 ["Media upload completes but post never commits","Privacy changes while timelines contain the post","Moderation removes a viral cached asset","Fanout consumer replays post-created","Edit and delete race on the same version"]),
"video-streaming": S(
 ["Creator Client","Resumable Upload API","Source Object Store","Media Probe","Workflow Orchestrator","Transcode Fleet","Quality Validator","Rendition Store","Manifest Publisher","Catalog DB","Playback API","Token / DRM Service","Multi-CDN Router","Viewer Player","QoE Event Stream"],
 ["POST /v1/videos/uploads — resumable source session","POST /v1/videos/{id}/publish — atomic manifest publish","GET /v1/playback/{id} — authorized manifest","POST /v1/qoe — batched playback telemetry"],
 ["video(video_id PK, owner_id, state, source_uri, manifest_version)","rendition(video_id, codec, resolution, bitrate, segment_prefix, state)","job(video_id, profile, attempt, lease_until)","manifest(video_id, version, renditions, published_at)"],
 ["Verify and probe the committed source before creating rendition jobs.","Fan out codec/resolution tasks with deterministic output keys and retry-safe jobs.","Validate duration, keyframes, audio sync, and segment checksums for every rendition.","Atomically publish one manifest version only after the minimum ladder is complete.","Authorize playback, issue short-lived tokens, and let the player adapt from throughput/buffer."],
 ["One rendition repeatedly fails","Manifest references a missing segment","CDN region serves stale authorization","Upload resumes with conflicting part","Live encoder falls behind wall clock"]),
"ride-hailing": S(
 ["Rider App","Driver App","Realtime Gateway","Location Ingest","Map Matcher","Geo Cell Index","Supply Service","Matching Engine","Driver Lease Store","Trip State Service","Pricing Service","ETA / Route Service","Payment Events","Safety / Audit"],
 ["POST /v1/rides/quotes — price and ETA estimate","POST /v1/rides — idempotent ride request","POST /v1/drivers/{id}/locations — batched updates","POST /v1/trips/{id}/transitions — versioned state move"],
 ["driver_location(driver_id, cell, lat, lon, heading, observed_at)","trip(trip_id PK, rider_id, driver_id, state, version)","offer(offer_id, trip_id, driver_id, lease_until, state)","pricing_quote(quote_id, inputs_hash, amount, expires_at)"],
 ["Map-match driver updates and upsert only newer observations into the geo index.","Search the pickup cell, expand rings, filter eligibility, and rank by ETA.","Create short candidate offers; reserve one driver using a conditional lease.","Advance trip state with expected version and append each transition to the event trail.","Use location/trip events for pricing, safety, receipts, and post-trip settlement."],
 ["Two matchers offer the same driver","Stale GPS makes nearest driver wrong","Accepted driver disconnects before pickup","Surge quote expires during request","Trip transition arrives out of order"]),
"ticket-booking": S(
 ["Buyer Client","Bot Defense","Virtual Waiting Room","Catalog API","Availability Cache","Inventory Shard","Reservation Service","Hold Expiry Wheel","Order Orchestrator","Payment Gateway","Ticket Issuer","Order Ledger","Refund Service","Audit / Fraud"],
 ["GET /v1/events/{id}/seats — versioned availability","POST /v1/holds — atomic seat hold","POST /v1/orders — idempotent checkout","POST /v1/orders/{id}/refunds — restore according to policy"],
 ["seat(event_id, seat_id, state, version, hold_id)","hold(hold_id PK, buyer_id, seats, expires_at, state)","order(order_id PK, hold_id, payment_intent, state)","ticket(ticket_id, order_id, barcode_hash, status)"],
 ["Admit a bounded cohort from the waiting room and issue a signed queue token.","Read approximate availability, but create holds with transactional/conditional seat updates.","Schedule hold expiry and make release idempotent against confirmation.","Authorize payment, confirm the hold, issue tickets, and append the order ledger.","If payment outcome is uncertain, reconcile by intent before releasing or charging again."],
 ["Two buyers select the same seat","Payment succeeds after hold timeout","Expiry worker races confirmation","Waiting-room tokens are replayed","Refund and ticket scan overlap"]),
"api-gateway": S(
 ["API Client","Anycast / DNS","DDoS / WAF","TLS Terminator","Gateway Worker","JWT / mTLS Auth","Rate Limiter","Route Matcher","Service Discovery","Load Balancer","Backend Service","Response Cache","Policy Control Plane","Telemetry Pipeline"],
 ["PUT /v1/routes/{id} — versioned route config","PUT /v1/policies/{id} — auth/limit/retry policy","GET /v1/snapshots/{version} — signed data-plane bundle","PROXY /{path} — deadline-bound request"],
 ["route(route_id, host, path, methods, cluster, policy_refs, version)","cluster(cluster_id, endpoints, health_policy, protocol)","snapshot(version PK, checksum, signature, created_at)","request_log(trace_id, route_id, outcome, latency_bucket)"],
 ["Terminate TLS, reject malformed traffic, and propagate a request deadline.","Authenticate, authorize the route/resource, and apply local or distributed quotas.","Match a route from one immutable snapshot and select a healthy backend endpoint.","Retry only safe requests within the remaining budget; trip per-cluster circuits.","Stream bounded telemetry while the data plane continues on last-known-good config."],
 ["Bad snapshot reaches part of fleet","Retry storm amplifies backend outage","Discovery returns zero healthy endpoints","Large body exhausts gateway memory","Auth provider is unavailable"]),
"distributed-cache": S(
 ["Application","Client Library","Key Hasher","Membership Snapshot","Primary Cache Node","Replica Cache Node","Memory Slabs","Eviction Engine","TTL Wheel","Replication Stream","Rebalancer","Hot-Key Detector","Origin Loader","Cache Metrics"],
 ["GET key — routed lookup with version metadata","SET key value ttl — primary then replica policy","DELETE key — tombstone/invalidation","GET /admin/ring — membership generation"],
 ["entry(key_hash PK, value, version, expires_at, size)","node(node_id, tokens, zone, generation, state)","replication(key_hash, version, operation)","hot_key(key_hash, qps, miss_rate, sampled_at)"],
 ["Hash the key against a versioned virtual-node ring in the client.","Read primary or permitted replica; lazily expire and promote recency metadata.","On miss, coalesce loaders so one caller fetches origin and populates the value.","Replicate according to durability mode and acknowledge at the chosen boundary.","During rebalance, dual-read old/new owners and stream ranges before ownership cutover."],
 ["Node loss causes synchronized origin misses","One key exceeds one node network capacity","Rebalance evicts the working set","Stale replica serves deleted value","Oversized values fragment memory"]),
"job-scheduler": S(
 ["Job Producer","Scheduler API","Job Definition DB","Timing Wheel","Due-Time Index","Shard Leader","Lease / Claim Store","Dispatch Queue","Priority Router","Worker Pool","Execution Heartbeats","Retry / DLQ","Cron Expander","History / Audit"],
 ["POST /v1/jobs — create delayed/recurring job","PATCH /v1/jobs/{id} — pause or reschedule version","POST /v1/executions/{id}/heartbeat — renew lease","GET /v1/jobs/{id}/history — execution attempts"],
 ["job(job_id PK, schedule, payload_ref, priority, state, version)","execution(execution_id, job_id, scheduled_for, attempt, lease_until, state)","dedupe(job_id, scheduled_for UNIQUE, execution_id)","INDEX jobs(shard, next_run_at)"],
 ["Persist the definition and expand only the next bounded recurrence horizon.","Shard by job ID and load near-future due times into a timing wheel.","At due time create one execution identity, claim a lease, and enqueue by priority.","Workers heartbeat, execute idempotently, then conditionally mark success or retry.","Expired leases requeue the same execution identity; DLQ preserves terminal failures."],
 ["Scheduler leader dies after enqueue","Clock jump advances or delays buckets","Long job loses lease during GC pause","Cron expansion creates duplicate occurrence","Priority tenant starves background work"]),
"web-crawler": S(
 ["Seeds / Sitemaps","URL Normalizer","Seen Bloom Filter","Durable URL Set","Host Frontier","Politeness Scheduler","DNS Cache","Fetcher Fleet","Robots Cache","Content Store","Parser / Extractor","Canonical Resolver","Link Graph","Recrawl Scorer"],
 ["POST /v1/seeds — add crawl scope","GET /v1/frontier/stats — host backlog","PUT /internal/fetch-result — commit outcome and links","POST /v1/recrawl — adjust freshness policy"],
 ["url(url_hash PK, canonical_url, host, state, next_fetch_at)","host(host_hash, robots_version, delay_ms, next_allowed_at)","fetch(url_hash, fetched_at, status, content_hash, storage_uri)","link(source_hash, target_hash, discovered_at)"],
 ["Normalize and canonicalize a discovered URL before checking fast and durable dedupe.","Place it in a per-host frontier ordered by priority and next allowed fetch time.","A politeness scheduler leases eligible URLs while enforcing robots and host concurrency.","Fetch with strict size/type/time limits, persist raw content, parse links, and commit result.","Score change frequency and importance to schedule the next crawl."],
 ["Crawler trap generates infinite URL space","Slow host holds worker resources","robots.txt changes during crawl","Duplicate content has many URLs","JavaScript renderer exhausts sandbox"]),
"search-autocomplete": S(
 ["Search Box","Edge Cache","Suggestion API","Normalizer / Locale","Prefix Router","FST Shards","Recent Overlay","Candidate Merger","Safety Filter","Personalization","Top-K Ranker","Snapshot Builder","Query Event Stream","Removal Control Plane"],
 ["GET /v1/suggest?q=&locale= — top-k suggestions","POST /internal/events — query/click aggregate","POST /v1/removals — urgent unsafe-term removal","PUT /v1/snapshots/{version} — atomic publish"],
 ["suggestion(normalized_query, locale, frequency, recency, safety_state)","snapshot(version, locale, shard_range, uri, checksum)","overlay(prefix, suggestion, score_delta, expires_at)","removal(term_hash, reason, effective_version)"],
 ["Normalize Unicode, case, whitespace, and locale before routing the prefix.","Read bounded candidates from an in-memory FST plus a small recent-trend overlay.","Merge shard results, remove unsafe/deleted terms, and optionally blend personal context.","Rank by frequency, recency, edit distance, locale, and business/safety constraints.","Publish immutable bulk snapshots atomically and expire the streaming overlay."],
 ["Popular one-character prefix becomes hot","Unsafe term must disappear immediately","Snapshot versions differ across replicas","Trend poisoning manipulates ranking","Personalization leaks prior queries"]),
"logging-monitoring": S(
 ["App SDK / Agent","Local Spool","Regional Collector","Tenant Quota","Durable Ingest Log","Parser / Redactor","Schema Registry","Hot Indexer","Search Shards","Trace Correlator","Alert Evaluator","Object Archive","Query Gateway","Retention Compactor"],
 ["POST /v1/logs — compressed batch ingest","GET /v1/search?query=&cursor= — tenant query","POST /v1/rules — versioned alert rule","GET /v1/export/{job} — archived result"],
 ["log_event(tenant, event_id, timestamp, service, severity, fields)","segment(tenant, time_range, index_uri, data_uri, checksum)","alert_rule(rule_id, query, window, threshold, version)","tenant_budget(tenant, bytes_per_sec, retention_class)"],
 ["Batch/compress at the agent and spill to bounded disk when collectors fail.","Collectors authenticate tenant, enforce byte/cardinality quotas, and append durably.","Parse against a schema, redact secrets, and route time-partitioned segments to indexers.","Serve recent indexed search; federate archived scans asynchronously for old windows.","Evaluate alert windows from durable offsets and dedupe notifications by incident key."],
 ["Logging storm consumes service disk","Parser poison event blocks partition","Tenant query fans across every shard","Secret reaches archive before redaction","Alert evaluator replays and duplicates pages"]),
"metrics-system": S(
 ["Instrumented Service","Scraper / Agent","Service Discovery","Remote Write Gateway","Label Guard","Durable Sample Log","Series Router","TSDB Ingest Node","WAL / Head Block","Object Block Store","Compactor","Query Frontend","Rule Evaluator","Alert Manager"],
 ["POST /api/v1/write — compressed sample batch","GET /api/v1/query_range — bounded time-series query","POST /v1/rules — recording/alert rule","GET /v1/cardinality — budget diagnostics"],
 ["series(fingerprint PK, metric, sorted_labels, tenant)","sample(fingerprint, timestamp, value)","block(tenant, min_time, max_time, level, object_uri)","rule(rule_id, expression, interval, for_duration, version)"],
 ["Discover targets and scrape with bounded concurrency or accept authenticated remote write.","Normalize labels, reject cardinality violations, and append batches to a durable log/WAL.","Route each fingerprint to one ingest owner and compact head chunks into immutable blocks.","Query frontend splits time/shards, deduplicates replicas, and caches partial results.","Rule evaluators checkpoint durable timestamps and send deduplicated alert state."],
 ["Unbounded label creates millions of series","Late sample targets compacted block","Query scans too many series","Replica dedupe hides missing data","Rule evaluation misses interval during failover"]),
"distributed-kv-store": S(
 ["KV Client","Token-Aware Router","Membership / Gossip","Partition Coordinator","WAL / Memtable","SSTable Engine","Primary Replica","Follower Replicas","Quorum Tracker","Hinted Handoff","Read Repair","Merkle Anti-Entropy","Compaction","Backup / Restore"],
 ["PUT /v1/kv/{key}?consistency=QUORUM","GET /v1/kv/{key}?consistency=ONE","DELETE /v1/kv/{key} — versioned tombstone","GET /admin/ring — token ownership"],
 ["cell(key, value, vector_or_timestamp, tombstone, expires_at)","token_range(start, end, replicas, epoch)","hint(target_node, mutation, expires_at)","sstable(range, min_version, max_version, checksum)"],
 ["Hash the key to a token and route using the current ring epoch.","Coordinator writes WAL/memtable on replica set and waits for configured acknowledgments.","Reads gather enough replicas, reconcile versions, and schedule read repair.","Unavailable targets receive bounded hints; anti-entropy compares Merkle ranges later.","Compaction merges versions while retaining tombstones until every replica repair horizon passes."],
 ["Sloppy quorum accepts divergent concurrent writes","Tombstone removed before lagging replica returns","Node joins and streams stale range","Compaction saturates disk","Ring partitions disagree on ownership epoch"]),
"payment-system": S(
 ["Checkout / Merchant","Payment API","Idempotency Store","Payment Orchestrator","Risk Engine","Token Vault","Processor Router","Processor Adapter","Webhook Gateway","Payment State DB","Double-Entry Ledger","Outbox / Kafka","Reconciliation","Refund / Dispute","Audit / Compliance"],
 ["POST /v1/payment_intents — create idempotent intent","POST /v1/payment_intents/{id}/confirm — authorize/capture","POST /v1/refunds — ledger-backed refund","POST /v1/webhooks/{processor} — signed callback"],
 ["payment_intent(id PK, merchant_id, amount, currency, state, version)","ledger_entry(txn_id, account_id, debit, credit, currency, effective_at)","processor_attempt(intent_id, attempt, provider_ref, status)","idempotency(merchant_id, key UNIQUE, request_hash, response)"],
 ["Authenticate merchant, validate amount/currency, and atomically create intent/idempotency result.","Score risk and resolve a tokenized funding instrument without exposing raw card data.","Route to a processor and record each uncertain attempt before external I/O.","Conditionally transition intent and append balanced ledger postings in one boundary.","Verify/dedupe webhooks and reconcile provider settlements against internal attempts/ledger."],
 ["Client times out after successful capture","Processor returns unknown outcome","Webhook arrives before synchronous response","Ledger posting is unbalanced","Settlement file disagrees with captured amount"]),
"shopping-cart": S(
 ["Buyer Client","Cart API","Cart Store","Catalog Service","Pricing Engine","Promotion Engine","Tax / Shipping","Inventory Service","Reservation Store","Checkout Saga","Order Service","Payment Service","Outbox Events","Fulfillment"],
 ["PUT /v1/carts/{id}/items — idempotent item mutation","POST /v1/carts/{id}/quote — authoritative price","POST /v1/checkouts — start saga","GET /v1/orders/{id} — durable result"],
 ["cart(cart_id PK, owner_id, items, version, expires_at)","quote(quote_id, cart_version, lines, totals, expires_at)","reservation(reservation_id, sku, quantity, expires_at, state)","order(order_id PK, quote_id, payment_intent, state)"],
 ["Store cart intent with optimistic versioning; merge guest/authenticated carts explicitly.","At checkout recompute catalog, promotions, tax, shipping, and produce an expiring quote.","Reserve inventory per SKU with idempotent tokens and start the checkout saga.","Confirm payment and create order; compensate stock/payment on terminal failure.","Publish order events through an outbox for fulfillment, email, and analytics."],
 ["Price changes after item added","Two checkouts consume same inventory","Payment succeeds but order write times out","Coupon budget races across carts","Reservation expires during payment challenge"]),
"collaborative-editor": S(
 ["Editor Client","Local Document Model","Realtime Gateway","Session Directory","Permission Service","Document Router","OT / CRDT Engine","Canonical Op Log","Snapshot Builder","Document Store","Presence Service","Cursor Broadcast","Offline Merge","Export / Audit"],
 ["WS APPLY_OP(doc_id, client_seq, base_version, op)","GET /v1/docs/{id}/sync?version= — snapshot plus ops","POST /v1/docs/{id}/share — versioned ACL","POST /v1/docs/{id}/export — immutable revision"],
 ["operation(doc_id, server_seq, actor_id, client_op_id, payload)","snapshot(doc_id, version, content_uri, checksum)","client_cursor(doc_id, device_id, acked_seq)","permission(doc_id, principal, role, version)"],
 ["Apply edits locally for instant feedback and enqueue client operation identity.","Gateway routes by document; server rechecks permission and base version.","Transform/merge against concurrent operations, assign canonical sequence, and append durably.","Broadcast canonical operation; clients reconcile pending local operations and acknowledge cursor.","Snapshot periodically and compact only after active/offline retention guarantees."],
 ["Offline client returns with compacted base","Permission revoked during active session","Duplicate client operation reconnects","Two operations target deleted range","Snapshot checksum differs from op replay"]),
"object-storage": S(
 ["SDK / CLI","Global Front Door","Auth / Bucket Policy","Metadata Partition","Multipart Coordinator","Placement Service","Chunk Gateway","Storage Nodes","Erasure Encoder","Manifest Store","Replication / Repair","Integrity Scrubber","Lifecycle Tiering","Event Notifications","Range Read Cache"],
 ["POST /bucket/key?uploads — multipart session","PUT /bucket/key?partNumber=&uploadId= — part","POST /bucket/key?uploadId= — atomic manifest commit","GET /bucket/key Range: bytes= — versioned range read"],
 ["object(bucket, key, version, manifest_id, etag, state)","manifest(manifest_id, ordered_chunks, erasure_scheme, checksum)","chunk(chunk_id, placements, size, checksum)","upload(upload_id, bucket, key, parts, expires_at)"],
 ["Authorize bucket/key and create a version-scoped multipart upload.","Checksum parts, erasure-code chunks, and place fragments across failure domains.","At complete, validate ordered parts and atomically publish an immutable manifest/version.","Range reads map bytes to chunks, fetch sufficient fragments, verify, and optionally cache.","Scrub continuously, repair under-replicated fragments, and tier versions by lifecycle policy."],
 ["Manifest publishes before fragment durability","Rack loss removes too many fragments","Multipart complete races abort","Corrupt fragment passes disk read","Delete marker conflicts with versioned read"]),
"message-queue": S(
 ["Producer","Schema Registry","Partitioner","Broker Front Door","Partition Leader","Follower Replicas","Commit Quorum","Segment Log","Index / Page Cache","Controller Quorum","Consumer Group Coordinator","Consumer","Offset Store","Tiered Object Store","Compaction / Retention"],
 ["PRODUCE(topic, key, batch, producer_epoch, sequence)","FETCH(topic, partition, offset, max_bytes)","COMMIT(group, partition, offset)","ADMIN create/expand topic — versioned metadata"],
 ["record(topic, partition, offset, timestamp, key, value, producer_seq)","partition(topic, id, leader, replicas, epoch, high_watermark)","group_offset(group, topic, partition, offset, generation)","segment(base_offset, max_offset, checksum, tier_uri)"],
 ["Validate schema and choose partition by stable key or explicit partition.","Leader dedupes producer epoch/sequence, appends batch, and replicates to followers.","Advance high watermark after in-sync quorum and acknowledge according to durability policy.","Consumers fetch ordered batches and commit offsets under a group generation.","Retention/compaction closes segments and optionally moves immutable data to object storage."],
 ["Leader fails after local append before quorum","Consumer rebalance overlaps processing","Slow replica falls out of ISR","Producer epoch is reused after retry","Compaction removes required tombstone"]),
"feature-flags": S(
 ["Application SDK","In-Process Evaluator","Local Snapshot Cache","Streaming Relay","Edge Relay Tier","Config Distribution Log","Flag Control Plane","Validation / Policy","Versioned Config DB","Rollout Controller","Experiment Assigner","Exposure Stream","Audit Log","Emergency Kill Path"],
 ["PUT /v1/flags/{key} — validated version","POST /v1/flags/{key}/rollouts — staged rollout","GET /v1/sdk/snapshot — signed snapshot","STREAM /v1/sdk/updates — ordered deltas"],
 ["flag(project, key, version, rules, default, state)","environment(project, env, active_snapshot)","rollout(flag_key, stage, cohort, health_gate, state)","exposure(subject_hash, flag_key, variation, version)"],
 ["Validate rule syntax, prerequisites, and permissions before storing immutable version.","Build and sign a complete environment snapshot, then append its version to distribution log.","Relays stream ordered deltas; SDK atomically swaps snapshots and retains last-known-good.","Evaluator hashes stable subject attributes for deterministic percentage assignment.","Rollout controller advances cohorts only while health gates pass; kill path promotes safe default."],
 ["Prerequisite cycle enters config","SDK misses deltas during disconnect","Percentage assignment changes after rule edit","Bad rollout harms one cohort","Control plane unavailable during emergency"]),
"recommendation-system": S(
 ["User Request","Recommendation API","Context Builder","Online Feature Store","Candidate Router","Collaborative Index","Content / Vector Index","Trending Store","Candidate Union","Policy / Safety","Online Ranker","Diversity Reranker","Model Registry","Exposure Log","Offline Lake / Training"],
 ["GET /v1/recommendations?surface=&cursor=","POST /v1/events — impression/click/conversion","PUT /internal/models/{version} — signed promotion","GET /internal/features/{entity} — point-in-time vector"],
 ["feature(entity_id, feature_name, event_time, value, version)","model(model_id, version, artifact_uri, feature_schema, state)","exposure(request_id, user_id_hash, candidates, scores, model_version)","embedding(entity_id, vector_version, shard, updated_at)"],
 ["Build request context and fetch online features with strict per-source deadlines.","Retrieve bounded candidates in parallel from collaborative, vector, and trending sources.","Union/dedupe, apply availability/safety policy, then score with a pinned model.","Rerank for diversity, freshness, exploration, and business constraints.","Return results and log candidates/scores/exposures so training and evaluation are reproducible."],
 ["Feature store returns stale vector","Candidate source exceeds deadline","Model artifact and feature schema mismatch","Feedback loop narrows diversity","Exposure logs drop during traffic spike"]),
"fraud-detection": S(
 ["Transaction API","Decision Gateway","Streaming Feature Engine","Online Feature Store","Profile Store","Rules Engine","Model Serving","Ensemble / Policy","Decision Service","Manual Review Queue","Case Management","Decision Audit Store","Label Pipeline","Model Monitor","Shadow Deployment"],
 ["POST /v1/decisions — synchronous risk decision","POST /v1/labels — chargeback/review outcome","PUT /v1/rules/{id} — versioned policy","POST /v1/models/{version}/shadow — compare only"],
 ["decision(decision_id, subject_id, outcome, score, reasons, policy_version)","feature_snapshot(decision_id, names, values, event_times)","case(case_id, decision_id, queue, state, reviewer)","label(decision_id, label, observed_at, source)"],
 ["Resolve entity/account/device keys and fetch streaming/profile features in parallel.","Evaluate deterministic rules and model under a fixed feature/model version budget.","Combine outputs through policy thresholds and return allow/challenge/review/deny.","Persist feature snapshot, reasons, and versions before asynchronous case routing.","Join delayed labels, monitor drift/calibration, and shadow new models before promotion."],
 ["Online feature missing at decision time","Adversary probes threshold","Manual-review backlog grows","Chargeback label arrives months later","New model shifts false-positive rate"]),
"configuration-service": S(
 ["Operator / CI","Config API","RBAC / Approval","Schema Validator","Policy Engine","Immutable Version Store","Environment Pointer","Rollout Controller","Change Log","Relay Root","Regional Relays","Client Watch","Local Last-Good Cache","Secret Reference Service","Health Gates"],
 ["POST /v1/configs/{name}/versions — immutable candidate","POST /v1/environments/{env}/promote — atomic pointer","GET /v1/snapshots/{version} — checksum bundle","WATCH /v1/environments/{env}?after= — ordered updates"],
 ["config_version(name, version, schema_version, payload, checksum)","environment_pointer(env, name, active_version, generation)","rollout(id, target_version, cohorts, current_stage, state)","client_ack(client_id, env, version, observed_at)"],
 ["Authenticate/authorize author, validate schema, references, and organization policy.","Store immutable candidate and produce a semantic diff for approval.","Canary by cohort; clients fetch checksum bundle and atomically swap local state.","Observe health/acknowledgment gates, then advance or roll back environment pointer.","Disconnected clients resume watch from generation or poll the complete snapshot."],
 ["Schema-valid config is operationally unsafe","Relay misses ordered update","Client cannot parse new schema","Global pointer advances too quickly","Secret reference resolves in wrong tenant"]),
"distributed-lock": S(
 ["Lock Client","Session Library","Leader Endpoint","Consensus Leader","Consensus Followers","Replicated Log","Lease Table","Fencing Counter","Watch Registry","Clock / Lease Monitor","Protected Database","Protected Object Store","Admin Recovery","Audit Stream"],
 ["POST /v1/locks/{name}/acquire — lease and fencing token","POST /v1/leases/{id}/renew — quorum renewal","DELETE /v1/leases/{id} — best-effort release","WATCH /v1/locks/{name}?revision= — ordered ownership"],
 ["lease(lock_name PK, owner_session, fencing_token, expires_revision)","session(session_id, principal, last_renew_revision, state)","log_entry(index, term, command, checksum)","watch(lock_name, start_revision, subscriber)"],
 ["Client opens an authenticated session and proposes acquire to the consensus leader.","Committed acquire increments fencing counter and returns lease plus token.","Protected resource requires token on every mutation and rejects values below its maximum.","Renewals extend the lease only after quorum commit; client stops work before uncertainty margin.","Expiry/release commits a new revision and notifies ordered watchers."],
 ["Old owner resumes after long pause","Leader changes during renewal","Client reaches resource after lease loss","Watch misses compaction window","Administrator force-releases active lock"]),
"multi-tenant-saas": S(
 ["Tenant User","Identity Provider","Global Gateway","Tenant Context","Quota / Entitlement","Tenant Router","Shared Service Fleet","Placement Directory","Pooled DB Shards","Dedicated DB Tier","Per-Tenant Key Service","Usage Event Stream","Billing / Metering","Support Access Broker","Isolation Monitor"],
 ["POST /v1/tenants — provision placement/policy","GET /v1/resources/{id} — trusted tenant scope","POST /v1/tenants/{id}/migrations — staged move","GET /v1/usage — metered dimensions"],
 ["tenant(tenant_id PK, tier, placement_id, key_ref, policy_version)","placement(placement_id, region, mode, shard_or_database, generation)","resource(tenant_id, resource_id, version, payload)","usage_event(event_id, tenant_id, dimension, quantity, occurred_at)"],
 ["Authenticate identity and derive tenant context from trusted claims, never request payload.","Resolve entitlements, quotas, encryption key reference, and current placement generation.","Route to pooled/partitioned/dedicated data using tenant-scoped credentials and keys.","Execute with tenant ID in every primary/index key and enforce dependency budgets.","Emit immutable usage and isolation signals; migration dual-reads/checks before pointer cutover."],
 ["Missing tenant predicate leaks data","Noisy tenant exhausts shared pool","Placement migration reads two versions","Support impersonation bypasses audit","Per-tenant key service unavailable"]),
"unique-id-generator": S(
 ["Service Client","Regional Endpoint","ID Worker","Monotonic Clock","Worker Lease Cache","Consensus Lease Service","Worker Registry","Epoch Config","Rollback Detector","Range Allocator","ID Decoder Tool","Collision Monitor","Metrics / Capacity","Audit Log"],
 ["GET /v1/ids?count= — allocate batch","POST /internal/workers/lease — unique worker identity","POST /internal/ranges/lease — numeric range","GET /v1/ids/{id}/decode — timestamp/region diagnostics"],
 ["worker_lease(worker_id PK, owner, generation, lease_until)","range_lease(start, end, owner, generation, consumed)","epoch(version, start_time, bit_layout)","collision(id, first_owner, second_owner, observed_at)"],
 ["Acquire a unique worker/region identity through consensus and persist generation locally.","Read monotonic time; detect wall-clock rollback before composing an ID.","Pack timestamp, region, worker, and per-millisecond sequence into configured bits.","When sequence exhausts, wait for next tick or consume a leased numeric range.","Stop generation on lost lease and monitor sampled/full uniqueness at system boundaries."],
 ["Clock moves backward","Two processes share worker ID","Sequence overflows one millisecond","Epoch/bit layout changes during rollout","Identifiers leak business volume"]),
"parking-lot": S(
 ["Driver / Attendant","Entry Gate","Ticket Kiosk","Vehicle Classifier","Parking Service","Spot Strategy","Floor Availability Index","Spot Aggregate","Ticket Store","Sensor Gateway","Exit Gate","Pricing Strategy","Payment Adapter","Display Boards","Reconciliation"],
 ["POST /v1/entries — issue ticket and allocate spot","POST /v1/exits/quote — calculate fee","POST /v1/tickets/{id}/pay — settle","POST /v1/sensors/events — reconcile occupancy"],
 ["spot(spot_id PK, floor, type, state, version, ticket_id)","ticket(ticket_id PK, plate_hash, spot_id, entered_at, state)","payment(payment_id, ticket_id, amount, method, state)","sensor_event(event_id, spot_id, occupied, observed_at)"],
 ["Classify vehicle and query the floor/type availability index.","Spot strategy selects candidate; conditional transition AVAILABLE→HELD prevents double assignment.","Commit ticket and spot occupancy, then open gate and update display projection.","At exit price from entry time/rules, settle idempotently, and mark ticket paid.","Open exit, release spot, and reconcile sensor disagreements into an operator queue."],
 ["Two entry gates choose same spot","Sensor says occupied before ticket commit","Payment succeeds but exit gate fails","Lost ticket has no entry evidence","Accessible/EV policy changes while held"]),
"elevator-system": S(
 ["Hall Panel","Cabin Panel","Building Controller","Dispatch Strategy","Request Deduper","Car Controller","Car State Machine","Motion Controller","Door Controller","Floor Sensors","Load Sensor","Safety Interlock","Fault Manager","Maintenance Console"],
 ["CALL(floor, direction) — hall request","SELECT(car, destination) — cabin request","EVENT(car, position/door/load) — hardware event","COMMAND(car, target, mode) — dispatcher action"],
 ["car(car_id, floor, direction, door_state, load, mode, version)","request(request_id, floor, direction, assigned_car, state)","stop_plan(car_id, ordered_stops, generation)","fault(car_id, code, observed_at, cleared_by)"],
 ["Deduplicate hall/cabin requests and snapshot all eligible car states.","Dispatch strategy scores direction, distance, load, stops, and service mode.","Assign request by generation; car controller inserts a legal stop into its plan.","State machine commands motion only with doors locked and safety interlocks healthy.","Sensor events advance floor/door states; faults remove car and reassign outstanding requests."],
 ["Car stops reporting position","Door obstruction repeats","Duplicate hall request survives assignment","Emergency overrides normal schedule","Destination-control demand spikes"]),
"library-management": S(
 ["Member / Staff UI","Catalog Search","Membership Service","Circulation Service","Policy Engine","Title Catalog","Copy Inventory","Loan Aggregate","Hold Queue","Branch Transfer","Fine Calculator","Payment Adapter","Notification Service","Digital License Adapter"],
 ["POST /v1/loans — checkout copy","POST /v1/holds — queue title request","POST /v1/returns — return and assign hold","POST /v1/loans/{id}/renew — policy transition"],
 ["title(title_id PK, isbn, metadata)","copy(copy_id PK, title_id, branch_id, state, version)","loan(loan_id, copy_id, member_id, due_at, state)","hold(title_id, member_id, position, pickup_branch, expires_at)"],
 ["Validate membership and circulation policy for the exact physical/digital copy.","Conditionally transition AVAILABLE→LOANED and create loan with computed due date.","A hold enqueues by title/branch policy; return assigns first eligible member atomically.","Renew only if policy permits and no higher-priority hold blocks the copy.","Fine calculator consumes overdue/loss transitions; notifications are asynchronous and idempotent."],
 ["Two librarians checkout same copy","Hold expires while member arrives","Return at different branch","Renewal races new hold","Digital license count exhausted"]),
"meeting-room-scheduler": S(
 ["Calendar Client","Availability API","Identity / Directory","Room Search","Constraint Filter","Booking Service","Conflict Detector","Room Calendar DB","Attendee Calendar Adapter","Recurrence Engine","Timezone Service","Notification Service","Check-In Sensor","Auto-Release Worker"],
 ["GET /v1/rooms/search?start=&end=&capacity=","POST /v1/bookings — conditional reservation","PATCH /v1/series/{id} — recurrence/exception","POST /v1/bookings/{id}/check-in"],
 ["room(room_id PK, capacity, equipment, timezone, state)","booking(booking_id, room_id, start_utc, end_utc, version, series_id)","series(series_id, rrule, timezone, horizon, version)","exception(series_id, occurrence, override_or_cancel)"],
 ["Normalize requested local time to UTC while retaining timezone/recurrence intent.","Filter candidate rooms by static constraints, then query interval availability.","Insert booking with exclusion constraint/serializable overlap check on room calendar.","Write attendee events asynchronously and preserve room booking as source of truth.","Expand recurring occurrences within a horizon; exceptions override one occurrence without rewriting series."],
 ["Two users book same interval","DST changes recurrence wall time","Room equipment becomes unavailable","No-show auto-release races late check-in","Series edit conflicts with occurrence override"]),
"atm": S(
 ["Card Reader","Keypad / Display","ATM Controller","Session State Machine","PIN / Auth Adapter","Transaction Orchestrator","Bank Core Adapter","Cash Inventory","Denomination Strategy","Cash Dispenser","Dispense Sensors","Receipt Printer","Local Journal","Reconciliation / Operator"],
 ["INSERT_CARD / AUTHENTICATE — device session","WITHDRAW(account, amount, request_id)","DISPENSE(plan) — hardware command","RECONCILE(journal_batch) — operator/bank settlement"],
 ["atm_session(session_id, card_token, auth_state, expires_at)","withdrawal(request_id, account_ref, amount, state, bank_ref)","cassette(denomination, count, version)","journal(sequence, request_id, event, device_state)"],
 ["Capture card token, authenticate PIN through bank adapter, and establish bounded session.","Validate amount and compute a feasible denomination plan from versioned cassette counts.","Authorize/reserve funds at bank using request ID before commanding hardware.","Dispense, verify sensors, then finalize debit; uncertain hardware outcome enters reconciliation.","Journal every transition locally so network/power recovery can compare bank and physical cash."],
 ["Debit succeeds but cash jams","Cash dispenses after network timeout","Cassette count differs from sensors","Power fails mid-dispense","Card retained during session fault"]),
"vending-machine": S(
 ["Display / Keypad","Machine Controller","Session State","Product Catalog","Slot Inventory","Selection Policy","Coin Acceptor","Cash Inventory","Card Terminal","Payment Strategy","Change Solver","Dispenser Motor","Drop Sensor","Fault / Refill Console"],
 ["INSERT_MONEY(value) / TAP_CARD(token)","SELECT(slot) — validate stock/price","DISPENSE(slot, vend_id)","REFUND(session) / COMPLETE(vend_id)"],
 ["slot(slot_id PK, product_id, price, count, version)","cash_bin(denomination, count, version)","vend(vend_id, slot_id, amount, payment_state, dispense_state)","fault(fault_id, component, code, observed_at)"],
 ["Accept money into a session and maintain refundable balance separately from machine cash.","Validate selected slot inventory and current price; calculate feasible change from actual coins.","Authorize card or reserve cash, then claim one slot item with expected version.","Command dispenser and confirm drop sensor before committing inventory/payment.","On jam/timeout refund or mark uncertain vend for operator reconciliation."],
 ["Motor runs but item does not drop","Exact change unavailable after payment","Two inputs race one machine session","Card authorization expires","Refill changes inventory during vend"]),
"board-card-game": S(
 ["Player Client","Lobby / Matchmaking","Game Gateway","Session Actor","Turn Coordinator","Rules Engine","Legal Move Generator","Random Seed / Deck","Authoritative State","Immutable Move Log","Snapshot Store","Clock Service","Spectator Fanout","Anti-Cheat / Audit"],
 ["POST /v1/matches — create/join","WS MOVE(match_id, turn, client_move_id, move)","GET /v1/matches/{id}/state?after_turn=","POST /v1/matches/{id}/resign"],
 ["match(match_id PK, ruleset, players, state, turn, version)","move(match_id, turn, actor, client_move_id, action, state_hash)","snapshot(match_id, turn, state_blob, checksum)","clock(match_id, player_id, remaining_ms, updated_at)"],
 ["Route all commands for a match to one session actor/serialized mailbox.","Check player, turn, sequence, clock, and dedupe client_move_id.","Pure rules engine validates move and returns deterministic next state plus events.","Append move/state hash durably, update snapshot, acknowledge player, and fan out.","Reconnect loads snapshot plus moves; anti-cheat verifies hidden information and timing server-side."],
 ["Duplicate move after reconnect","Clock expires during valid move","Session owner crashes after append","Random deck differs across replicas","Spectator receives hidden state"]),
"logging-framework": S(
 ["Application Call Site","Logger Facade","Level Filter","Context / MDC","Event Builder","Redaction Filter","Bounded Ring Buffer","Async Dispatcher","Formatter","Console Appender","File Appender","Network Appender","Rotation Manager","Failure Fallback","Metrics"],
 ["logger.info(template, fields) — structured event","with_context(trace_id, tenant) — scoped metadata","set_level(logger, version) — dynamic config","flush(deadline) — bounded shutdown"],
 ["LogEvent(timestamp, level, logger, template, fields, context, throwable)","Appender(name, filter, formatter, failure_policy)","RotationPolicy(max_bytes, interval, retained_files)","BufferState(capacity, used, dropped_by_level)"],
 ["Check level before allocating expensive event fields.","Build immutable structured event and redact known sensitive keys at the boundary.","Offer to bounded ring buffer under explicit block/drop/sample policy by severity.","Dispatcher batches, formats once per appender needs, and isolates sink failures.","Rotation atomically renames/reopens; shutdown flushes until deadline then records drops."],
 ["Network appender recursively logs failure","Buffer fills during outage","Mutable context leaks across requests","Rotation loses file handle","Shutdown deadlocks application thread"]),
"lru-cache": S(
 ["Cache Caller","Cache API","Key Hash Map","Entry Node","Doubly Linked List","Head / MRU","Tail / LRU","Capacity Accountant","TTL Min-Heap","Expiry Sweeper","Loader Coalescer","Concurrency Lock","Eviction Listener","Hit / Miss Metrics"],
 ["get(key) → value/miss","put(key,value,ttl) → prior/evictions","compute_if_absent(key,loader)","invalidate(key) / resize(capacity)"],
 ["Node(key, value, weight, expires_at, prev, next)","Map<key, Node> for O(1) lookup","List head=MRU, tail=LRU","InFlight<key, promise> for loader coalescing"],
 ["Under one consistency boundary, find node in hash map.","If expired remove map/list/weight and return miss; otherwise move node to MRU.","Put updates or inserts node, updates total weight, and links at head.","Evict from tail until entry/byte capacity holds; notify outside the lock.","compute_if_absent registers one in-flight loader so concurrent misses share result."],
 ["TTL heap contains stale update entries","Eviction callback reenters cache","Large value evicts entire working set","Concurrent get races remove","Loader fails while callers wait"]),
"task-management": S(
 ["Web / Mobile","Task API","Auth / Workspace","Task Aggregate","Workflow Engine","Transition Policy","Dependency Graph","Cycle Detector","Task DB","Activity Log","Comment Service","Search Index","Notification Router","Recurring Task Worker","Audit / Export"],
 ["POST /v1/tasks — create in workspace","PATCH /v1/tasks/{id} If-Match: version","POST /v1/tasks/{id}/transitions — policy command","POST /v1/tasks/{id}/dependencies — cycle-checked edge"],
 ["task(task_id PK, workspace_id, status, assignee, version, due_at)","workflow(workspace_id, version, states, transitions)","dependency(predecessor_id, successor_id UNIQUE)","activity(task_id, sequence, actor, type, payload)"],
 ["Authenticate workspace actor and load task plus pinned workflow version.","Validate requested fields/transition against role, current state, and expected version.","For dependency edge, traverse bounded ancestors or use maintained topological metadata to reject cycle.","Conditionally update task and append immutable activity/outbox in one transaction.","Index/search/notify asynchronously; recurring worker creates deduped occurrence IDs."],
 ["Two users edit same task version","Dependency edge creates long cycle","Workflow changes while tasks active","Recurring worker retries occurrence","Notification fan-out spams watchers"]),
}

# Fill designs whose topology follows another explicit substrate while preserving
# their own component names from the main curriculum. The renderer still adds
# their six named components and these design-specific extensions.
EXTENSIONS = {
"file-storage": ["Conflict Resolver","Permission Audit"],
"notification-system": ["Campaign Fanout","Suppression List"],
"news-feed": ["Delete Propagator","Cache Invalidator"],
"social-post-service": ["Privacy Cache","Delete Propagator"],
"video-streaming": ["Caption Pipeline","Regional Origin Shield"],
"ride-hailing": ["Driver Heartbeats","Trip Reconciler"],
"ticket-booking": ["Barcode Scanner","Settlement Reconciler"],
"api-gateway": ["Canary Router","Config Relay"],
"distributed-cache": ["Failure Detector","Origin Shield"],
"job-scheduler": ["Tenant Quotas","Backfill Controller"],
"web-crawler": ["Content Deduper","Render Sandbox"],
"search-autocomplete": ["Locale Models","Trend Detector"],
"logging-monitoring": ["Sampling Policy","Incident Notifier"],
"metrics-system": ["Downsampler","Tenant Query Limits"],
"distributed-kv-store": ["Failure Detector","Snapshot Transfer"],
"payment-system": ["Settlement Files","Merchant Webhooks"],
"shopping-cart": ["Fraud Check","Customer Notification"],
"collaborative-editor": ["Comment Threads","Revision Browser"],
"object-storage": ["Bucket Index","Cross-Region Replicator"],
"message-queue": ["Schema Compatibility","Quota Manager"],
"feature-flags": ["SDK Telemetry","Stale Flag Scanner"],
"recommendation-system": ["A/B Allocator","Drift Monitor"],
"fraud-detection": ["Device Graph","Threshold Config"],
"configuration-service": ["Diff Viewer","Rollback Pointer"],
"distributed-lock": ["Session Reaper","Quorum Health"],
"multi-tenant-saas": ["Tenant Migration","Data Residency Policy"],
"unique-id-generator": ["Region Registry","Sequence Exhaustion Alarm"],
"parking-lot": ["Reservation API","Operator Override"],
"elevator-system": ["Destination Planner","Energy Optimizer"],
"library-management": ["Pickup Shelf","Digital Rights"],
"meeting-room-scheduler": ["Equipment Inventory","Calendar Webhooks"],
"atm": ["Cash Replenishment","Remote Diagnostics"],
"vending-machine": ["Telemetry Upload","Promotion Policy"],
"board-card-game": ["Reconnect Manager","Tournament Service"],
"logging-framework": ["Config Watcher","Emergency Sink"],
"lru-cache": ["Admission Policy","Memory Pressure Hook"],
"task-management": ["Permission Inheritance","Bulk Mutation Worker"],
}

def get_spec(slug, fallback_components):
    spec = SPECS.get(slug)
    if spec:
        return spec
    nodes = list(fallback_components) + EXTENSIONS.get(slug, [])
    return S(nodes, [], [], [], [])
