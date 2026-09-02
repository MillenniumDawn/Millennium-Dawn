import importlib.util
import sys

import pytest


def _module():
    from shared.paths import GENERATORS_DIR

    path = GENERATORS_DIR / "generate_tribute_ideas.py"
    spec = importlib.util.spec_from_file_location("generate_tribute_ideas", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generation_does_not_touch_caller_owned_temp_names(tmp_path, monkeypatch):
    module = _module()
    repo = tmp_path / "repo"
    tag_dir = repo / "common" / "country_tags"
    ideas = repo / "common" / "ideas"
    loc = repo / "localisation" / "english"
    tag_dir.mkdir(parents=True)
    ideas.mkdir(parents=True)
    loc.mkdir(parents=True)
    (tag_dir / "00_countries.txt").write_text('USA = "x"\n', encoding="utf-8")
    (tag_dir / "zz_dynamic_countries.txt").write_text('D01 = "x"\n', encoding="utf-8")
    caller_file = tmp_path / "tribute_ideas.txt"
    caller_file.write_text("caller owned", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "REPO_ROOT", str(repo))
    monkeypatch.setattr(module, "TAG_DIR", str(tag_dir))

    module.main()

    assert caller_file.read_text(encoding="utf-8") == "caller owned"
    assert (ideas / "tribute_ideas.txt").is_file()
    generated_loc = loc / "MD_tribute_ideas_l_english.yml"
    assert generated_loc.read_bytes().startswith(b"\xef\xbb\xbf")


def test_missing_required_path_exits(tmp_path, monkeypatch):
    module = _module()
    monkeypatch.setattr(module, "REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(module, "TAG_DIR", str(tmp_path / "missing_tags"))
    with pytest.raises(SystemExit, match="required path not found"):
        module.main()


def test_tools_dir_is_put_on_sys_path(monkeypatch):
    monkeypatch.setattr(
        sys, "path", [entry for entry in sys.path if not entry.endswith("tools")]
    )
    module = _module()
    assert module.TOOLS_DIR in sys.path
