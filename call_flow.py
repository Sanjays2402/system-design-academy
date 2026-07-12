"""Build system-specific call-flow routes from each design specification."""
import re


def _kind(name):
    n=name.lower()
    words=set(re.findall(r'[a-z0-9]+',n))
    if any(x in words for x in ('client','app','browser','mobile','web','ui','creator','viewer','buyer','driver','rider','merchant','operator','player','panel','keypad')): return 'external'
    if any(x in n for x in ('auth','risk','policy','waf','fraud','vault','classifier','scanner','abuse','safety','interlock')): return 'security'
    if any(x in n for x in ('queue','stream','kafka','log','journal','outbox')): return 'stream'
    if any(x in words for x in ('db','database','store','ledger','inventory','wal','sstable','table','manifest')) or any(x in n for x in ('metadata shard','hash map','linked list','entry node','ttl min-heap','head / mru','tail / lru')): return 'data'
    if any(x in n for x in ('audit','metric','monitor','observ','reconcil','history','case','slo','fault')): return 'ops'
    if any(x in n for x in ('edge','gateway','front door','cdn','dns','endpoint','kiosk','api')): return 'edge'
    return 'service'


def _first(nodes, kinds, after=-1, reverse=False):
    indices=range(len(nodes)-1,-1,-1) if reverse else range(after+1,len(nodes))
    for i in indices:
        if _kind(nodes[i]) in kinds:
            return i
    return None


def _unique(values):
    out=[]
    for value in values:
        if value is not None and value not in out: out.append(value)
    return out


def _named(nodes, include, exclude=(), after=-1, reverse=False):
    indices=range(len(nodes)-1,-1,-1) if reverse else range(after+1,len(nodes))
    for i in indices:
        name=nodes[i].lower()
        if any(word in name for word in include) and not any(word in name for word in exclude): return i
    return None


def _all_kind(nodes, kinds, limit=2):
    return [i for i,node in enumerate(nodes) if _kind(node) in kinds][:limit]

def _authoritative_data(nodes, limit=2):
    skip=('analytics','olap','archive','read replica','rollup','feature','case','history')
    values=[i for i,node in enumerate(nodes) if _kind(node)=='data' and not any(x in node.lower() for x in skip)]
    return values[:limit]

def _failure_target(nodes, failure):
    f=failure.lower()
    clues=[]
    for word in ('cache','redis','provider','adapter','gateway','leader','worker','ledger','payment','store','database','db','queue','stream','sensor','clock','lease','manifest','inventory'):
        if word in f:clues.append(word)
    if clues:
        for i,node in enumerate(nodes):
            if any(word in node.lower() for word in clues):return i
    return _named(nodes,('adapter','provider','worker','leader','gateway','service','controller'),reverse=True)


