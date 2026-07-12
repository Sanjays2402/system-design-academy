(function(){
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  const reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('[data-call-flow]').forEach(panel=>{
    let flows;
    try{flows=JSON.parse(panel.dataset.flows||'[]')}catch{return}
    if(!flows.length)return;
    const svg=panel.querySelector('svg');
    const overlay=svg?.querySelector('[data-call-flow-overlay]');
    if(!svg||!overlay)return;
    const state={flow:0,step:0,playing:false,timer:null};
    const counter=panel.querySelector('[data-flow-counter]');
    const title=panel.querySelector('[data-flow-title]');
    const description=panel.querySelector('[data-flow-description]');
    const list=panel.querySelector('[data-flow-list]');
    const play=panel.querySelector('[data-flow-play]');

    function element(name,attrs={}){
      const node=document.createElementNS(NS,name);
      Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,String(value)));
      return node;
    }
    function center(index){
      const node=svg.querySelector(`[data-node-index="${index}"]`);
      if(!node)return null;
      const box=node.getBBox();
      return{x:box.x+box.width/2,y:box.y+box.height/2,node};
    }
    function stop(){
      state.playing=false;clearTimeout(state.timer);state.timer=null;
      if(play){play.textContent='Play';play.setAttribute('aria-label','Play call flow')}
    }
    function schedule(){
      clearTimeout(state.timer);
      if(!state.playing||reduced)return;
      state.timer=setTimeout(()=>{
        const total=flows[state.flow].steps.length;
        if(state.step>=total-1){stop();return}
        state.step++;render();schedule();
      },1800);
    }
    function renderList(flow){
      list.innerHTML='';
      flow.steps.forEach((step,index)=>{
        const item=document.createElement('li');item.dataset.staticFlowStep=String(index);
        if(index===state.step)item.classList.add('active');
        if(index<state.step)item.classList.add('complete');
        const heading=document.createElement('b');heading.textContent=`${String(index+1).padStart(2,'0')} · ${step.title}`;
        const copy=document.createElement('span');copy.textContent=step.text;
        item.append(heading,copy);item.addEventListener('click',()=>{stop();state.step=index;render()});list.append(item);
      });
    }
    function render(){
      const flow=flows[state.flow],steps=flow.steps;
      state.step=Math.max(0,Math.min(state.step,steps.length-1));
      const active=steps[state.step];
      counter.textContent=`Step ${state.step+1} / ${steps.length}`;
      title.textContent=active.title;description.textContent=active.text;
      panel.querySelectorAll('[data-flow-select]').forEach((button,index)=>{
        const selected=index===state.flow;button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));
      });
      svg.querySelectorAll('.arch-node').forEach(node=>node.classList.remove('flow-active','flow-complete','flow-upcoming'));
      overlay.replaceChildren();
      const points=steps.map(step=>center(step.node)).filter(Boolean);
      points.forEach((point,index)=>{
        point.node.classList.add(index<state.step?'flow-complete':index===state.step?'flow-active':'flow-upcoming');
      });
      if(points.length>1){
        const route=element('polyline',{points:points.map(p=>`${p.x},${p.y}`).join(' '),class:'flow-route',stroke:flow.color});
        overlay.append(route);
        // Keep numbering in the synchronized step list; center badges obscure node labels.
        if(state.step<points.length-1&&!reduced){
          const from=points[state.step],to=points[state.step+1];
          const packet=element('circle',{r:6,class:'flow-packet',fill:flow.color});
          const motion=element('animateMotion',{dur:'1.25s',repeatCount:'indefinite',path:`M${from.x} ${from.y} L${to.x} ${to.y}`});
          packet.append(motion);overlay.append(packet);
        }
      }
      renderList(flow);
    }

    panel.querySelectorAll('[data-flow-select]').forEach((button,index)=>button.addEventListener('click',()=>{stop();state.flow=index;state.step=0;render()}));
    panel.querySelector('[data-flow-prev]')?.addEventListener('click',()=>{stop();state.step--;render()});
    panel.querySelector('[data-flow-next]')?.addEventListener('click',()=>{stop();state.step++;render()});
    panel.querySelector('[data-flow-restart]')?.addEventListener('click',()=>{stop();state.step=0;render()});
    play?.addEventListener('click',()=>{
      if(reduced){state.step=(state.step+1)%flows[state.flow].steps.length;render();return}
      state.playing=!state.playing;
      play.textContent=state.playing?'Pause':'Play';play.setAttribute('aria-label',state.playing?'Pause call flow':'Play call flow');
      if(state.playing&&state.step>=flows[state.flow].steps.length-1)state.step=0;
      render();schedule();
    });
    panel.addEventListener('keydown',event=>{
      if(event.target.matches('input,textarea,select'))return;
      if(event.key==='ArrowRight'){event.preventDefault();stop();state.step++;render()}
      else if(event.key==='ArrowLeft'){event.preventDefault();stop();state.step--;render()}
      else if(event.key===' '){event.preventDefault();play?.click()}
    });
    panel.tabIndex=0;render();
  });
})();
