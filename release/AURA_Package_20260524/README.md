# AURA 发布包

AURA 是一个本地 AI 语音助手，包含 Windows 服务端、Chrome 浏览器扩展和 Android 手机 APP。

## 目录说明

| 路径 | 用途 |
| --- | --- |
| `AURA.exe` | Windows 服务端启动程序 |
| `_internal/` | 服务端内置运行库，必须与 `AURA.exe` 放在一起 |
| `Start_AURA_Server.bat` | 服务端一键检测与启动脚本 |
| `extension/` | Chrome 扩展源码目录 |
| `mobile/app-arm64-v8a-release.apk` | 适用于大多数现代 Android 手机的安装包 |
| `models/` | 首次启动后自动生成的模型缓存目录 |

## 服务端启动

1. 保持 `AURA.exe` 与 `_internal/` 在同一目录，不要只单独复制 `.exe`。
2. 双击 `Start_AURA_Server.bat`。
3. 首次运行时，脚本会检测 ModelScope 网络连接，服务端将自动下载语音模型。
4. 模型下载完成后会缓存在 `models/` 中，后续启动直接使用本地模型。

服务端已经包含 Python 运行环境和 Python 依赖，不需要安装 Python，也不需要执行 `pip install`。

## 手机连接与防火墙

手机端通过局域网发现并连接电脑服务端。首次使用手机连接前，建议右键 `Start_AURA_Server.bat`，选择“以管理员身份运行”一次，以自动添加以下防火墙规则：

| 端口 | 协议 | 用途 |
| --- | --- | --- |
| `8765` | TCP | WebSocket 通信 |
| `8766` | TCP | 文件传输 |
| `5353` | UDP | mDNS 自动发现 |

## Chrome 扩展安装

Windows 正式版 Chrome 会禁用直接安装的本地 `.crx` 扩展。因此请使用开发者模式加载目录：

1. 打开 `chrome://extensions/`。
2. 开启右上角“开发者模式”。
3. 点击“加载已解压的扩展程序”。
4. 选择本发布包中的 `extension/` 文件夹。

扩展签名私钥 `.pem` 不包含在发布包中。它仅用于开发者重新打包扩展，不应向用户分发。

## Android APP 安装

将 `mobile/app-arm64-v8a-release.apk` 发送到手机并安装即可。此安装包仅包含 `arm64-v8a` 架构，适用于绝大多数近年的 Android 手机，体积比通用 APK 更小。

## 首次运行流程

1. 在电脑上启动 `Start_AURA_Server.bat`，等待模型初始化完成。
2. 在 Chrome 中加载 `extension/` 扩展目录。
3. 在手机上安装并启动 APK。
4. 确保手机和电脑连接到同一 WiFi。
5. 手机通过 mDNS 自动发现桌面服务后，即可上传录音和截图。

## 注意事项

- 模型文件较大，不随发布包上传；首次启动时从国内可访问的 ModelScope 下载。
- 不要删除或移动 `_internal/`，否则 `AURA.exe` 无法运行。
- 不要公开上传扩展私钥 `.pem`。
