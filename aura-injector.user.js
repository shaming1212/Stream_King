// ==UserScript==
// @name         AURA Voice Injector
// @namespace    aura.local
// @version      2.0.0
// @description  接收 AURA 本地语音助手推送的文字和图片，注入到 AI 对话输入框
// @author       AURA
// @match        *://chat.deepseek.com/*
// @match        *://kimi.moonshot.cn/*
// @match        *://www.doubao.com/*
// @match        *://chatgpt.com/*
// @match        *://chat.openai.com/*
// @match        *://tongyi.aliyun.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const WS_URL = 'ws://127.0.0.1:8765';
  let ws = null;

  // ── 站点适配器 ──
  const SITE_ADAPTERS = {
    'chat.deepseek.com': {
      selectors: ['#chat-input', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    },
    'kimi.moonshot.cn': {
      selectors: ['textarea', '.chat-input-editor textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    },
    'www.doubao.com': {
      selectors: ['textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    },
    'chatgpt.com': {
      selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    },
    'chat.openai.com': {
      selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    },
    'tongyi.aliyun.com': {
      selectors: ['textarea', '[contenteditable="true"]'],
      inputMode: 'value'
    }
  };

  const FALLBACK_ADAPTER = {
    selectors: ['textarea', '[contenteditable="true"]'],
    inputMode: 'auto'
  };

  function getAdapter() {
    return SITE_ADAPTERS[location.hostname] || FALLBACK_ADAPTER;
  }

  function getChatInput() {
    const adapter = getAdapter();
    for (const sel of adapter.selectors) {
      try {
        const el = document.querySelector(sel);
        if (el) return el;
      } catch (_) {}
    }
    return null;
  }

  // ── DOM 操作方法 ──
  function focusInput() {
    const el = getChatInput();
    if (el) el.focus();
  }

  function injectText(text) {
    const el = getChatInput();
    if (!el) return;

    const adapter = getAdapter();
    const mode = adapter.inputMode === 'auto'
      ? (el.isContentEditable ? 'contenteditable' : 'value')
      : adapter.inputMode;

    if (mode === 'contenteditable') {
      el.textContent = (el.textContent || '') + text;
    } else {
      el.value = (el.value || '') + text;
    }

    el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
    if (mode === 'value') {
      el.selectionStart = el.selectionEnd = el.value.length;
    }
  }

  function injectImage(base64Uri, filename) {
    const el = getChatInput();
    if (!el) return;

    const parts = base64Uri.split(',');
    if (!parts || parts.length < 2) return;
    const mimeMatch = parts[0].match(/:(.*?);/);
    if (!mimeMatch) return;

    const mime = mimeMatch[1];
    let bstr;
    try { bstr = atob(parts[1]); } catch (_) { return; }

    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) u8arr[n] = bstr.charCodeAt(n);

    const file = new File([u8arr], filename, { type: mime });
    const dt = new DataTransfer();
    dt.items.add(file);

    const pasteEvent = new ClipboardEvent('paste', {
      clipboardData: dt,
      bubbles: true,
      cancelable: true
    });
    el.dispatchEvent(pasteEvent);
    if (dt.files.length > 0) document.dispatchEvent(pasteEvent);
  }

  // ── WebSocket 连接（直接在页面上下文中）──
  function connect() {
    if (ws && ws.readyState !== WebSocket.CLOSED) return;

    console.log('[AURA] 连接 ws://127.0.0.1:8765 ...');
    ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log('[AURA] 已连接');

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.action === 'focus_input') focusInput();
        else if (payload.action === 'insert_text') injectText(payload.text || '');
        else if (payload.action === 'upload_image') injectImage(payload.data, 'snapshot.jpg');
      } catch (e) {
        console.error('[AURA] 消息解析失败', e);
      }
    };

    ws.onclose = () => {
      console.log('[AURA] 断开，3 秒后重连');
      ws = null;
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {}; // onclose 会紧随触发
  }

  // ── 心跳保活 ──
  setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'ping' }));
    } else if (!ws || ws.readyState === WebSocket.CLOSED) {
      connect();
    }
  }, 60000);

  // 启动
  connect();
  console.log('[AURA] Injector 就绪');
})();
