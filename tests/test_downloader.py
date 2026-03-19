from retrohub.models import DownloadAsset
from retrohub.services.downloader import DownloadError, DownloadService


def test_pick_asset_prefers_zip() -> None:
    assets = [
        DownloadAsset(url="https://example.com/a.iso", filename="a.iso", format_hint="iso"),
        DownloadAsset(url="https://example.com/b.zip", filename="b.zip", format_hint="zip"),
    ]
    picked = DownloadService._pick_asset(assets)
    assert picked.filename == "b.zip"


def test_validate_member_path_blocks_parent_traversal() -> None:
    try:
        DownloadService._validate_member_path("../evil.exe")
    except DownloadError:
        return
    raise AssertionError("Traversal path should raise DownloadError")
