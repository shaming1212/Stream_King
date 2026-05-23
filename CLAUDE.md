# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

```bash
# 启动桌面应用
python main.py

# 编译手机 APK
cd AppWorking/mobile/aura_mobile && flutter build apk --release

# 运行全部测试
pytest tests/ -v

# 安装 Python 依赖
pip install -r requirements.txt

# Flutter 依赖
cd AppWorking/mobile/aura_mobile && flutter pub get
```

## 架构概要

AURA 是一个本地 AI 语音助手，核心链路：**按住 Alt+1 说话 → FunASR 离线语音识别 → WebSocket 推送文本 → Chrome 扩展注入 AI 网页输入框**。同时支持 Alt+2 摄像头拍照、Alt+3 屏幕截图，**手机 APP 通过 WiFi + mDNS 自动发现桌面服务，拍照/录音/截图上传**。

整个系统分六层：

- **`core/`** — 纯 Python 逻辑层。`voice_engine.py` 通过 8 个回调与外部通信，Paraformer-Large（220M 参数）离线 ASR。`camera_engine.py` 懒初始化 + threading.Lock。`screenshot_tool.py` mss 全屏捕捉 + OpenCV 裁剪编码。`config.py` 是所有可调参数的唯一入口（快捷键、模型名、端口）。
- **`gui/`** — PyQt6 表现层。`main_window.py` 无边框主窗口，热键 1s 防抖，截图通过 `pyqtSignal` 线程安全更新 UI，启动时检测摄像头可用性。
- **`server/`** — WebSocket + mDNS 服务层。`ws_server.py` 绑定 `0.0.0.0:8765`（支持局域网），30s ping 保活，ping/pong 应用层心跳。`zeroconf` 广播 `_aura._tcp` mDNS 服务，手机自动发现。HTTP 文件端点待建（`8766`）。
- **`extension/`** — Chrome MV3 扩展。`background.js` 维护 WS 长连接 + `chrome.tabs.query` 路由。`content.js` 站点适配器模式（DeepSeek/Kimi/ChatGPT/豆包/通义千问/通用回退），图片通过 `DragEvent` 注入，文字通过 `insert_text`。
- **`models/`** — FunASR 模型缓存（Paraformer-Large + FSMN-VAD + CT-Transformer large），约 3GB。
- **`AppWorking/mobile/`** — Flutter 手机 APP。mDNS 自动发现 → WebSocket 连接桌面服务 → 拍照/录音/截图上传 → 推送到浏览器 AI 输入框。连接采用指数退避重连（3s→6s→12s→24s→30s）。

## 重要约束

- `core/config.py` 必须在 funasr import 之前执行（`main.py:15` 用 `import core.config` 确保环境变量先设置）
- WS_HOST 设为 `0.0.0.0` 才能让手机通过 WiFi 连上（之前 `127.0.0.1` 只监听本机）
- VoiceEngine `_hotkey_armed` 标志位 + 0.5s Timer 防止误触发；`processing` 锁防止快速按放
- 音频缓冲区上限 `SAMPLE_RATE * 120`（120 秒），超出自动丢弃旧帧
- WebSocket 服务通过 `asyncio.Event` 优雅关闭，`closeEvent` 调用 `ws_manager.stop()`
- mDNS 用 `AsyncZeroconf`（非同步版），`async_register_service` 注册，不可用 `Zeroconf` 同步版否则 asyncio 死锁
- 跨线程通信仅通过 `pyqtSignal`（线程安全）和 `asyncio.run_coroutine_threadsafe`
- 手机端 mDNS 发现到服务器后立即停止扫描（`_foundServer` 标志），防止广播重复触发连接循环
- 从根目录运行所有 Python 命令，模块导入依赖 `ROOT_DIR` 在 `sys.path` 中
- Windows 防火墙需开放 8765(TCP)、8766(TCP)、5353(UDP) 三个端口
- 编译 Flutter 需 Windows 开发者模式（插件符号链接）

## 手机端编译环境

| 组件 | 路径 |
|------|------|
| Flutter SDK | `C:\flutter\` |
| Java JDK 21 | `C:\jdk21\jdk-21.0.11+10\` |
| Android SDK | `C:\Android\` |
| APK 输出 | `AppWorking\mobile\aura_mobile\build\app\outputs\flutter-apk\` |

编译前需设环境变量：`JAVA_HOME=C:\jdk21\jdk-21.0.11+10`，`PATH` 含 `C:\flutter\bin`

## 技术栈

Python 3.10+ / PyQt6 / FunASR (Paraformer-Large) / sounddevice / OpenCV / mss / websockets / zeroconf / keyboard / Chrome Extension MV3 / Flutter 3.x / Dart / multicast_dns / photo_manager / record / camera
