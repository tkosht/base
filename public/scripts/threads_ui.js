(function () {
  if (window.threadsSetup) return;
  window.threadsSetup = function () {
    if (window.__threadsSetupDone) return;
    window.__threadsSetupDone = true;

    const start = document.querySelector('gradio-app') || document;
    const qsDeep = (sel) => {
      const seen = new Set();
      const search = (root) => {
        if (!root || seen.has(root)) return null;
        seen.add(root);
        try {
          if (root.querySelector) {
            const f = root.querySelector(sel);
            if (f) return f;
          }
        } catch (e) {}
        const sr = root.shadowRoot;
        if (sr) {
          const f = search(sr);
          if (f) return f;
        }
        const kids = root.children || root.childNodes || [];
        for (const k of kids) {
          const f = search(k);
          if (f) return f;
        }
        return null;
      };
      return search(start) || document.querySelector(sel);
    };
    const gi = (id) => qsDeep('#' + id);
    const qs = (sel) => qsDeep(sel);
    const qsWithin = (root, sel) => {
      const seen = new Set();
      const search = (node) => {
        if (!node || seen.has(node)) return null;
        seen.add(node);
        try {
          if (node.querySelector) {
            const f = node.querySelector(sel);
            if (f) return f;
          }
        } catch (e) {}
        const sr = node.shadowRoot;
        if (sr) {
          const f = search(sr);
          if (f) return f;
        }
        const kids = node.children || node.childNodes || [];
        for (const k of kids) {
          const f = search(k);
          if (f) return f;
        }
        return null;
      };
      return search(root);
    };
    const qsaDeep = (sel) => {
      const out = [];
      const pushAll = (arr) => {
        for (const n of arr) out.push(n);
      };
      const rec = (root) => {
        try {
          if (root.querySelectorAll) {
            pushAll(root.querySelectorAll(sel));
          }
        } catch (e) {}
        const sr = root.shadowRoot;
        if (sr) rec(sr);
        const kids = root.children || root.childNodes || [];
        for (const k of kids) rec(k);
      };
      rec(document.querySelector('gradio-app') || document);
      if (!out.length) {
        try {
          pushAll(document.querySelectorAll(sel));
        } catch (e) {}
      }
      return out;
    };
    const setValueC = (cls, value) => {
      const root = qs('.' + cls);
      if (!root) return false;
      const inp = qsWithin(root, 'textarea, input');
      if (!inp) return false;
      try {
        inp.value = value;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
      } catch (e) {}
      return true;
    };
    const triggerC = (cls) => {
      const root = qs('.' + cls);
      if (!root) return false;
      const b = qsWithin(root, 'button, [role="button"], .gr-button');
      const tgt = b || root;
      try {
        tgt.click();
      } catch (e) {
        try {
          tgt.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        } catch (_) {}
      }
      return true;
    };
    const ensureCtx = () => {
      let m = document.querySelector('.ctx-menu');
      if (!m) {
        m = document.createElement('div');
        m.className = 'ctx-menu';
        m.style.display = 'none';
        m.innerHTML = "<div class='ctx-item' data-act='rename'>名前変更</div><div class='ctx-item' data-act='share'>共有</div><div class='ctx-item' data-act='delete'>削除</div>";
        document.body.appendChild(m);
        m.addEventListener('click', (e) => {
          const act = e.target.getAttribute('data-act');
          const id = m.getAttribute('data-tid') || '';
          const curTitle = m.getAttribute('data-title') || '';
          // 設定順序: kindクリア → arg → id → kind （change発火を1回に）
          setValueC('th_action_kind', '');
          if (act === 'rename') {
            const newTitle = window.prompt('新しいスレッド名を入力', curTitle);
            if (!newTitle || !newTitle.trim()) {
              m.style.display = 'none';
              return;
            }
            setValueC('th_action_arg', newTitle.trim());
            setValueC('th_action_id', id);
            setValueC('th_action_kind', 'rename');
          } else if (act === 'share') {
            setValueC('th_action_arg', '');
            setValueC('th_action_id', id);
            setValueC('th_action_kind', 'share');
          } else if (act === 'delete') {
            const ok = window.confirm(`「${curTitle || '無題'}」を削除しますか？`);
            if (!ok) {
              m.style.display = 'none';
              return;
            }
            setValueC('th_action_arg', '');
            setValueC('th_action_id', id);
            setValueC('th_action_kind', 'delete');
            removeThreadDom(id);
          }
          m.style.display = 'none';
        });
      }
    };
    // メニュー外クリックやESCで閉じる
    document.addEventListener('click', (e) => {
      const m = document.querySelector('.ctx-menu');
      if (!m || m.style.display === 'none') return;
      const path = e.composedPath ? e.composedPath() : [e.target];
      if (!path.some((n) => n === m)) {
        m.style.display = 'none';
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const m = document.querySelector('.ctx-menu');
        if (m) m.style.display = 'none';
      }
    });
    // DOM即時反映ユーティリティ（サイドバー/タブ両方を更新）
    const updateTitleDom = (tid, title) => {
      ['#threads_list', '#threads_list_tab'].forEach((sel) => {
        const root = qs(sel);
        if (!root) return;
        const el = root.querySelector(
          `.thread-link[data-tid='${tid}'] .thread-title`
        );
        if (el) el.textContent = title;
      });
    };
    const removeThreadDom = (tid) => {
      ['#threads_list', '#threads_list_tab'].forEach((sel) => {
        const root = qs(sel);
        if (!root) return;
        const node = root.querySelector(`.thread-link[data-tid='${tid}']`);
        if (node) node.remove();
      });
    };
    // F2: 選択中スレッドの名称変更（現在名を初期値として提示）
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'F2') return;
      const el = qs('.thread-link.selected');
      if (!el) return;
      const tid = el.getAttribute('data-tid') || '';
      const curTitle = (el.querySelector('.thread-title')?.textContent || '').trim();
      const newTitle = window.prompt('新しいスレッド名を入力', curTitle);
      if (!newTitle || !newTitle.trim()) return;
      setValueC('th_action_kind', '');
      setValueC('th_action_arg', newTitle.trim());
      setValueC('th_action_id', tid);
      setValueC('th_action_kind', 'rename');
    });
    const hideCtx = () => {
      const m = document.querySelector('.ctx-menu');
      if (m) m.style.display = 'none';
    };
    const defer = (fn, times = 2) => {
      const step = (n) => {
        if (n <= 0) {
          fn();
          return;
        }
        requestAnimationFrame(() => step(n - 1));
      };
      step(times);
    };
    const ensureChatTab = (attempts = 6) => {
      const tryOnce = (n) => {
        if (n <= 0) return;
        const tabs = qsaDeep('[role="tab"]');
        let chat = null;
        for (const t of tabs) {
          const txt = (t.textContent || '').trim();
          if (txt.includes('チャット')) {
            chat = t;
            break;
          }
        }
        if (chat) {
          const selected = chat.getAttribute('aria-selected') === 'true';
          if (!selected) {
            try {
              chat.click();
            } catch (e) {}
          }
          // 再確認して未選択ならリトライ
          if (!selected) setTimeout(() => tryOnce(n - 1), 80);
        } else {
          setTimeout(() => tryOnce(n - 1), 80);
        }
      };
      tryOnce(attempts);
    };
    document.addEventListener('click', (e) => {
      const path = e.composedPath ? e.composedPath() : [e.target];
      let el = null;
      for (const n of path) {
        if (n && n.closest) {
          el = n.closest('.thread-link');
          if (el) break;
        }
      }
      if (!el && e.target && e.target.closest)
        el = e.target.closest('.thread-link');
      if (!el) return;
      const id = el.getAttribute('data-tid') || '';
      // 2回目以降のクリックでも change を確実化: 一旦kindをクリアしてから id→kind の順で設定
      setValueC('th_action_kind', '');
      setTimeout(() => {
        setValueC('th_action_id', id);
        setValueC('th_action_kind', 'open');
        triggerC('th_open_trigger');
      }, 0);
      // 可視選択状態の反映（サイドバー/タブの両方）
      const markSelected = (rootList) => {
        if (!rootList) return;
        const items = rootList.querySelectorAll('.thread-link');
        items.forEach((it) =>
          it.classList[it.getAttribute('data-tid') === id ? 'add' : 'remove'](
            'selected'
          )
        );
      };
      const sidebar = qs('#threads_list');
      const tab = qs('#threads_list_tab');
      markSelected(sidebar);
      markSelected(tab);
      const isInThreadsTab = (path || []).some((n) => n && n.id === 'threads_list_tab');
      if (isInThreadsTab) {
        ensureChatTab(8);
      }
    });
    document.addEventListener('contextmenu', (e) => {
      const path = e.composedPath ? e.composedPath() : [e.target];
      let el = null;
      for (const n of path) {
        if (n && n.closest) {
          el = n.closest('.thread-link');
          if (el) break;
        }
      }
      if (!el && e.target && e.target.closest)
        el = e.target.closest('.thread-link');
      if (!el) return;
      e.preventDefault();
      ensureCtx();
      const m = document.querySelector('.ctx-menu');
      m.style.left = e.pageX + 'px';
      m.style.top = e.pageY + 'px';
      m.setAttribute('data-tid', el.getAttribute('data-tid') || '');
      const curTitle = (el.querySelector('.thread-title')?.textContent || '').trim();
      m.setAttribute('data-title', curTitle);
      m.style.display = 'block';
    });
    // メニュー選択の実行は Textbox change 経由でPython側にディスパッチ
    // グローバル関数を公開（デバッグ・手動呼出用）
    window.qsDeep = qsDeep;
    window.qsWithin = qsWithin;
    setTimeout(() => {
      const dbg_list = gi('threads_list');
      const dbg_inp = qsWithin(qs('.th_action_id') || document, 'textarea, input');
      const dbg_btn = qsWithin(
        qs('.th_open_trigger') || document,
        'button, [role="button"], .gr-button'
      );
      console.log('[threads-js] init2', {
        list_found: !!dbg_list,
        input_found: !!dbg_inp,
        open_button_found: !!dbg_btn,
      });
    }, 300);
  };
})();


