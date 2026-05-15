# AURA Voice Assistant

本地 AI 语音助手 + Chrome 浏览器插件联动系统。按住快捷键说话，本地 FunASR 引擎实时识别，通过 WebSocket + Chrome 扩展将文字/图片注入 Kimi、豆包、ChatGPT、DeepSeek、通义千问等 AI 对话页面。

## 快速启动

```bash
pip install -r requirements.txt
python main.py
```

首次启动会自动下载 AI 模型文件（约 500MB），请耐心等待。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Alt + 1` | 按住说话，松开识别并注入文字 |
| `Alt + 2` | 拍摄摄像头画面并注入图片 |
| `Alt + 3` | 屏幕截图选区并注入图片 |

## 项目结构

```
├── core/                       # 核心引擎层（纯逻辑，不依赖 GUI）
│   ├── config.py               # 全局配置（快捷键、模型、端口）
│   ├── voice_engine.py         # 语音识别引擎（FunASR）
│   ├── camera_engine.py        # 摄像头采集引擎（OpenCV）
│   └── screenshot_tool.py      # 屏幕截图引擎（mss + OpenCV）
│
├── gui/                        # GUI 表现层（PyQt6 暗黑悬浮窗）
│   ├── main_window.py          # 主窗口（无边框、拖拽、信号连接）
│   ├── signal_bridge.py        # core → PyQt 线程安全信号适配器
│   ├── style.qss               # 暗黑主题样式表
│   └── widgets/                # UI 组件
│       ├── top_bar.py          # 顶栏（Logo + 菜单 + 头像）
│       ├── audio_wave.py       # 双色贝塞尔曲线波形可视化
│       ├── bottom_nav.py       # 底部导航（语音 / 历史 / 设置）
│       ├── history_dialog.py   # 识别历史弹窗
│       └── screenshot_overlay.py  # 截图选区全屏遮罩
│
├── server/                     # 本地通信层
│   └── ws_server.py            # WebSocket 服务（ws://127.0.0.1:8765）
│
├── extension/                  # Chrome 浏览器插件（Manifest V3）
│   ├── manifest.json           # 扩展配置（6 个 AI 站点）
│   ├── background.js           # Service Worker（WS 长连接 + 标签路由）
│   └── content.js              # 网页注入脚本（站点适配器 + DOM 注入）
│
├── tampermonkey/               # 油猴脚本备用方案
│   └── aura-injector.user.js
│
├── tests/                      # 单元测试
│   ├── test_config.py
│   ├── test_voice_engine.py
│   ├── test_camera_engine.py
│   └── test_signal_bridge.py
│
├── docs/                       # 技术文档
│   ├── Technical_Architecture.md  # 技术架构文档
│   ├── Architecture_Doc.md        # 设计演进与问题追踪
│   └── User_Guide.md              # 用户手册
│
├── models/                     # AI 模型缓存（自动下载）
├── main.py                     # 统一入口
└── requirements.txt            # Python 依赖
```

## 安装 Chrome 扩展

1. 打开 Chrome，地址栏输入 `chrome://extensions/`
2. 开启右上角「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择项目中的 `extension/` 文件夹
5. 确认扩展已启用，打开任意支持的 AI 对话页面即可使用

## 支持的 AI 平台

| 平台 | 网址 |
|------|------|
| DeepSeek | chat.deepseek.com |
| Kimi | kimi.moonshot.cn |
| 豆包 | www.doubao.com |
| ChatGPT | chatgpt.com |
| 通义千问 | tongyi.aliyun.com |
| 其他 | 通用 textarea / contenteditable 回退 |

## 常见问题

### 启动后一直显示 LOADING？
首次运行需从 ModelScope 下载 AI 模型（约 500MB），网络速度影响较大，需等待 2-10 分钟。后续启动秒级就绪。

### 说话后文字没出现在网页中？
1. 确认 Chrome 扩展已启用
2. 确认 AI 对话页面是当前激活的标签页
3. 尝试刷新 AI 对话页面
4. 检查 WebSocket 连接状态（扩展 Service Worker 控制台可查看日志）

