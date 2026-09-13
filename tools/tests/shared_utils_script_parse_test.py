"""Unit tests for the shared script walkers in shared_utils."""

from shared_utils import (
    iter_focus_blocks,
    iter_statement_ops,
    iter_statements,
    line_of,
    read_script,
)


def _focus(body):
    return "\tfocus = {\n" + body + "\n\t}\n"


class TestStatements:
    def test_scalar_block_and_quoted_values(self):
        body = 'name = "DEN_AI" option = { name = HISTORICAL } flag = X'
        assert list(iter_statements(body)) == [
            ("name", "DEN_AI", None),
            ("option", None, " name = HISTORICAL "),
            ("flag", "X", None),
        ]

    def test_nested_blocks_are_not_yielded_twice(self):
        keys = [key for key, _, _ in iter_statements("a = { b = { c = 1 } } d = 2")]
        assert keys == ["a", "d"]

    def test_operators_are_reported_separately(self):
        body = "has_stability > 0.66 threat < 0.4 date >= 2005.1.1"
        assert list(iter_statement_ops(body)) == [
            ("has_stability", ">", "0.66", None),
            ("threat", "<", "0.4", None),
            ("date", ">=", "2005.1.1", None),
        ]

    def test_two_character_operator_keeps_its_value(self):
        # `>=` used to split into `>` plus a stray `=` scalar, losing the value.
        assert list(iter_statements("x >= 5")) == [("x", "5", None)]

    def test_at_sign_belongs_to_the_key(self):
        assert list(iter_statements("trade_agreement@GER = yes")) == [
            ("trade_agreement@GER", "yes", None)
        ]

    def test_unbalanced_block_stops_the_walk(self):
        assert list(iter_statements("a = { b = 1 c = 2")) == []


class TestFocusBlocks:
    def test_reads_id_kind_and_line(self):
        text = "\n" + _focus("\t\tid = a\n\t\tx = 1")
        assert list(iter_focus_blocks(text)) == [
            ("a", "focus", 2, "\n\t\tid = a\n\t\tx = 1\n\t")
        ]

    def test_shared_and_joint_focus_are_recognised(self):
        text = (
            "shared_focus = {\n\tid = s\n}\n"
            "joint_focus = {\n\tid = j\n}\n"
            "focus = {\n\tid = f\n}\n"
        )
        assert [(i, k) for i, k, _, _ in iter_focus_blocks(text)] == [
            ("s", "shared_focus"),
            ("j", "joint_focus"),
            ("f", "focus"),
        ]

    def test_block_without_an_id_is_skipped(self):
        text = _focus("\t\tx = 1") + _focus("\t\tid = b")
        assert [i for i, _, _, _ in iter_focus_blocks(text)] == ["b"]

    def test_nested_focus_keyword_is_not_a_block(self):
        text = _focus("\t\tid = a\n\t\tprerequisite = { focus = b }")
        assert [i for i, _, _, _ in iter_focus_blocks(text)] == ["a"]

    def test_unclosed_block_ends_the_scan(self):
        assert list(iter_focus_blocks("focus = {\n\tid = a\n")) == []


def test_line_of_counts_from_one():
    text = "a\nb\nc"
    assert line_of(text, 0) == 1
    assert line_of(text, text.index("c")) == 3


class TestReadScript:
    def test_comments_and_quotes_are_blanked_in_place(self, tmp_path):
        path = tmp_path / "f.txt"
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write('a = 1 # note\nlog = "x = { }"\n')
        text = read_script(str(path))
        assert list(iter_statements(text)) == [
            ("a", "1", None),
            ("log", " " * len("x = { }"), None),
        ]

    def test_keep_quotes_preserves_the_value(self, tmp_path):
        path = tmp_path / "f.txt"
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write('name = "GER_idea"\n')
        assert list(iter_statements(read_script(str(path), keep_quotes=True))) == [
            ("name", "GER_idea", None)
        ]

    def test_bom_is_stripped(self, tmp_path):
        path = tmp_path / "f.txt"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            handle.write("a = 1\n")
        assert list(iter_statements(read_script(str(path)))) == [("a", "1", None)]
