let ws = null;
const WS_URL = "ws://127.0.0.1:8765";
let connecting = false;

const HOSTS = ["deepseek.com", "moonshot.cn", "doubao.com", "chatgpt.com", "chat.openai.com", "aliyun.com"];

function isSupported(url) {
  return url && HOSTS.some(h => url.includes(h));
}

function connect() {
  if (ws && ws.readyState !== WebSocket.CLOSED) return;
  if (connecting) return;
  connecting = true;
  console.log("[AURA] connecting to", WS_URL);
  try {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => { console.log("[AURA] connected"); connecting = false; };
    ws.onmessage = (e) => {
      try {
        const p = JSON.parse(e.data);
        console.log("[AURA] action:", p.action);
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs.length && isSupported(tabs[0].url)) {
            chrome.tabs.sendMessage(tabs[0].id, p, (r) => {
              if (chrome.runtime.lastError) console.warn("[AURA] send failed:", chrome.runtime.lastError.message);
              else console.log("[AURA] delivered:", r);
            });
          }
        });
      } catch (err) { console.error("[AURA] parse error:", err); }
    };
    ws.onclose = () => { console.log("[AURA] closed"); ws = null; connecting = false; setTimeout(connect, 3000); };
    ws.onerror = () => {};
  } catch (err) { console.error("[AURA] connect error:", err); connecting = false; setTimeout(connect, 3000); }
}

connect();

chrome.alarms.create("keepAlive", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    if (!ws || ws.readyState === WebSocket.CLOSED) connect();
    else if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ action: "ping" }));
  }
});