### 如何修改快捷键？
编辑 `core/config.py`，修改 `HOTKEY_VOICE`、`HOTKEY_CAMERA`、`HOTKEY_SCREENSHOT` 即可。快捷键格式参考 [keyboard 模块文档](https://github.com/boppreh/keyboard)。

### 端口 8765 被占用？
编辑 `core/config.py` 修改 `WS_PORT`，同时修改 `extension/background.js` 中的 `WS_URL`，保持一致。

---

---

## 愿景：全设备本地推流网络

> 让每一块屏幕都看见彼此，让每一次表达都穿透设备的边界。

### 我们走到了哪一步

这个项目诞生于一个朴素的想法：说话应该比打字快。于是有了 AURA——一个按住 Alt+1 说话、松开出字的桌面语音助手。它是这趟旅程的起点，也只是一张巨大蓝图上的第一笔。

**目前已经交付的：**

| 模块 | 状态 | 说明 |
|------|------|------|
| 语音识别引擎 (FunASR) | ✅ 完成 | SenseVoiceSmall + VAD + 标点恢复，本地离线，延迟 < 2s |
| PyQt6 桌面悬浮窗 | ✅ 完成 | 无边框暗黑窗口、双色波形可视化、状态指示灯、拖拽交互 |
| Chrome 浏览器扩展 | ✅ 完成 | Manifest V3、6 个 AI 平台适配、文字注入 + 图片粘贴 |
| 摄像头采集 + 截图 | ✅ 完成 | 摄像头拍照、屏幕选区截图，JPEG 编码 + base64 推送 |
| WebSocket 服务 | ✅ 完成 | 本地 ws://127.0.0.1:8765，优雅启停，广播推送 |
| 多站点适配 | ✅ 完成 | DeepSeek / Kimi / 豆包 / ChatGPT / 通义千问 + 通用回退 |
| 单元测试 | ✅ 完成 | 4 个测试文件，覆盖核心模块 |

**前面还有整片海：**

| 模块 | 状态 | 说明 |
|------|------|------|
| 多设备推流 → 订阅 | ⬜ 待开工 | 手机/平板/笔记本接入本地流服务，浏览器即终端 |
| WebRTC 实时音视频 | ⬜ 待开工 | 麦克风/摄像头/屏幕实时采集编码，低延迟分发 |
| Web 控制台 Dashboard | ⬜ 待开工 | 设备拓扑图、流列表、实时预览、带宽监控 |
| AI 实时处理管线 | ⬜ 待开工 | 音频流转字幕、视频帧 OCR、视觉理解、翻译管道 |
| OBS / VRChat / HA 集成 | ⬜ 待开工 | 跨生态融合，让 AURA 成为局域网基础设施 |
| CLI 工具链 + SDK | ⬜ 待开工 | `aura stream push`、开放 API，社区可自由开发下游 |
| 录制回放 + 合屏 | ⬜ 待开工 | 多流录制、时间轴回放、画中画/画廊布局 |
| 远程开发桥 | ⬜ 待开工 | 手机写代码，桌面跑编译，接收编译日志流 |

### 需要什么

这不是一个周末玩具。从单机语音助手到全设备推流平台，要走的路还很长。四阶段的完整蓝图，单人全职预估 **40–54 周**——还不算测试和文档。这需要大量的 API token、GPU 算力、多设备测试环境，以及最重要的——时间。如果你对这个方向感兴趣，愿意贡献代码、设备、算力或者只是一个好想法，欢迎随时参与进来。

### 为什么值得做

我们活在一个设备比人多的时代。每个像素都困在自己的玻璃牢笼里。把摄像头画面从手机搬到电脑，不该经过一个远在千里之外的服务器——信号本可以在空气里走完这一米。不是发明新协议，不是造轮子，而是把已经成熟的技术编织成一张每个人都能用的网，让你的每一块屏幕终于学会互相呼吸。

欢迎加入，一起搭建属于所有人的本地推流网络。
