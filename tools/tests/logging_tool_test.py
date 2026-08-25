"""Failure handling tests for the logging tool."""

import logging_tool


def test_idea_add_fails_when_output_cannot_be_written(tmp_path, monkeypatch):
    ideas = tmp_path / "common" / "ideas"
    ideas.mkdir(parents=True)
    source = ideas / "ideas.txt"
    source.write_text(
        "ideas = {\n\tidea_one = {\n\t\tname = idea_one\n\t}\n}\n" + "# filler\n" * 20,
        encoding="utf-8",
    )
    real_open = open

    def fail_write(path, mode="r", *args, **kwargs):
        if "w" in mode:
            raise OSError("read-only")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(logging_tool, "open", fail_write, raising=False)

    try:
        logging_tool.idea_add(str(tmp_path))
    except OSError as error:
        assert "read-only" in str(error)
    else:
        assert False, "idea_add should fail when the output cannot be written"
