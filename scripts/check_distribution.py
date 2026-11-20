"""校验 wheel 的插件市场元数据与本次发布版本。"""

import json
import os
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile


def main() -> None:
    (wheel,) = Path("dist").glob("*.whl")
    with ZipFile(wheel) as archive:
        (path,) = (
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = BytesParser(policy=policy.default).parsebytes(archive.read(path))

    keywords = {item.strip() for item in metadata["Keywords"].split(",")}
    if keywords != {"auto-mas-plugin", "auto-mas-id:desktop_session"}:
        raise SystemExit("wheel 缺少正确的插件市场关键词")
    urls = dict(value.split(",", 1) for value in metadata.get_all("Project-URL", []))
    for label in ("Repository", "Documentation", "Changelog"):
        url = urlsplit(urls.get(label, "").strip())
        if url.scheme != "https" or not url.netloc:
            raise SystemExit(f"{label} 必须是 HTTPS 链接")
    description = metadata.get_payload(decode=True).decode("utf-8")
    match = re.match(r"\s*<!--\s*auto-mas:i18n\s+(.*?)\s*-->", description, re.S)
    if match is None:
        raise SystemExit("wheel 缺少插件市场多语言声明")
    display = json.loads(match[1])
    for locale in ("zh_CN", "en", "ja"):
        for field in ("display_name_i18n", "description_i18n"):
            value = display[field].get(locale)
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(f"{field} 缺少 {locale} 文案")
        tags = display["tags_i18n"].get(locale)
        if (
            not isinstance(tags, list)
            or not tags
            or not all(isinstance(tag, str) and tag.strip() for tag in tags)
        ):
            raise SystemExit(f"tags_i18n 缺少 {locale} 标签")

    version = metadata["Version"]
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.M
    ):
        raise SystemExit(f"CHANGELOG.md 缺少 {version} 版本段")
    if (
        os.getenv("GITHUB_REF_TYPE") == "tag"
        and os.getenv("GITHUB_REF_NAME") != f"v{version}"
    ):
        raise SystemExit(f"发布标签必须为 v{version}")


if __name__ == "__main__":
    main()
