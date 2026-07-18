from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_user_facing_material_avoids_forbidden_product_claims() -> None:
    forbidden = [
        "world" + "-first",
        "ai act " + "compliant",
        "ai act " + "certified",
        "fully " + "autonomous",
        "guaran" + "teed",
        "zero " + "hallucination",
    ]
    paths = [ROOT / "web" / "index.html", ROOT / "web" / "app.js"]
    for optional in ("README.md", "VIDEO_SCRIPT.md", "BUILD_WEEK_SUBMISSION.md"):
        path = ROOT / optional
        if path.exists():
            paths.append(path)
    for path in paths:
        text = path.read_text(encoding="utf-8").casefold()
        for claim in forbidden:
            assert claim not in text, f"forbidden product claim found in {path.name}"


def test_repository_contains_no_obvious_secret_or_private_key_material() -> None:
    excluded = {
        ".git",
        ".venv",
        ".deps",
        ".demo-data",
        ".pytest_cache",
        "__pycache__",
    }
    secret_prefix = "s" + "k-"
    private_marker = "BEGIN " + "PRIVATE KEY"
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.name == "test_repository_hygiene.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert secret_prefix not in text
        assert private_marker not in text


def test_interface_requires_a_manual_human_edit() -> None:
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert "safeEditButton" not in html
    assert "safeEditButton" not in javascript
    assert "suggestedCorrection" not in javascript
    assert 'correction !== original' in javascript
    assert "This demo does not auto-repair the draft." in html
