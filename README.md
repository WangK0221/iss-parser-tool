# ISS 贴片程序解析工具

本项目是本地 Windows 桌面工具，用于解析 SMT `.iss` 程序文件并导出 Excel。

## 当前源码结构

```text
ISSParserTool
├─ assets
│  └─ app.ico
├─ iss_parser_core
│  ├─ iss_parser.py
│  └─ __init__.py
├─ pyinstaller_hooks
│  └─ pre_find_module_path
│     └─ hook-tkinter.py
├─ services
│  ├─ data_mapper.py
│  ├─ excel_exporter.py
│  ├─ feeder_mapping_analyzer.py
│  ├─ license_service.py
│  └─ __init__.py
├─ settings
│  └─ customer_export.json
├─ tools
│  ├─ analyze_feeder_mapping.py
│  ├─ build_win10_win11.ps1
│  ├─ build_win7.ps1
│  ├─ generate_license.py
│  ├─ license_generator_gui.py
│  └─ __init__.py
├─ ui
│  ├─ export_settings_dialog.py
│  ├─ main_window.py
│  └─ __init__.py
├─ utils
│  ├─ export_settings.py
│  ├─ file_utils.py
│  ├─ logger.py
│  └─ __init__.py
├─ config.py
├─ ISSParserTool_win10_win11.spec
├─ ISSParserTool_win7.spec
├─ LicenseGenerator.spec
├─ license_generator.py
├─ main.py
├─ README.md
└─ requirements.txt
```

说明：

- 源码目录已移除虚拟环境、样例文件和历史日志。
- 执行打包后会重新生成 `dist/` 等构建产物；若仅交付源码，可在发送前删除这些目录。
- 主程序只保留 2 个 `.spec`：
  - `ISSParserTool_win10_win11.spec`
  - `ISSParserTool_win7.spec`
- 旧的 `ISSParserTool_v5.spec` 已移除，因为它与 Win10/11 规格实质重复，且当前脚本未引用。

## 源码结构说明

- `main.py`
  - 主程序入口，仅负责启动日志和主窗口。
- `ui/`
  - 桌面界面层。
  - `main_window.py` 是主界面。
  - `export_settings_dialog.py` 是客户导出表头设置窗口。
- `iss_parser_core/`
  - 底层 `.iss` 解析器。
  - `iss_parser.py` 负责读取 XML、提取元件、位号、供料器/托盘和机台信息。
- `services/`
  - 业务处理层。
  - `data_mapper.py` 把解析结果转换成客户表、站位表、位号表、汇总表。
  - `excel_exporter.py` 负责写入 Excel。
  - `license_service.py` 负责机器码、授权校验和授权安装。
  - `feeder_mapping_analyzer.py` 负责飞达映射分析辅助。
- `utils/`
  - 通用辅助函数。
  - 包括导出设置读写、文件扫描、日志初始化等。
- `settings/customer_export.json`
  - 客户导出字段、列头和布局的持久化配置。
- `tools/`
  - 辅助脚本。
  - `build_win10_win11.ps1` / `build_win7.ps1` 用于打包主程序。
  - `generate_license.py` 用于命令行生成授权。
  - `license_generator_gui.py` 是授权生成器窗口实现。
  - `analyze_feeder_mapping.py` 是飞达映射分析脚本。
- `license_generator.py`
  - 授权生成器图形界面入口，不是重复文件。
- `pyinstaller_hooks/`
  - 打包专用 hook。
  - 当前用于覆盖 PyInstaller 的 `tkinter` 预查找逻辑，避免 Tcl/Tk 被错误排除。
- `*.spec`
  - PyInstaller 打包配置。
  - `ISSParserTool_win10_win11.spec` 和 `ISSParserTool_win7.spec` 对应主程序。
  - `LicenseGenerator.spec` 对应授权生成器。

## 运行环境

- 主运行环境：Python 3.11.x，Windows 10 / 11
- Win7 专用构建环境：Python 3.8.x

## 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 启动

```powershell
python main.py
```

## 授权

- 程序启动后会显示当前电脑机器码。
- 未授权前，禁止解析导出。
- 程序优先读取运行目录下的授权文件。
- 支持手动导入授权文件。

授权文件查找路径：

- `ISSParserTool.exe` 同目录下的 `license.json`
- `license\license.json`

生成授权文件示例：

```powershell
python tools\generate_license.py --machine-code 机器码 --customer 客户名称 --expire-at 2027-12-31 --output license.json
```

图形化授权生成器：

```powershell
python license_generator.py
```

说明：

- `--expire-at` 留空表示长期。
- 当前方案是简单离线鉴权，只防普通转发，不防逆向。

## 功能

- 支持选择单个或多个 `.iss` 文件。
- 支持选择文件夹后扫描全部 `.iss`。
- 支持按文件分别导出。
- 支持多文件合并导出。
- 支持导出客户格式主表。
- 支持导出元件、站位、位号、汇总表。
- 支持导出原始解析表和飞达调试表。
- 支持异常不中断批量流程。
- 运行时日志输出到 `logs\app.log`。

## 客户格式主表

- 标题取程序文件名。
- 副标题显示机台信息，例如 `[#1(3010AL)]`。
- 固定字段顺序：
  - `站位`
  - `物料编码`
  - `物料规格`
  - `位号`
  - `包装`
  - `飞达`
  - `用量`
- `位号` 默认按同物料逗号拼接。
- `站位`、`包装`、`飞达` 均通过规则函数生成，可继续按客户规则调整。
- 站位规则当前优先按机台区位生成：
  - 前后机输出 `F-xx` / `R-xx`
  - 四区机输出 `LF-xx` / `RF-xx` / `LR-xx` / `RR-xx`
  - `trayPosition/tray` 类型托盘按前后区输出，例如 `R-78`
  - `multiTrayPosition/multiTray` 类型托盘固定输出 `MTS-xx`，例如 `MTS-1`

## 打包

### Win10 / 11

要求：

- Python 3.11.x
- 已安装 `pyinstaller`

执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_win10_win11.ps1
```

产物：

- `dist\win10_win11\ISSParserTool_v5_win10_win11.exe`

说明：

- 该包只面向 Win10 / 11。
- 当前打包脚本只引用 `ISSParserTool_win10_win11.spec`。
- 该 spec 会显式引用 `pyinstaller_hooks`，保证 `tkinter` 相关资源能被正确打包。

### Win7

要求：

- Python 3.8.x
- 单独虚拟环境
- 已安装 `pyinstaller`

示例：

```powershell
py -3.8 -m venv .venv-win7
.venv-win7\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_win7.ps1
```

如需显式指定解释器：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_win7.ps1 -PythonExe "D:\path\to\.venv-win7\Scripts\python.exe"
```

产物：

- `dist\win7\ISSParserTool_v5_win7.exe`

说明：

- 该包必须在 Python 3.8.x 下构建。
- 当前打包脚本只引用 `ISSParserTool_win7.spec`。
- 是否真实兼容 Win7，必须在 Win7 SP1 实机验证。

### 授权生成器

如需单独打包授权生成器：

```powershell
py -3.11 -m PyInstaller --noconfirm --clean LicenseGenerator.spec
```

## 备注

- 解析器按宽松 XML 规则提取数据，不依赖单一固定模板。
- 若节点缺失，程序使用空值填充并记录日志。
- 若 Excel 被占用，程序记录错误并继续处理其他文件。
- `pyinstaller_hooks` 是当前打包链路必需目录，不应删除。
- 当前已验证可生成 Win10/11 主程序和授权生成器；Win7 包仍需在独立 Python 3.8 环境下构建并在 Win7 SP1 实机验证。
