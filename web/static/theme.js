(function(){
  const KEY='netsentinel-theme';
  const root=document.documentElement;
  function preferred(){
    const saved=localStorage.getItem(KEY);
    if(saved==='light'||saved==='dark')return saved;
    return window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  function apply(theme){
    root.dataset.theme=theme;
    localStorage.setItem(KEY,theme);
    document.querySelectorAll('[data-theme-label]').forEach(el=>{
      el.textContent=theme==='dark'?'Dark':'Light';
    });
    document.dispatchEvent(new CustomEvent('themechange',{detail:{theme}}));
  }
  window.setNetSentinelTheme=apply;
  window.toggleNetSentinelTheme=function(){
    apply(root.dataset.theme==='dark'?'light':'dark');
  };
  apply(preferred());
  document.addEventListener('DOMContentLoaded',()=>apply(root.dataset.theme||preferred()));
})();