def build_flows(spec):
    nodes=spec['nodes']; n=len(nodes)
    external=_first(nodes,{'external'})
    ingress=_first(nodes,{'edge'},after=external if external is not None else -1)
    mutation_service=_named(nodes,('create','write','orchestrat','coordinator','controller','booking','payment api','post api','upload','scheduler','circulation','parking service'),('analytics','read','redirect'))
    service=mutation_service if mutation_service is not None else _first(nodes,{'service'},after=ingress if ingress is not None else -1)
    security=_first(nodes,{'security'},after=ingress if ingress is not None else -1)
    coordination_candidates=[i for i,node in enumerate(nodes) if i>(service if service is not None else -1) and any(x in node.lower() for x in ('allocator','sequencer','matcher','strategy','engine','router','adapter','coordinator','orchestrat'))][:2]
    data_nodes=_authoritative_data(nodes,2)
    data=data_nodes[0] if data_nodes else None
    stream=_first(nodes,{'stream'},after=service if service is not None else -1)
    ops=_first(nodes,{'ops'},reverse=True)
    cache_candidates=[i for i,x in enumerate(nodes) if any(k in x.lower() for k in ('cache','redis','index','snapshot','read replica','fst','trie'))]
    cache=cache_candidates[0] if cache_candidates else None

    mutation=_unique([external,ingress,service,security,*coordination_candidates,*data_nodes,stream,ops])
    if len(mutation)<5: mutation=_unique([0,1,2,3,min(7,n-1),n-1])
    read_service=_named(nodes,('redirect','read','query','search','suggest','feed api','playback','availability','catalog','sync api','recommendation api'),('worker','store'))
    if read_service is None:read_service=_first(nodes,{'service'},after=ingress if ingress is not None else -1)
    leading_edges=[i for i,node in enumerate(nodes) if _kind(node)=='edge' and (read_service is None or i<read_service)][:2]
    read=_unique([external,*leading_edges,read_service,cache,*data_nodes,ops])
    if len(read)<4: read=_unique([0,1,2,min(5,n-1),n-1])
    failed=_failure_target(nodes,spec['failures'][0])
    reconciler=_named(nodes,('reconcil','repair','audit','monitor','history','case'),reverse=True)
    recovery=_unique([failed,service,*data_nodes,stream,reconciler,ops,n-1])
    if len(recovery)<4: recovery=_unique([min(2,n-1),min(6,n-1),min(9,n-1),n-1])

    def mutation_steps(route):
        descriptions=[]
        lifecycle=spec['steps']
        for i,node_idx in enumerate(route):
            if i==0: text=f"The caller starts the operation at {nodes[node_idx]} with a stable request and retry identity."
            elif i-1<len(lifecycle): text=lifecycle[i-1]
            elif _kind(nodes[node_idx])=='stream': text=f"{nodes[node_idx]} durably records side effects so workers can replay them independently."
            elif _kind(nodes[node_idx])=='ops': text=f"{nodes[node_idx]} observes completion and proves the business invariant after commit."
            else: text=f"{nodes[node_idx]} receives the committed result or event and advances its versioned state."
            descriptions.append({'node':node_idx,'title':nodes[node_idx],'text':text})
        return descriptions

    def read_steps(route):
        descriptions=[]
        for i,node_idx in enumerate(route):
            kind=_kind(nodes[node_idx])
            if i==0: text=f"A user call enters through {nodes[node_idx]}; the client carries authentication, cursor, and deadline context."
            elif kind in ('edge','security'): text=f"{nodes[node_idx]} terminates the protocol, authenticates, applies quotas, and routes the request."
            elif node_idx==cache: text=f"{nodes[node_idx]} serves the low-latency lookup when its version and TTL are valid; misses continue to durable state."
            elif kind=='data': text=f"{nodes[node_idx]} is the source-of-truth fallback and returns the authoritative version used to refill projections."
            elif kind=='ops': text=f"{nodes[node_idx]} receives asynchronous telemetry; it never delays the user response."
            else: text=f"{nodes[node_idx]} validates the read, resolves ownership, and requests only the bounded data needed for the response."
            descriptions.append({'node':node_idx,'title':nodes[node_idx],'text':text})
        return descriptions

    def recovery_steps(route):
        descriptions=[]; failure=spec['failures'][0]
        for i,node_idx in enumerate(route):
            kind=_kind(nodes[node_idx])
            if i==0: text=f"Failure drill: {failure}. {nodes[node_idx]} stops unsafe progress and preserves the original operation identity."
            elif kind=='data': text=f"{nodes[node_idx]} reveals the last committed version; recovery never guesses from an ambiguous response."
            elif kind=='stream': text=f"{nodes[node_idx]} replays durable events from the consumer checkpoint using idempotent handlers."
            elif kind=='ops': text=f"{nodes[node_idx]} reconciles derived state against durable truth and reports any invariant gap."
            else: text=f"{nodes[node_idx]} resumes only after ownership, lease, or dependency health is verified."
            descriptions.append({'node':node_idx,'title':nodes[node_idx],'text':text})
        return descriptions

    return [
      {'id':'mutation','label':'Mutation / commit','color':'#34d399','steps':mutation_steps(mutation)},
      {'id':'read','label':'Online / read','color':'#22d3ee','steps':read_steps(read)},
      {'id':'recovery','label':'Failure / recovery','color':'#fb923c','steps':recovery_steps(recovery)},
    ]
