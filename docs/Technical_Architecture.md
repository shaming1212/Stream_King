# AURA Voice Assistant — 技术架构文档

## 1. 项目概述

AURA 是一个本地 AI 语音助手，核心流程：**按住快捷键说话 → 本地 AI 识别 → 文字注入浏览器 AI 对话页面**。支持语音输入、摄像头拍照、屏幕截图三种输入模式。

- **语言**: Python 3.10+
- **GUI**: PyQt6
- **语音识别**: FunASR (SenseVoiceSmall + FSMN-VAD + CT-Transformer 标点)
- **浏览器通信**: WebSocket + Chrome Extension (Manifest V3)
- **音频**: sounddevice (PortAudio)
- **摄像头**: OpenCV
- **截图**: mss + PyQt6 选区窗口

---

## 2. 系统架构全景图

```
┌──────────────────────────────────────────────────────────────────┐
│                        用户操作层                                  │
│  Alt+1 语音  │  Alt+2 拍照  │  Alt+3 截图  │  GUI 波形  │  浏览器  │
└────────┬──────────┬──────────┬──────────┬──────────┬────────────┘
         │          │          │          │          │
         ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐
│VoiceEngine│ │CameraEng.│ │Screenshot│ │PyQt6   │ │Chrome 扩展    │
│·音频采集  │ │·摄像头抓帧│ │Tool      │ │GUI     │ │·WS 长连接    │
│·ASR 识别  │ │·JPEG编码 │ │·mss 全屏 │ │·波形    │ │·标签路由     │
│·回调通知  │ │          │ │·选区裁剪 │ │·状态灯 │ │·DOM 注入     │
└─────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └──────┬───────┘
      │            │            │           │             │
      │         信号桥 (signal_bridge / pyqtSignal)        │
      └────────────┴────────────┴───────────┘             │
                         │                                 │
                    识别文本 / 图片                          │
                         ▼                                 │
┌──────────────────────────────────────────────────────────┴──────┐
│               WebSocket Server (ws://127.0.0.1:8765)              │
│          broadcast_text(text)  │  broadcast_image(base64)         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块解构

### 3.1 `main.py` — 统一入口

```
main()
  ├── ws_manager.start()        # 启动 WebSocket 守护线程
  ├── QApplication()            # 创建 Qt 事件循环
  ├── MainWindow().show()       # 显示 GUI 窗口
  └── app.exec()                # 进入事件循环
```

### 3.2 `core/config.py` — 配置中心

| 配置项 | 值 | 说明 |
|--------|-----|------|
| MODEL_NAME | `iic/SenseVoiceSmall` | 语音识别模型 |
| VAD_MODEL | `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` | 语音活动检测 |
| PUNC_MODEL | `iic/punc_ct-transformer_cn-en-common-vocab471067-large` | 标点恢复 |
| HOTKEY_VOICE | `alt+1` | 按住说话 |
| HOTKEY_CAMERA | `alt+2` | 拍照上传 |
| HOTKEY_SCREENSHOT | `alt+3` | 截图上传 |
| WS_HOST/PORT | `127.0.0.1:8765` | WebSocket 地址 |

### 3.3 `core/voice_engine.py` — 语音识别引擎

纯 Python 模块，不依赖任何 GUI 框架。通过 **回调函数** 与外部通信。

```
VoiceEngine
├── init_model()
│   ├── snapshot_download() × 3    # 模型名 → 本地路径
│   └── AutoModel(model, vad, punc)
│
├── start_listening()
│   ├── keyboard.add_hotkey() × 2  # 按下/松开
│   └── sd.InputStream()           # 开启麦克风流
│
├── _on_hotkey_press()             # 开始录音
│   └── → on_recording_start
│
├── _on_hotkey_release()           # 停止录音
│   └── → Thread(_process_audio)
│
└── _process_audio()
    ├── np.concatenate(buffer)     # 拼接音频
    ├── model.generate(audio)      # FunASR 识别
    ├── rich_transcription_postprocess()
    └── → on_result(text)          # 回调结果
