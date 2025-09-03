from pathlib import Path

def test_no_atleat_typo_in_source():
    # Locate the source file directly
    src_file = Path("src/fabio/eigerimage.py")
    assert src_file.exists(), f"Source file not found: {src_file}"
    content = src_file.read_text(encoding="utf-8")
    assert "atleat_2d" not in content, "Typo 'atleat_2d' still present in eigerimage.py"
