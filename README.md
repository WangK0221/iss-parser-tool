# ISS 贴片程序解析工具

本项目是本地 Windows 桌面工具，用于解析 SMT `.iss` 程序并导出客户格式 Excel 报表。

## 当前目录结构

```text
ISSParserTool
├─ assets
│  ├─ about_qr.jpg
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
│  ├─ build.ps1
│  ├─ generate_license.py
│  ├─ license_generator_gui.py
│  └─ __init__.py
├─ ui
│  ├─ about_dialog.py
│  ├─ export_settings_dialog.py
│  ├─ main_window.py
│  └─ __init__.py
├─ utils
│  ├─ export_settings.py
│  ├─ file_utils.py
│  ├─ logger.py
│  └─ __init__.py
├─ config.py
├─ ISSParserTool.spec
├─ LicenseGenerator.spec
├─ license_generator.py
├─ main.py
├─ README.md
└─ requirements.txt
```

## 结构说明

- `main.py`
  - 主程序入口。
- `ui/`
  - 界面层。
  - `main_window.py` 是主窗口。
  - `export_settings_dialog.py` 是客户导出配置窗口。
  - `about_dialog.py` 是“关于”窗口。
- `iss_parser_core/`
  - `.iss` 解析层。
  - `iss_parser.py` 负责提取机台、元件、位号、供料器、托盘等信息。
- `services/`
  - 业务处理层。
  - `data_mapper.py` 负责把解析结果转换成客户主表、站位表、位号表、汇总表和飞达调试表。
  - `excel_exporter.py` 负责导出 Excel。
  - `license_service.py` 负责机器码和授权校验。
  - `feeder_mapping_analyzer.py` 负责飞达规则分析辅助。
- `settings/customer_export.json`
  - 客户格式报表字段、列头、布局配置。
- `tools/`
  - 辅助脚本。
  - `build.ps1` 是统一打包脚本，只保留 Win7 兼容构建链路。
  - `analyze_feeder_mapping.py` 用于飞达规则分析。
  - `generate_license.py` 用于命令行生成授权。
  - `license_generator_gui.py` 是授权生成器界面实现。
- `pyinstaller_hooks/`
  - PyInstaller 打包补丁。
  - 当前用于修正 `tkinter` 相关资源探测，不能删除。
- `ISSParserTool.spec`
  - 主程序唯一打包规格。
- `LicenseGenerator.spec`
  - 授权生成器打包规格。

## 运行与构建环境

- 源码运行环境：Python 3.11.x
- 打包环境：Python 3.8.x

说明：

- 只保留一套 Win7 兼容打包链路。
- 实际交付时直接发 Win7 兼容包，统一覆盖 Win7 / Win10 / Win11。
- 是否真实兼容 Win7，仍需 Win7 SP1 实机验证。

## 安装依赖

源码运行：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

打包环境示例：

```powershell
py -3.8 -m venv .venv-py38
.venv-py38\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

## 启动

```powershell
python main.py
```

## 授权

- 程序启动后显示机器码。
- 未授权前禁止导出。
- 程序优先读取运行目录下的 `license.json`。
- 也支持手动导入授权文件。

授权文件查找路径：

- `ISSParserTool.exe` 同目录下的 `license.json`
- `license\license.json`

命令行生成授权：

```powershell
python tools\generate_license.py --machine-code 机器码 --customer 客户名称 --expire-at 2027-12-31 --output license.json
```

图形化授权生成器：

```powershell
python license_generator.py
```

## 功能

- 支持选择单个或多个 `.iss` 文件
- 支持扫描文件夹中的全部 `.iss`
- 支持按文件分别导出
- 支持多文件合并导出
- 支持客户格式主表、元件表、站位表、位号表、汇总表
- 支持原始解析表和飞达调试表
- 支持 tray / multiTray 区分站位规则
- 支持飞达规则映射和调试
- 支持“关于”窗口展示固定二维码和联系方式

## 当前业务规则摘要

- `trayPosition/tray` 类型托盘按前后区输出，例如 `R-78`
- `multiTrayPosition/multiTray` 类型托盘固定输出，例如 `MTS-1`
- 飞达映射当前支持：
  - `package`
  - `reelTypeId`
  - `pitch`
  - `pitchCount`
  - `pitchTotal`
  - `pitchSignature`
  - `feederTypeId`
  - `bankKind`
  - `componentType`
- 程序内部已可派生：
  - `pitchTotal`，例如 `16`
  - `pitchSignature`，例如 `16mm(8*2)`

## 打包

统一使用 `ISSParserTool.spec` 和 `tools\build.ps1`。

执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build.ps1
```

如需显式指定 Python 3.8：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build.ps1 -PythonExe "D:\path\to\python.exe"
```

产物：

- `dist\ISSParserTool.exe`

说明：

- 打包必须使用 Python 3.8.x，目的是保持 Win7 兼容。
- `tools\build.ps1` 会优先尝试 `py -3.8`，找不到时再使用显式传入的 `-PythonExe`。

## 备注

- 解析器按宽松 XML 规则提取信息，不依赖单一模板。
- 缺失节点会以空值处理并写日志。
- `pyinstaller_hooks` 是当前打包链路的必需目录。
- 若只交付源码，可删除 `dist/`、`build/`、运行日志和本地虚拟环境。
