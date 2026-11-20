"""从独立的源码目录或已安装的发行包启动 Windows 子进程。"""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def main() -> None:
    source = Path(sys.argv[1]).resolve(strict=True)
    action = sys.argv[2]
    # 使用 -I 排除当前目录和用户 PYTHONPATH，显式加载本次运行的宿主与插件。
    sys.path[:0] = [
        str(source),
        str(source / "plugins" / "auto_mas_core" / "src"),
    ]
    # 提权助手只加载本插件，发行包所在目录可能还安装了其他插件。
    package_dir = Path(__file__).resolve().parent
    spec = spec_from_file_location("desktop_session", package_dir / "__init__.py")
    if spec is None or spec.loader is None:
        raise ImportError("cannot load desktop session package")
    package = module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    if action == "preview":
        from desktop_session.host import main as preview

        preview(Path(sys.argv[3]).resolve(strict=True), source)
    elif action == "repair":
        from desktop_session.repair import main as repair

        sys.exit(repair(*sys.argv[3:]))
    else:
        raise ValueError("unknown desktop session action")


if __name__ == "__main__":
    main()
