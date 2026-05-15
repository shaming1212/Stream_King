console.log("[AURA] content script loaded");

const ADAPTERS = {
  "chat.deepseek.com": { selectors: ["#chat-input", "textarea", '[contenteditable="true"]'], mode: "value" },
  "kimi.moonshot.cn": { selectors: ["textarea", ".chat-input-editor textarea", '[contenteditable="true"]'], mode: "value" },
  "www.doubao.com": { selectors: ["textarea", '[contenteditable="true"]'], mode: "value" },
  "chatgpt.com": { selectors: ["#prompt-textarea", "textarea", '[contenteditable="true"]'], mode: "value" },
  "chat.openai.com": { selectors: ["#prompt-textarea", "textarea", '[contenteditable="true"]'], mode: "value" },
  "tongyi.aliyun.com": { selectors: ["textarea", '[contenteditable="true"]'], mode: "value" }
};
const FALLBACK = { selectors: ["textarea", '[contenteditable="true"]'], mode: "auto" };

function getAdapter() { return ADAPTERS[location.hostname] || FALLBACK; }

function getInput() {
  const sel = getAdapter().selectors;
  for (const s of sel) { try { const el = document.querySelector(s); if (el) return el; } catch (_) {} }
  return null;
}

chrome.runtime.onMessage.addListener((req, _sender, sendResponse) => {
  if (req.action === "focus_input") { const el = getInput(); if (el) el.focus(); }
  else if (req.action === "insert_text") { injectText(req.text || ""); }
  else if (req.action === "upload_image") { injectImage(req.data, "snapshot.jpg"); }
  sendResponse({ status: "success" });
  return true;
});

function injectText(text) {
  const el = getInput();
  if (!el) return;
  const mode = (() => {
    const m = getAdapter().mode;
    if (m !== "auto") return m;
    return el.isContentEditable ? "contenteditable" : "value";
  })();
  if (mode === "contenteditable") el.textContent = (el.textContent || "") + text;
  else el.value = (el.value || "") + text;
  el.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
  if (mode === "value") { el.selectionStart = el.selectionEnd = el.value.length; }
}

function injectImage(base64Uri, filename) {
  const el = getInput();
  if (!el) return;
  const parts = base64Uri.split(",");
  if (!parts || parts.length < 2) return;
  const m = parts[0].match(/:(.*?);/);
  if (!m) return;
  const mime = m[1];
  let bstr;
  try { bstr = atob(parts[1]); } catch (_) { return; }
  const u8 = new Uint8Array(bstr.length);
  for (let i = bstr.length - 1; i >= 0; i--) u8[i] = bstr.charCodeAt(i);
  const file = new File([u8], filename, { type: mime });
  const dt = new DataTransfer();
  dt.items.add(file);
  el.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true }));
  if (dt.files.length > 0) document.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true }));
}
