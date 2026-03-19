from pathlib import Path

from retrohub.providers.exodos_manifest import ExoDOSManifestProvider


def test_manifest_search(tmp_path: Path) -> None:
    manifest = tmp_path / "exodos.xml"
    manifest.write_text(
        "<LaunchBox><Game><Title>Doom</Title><Genre>Action</Genre><Notes>Classic DOS shooter</Notes></Game></LaunchBox>",
        encoding="utf-8",
    )
    provider = ExoDOSManifestProvider(manifest)
    result = provider.search("doom")
    assert len(result.results) == 1
    assert result.results[0].title == "Doom"