```

**回调体系**: `on_model_loading` | `on_model_ready` | `on_model_error` | `on_recording_start` | `on_recording_stop` | `on_processing` | `on_result` | `on_error`

**关键设计**:
- `_hotkey_armed` 标志位 + 0.5s Timer — 防止热键注册瞬间误触发
- `processing` 锁 — 防止快速按放启动多个识别线程
- `_max_buffer_frames = SAMPLE_RATE * 120` — 音频缓冲区 120 秒上限

### 3.4 `core/camera_engine.py` — 摄像头采集

```
CameraEngine
├── capture_frame_base64()
│   ├── cv2.VideoCapture(0)       # 懒初始化
│   ├── cap.read()                # 抓帧（锁保护）
│   └── → "data:image/jpeg;base64,..."
└── release()                     # 释放摄像头（锁保护）
```

### 3.5 `core/screenshot_tool.py` — 屏幕截图引擎

纯逻辑模块，负责全屏捕捉和裁剪编码。

```
capture_fullscreen()
  ├── mss.mss().grab(monitors[1])   # 全屏截图 → np.ndarray (H,W,3)
  └── → RGB numpy array

crop_to_jpeg_base64(img, x, y, w, h)
  ├── img[y:y+h, x:x+w]             # 裁剪选区
  ├── cv2.imencode('.jpg', crop)     # JPEG 编码
  └── → "data:image/jpeg;base64,..."
```

### 3.5.1 `gui/widgets/screenshot_overlay.py` — 截图选区窗口

PyQt6 全屏遮罩窗口，受 Flameshot 启发。

```
ScreenshotOverlay(screen_img)
├── 全屏 Tool 窗口 (FramelessWindowHint | StaysOnTopHint)
├── 绘制背景图 + 半透明暗色遮罩
├── mousePressEvent  → 记录起点
├── mouseMoveEvent   → 实时绘制选区边框 (挖空效果)
├── mouseReleaseEvent → 关闭窗口 → emit sig_captured(x,y,w,h)
└── keyPressEvent(Esc) → emit sig_cancelled
```

触发流程：
1. 用户按 `Alt+3` → MainWindow 调用 `capture_fullscreen()` 获取屏幕像素
2. 创建 `ScreenshotOverlay(screen_img)` 全屏遮罩
3. 用户鼠标拖拽选区 → 松开后 `sig_captured` 发射坐标
4. MainWindow 在子线程中 `crop_to_jpeg_base64()` → `ws_manager.broadcast_image()`

### 3.6 `server/ws_server.py` — WebSocket 服务

```
WebSocketServer
├── start()
│   └── Thread(_thread_target)     # daemon 线程
│       └── asyncio.run(_start_server)
│           └── websockets.serve(handle_client)
│
├── stop()
│   └── _stop_event.set()          # 优雅关闭
│
├── broadcast_text(text)
│   └── → {"action":"insert_text", "text":"..."}
│
├── broadcast_image(b64)
│   └── → {"action":"upload_image", "data":"..."}
│
└── handle_client(ws)
    └── async for message in ws    # 心跳 ping 过滤
```

**全局单例**: `ws_manager = WebSocketServer()`

### 3.7 `gui/` — PyQt6 图形界面

```
gui/
├── main_window.py       # 主窗口 (MainWindow)
├── signal_bridge.py     # core ↔ PyQt 信号适配器
├── style.qss            # 暗黑主题样式表
└── widgets/
    ├── top_bar.py              # 顶栏 (Logo + 菜单 + 头像)
    ├── audio_wave.py           # 双色贝塞尔曲线波形可视化
    ├── bottom_nav.py           # 底部导航 (语音/历史/设置)
    ├── history_dialog.py       # 识别历史弹窗
    └── screenshot_overlay.py   # 截图选区全屏遮罩
```

**MainWindow 信号流**:

```
VoiceEngineBridge                  MainWindow
    ├── sig_model_loading    →    _on_model_loading    (黄灯 LOADING)
    ├── sig_model_ready      →    _on_model_ready      (绿灯 READY)
    ├── sig_model_error      →    _on_model_error      (红灯 ERROR)
    ├── sig_recording_start  →    _on_recording_start  (亮绿 LISTENING, 波形放大)
    ├── sig_recording_stop   →    _on_recording_stop   (波形恢复)
    ├── sig_processing       →    _on_processing       (黄灯 PROCESSING)
    ├── sig_result           →    _on_result           (显示文字 + WS推送)
    └── sig_error            →    _on_error            (显示错误)

CameraBridge
    ├── sig_capture_success  →    _on_capture_success  (WS推送图片)
    └── sig_capture_error    →    _on_capture_error

