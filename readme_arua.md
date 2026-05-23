# AURA Voice Assistant

本地 AI 语音助手 — 按住说话，松开出字，自动注入 AI 网页输入框。

## 它能做什么

- **语音输入** — 按住 `Alt+1` 说话，松开后离线识别文字，自动发送到 AI 网页（DeepSeek/Kimi/ChatGPT/豆包/通义千问/Gemini）
- **摄像头拍照** — `Alt+2` 拍照，图片自动上传到当前 AI 对话
- **全屏截图** — `Alt+3` 截取全屏，推送到 AI 输入框
- **手机联动** — 手机 APP 通过 WiFi 自动发现桌面服务，支持拍照/录音/截图上传

## 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  手机 APP    │────▶│  WS 服务端    │────▶│  Chrome 扩展     │────▶│  AI 网页     │
│  (Flutter)   │◀────│  (Python)     │◀────│  (MV3)          │     │  DeepSeek等  │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
       │                   │
       │            ┌──────┴──────┐
       └───────────▶│  桌面客户端   │
                    │  (PyQt6)     │
                    └─────────────┘
```

### 数据流

| 操作 | 路径 |
|------|------|
| 语音 (Alt+1) | 麦克风 → FunASR 离线识别 → WebSocket → 扩展注入文字 |
| 拍照 (Alt+2) | 摄像头 → OpenCV → WebSocket → 扩展拖拽上传图片 |
| 截图 (Alt+3) | mss 全屏 → OpenCV 裁剪 → WebSocket → 扩展注入图片 |
| 手机拍照 | 手机摄像头 → WebSocket → 桌面转发 → 扩展注入图片 |
| 手机录音 | 手机麦克风 → WebSocket → FunASR 识别 → 扩展注入文字 |

## 项目结构

```
softwareInstruct/
├── main.py                    # 入口：启动 WebSocket 服务 + PyQt6 窗口
├── core/
│   ├── config.py              # 全局配置（快捷键、模型名、端口）
│   ├── voice_engine.py        # 语音引擎：FunASR 离线识别，8 回调对外通信
│   ├── camera_engine.py       # 摄像头引擎：懒初始化 + threading.Lock
│   ├── screenshot_tool.py     # 截图工具：mss 全屏 + OpenCV 编码
│   └── history_store.py       # 历史记录：语音/图片持久化到 history/
├── gui/
│   ├── main_window.py         # 主窗口：无边框 UI，热键 1s 防抖
│   ├── signal_bridge.py       # 信号桥：线程安全的 pyqtSignal 通信
│   ├── style.qss              # 暗色主题样式
│   └── widgets/
│       ├── top_bar.py         # 顶栏：LOGO + 菜单按钮
│       ├── bottom_nav.py      # 底栏：麦克风/历史/设置
│       ├── audio_wave.py      # 音频波形动画（双色正弦波）
│       ├── history_dialog.py  # 历史记录弹窗
│       └── settings_dialog.py # 设置弹窗（摄像头切换）
├── server/
│   ├── ws_server.py           # WebSocket 服务：0.0.0.0:8765，广播文本/图片
│   └── file_server.py         # HTTP 文件服务：8766，按需启动
├── extension/
│   ├── manifest.json          # Chrome MV3 扩展清单
│   ├── background.js          # Service Worker：WS 长连接 + 指数退避重连
│   └── content.js             # 内容脚本：站点适配器模式注入文字/图片
├── models/                    # FunASR 模型缓存（~3GB，首次运行自动下载）
├── AppWorking/mobile/aura_mobile/  # Flutter 手机 APP
│   ├── lib/
│   │   ├── main.dart          # APP 入口
│   │   ├── screens/           # UI 页面（首页/相机/悬浮窗/设置）
│   │   └── services/          # 服务层
│   │       ├── discovery_service.dart  # mDNS 自动发现桌面服务
│   │       ├── ws_service.dart         # WebSocket 客户端 + 断线重连
│   │       ├── audio_service.dart      # 录音服务
│   │       ├── camera_service.dart     # 相机服务
│   │       └── upload_queue_service.dart # 上传队列（离线缓存）
│   └── android/               # Android 原生代码
│       └── app/src/main/kotlin/.../KeepAliveService.kt  # 前台服务保活
├── tests/                     # 单元测试
└── requirements.txt           # Python 依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动桌面端

```bash
python main.py
```

首次运行会自动下载 FunASR 模型（约 3GB），需 2-10 分钟。模型下载完成后状态变为 `READY`。

### 3. 安装 Chrome 扩展

1. 打开 `chrome://extensions/`
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」，选择 `extension/` 目录

### 4. 使用

| 快捷键 | 功能 |
|--------|------|
| `Alt+1` (按住说话) | 语音识别，松开后文字发送到 AI 网页 |
| `Alt+2` | 摄像头拍照并上传 |
| `Alt+3` | 全屏截图并上传 |

### 5. 手机 APP（可选）

```bash
cd AppWorking/mobile/aura_mobile
flutter pub get
flutter build apk --release
```

编译环境要求：
- Flutter SDK：`C:\flutter\`
- JDK 21：`C:\jdk21\jdk-21.0.11+10\`
- Android SDK：`C:\Android\`
- Windows 开发者模式（插件符号链接）

手机与电脑连接同一 WiFi 后，APP 通过 mDNS 自动发现桌面服务。

## 技术栈

| 层 | 技术 |
|----|------|
| 语音识别 | FunASR (Paraformer-Large 220M) / sounddevice |
| 桌面 UI | PyQt6 / QSS 暗色主题 |
| 网络通信 | websockets / asyncio |
| 服务发现 | zeroconf (mDNS) |
| 截图/拍照 | mss / OpenCV |
| 热键 | keyboard |
| 浏览器扩展 | Chrome MV3 / Service Worker / Content Script |
| 手机端 | Flutter / Dart / web_socket_channel / multicast_dns |

## 端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 8765 | WebSocket | 桌面 ↔ 扩展 ↔ 手机 |
| 8766 | HTTP | 文件下载（按需启动） |
| 5353 | UDP | mDNS 服务发现 |

Windows 防火墙需开放以上三个端口。

## 配置

所有可调参数在 `core/config.py`：

```python
HOTKEY_VOICE = "alt+1"       # 语音快捷键
HOTKEY_CAMERA = "alt+2"      # 拍照快捷键
HOTKEY_SCREENSHOT = "alt+3"  # 截图快捷键
WS_HOST = "0.0.0.0"          # WebSocket 监听地址
WS_PORT = 8765               # WebSocket 端口
SAMPLE_RATE = 16000          # 音频采样率
```

## 支持的 AI 网站

- ChatGPT (chatgpt.com / chat.openai.com)
- DeepSeek (chat.deepseek.com)
- Kimi (kimi.moonshot.cn)
- Gemini (gemini.google.com)
- 豆包 (doubao.com)
- 通义千问 (tongyi.aliyun.com)

其他网站使用通用回退适配器（自动检测 textarea / contenteditable 输入框）。

## 测试

```bash
pytest tests/ -v
```

## 运行测试

```bash
# 启动桌面应用
python main.py

# 编译手机 APK
cd AppWorking/mobile/aura_mobile && flutter build apk --release

# 运行测试
pytest tests/ -v
```
