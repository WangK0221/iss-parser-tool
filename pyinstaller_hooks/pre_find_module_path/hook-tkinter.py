from __future__ import annotations


def pre_find_module_path(hook_api):
    """
    覆盖 PyInstaller 内置的 tkinter 预查找 hook。

    当前机器上内置 hook 会因为 Tcl/Tk 探测失败而直接把 search_dirs 清空，
    导致 tkinter 模块在分析阶段被排除。这里保持默认搜索路径，不做排除。
    """
    return
