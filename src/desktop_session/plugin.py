"""登记桌面分身能力并随插件启停。"""

import platform
import sys
from pathlib import Path

from auto_mas_core import BasePlugin, PluginPrecheckError


class Plugin(BasePlugin):
    requires = ("win_process.desktop_scope",)
    provides_services = {"desktop_session.launcher": "launcher"}

    async def pre_enable(self) -> None:
        if sys.platform != "win32" or platform.machine().upper() != "AMD64":
            raise PluginPrecheckError("桌面分身插件仅支持 Windows x64")

        try:
            from auto_mas_core.host.windows_session import assert_preview_closed
        except ModuleNotFoundError as exc:
            if exc.name != "auto_mas_core.host.windows_session":
                raise
            raise PluginPrecheckError(
                "当前 AUTO-MAS 缺少桌面分身接口，请更新主程序"
            ) from exc

        # 在启用时确认宿主支持所需 SDK，避免打开预览后才报导入错误。
        self._assert_preview_closed = assert_preview_closed

    async def on_enable(self) -> None:
        self.services.require("win_process.desktop_scope")()

    async def pre_disable(self) -> None:
        self._assert_preview_closed()

    async def pre_reload(self) -> None:
        self._assert_preview_closed()

    async def pre_unload(self) -> None:
        self._assert_preview_closed()

    def launcher(self) -> Path:
        return Path(__file__).with_name("bootstrap.py").resolve()
