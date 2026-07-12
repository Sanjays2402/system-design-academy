
(function(){
  const root=document.documentElement;
  const safeGet=(k)=>{try{return localStorage.getItem(k)}catch{return null}};
  const safeSet=(k,v)=>{try{localStorage.setItem(k,v)}catch{/* storage is optional */}};
  function apply(theme){root.dataset.theme=theme;document.querySelectorAll('[data-theme-toggle]').forEach(b=>{b.setAttribute('aria-pressed',String(theme==='dark'));b.textContent=theme==='dark'?'Light page':'Dark page'})}
  const saved=safeGet('sda-theme');const preferred=document.body?.dataset.defaultTheme||'light';apply(saved==='dark'||saved==='light'?saved:preferred);
  document.addEventListener('click',e=>{const b=e.target.closest('[data-theme-toggle]');if(b){const next=root.dataset.theme==='dark'?'light':'dark';apply(next);safeSet('sda-theme',next)}const m=e.target.closest('[data-menu]');if(m)document.querySelector('.sidebar')?.classList.toggle('open')});
  const search=document.querySelector('[data-search]');if(search){search.addEventListener('input',()=>{const q=search.value.trim().toLowerCase();let shown=0;document.querySelectorAll('.design-card').forEach(c=>{const ok=c.textContent.toLowerCase().includes(q);c.hidden=!ok;if(ok)shown++});document.querySelector('.empty').style.display=shown?'none':'block'})}
})();
