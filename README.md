<!-- auto-mas:i18n
{
  "display_name_i18n": {"zh_CN": "桌面分身", "en": "Desktop Session", "ja": "デスクトップセッション"},
  "description_i18n": {
    "zh_CN": "在独立的 Windows 桌面中预览和运行 AUTO-MAS 任务。",
    "en": "Preview and run AUTO-MAS tasks in a separate Windows desktop session.",
    "ja": "独立した Windows デスクトップで AUTO-MAS タスクをプレビューして実行します。"
  },
  "tags_i18n": {"zh_CN": ["桌面工具"], "en": ["Desktop"], "ja": ["デスクトップ"]}
}
-->

# AUTO-MAS 桌面分身

在 Windows x64 的 AUTO-MAS 桌面客户端中启用后，从「设置 → 桌面分身」打开预览并选择任务。
保留原有 Windows 凭据和已选任务，使用同一数据目录时无需重新配置。

## 本地联调

将本仓库放入配套 AUTO-MAS 主程序源码的 `plugins/desktop_session`，配套适配源码放在
`plugins/win_process_adapter`，然后启动 Electron 和本地后端。在「插件中心 → 已安装」
启用「桌面分身」时，宿主会先启用通用 Windows 进程适配。

发行版联调时，用 `uv build --wheel` 构建两个配套 wheel，在后端停止期间将两个源码目录移出
扫描目录，再用 `uv pip install --target <用户根目录>/plugins/pypi/site-packages --no-deps <适配 wheel> <分身 wheel>`
安装。发布前可通过 `UV_EXTRA_INDEX_URL` 向后端提供包含两个 wheel 的本地 Simple
索引，供启动时联合解析依赖。使用本地 HTTP 索引且启用了代理时，将索引主机加入
`NO_PROXY`。启动后端后在插件中心启用。正式发行版由插件市场安装。

发行包要求 AUTO-MAS SDK 5.9.0b2 或更新的 5.x 版本。首发前须确认配套 SDK 已发行且包含
`auto_mas_core.host.windows_session`，并用该版本验证安装与启用。联合调试可继续使用包含该接口的宿主源码。

## 回归测试

使用主程序的 Python 开发环境，将本仓库 `src`、主程序根目录及其
`plugins/auto_mas_core/src` 加入 `PYTHONPATH`，从主程序根目录运行以下命令。

```powershell
uv run --no-sync python -m pytest plugins/desktop_session/tests -q
```
