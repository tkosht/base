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
  function applyUiMode(){
    try{
      var root=document.documentElement;
      var theme=getThemeParam();
      var isLight;
      if(theme){
        isLight = (theme==='light');
      } else {
        var el=document.querySelector('#sidebar_col')||document.body||document.documentElement;
        var bg=getComputedStyle(el).backgroundColor||'rgb(255,255,255)';
        isLight = getLum(bg) > 0.5;
      }
      root.classList.toggle('ui-light', isLight);
      root.classList.toggle('ui-dark', !isLight);
    }catch(e){}
  }
  window.addEventListener('load', applyUiMode);
  window.addEventListener('focus', applyUiMode);
  setTimeout(applyUiMode, 0);
  setTimeout(applyUiMode, 150);
  setTimeout(applyUiMode, 600);
})();