Screenshot 触发 (Alt+3)
    ├── capture_fullscreen()                     → 全屏像素
    ├── ScreenshotOverlay(screen_img)            → 用户选区
    ├── crop_to_jpeg_base64(img, x, y, w, h)     → base64
    └── ws_manager.broadcast_image(b64)          → 浏览器
```

**WaveForm 渲染**: `AudioWaveWidget` 用 QPainter 绘制双色（青+紫）贝塞尔曲线，叠加径向渐变发光效果。录音时 30fps，空闲 5fps。

### 3.8 `extension/` — Chrome 浏览器扩展

```
extension/
├── manifest.json       # MV3 配置 (6 个 AI 站点)
├── background.js       # Service Worker
│   ├── WebSocket 连接 ws://127.0.0.1:8765
│   ├── 自动重连 (3s)
│   ├── alarms 心跳保活 (1min)
│   └── 路由 → chrome.tabs.sendMessage
└── content.js          # 网页注入脚本
    ├── SITE_ADAPTERS   # 站点适配器
    ├── getChatInput()  # 选择器探测
    ├── injectText()    # value/contenteditable 分流
    └── injectImage()   # ClipboardEvent 粘贴
```

**站点适配器**: 按 `location.hostname` 匹配不同 AI 平台的输入框选择器和注入策略。

| 站点 | 选择器优先级 |
|------|-------------|
| chat.deepseek.com | `#chat-input` → `textarea` → `[contenteditable]` |
| kimi.moonshot.cn | `textarea` → `.chat-input-editor textarea` |
| chatgpt.com | `#prompt-textarea` → `textarea` |
| 通用回退 | `textarea` → `[contenteditable]`, inputMode=auto |

---

## 4. 数据流详解

### 4.1 语音 → 浏览器 完整链路

```
[用户按住 Alt+1]
    │
    ▼
keyboard 全局钩子
    │
    ├── _on_hotkey_press()
    │   ├── recording = True
    │   ├── audio_buffer = []
    │   └── emit sig_recording_start → GUI 显示 "LISTENING..."
    │
    ├── [期间] _audio_callback() 持续追加 ndarray 到 audio_buffer
    │
    ▼
[用户松开 Alt+1]
    │
    ▼
_on_hotkey_release()
    ├── recording = False
    ├── emit sig_recording_stop → GUI 波形缩小
    └── Thread(_process_audio)
        ├── np.concatenate(audio_buffer) → 完整音频 ndarray
        ├── model.generate(input=audio, batch_size_s=300)
        │   ├── SenseVoiceSmall 语音→文本
        │   ├── FSMN-VAD 语音活动检测
        │   └── CT-Transformer 标点恢复
        ├── rich_transcription_postprocess(text) → "你好，请问..."
        └── emit sig_result(text)
            ├── MainWindow._on_result
            │   ├── GUI 显示识别结果
            │   ├── _history.append(text)
            │   └── ws_manager.broadcast_text(text)
            │       └── {"action":"insert_text", "text":"你好，请问..."}
            │           ▼
            │       Chrome Extension (background.js)
            │           ├── chrome.tabs.query({active:true})
            │           └── chrome.tabs.sendMessage(tabId, payload)
            │               ▼
            │           content.js
            │               ├── getChatInput() → 找到 textarea
            │               ├── el.value = (old || "") + text
            │               └── el.dispatchEvent(new Event('input'))
            │                   ▼
            │               DeepSeek React 状态更新 → 输入框出现文字
```

### 4.2 拍照 → 浏览器 完整链路

```
[用户按 Alt+2]
    │
    ▼
CameraBridge.capture() [子线程]
    ├── CameraEngine.capture_frame_base64()
    │   ├── cv2.VideoCapture(0).read() → frame
    │   └── cv2.imencode('.jpg') → base64
    └── emit sig_capture_success(b64)
        └── ws_manager.broadcast_image(b64)
            └── {"action":"upload_image", "data":"data:image/jpeg;base64,..."}
                ▼
            content.js
                ├── base64 → Blob → File
                ├── DataTransfer.items.add(file)
                └── dispatchEvent(new ClipboardEvent('paste'))
                    ▼
                AI 网页图片上传处理
```

### 4.3 截图 → 浏览器 完整链路

