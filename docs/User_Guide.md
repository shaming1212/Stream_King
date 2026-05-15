# AURA Voice Assistant 使用文档

## 简介

AURA 是一个本地 AI 语音助手，支持**按住说话 → 自动识别 → 文字注入 DeepSeek 网页版**。搭配 Chrome 浏览器插件使用，免除手动打字，实现语音到 AI 对话的无缝流转。

## 系统要求

- Windows 10/11
- Python 3.10+
- Chrome 浏览器（用于安装插件）
- 麦克风设备
- （可选）摄像头设备

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

首次启动时，AI 模型会自动下载到项目的 `models/` 目录（约 500MB），请耐心等待。

### 2. 安装 Chrome 扩展

1. 打开 Chrome，地址栏输入 `chrome://extensions/`
2. 打开右上角"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择项目中的 `extension/` 文件夹
5. 确认扩展已启用

## 启动

```bash
python main.py
```

启动后会弹出桌面窗口，并在后台启动 WebSocket 服务（`ws://127.0.0.1:8765`）。Chrome 扩展会自动连接。

## 界面说明

```
┌──────────────────────┐
│  ⚄    A U R A    👤  │  ← 顶栏：菜单 / Logo / 头像
│──────────────────────│
│                      │
│     ════~~═══        │  ← 音频波形可视化区
│        ~~~           │     (录音时动态放大)
│                      │
│   ┌──────────────┐   │
│   │ ●  READY      │   │  ← 状态指示灯（绿=就绪 / 黄=处理中 / 红=错误）
│   └──────────────┘   │
│                      │
│   How can I help?    │  ← 主提示文字
│   按住 ALT + 1 说话  │  ← 操作提示
│                      │
│ ┌───🎙────⏱────⚙───┐ │  ← 底部导航：语音 / 历史 / 设置
│ └──────────────────┘ │
└──────────────────────┘
```

## 使用方法

### 语音输入（核心功能）

| 步骤 | 操作 | 界面反馈 |
|------|------|----------|
| 1 | 打开支持的 AI 对话网页（如 DeepSeek、Kimi、豆包等） | 扩展自动检测 |
| 2 | 按住 `Alt + 1` 开始说话 | 波形放大，状态显示 "LISTENING..." |
| 3 | 说完后松开 `Alt + 1` | 状态显示 "PROCESSING..." |
| 4 | 稍等 1~3 秒 | 文字自动出现在 DeepSeek 输入框中 |

> **注意**：请确保受支持的 AI 对话页面是当前活动标签页，否则文字不会注入。

### 拍照上传

| 快捷键 | 功能 |
|--------|------|
| `Alt + 2` | 拍摄摄像头画面并注入 AI 对话输入框 |

## 状态指示灯

| 颜色 | 状态 | 含义 |
|------|------|------|
| 🟡 橙黄 | LOADING... | 正在加载 AI 模型 |
| 🟢 绿色 | READY | 就绪，可以开始说话 |
| 🟢 亮绿 | LISTENING... | 正在录音中 |
| 🟡 橙黄 | PROCESSING... | 正在识别语音 |
| 🔴 红色 | ERROR | 模型加载失败 |

## 常见问题

### Q: 启动后一直显示"LOADING"？

首次运行需要从 ModelScope 下载 AI 模型文件（SenseVoiceSmall），取决于网速可能需要 2~10 分钟。后续启动会跳过下载，几秒内即可就绪。

### Q: 按住快捷键说话，但没有文字出现在网页中？

1. 确认 Chrome 扩展已启用（扩展图标无报错）
2. 确认 DeepSeek 页面是当前激活的标签页
3. 确认 WebSocket 连接正常（在 Chrome 扩展的 Service Worker 控制台查看日志）
4. 尝试刷新 DeepSeek 页面

### Q: 识别准确率不高？

- 尽量在安静环境下使用
- 吐字清晰，语速适中
- 避免过长的句子（建议 15 秒以内）

### Q: 如何修改快捷键？

编辑 `core/config.py` 文件：

```python
HOTKEY_VOICE = "alt+1"       # 改为你想要的快捷键
HOTKEY_CAMERA = "alt+2"      # 同上
```

快捷键格式参考 [keyboard 模块文档](https://github.com/boppreh/keyboard)，支持组合键如 `ctrl+shift+v`。

### Q: 端口 8765 被占用？

编辑 `core/config.py`，修改：

```python
WS_PORT = 8766  # 换成其他端口
```

同时修改 `extension/background.js` 中的 `WS_URL`，保持一致。

### Q: 如何关闭桌面窗口？

点击窗口右上角关闭按钮，或直接关闭命令行窗口。程序会释放麦克风和键盘监听资源。

## 项目结构速查

```
├── main.py                 # 入口
├── core/
│   ├── config.py           # 所有可配置参数
│   ├── voice_engine.py     # 语音识别核心
│   └── camera_engine.py    # 摄像头采集（预留）
├── gui/
│   ├── main_window.py      # 主窗口
│   ├── signal_bridge.py    # 线程桥接
│   └── style.qss           # UI 样式
├── server/
│   └── ws_server.py        # WebSocket 服务
├── extension/              # Chrome 扩展
├── models/                 # AI 模型缓存
└── requirements.txt
```
