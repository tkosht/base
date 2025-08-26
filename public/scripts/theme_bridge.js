(function(){
  function getLum(c){
    try{
      var m=(c||'').match(/\d+/g)||[255,255,255];
      var r=+m[0], g=+m[1], b=+m[2];
      return (0.2126*r+0.7152*g+0.0722*b)/255;
    }catch(e){ return 1; }
  }
  function getThemeParam(){
    try{
      var v=new URLSearchParams(window.location.search).get('__theme');
      if(v==='light' || v==='dark') return v;
    }catch(e){}
    return null;
  }
  function isTransparent(rgb){
    try{
      if(!rgb) return true;
      if(rgb==='transparent') return true;
      return /rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0(\.0+)?\s*\)/i.test(rgb);
    }catch(e){ return false; }
  }
  function getEffectiveBG(el){
    var cur = el;
    try{
      while(cur){
        var cs;
        try{ cs = getComputedStyle(cur); }catch(_){}
        var bg = (cs && cs.backgroundColor) || '';
        if(bg && !isTransparent(bg)) return bg;
        cur = cur.parentElement;
      }
    }catch(e){}
    return 'rgb(255,255,255)'; // fallback: light
  }
  function detectIsLight(){
    var theme = getThemeParam();
    if(theme==='light') return true;
    if(theme==='dark') return false;
    var mediaPref = null;
    try{
      if(window.matchMedia){
        if(window.matchMedia('(prefers-color-scheme: dark)').matches) mediaPref = 'dark';
        else if(window.matchMedia('(prefers-color-scheme: light)').matches) mediaPref = 'light';
      }
    }catch(e){}
    var el = document.querySelector('#sidebar_col')||document.body||document.documentElement;
    var bg = getEffectiveBG(el);
    var bgIsLight = getLum(bg) > 0.5;
    if(mediaPref){
      // 優先度: 実背景の見た目を最優先。矛盾時は背景を採用。
      if(mediaPref==='light' && !bgIsLight) return false;
      if(mediaPref==='dark' && bgIsLight) return true;
      return mediaPref==='light';
    }
    return bgIsLight;
  }
  function ensureShadowStyles(isLight){
    try{
      var ga = document.querySelector('gradio-app');
      var sr = ga && ga.shadowRoot;
      if(!sr) return;
      var styleId = 'ui-theme-bridge';
      var node = sr.getElementById ? sr.getElementById(styleId) : sr.querySelector('#'+styleId);
      var css;
      var common = "#sidebar-toggle-row button{min-width:36px;height:36px;}\n"
                 + "#sidebar_toggle_btn button{width:36px;height:36px;}\n"
                 + "#edge_col .gr-button, #edge_col .gr-button>button{width:36px;min-width:36px;height:36px;padding:0;}\n";
      if(isLight){
        css = "#threads_list .thread-title, #threads_list_tab .thread-title{color:#111827 !important;}\n"
            + "label, [data-testid='block-label'], .label{color:#111827 !important;}\n"
            + "[role='slider'] ~ *, input[type='range'] ~ *{color:#111827 !important;}\n"
            + common;
      } else {
        css = "#threads_list .thread-title, #threads_list_tab .thread-title{color:#e5e7eb !important;}\n"
            + "label, [data-testid='block-label'], .label{color:#e5e7eb !important;}\n"
            + "[role='slider'] ~ *, input[type='range'] ~ *{color:#e5e7eb !important;}\n"
            + common;
      }
      if(!node){
        node = document.createElement('style');
        node.id = styleId;
        node.textContent = css;
        sr.appendChild(node);
      } else {
        node.textContent = css;
      }
    }catch(e){}
  }
  function applyUiMode(){
    try{
      var root=document.documentElement;
      var isLight = detectIsLight();
      root.classList.toggle('ui-light', isLight);
      root.classList.toggle('ui-dark', !isLight);
      ensureShadowStyles(isLight);
    }catch(e){}
  }
  window.addEventListener('DOMContentLoaded', applyUiMode);
  window.addEventListener('load', applyUiMode);
  window.addEventListener('focus', applyUiMode);
  window.addEventListener('visibilitychange', applyUiMode);
  window.addEventListener('resize', applyUiMode);
  window.addEventListener('pageshow', applyUiMode);
  setTimeout(applyUiMode, 0);
  setTimeout(applyUiMode, 150);
  setTimeout(applyUiMode, 600);
})();

