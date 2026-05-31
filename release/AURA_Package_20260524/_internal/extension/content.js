(() => {
if (globalThis.__AURA_CONTENT_SCRIPT_LOADED__) {
  console.log('[AURA] content script already injected, skip');
  return;
}
globalThis.__AURA_CONTENT_SCRIPT_LOADED__ = true;
console.log('[AURA] content script injected');

const AURA_RECENT_IMAGES = new Map();
const AURA_IMAGE_TTL_MS = 5 * 60 * 1000;

function getImageDedupeKey(payload, dataUrl) {
  return payload?.id || payload?.messageId || payload?.taskId ||
    `${dataUrl.length}:${dataUrl.slice(0, 96)}:${dataUrl.slice(-96)}`;
}

function isDuplicateImage(key) {
  const now = Date.now();
  for (const [k, ts] of AURA_RECENT_IMAGES.entries()) {
    if (now - ts > AURA_IMAGE_TTL_MS) AURA_RECENT_IMAGES.delete(k);
  }
  if (!key) return false;
  if (AURA_RECENT_IMAGES.has(key)) {
    console.warn('[AURA] duplicate image ignored', key);
    return true;
  }
  AURA_RECENT_IMAGES.set(key, now);
  return false;
}

const ADAPTERS = {
  'chatgpt.com': {
    selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: '[data-testid="send-button"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'chat.openai.com': {
    selectors: ['#prompt-textarea', 'textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: '[data-testid="send-button"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'chat.deepseek.com': {
    selectors: ['#chat-input', 'textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[type="submit"]',
    uploadMode: 'drag',
    fileInputs: ['input[type="file"]']
  },
  'gemini.google.com': {
    selectors: ['rich-textarea', '.ql-editor', 'textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[aria-label="Send message"], button[aria-label="发送"], button[aria-label*="send" i], button[aria-label*="发送"]',
    uploadMode: 'clipboard',
    fileInputs: []
  },
  'claude.ai': {
    selectors: ['div[contenteditable="true"]', '[role="textbox"]', 'textarea'],
    sendBtn: 'button[aria-label*="Send"], button[type="submit"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'perplexity.ai': {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[aria-label*="Submit"], button[aria-label*="Send"], button[type="submit"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'poe.com': {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[type="submit"], button[aria-label*="Send"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'copilot.microsoft.com': {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[aria-label*="Submit"], button[aria-label*="Send"], button[type="submit"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'grok.com': {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: 'button[aria-label*="Submit"], button[aria-label*="Send"], button[type="submit"]',
    uploadMode: 'fileInput',
    fileInputs: ['input[type="file"]']
  },
  'kimi.moonshot.cn': {
    selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
    sendBtn: '[data-testid="send-button"], button[type="submit"]',
    uploadMode: 'drag',
    fileInputs: ['input[type="file"]']
  }
};

const FALLBACK = {
  selectors: ['textarea', '[contenteditable="true"]', '[role="textbox"]'],
  sendBtn: 'button[type="submit"]',
  uploadMode: 'drag',
  fileInputs: ['input[type="file"]']
};

function getAdapter() {
  const host = location.hostname;
  if (ADAPTERS[host]) return ADAPTERS[host];
  for (const [domain, adapter] of Object.entries(ADAPTERS)) {
    if (host.endsWith(`.${domain}`)) return adapter;
  }
  return FALLBACK;
}

function queryFirst(selectors) {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el) return el;
  }
  return null;
}

function getInput() {
  return queryFirst(getAdapter().selectors);
}

function getSendButton() {
  return document.querySelector(getAdapter().sendBtn);
}

function injectText(text, shouldSend = false) {
  const el = getInput();
  if (!el) {
    console.warn('[AURA] Input not found');
    return false;
  }

  el.focus();
  if (el.classList?.contains('ql-editor') || el.closest?.('.ql-editor')) {
    // Gemini uses Quill editor — set innerHTML with <p> tags
    el.innerHTML = `<p>${text}</p>`;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  } else if (el.isContentEditable || el.tagName?.toLowerCase() === 'rich-textarea') {
    el.textContent = text;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    el.value = text;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }

  if (shouldSend) {
    setTimeout(() => {
      const btn = getSendButton();
      if (btn && !btn.disabled) {
        btn.click();
      } else {
        el.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
        }));
      }
    }, 300);
  }
  return true;
}

function normalizeDataUrl(payload) {
  const raw = payload?.dataUrl || payload?.imageDataUrl || payload?.image_url ||
    payload?.imageUrl || payload?.image || payload?.base64 || payload?.data || '';
  if (!raw || typeof raw !== 'string') return '';
  if (raw.startsWith('data:image/')) return raw;
  return `data:image/png;base64,${raw}`;
}

async function dataUrlToFile(dataUrl) {
  const res = await fetch(dataUrl);
  const blob = await res.blob();
  const ext = blob.type.includes('png') ? 'png' : blob.type.includes('webp') ? 'webp' : 'jpg';
  return new File([blob], `aura-screenshot-${Date.now()}.${ext}`, { type: blob.type || 'image/jpeg' });
}

async function uploadViaFileInput(file) {
  const adapter = getAdapter();
  const input = queryFirst(adapter.fileInputs || ['input[type="file"]']);
  if (!input) return false;

  const dt = new DataTransfer();
  dt.items.add(file);

  try {
    input.files = dt.files;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('[AURA] Image uploaded via file input', file.name, file.size);
    return true;
  } catch (err) {
    console.warn('[AURA] file input upload failed', err);
    return false;
  }
}

function showClipboardHint() {
  // Remove previous hint if any
  const old = document.getElementById('aura-clipboard-hint');
  if (old) old.remove();

  const div = document.createElement('div');
  div.id = 'aura-clipboard-hint';
  div.textContent = 'AURA: 图片已复制到剪贴板，请按 Ctrl+V 粘贴';
  Object.assign(div.style, {
    position: 'fixed', top: '16px', right: '16px', zIndex: '999999',
    background: '#1a73e8', color: '#fff', padding: '12px 20px',
    borderRadius: '8px', fontSize: '14px', fontFamily: 'sans-serif',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)', transition: 'opacity 0.5s',
    opacity: '1'
  });
  document.body.appendChild(div);
  setTimeout(() => { div.style.opacity = '0'; }, 4000);
  setTimeout(() => { div.remove(); }, 4500);
}

function uploadViaDrag(file) {
  const target = getInput() || document.querySelector('main') || document.body;
  if (!target) return false;

  const dt = new DataTransfer();
  dt.items.add(file);

  for (const type of ['dragenter', 'dragover', 'drop']) {
    target.dispatchEvent(new DragEvent(type, {
      bubbles: true,
      cancelable: true,
      dataTransfer: dt
    }));
  }
  console.log('[AURA] Image drop events dispatched', file.name, file.size);
  return true;
}

async function uploadImage(payload) {
  const dataUrl = normalizeDataUrl(payload);
  if (!dataUrl) {
    console.warn('[AURA] Empty image payload');
    return false;
  }

  const dedupeKey = getImageDedupeKey(payload, dataUrl);
  if (isDuplicateImage(dedupeKey)) return true;

  try {
    const file = await dataUrlToFile(dataUrl);
    const adapter = getAdapter();
    let ok = false;

    // Strict single-path upload: one incoming image may use exactly one
    // injection method. This prevents fileInput + drag/drop double attachments.
    if (adapter.uploadMode === 'clipboard') {
      // Gemini rejects synthetic events (isTrusted check). Image is already on
      // system clipboard by the server. Just show a hint to the user.
      showClipboardHint();
      return true;
    } else if (adapter.uploadMode === 'fileInput') {
      ok = await uploadViaFileInput(file);
    } else if (adapter.uploadMode === 'drag') {
      ok = uploadViaDrag(file);
    } else {
      ok = uploadViaDrag(file);
    }

    if (!ok) console.warn('[AURA] Image upload failed: no usable target', dedupeKey);
    return ok;
  } catch (err) {
    console.error('[AURA] uploadImage error', err);
    return false;
  }
}

chrome.runtime.onMessage.addListener((payload, sender, sendResponse) => {
  console.log('[AURA] Received', payload);

  if (payload.action === 'insert_text') {
    const ok = injectText(payload.text || '', !!payload.send);
    sendResponse?.({ ok });
    return true;
  }

  if (['upload_image', 'insert_image', 'paste_image', 'screenshot'].includes(payload.action) ||
      ['image', 'screenshot'].includes(payload.type)) {
    uploadImage(payload).then((ok) => sendResponse?.({ ok }));
    return true;
  }

  return false;
});

})();