```
[用户按 Alt+3]
    │
    ▼
_on_screenshot_hotkey() [MainThread]
    ├── capture_fullscreen() [mss]
    │   └── → 全屏 RGB ndarray
    ├── ScreenshotOverlay(screen_img)
    │   ├── 全屏遮罩 + 背景图 + 暗色叠加
    │   ├── 用户鼠标拖拽选区
    │   ├── 松开 → emit sig_captured(x, y, w, h)
    │   └── Esc → emit sig_cancelled
    └── sig_captured 回调 [子线程]
        ├── crop_to_jpeg_base64(img, x, y, w, h)
        │   ├── img[y:y+h, x:x+w] → 裁剪
        │   └── cv2.imencode('.jpg') → base64
        └── ws_manager.broadcast_image(b64)
            └── {"action":"upload_image", "data":"data:image/jpeg;base64,..."}
                ▼
            content.js → 图片注入浏览器
```

---

## 5. 线程模型

```
┌─────────────────┐
│  MainThread      │  QApplication 事件循环 + GUI 渲染
│  (主线程)         │  + ScreenshotOverlay 选区交互
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────────┬──────────────┐
    ▼         ▼             ▼              ▼              ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Model-   │ │WebSocket  │ │keyboard   │ │Camera    │ │Screen-   │
│Loader   │ │asyncio    │ │hotkey     │ │capture   │ │shot      │
│Thread   │ │loop       │ │callback   │ │Thread    │ │crop      │
│(QThread)│ │(daemon)   │ │(hook线程) │ │(daemon)  │ │Thread    │
└────────┘ └──────────┘ └──────────┘ └──────────┘ │(daemon)  │
     │                                             └──────────┘
     ▼
┌──────────┐
│_process_ │  每次松键 new Thread
│audio     │  (daemon, 处理完即结束)
└──────────┘
```

- **跨线程通信**: 仅通过 `pyqtSignal` (线程安全) 和 `asyncio.run_coroutine_threadsafe`
- **音频缓冲区**: `threading.Lock` 保护 `audio_buffer`

---

## 6. 关键技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 语音引擎与 GUI 解耦 | VoiceEngine 纯 Python + 回调 | 可脱离 GUI 独立使用、可测试 |
| 浏览器文字注入 | WebSocket + Extension | HTTPS 页面封锁 ws://；Extension Service Worker 有独立安全上下文 |
| 热键抢占 | `suppress=True` + 0.5s 防抖 | 避免注册瞬间误触发、阻止其他程序响应 |
| 模型加载 | `snapshot_download` → 本地路径 | 跳过 modelscope registry 在线查询，避免网络波动导致 "not registered" |
| 截图实现 | mss 全屏 + PyQt6 遮罩选区 | mss 比 PIL 快 10 倍；窗体遮罩受 Flameshot 启发，原生体验 |
| GUI 框架 | PyQt6 无边框 + QSS | 暗黑主题、圆角悬浮窗、硬件加速渲染 |

---

## 7. 项目文件清单

```
AURA/
├── main.py                     # 入口
├── requirements.txt            # 依赖
├── aura-injector.user.js       # 油猴脚本 (备用)
├── chrome-whitelist.reg        # 扩展白名单注册表
├── core/
│   ├── config.py               # 全局配置
│   ├── voice_engine.py         # 语音识别引擎
│   ├── camera_engine.py        # 摄像头采集
│   └── screenshot_tool.py      # 截图引擎
├── gui/
│   ├── main_window.py          # 主窗口
│   ├── signal_bridge.py        # core ↔ Qt 适配器
│   ├── style.qss               # 暗黑主题
│   └── widgets/
│       ├── top_bar.py              # 顶栏
│       ├── audio_wave.py           # 波形可视化
│       ├── bottom_nav.py           # 底部导航
│       ├── history_dialog.py       # 历史记录
│       └── screenshot_overlay.py   # 截图选区遮罩
├── server/
│   └── ws_server.py            # WebSocket 服务
├── extension/
│   ├── manifest.json           # Chrome 扩展配置
│   ├── background.js           # Service Worker
│   └── content.js              # 网页注入脚本
├── tests/
│   ├── test_config.py          # 配置测试
│   ├── test_voice_engine.py    # 语音引擎测试
│   ├── test_camera_engine.py   # 摄像头测试
│   └── test_signal_bridge.py   # 信号桥测试
├── docs/
│   ├── Architecture_Doc.md     # 问题跟踪 & 设计演进
│   ├── Technical_Architecture.md  # 本文档
│   └── User_Guide.md           # 用户手册
├── models/                     # AI 模型缓存 (自动下载)
├── tampermonkey/               # 油猴备用脚本
└── extension.pem               # 扩展私钥
```
