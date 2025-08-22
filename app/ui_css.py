"""Gradio UI のカスタム CSS。

`app/demo.py` に記述されていた CSS をそのまま移設する。
"""

CSS = r"""
/* =================== Tokens =================== */
:root{
  --avatar-base: 32px;     /* 内部が32pxでもOK：基準実寸（触らない） */
  --avatar-zoom: 1.1;      /* ← 見かけの拡大率（2.0〜3.2で調整） */
  --avatar-gap: .3rem;     /* アバターと本文の隙間 */
  --avatar-shift-y: -2px;  /* 上下微調整（負=上へ） */
  --avatar-ring: 0px;      /* ← 外周の白リングの太さ（見え方確認用） */

  --text:#111827; --card:#fff; --card-border:#e5e7eb; --code-bg:#f8fafc;
  --chat-btn-gap:10px; --stop-nudge:12px; --stop-diameter:36px;
  --stop-bg:#6b7280; --send-bg:#60A5FA; --stop-total-w:var(--stop-diameter);
  --chip-bg:#e5e7eb; --search-band-bg:#F1F5F9; --search-band-radius:10px; --search-band-pad:12px;
  --search-bg:#EEF2FF; --search-text:#111827; --search-border:#BFDBFE; --search-ph:#6B7280;
  --search-bg-focus:#fff; --search-outline:rgba(37,99,235,.25);
}

/* ===== Chat bubbles ===== */
.gr-chatbot .message{
  background:var(--card) !important; color:var(--text) !important;
  border:1px solid var(--card-border) !important; border-radius:14px !important; box-shadow:none !important;
}
.gr-chatbot .message-row{ box-shadow:none !important; background:transparent !important; }

/* ===== アバター列：列幅は拡大後寸法に合わせる ===== */
.gr-chatbot .message-row{
  display:grid !important;
  /* 列1 = 見かけ寸法（base × zoom）、列2 = 本文 */
  grid-template-columns: calc(var(--avatar-base) * var(--avatar-zoom)) 1fr !important;
  align-items:center !important;
  column-gap: var(--avatar-gap) !important;
  /* 行の高さも見かけ寸法に合わせる */
  min-height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  overflow:visible !important;
}

/* avatar sizing now handled by .avatar-container */

/* legacy inner selectors removed */

/* image centering is handled by .avatar-container > img */

/* avatar-image direct rule removed; .avatar-container covers it */

/* GradioのDOMで用いられる avatar-container を直接拡大（確実適用） */
.avatar-container{
  width: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  min-width: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  min-height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  display:grid !important; place-items:center !important;
  border-radius:9999px !important; overflow:visible !important;
  background:#fff !important;
  box-shadow: 0 0 0 var(--avatar-ring) #fff !important;
}
.avatar-container > :is(img,svg){
  width:100% !important; height:100% !important; display:block !important;
  object-fit:contain !important;
  object-position: center calc(50% + var(--avatar-shift-y)) !important;
  border-radius:9999px !important;
}

/* fallbacks removed; container-based sizing is sufficient */

/* ===== 入力行（既存のまま） ===== */
#msgrow{ position:relative; width:100%; }
#msgrow .gr-button > button{ min-width:0 !important; }
#stopbtn,#sendbtn{
  position:absolute; top:50%; transform:translateY(-50%);
  right:calc(var(--chat-btn-gap) + var(--stop-nudge));
  width:var(--stop-diameter) !important; height:var(--stop-diameter) !important;
  border-radius:9999px !important; display:flex; align-items:center; justify-content:center;
  padding:0 !important; margin:0 !important; z-index:5;
}
#stopbtn{ background:var(--stop-bg) !important; } #sendbtn{ background:var(--send-bg) !important; }
#stopbtn > button,#sendbtn > button{
  width:100% !important; height:100% !important; background:transparent !important; color:#fff !important;
  border:none !important; box-shadow:none !important; font-size:14px; line-height:1;
  display:inline-flex; align-items:center; justify-content:center;
}
#msgrow input,#msgrow textarea{
  padding-right:calc(var(--stop-total-w) + var(--chat-btn-gap) + var(--stop-nudge)) !important;
}
#msgrow .gr-textbox{ margin-bottom:0 !important; }

/* ===== ステータス / 検索UI（省略可、既存どおり） ===== */
#status{ min-height:1.6em; line-height:1.6em; overflow:hidden !important; }
#status *{ overflow:hidden !important; margin:0 !important; }
#status .prose,#status .markdown,#status .gr-prose{ white-space:nowrap; text-overflow:ellipsis; }
.combo-field .wrap, .combo-field .wrap.svelte-1ipelgc{ gap:.5rem; }
.combo-field .gr-textbox input{ border-top-right-radius:0; border-bottom-right-radius:0; }
.combo-field .gr-button{ border-top-left-radius:0; border-bottom-left-radius:0; }
.combo-field .chips{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.25rem; }
.combo-field .chip{ background:var(--chip-bg); border-radius:9999px; padding:.2rem .6rem; font-size:.9rem; }
.combo-hint{ opacity:.8; margin-top:.25rem; }
#search_band{ background:var(--search-band-bg) !important; border-radius:var(--search-band-radius); padding:var(--search-band-pad); }
#search_band .gr-textbox,#search_band .gr-button{ margin-top:0 !important; margin-bottom:0 !important; }
#searchbox input,#searchbox textarea{ background:var(--search-bg) !important; color:var(--search-text) !important; border-color:var(--search-border) !important; }
#searchbox input::placeholder,#searchbox textarea::placeholder{ color:var(--search-ph) !important; opacity:1; }
#searchbox input:focus,#searchbox textarea:focus{
  background:var(--search-bg-focus) !important; border-color:#2563EB !important;
  box-shadow:0 0 0 3px var(--search-outline) !important; outline:none !important;
}
"""


