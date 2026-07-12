(function(){
  'use strict';
  const reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cards=[...document.querySelectorAll('.design-card')];
  const search=document.querySelector('[data-curriculum-search]');
  const filters=[...document.querySelectorAll('[data-filter]')];
  const countEl=document.querySelector('[data-visible-count]');
  let category='all';

  function applyFilters(){
    const query=(search?.value||'').trim().toLowerCase();
    let visible=0;
    cards.forEach(card=>{
      const matchesText=!query||card.textContent.toLowerCase().includes(query);
      const matchesCategory=category==='all'||card.dataset.category===category;
      const show=matchesText&&matchesCategory;
      card.hidden=!show;
      if(show) visible++;
    });
    if(countEl) countEl.textContent=`${visible} of ${cards.length} chapters`;
    const empty=document.querySelector('.empty');
    if(empty) empty.style.display=visible?'none':'block';
  }
  search?.addEventListener('input',applyFilters);
  filters.forEach(button=>button.addEventListener('click',()=>{
    category=button.dataset.filter;
    filters.forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active))});
    applyFilters();
  }));
  applyFilters();

  if(!reduce&&'IntersectionObserver' in window){
    const reveal=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(entry.isIntersecting){
        entry.target.classList.add('revealed');
        reveal.unobserve(entry.target);
      }
    }),{rootMargin:'0px 0px -5% 0px',threshold:.06});
    cards.forEach((card,index)=>{card.style.transitionDelay=`${Math.min(index%9,8)*38}ms`;reveal.observe(card)});
  }else cards.forEach(card=>card.classList.add('revealed'));

  document.querySelectorAll('[data-count]').forEach(element=>{
    const target=Number(element.dataset.count)||0;
    if(reduce){element.textContent=target.toLocaleString();return}
    const start=performance.now();const duration=900;
    function tick(now){
      const t=Math.min(1,(now-start)/duration);const eased=1-Math.pow(1-t,3);
      element.textContent=Math.round(target*eased).toLocaleString();
      if(t<1)requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });

  const stage=document.querySelector('.hero-stage');
  if(stage&&!reduce){
    stage.addEventListener('pointermove',event=>{
      const rect=stage.getBoundingClientRect();
      document.documentElement.style.setProperty('--spot-x',`${event.clientX}px`);
      document.documentElement.style.setProperty('--spot-y',`${event.clientY}px`);
      stage.style.setProperty('--pointer-x',String((event.clientX-rect.left)/rect.width-.5));
      stage.style.setProperty('--pointer-y',String((event.clientY-rect.top)/rect.height-.5));
    },{passive:true});
  }

  const canvas=document.querySelector('[data-topology]');
  if(!canvas||reduce)return;
  const context=canvas.getContext&&canvas.getContext('2d');
  if(!context)return;
  const shell=canvas.parentElement;
  const nodes=[
    [.10,.56,'client'],[.27,.30,'edge'],[.45,.51,'gateway'],[.63,.25,'service'],
    [.65,.70,'stream'],[.84,.45,'store'],[.89,.76,'observe'],[.38,.80,'cache']
  ];
  const edges=[[0,1],[1,2],[2,3],[2,4],[2,7],[3,5],[4,5],[4,6],[7,5]];
  const packets=Array.from({length:14},(_,index)=>({edge:index%edges.length,t:(index*.137)%1,speed:.0012+(index%5)*.00018}));
  let width=0,height=0,dpr=1,frame=0,raf=0,visible=true,last=performance.now();

  function resize(){
    const rect=shell.getBoundingClientRect();
    width=Math.max(1,rect.width);height=Math.max(1,rect.height);dpr=Math.min(2,window.devicePixelRatio||1);
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
    canvas.style.width=`${width}px`;canvas.style.height=`${height}px`;
    context.setTransform(dpr,0,0,dpr,0,0);
  }
  const observer='ResizeObserver' in window?new ResizeObserver(resize):null;
  observer?.observe(shell);window.addEventListener('resize',resize,{passive:true});resize();
  if('IntersectionObserver' in window){
    const io=new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting!==false},{threshold:0});io.observe(canvas);
  }

  function palette(){
    const dark=document.documentElement.dataset.theme==='dark';
    return dark?{line:'rgba(255,255,255,.17)',node:'#f5f5f2',ink:'#111',muted:'rgba(255,255,255,.56)',packet:'#fff',halo:'rgba(255,255,255,.08)'}:{line:'rgba(17,17,17,.16)',node:'#111',ink:'#fff',muted:'rgba(17,17,17,.55)',packet:'#111',halo:'rgba(17,17,17,.07)'};
  }
  function point(index){const node=nodes[index];return{x:node[0]*width,y:node[1]*height,label:node[2]}}
  function draw(now){
    raf=requestAnimationFrame(draw);if(!visible)return;
    const delta=Math.min(40,now-last);last=now;frame++;
    const colors=palette();context.clearRect(0,0,width,height);
    context.lineWidth=1;
    edges.forEach(([a,b],index)=>{
      const p1=point(a),p2=point(b);context.strokeStyle=colors.line;
      context.setLineDash(index===4||index===7?[5,6]:[]);context.beginPath();context.moveTo(p1.x,p1.y);context.lineTo(p2.x,p2.y);context.stroke();
    });
    context.setLineDash([]);
    packets.forEach(packet=>{
      packet.t=(packet.t+packet.speed*delta)%1;const [a,b]=edges[packet.edge],p1=point(a),p2=point(b);
      const x=p1.x+(p2.x-p1.x)*packet.t,y=p1.y+(p2.y-p1.y)*packet.t;
      context.fillStyle=colors.halo;context.beginPath();context.arc(x,y,7,0,Math.PI*2);context.fill();
      context.fillStyle=colors.packet;context.beginPath();context.arc(x,y,2.2,0,Math.PI*2);context.fill();
    });
    nodes.forEach((node,index)=>{
      const p=point(index),pulse=1+Math.sin((frame+index*18)*.035)*.06;
      context.fillStyle=colors.halo;context.beginPath();context.arc(p.x,p.y,20*pulse,0,Math.PI*2);context.fill();
      context.fillStyle=colors.node;context.beginPath();context.arc(p.x,p.y,9,0,Math.PI*2);context.fill();
      context.fillStyle=colors.ink;context.font='600 8px Geist Mono, monospace';context.textAlign='center';context.textBaseline='middle';context.fillText(String(index+1),p.x,p.y+.5);
      context.fillStyle=colors.muted;context.font='500 9px Geist Mono, monospace';context.fillText(p.label.toUpperCase(),p.x,p.y+26);
    });
  }
  raf=requestAnimationFrame(draw);
  window.addEventListener('pagehide',()=>{cancelAnimationFrame(raf);observer?.disconnect()},{once:true});
})();
