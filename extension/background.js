const WS_URL = 'ws://127.0.0.1:8765';
const RECONNECT_MIN_MS = 1000;
const RECONNECT_MAX_MS = 15000;

let ws = null;
let reconnectDelay = RECONNECT_MIN_MS;
let reconnectTimer = null;
let heartbeatTimer = null;
const recentPayloadIds = new Map();
const RECENT_PAYLOAD_TTL_MS = 5 * 60 * 1000;

const AI_HOST_KEYWORDS = [
  'chatgpt.com',
  'chat.openai.com',
  'chat.deepseek.com',
  'deepseek.com',
  'kimi.moonshot.cn',
  'moonshot.cn',
  'doubao.com',
  'tongyi.aliyun.com',
  'gemini.google.com',
  'claude.ai',
  'perplexity.ai',
  'poe.com',
  'copilot.microsoft.com',
  'grok.com'
];

function isAiUrl(url = '') {
  return AI_HOST_KEYWORDS.some((host) => url.includes(host));
}

function isDuplicatePayload(payload) {
  if (!payload || !['upload_image', 'insert_image', 'paste_image', 'screenshot'].includes(payload.action)) {
    return false;
  }

  const data = payload.data || payload.dataUrl || payload.imageDataUrl || payload.image || '';
  const key = payload.id || payload.messageId || payload.taskId || `${data.length}:${String(data).slice(0, 96)}:${String(data).slice(-96)}`;
  const now = Date.now();

  for (const [k, ts] of recentPayloadIds.entries()) {
    if (now - ts > RECENT_PAYLOAD_TTL_MS) recentPayloadIds.delete(k);
  }

  if (recentPayloadIds.has(key)) {
    console.warn('[AURA] duplicate websocket payload ignored', key);
    return true;
  }

  recentPayloadIds.set(key, now);
  return false;
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = reconnectDelay;
  reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_MS);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWS();
  }, delay);
  console.log(`[AURA] reconnect scheduled in ${delay}ms`);
}

function startHeartbeat() {
  clearInterval(heartbeatTimer);
  heartbeatTimer = setInterval(() => {
    try {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping', source: 'extension', ts: Date.now() }));
      }
    } catch (err) {
      console.warn('[AURA] heartbeat failed', err);
    }
  }, 20000);
}

function connectWS() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  console.log('[AURA] Connecting local server...');
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('[AURA] Connected');
    reconnectDelay = RECONNECT_MIN_MS;
    try {
      ws.send(JSON.stringify({ action: 'client_hello', source: 'extension' }));
    } catch (_) {}
    startHeartbeat();
  };

  ws.onmessage = async (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (!payload || !payload.action) return;

      // ACK/pong are for mobile/server state, not content pages.
      if (payload.action.endsWith('_ack') || payload.action === 'pong') return;
      if (isDuplicatePayload(payload)) return;

      const tabs = await chrome.tabs.query({});
      for (const tab of tabs) {
        if (!tab.id || !tab.url || !isAiUrl(tab.url)) continue;
        try {
          await chrome.tabs.sendMessage(tab.id, payload);
        } catch (err) {
          // Content script may not be injected after SPA navigation. Try injecting once.
          try {
            await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
            await chrome.tabs.sendMessage(tab.id, payload);
          } catch (_) {}
        }
      }
    } catch (err) {
      console.error('[AURA] Message error', err);
    }
  };

  ws.onclose = () => {
    console.log('[AURA] Disconnected');
    clearInterval(heartbeatTimer);
    ws = null;
    scheduleReconnect();
  };

  ws.onerror = () => {
    // onclose will schedule reconnect. Keep this quiet to avoid error spam in MV3.
  };
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('aura_keepalive', { periodInMinutes: 1 });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create('aura_keepalive', { periodInMinutes: 1 });
  connectWS();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'aura_keepalive') connectWS();
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (!tab.url || !isAiUrl(tab.url)) return;
  if (changeInfo.status === 'complete' || changeInfo.url) {
    try {
      await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
    } catch (_) {}
  }
});

connectWS();
