// ==UserScript==
// @name         AURA Voice Injector
// @namespace    aura.local
// @version      2.1.0
// @description  接收 AURA 本地语音助手推送的文字和图片，注入任意网页输入框并自动发送
// @author       AURA
// @match        *://*/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const WS_URL = 'wss://127.0.0.1:8765';
  let ws = null;

  const ADAPTERS = {
    'chat.deepseek.com': {
      selectors: ['#chat-input', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: '[data-send="true"], .send-btn, button[type="submit"]'
    },
    'kimi.moonshot.cn': {
      selectors: ['textarea', '.chat-input-editor textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: '[data-testid="send-button"], button[type="submit"], .send-btn'
    },
    'www.doubao.com': {
      selectors: ['textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: 'button[type="submit"], .send-btn'
    },
    'chatgpt.com': {
      selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: '[data-testid="send-button"]'
    },
    'chat.openai.com': {
      selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: '[data-testid="send-button"]'
    },
    'tongyi.aliyun.com': {
      selectors: ['textarea', '[contenteditable="true"]'],
      inputMode: 'value',
      sendBtn: 'button[type="submit"], .send-btn'
    }
  };

  const FALLBACK = {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    inputMode: 'auto',
    sendBtn: 'button[type="submit"]'
  };

  function getAdapter() {
    return ADAPTERS[location.hostname] || FALLBACK;
  }

  function getInput() {
    const adapter = getAdapter();
    for (const sel of adapter.selectors) {
      try {
        const el = document.querySelector(sel);
        if (el) return el;
      } catch (_) {}
    }
    return null;
  }

  function getSendButton() {
    const sel = getAdapter().sendBtn;
    if (!sel) return null;
    try { return document.querySelector(sel); } catch (_) { return null; }
  }

  function focusInput() {
    const el = getInput();
    if (el) el.focus();
  }

  function injectText(text, shouldSend) {
    const el = getInput();
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

    if (shouldSend) submitInput(el);
  }

  function submitInput(el) {
    el.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
      bubbles: true, cancelable: true, composed: true
    }));
    el.dispatchEvent(new KeyboardEvent('keyup', {
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
      bubbles: true, cancelable: true, composed: true
    }));

    const btn = getSendButton();
    if (btn && !btn.disabled) {
      setTimeout(() => { try { btn.click(); } catch (_) {} }, 100);
    }
  }

  function injectImage(base64Uri, filename) {
    const el = getInput();
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

    el.dispatchEvent(new ClipboardEvent('paste', {
      clipboardData: dt, bubbles: true, cancelable: true
    }));
    if (dt.files.length > 0) {
      document.dispatchEvent(new ClipboardEvent('paste', {
        clipboardData: dt, bubbles: true, cancelable: true
      }));
    }
  }

  function connect() {
    if (ws && ws.readyState !== WebSocket.CLOSED) return;
    console.log('[AURA] 连接 wss://127.0.0.1:8765 ...');
    ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log('[AURA] 已连接');

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.action === 'focus_input') {
          focusInput();
        } else if (payload.action === 'insert_text') {
          injectText(payload.text || '', !!payload.send);
        } else if (payload.action === 'upload_image') {
          injectImage(payload.data, 'snapshot.jpg');
        }
      } catch (e) {
        console.error('[AURA] 消息解析失败', e);
      }
    };

    ws.onclose = () => {
      console.log('[AURA] 断开，3 秒后重连');
      ws = null;
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {};
  }

  setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'ping' }));
    } else if (!ws || ws.readyState === WebSocket.CLOSED) {
      connect();
    }
  }, 60000);

  connect();
  console.log('[AURA] Injector 就绪');
})();
