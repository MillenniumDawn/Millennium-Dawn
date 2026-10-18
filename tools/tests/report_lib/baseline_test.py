"""Tests for `report_lib.baseline`."""

import json
from collections import Counter

import pytest
from report_lib import (
    Severity,
    classify,
    load_baseline,
    load_changed_files,
    load_issues,
    tag_changed_files,
    write_baseline,
)
from report_lib.baseline import (
    META_FILENAME,
    issue_key,
    load_hunks,
    load_renames,
    rename_issues,
    tool_effect,
)
from shared.suite import issue_dict, make_issue, write_text
from shared.suite import write_slug_json as _write_sidecar


def _issue_dict(severity, file="a.txt", line=1, message="m", category="missing_key"):
    return issue_dict(
        severity, file=file, line=line, message=message, category=category
    )


def _write_meta(path, toolshash="h", sidecars=("events.json",)):
    write_text(
        path / META_FILENAME,
        json.dumps(
            {"toolshash": toolshash, "commit_sha": "base", "sidecars": list(sidecars)}
        ),
    )


def _baseline(path, issues=(), toolshash="h"):
    _write_meta(path, toolshash)
    _write_sidecar(path, "events", list(issues))
    baseline = load_baseline(str(path), toolshash)
    assert baseline is not None
    return baseline.issues()


def test_load_baseline_returns_none_without_meta(tmp_path):
    _write_sidecar(tmp_path, "events", [_issue_dict("error")])
    assert load_baseline(str(tmp_path)) is None


def test_load_baseline_returns_none_on_toolshash_mismatch(tmp_path):
    _write_meta(tmp_path, "old-hash")
    assert load_baseline(str(tmp_path), "new-hash") is None


@pytest.mark.parametrize(("expected", "loads"), [("base", True), ("other", False)])
def test_load_baseline_accepts_only_the_pinned_commit(tmp_path, expected, loads):
    # Another main commit's findings would read as the PR's own.
    _write_meta(tmp_path)
    _write_sidecar(tmp_path, "events", [])
    baseline = load_baseline(str(tmp_path), "h", expected)
    assert (baseline is not None) is loads


@pytest.mark.parametrize(
    ("sidecars", "files"),
    [
        pytest.param(None, {}, id="metadata only"),
        pytest.param([], {}, id="empty sidecar list"),
        pytest.param(["events.json"], {}, id="listed sidecar missing"),
        pytest.param(
            ["events.json"],
            {"events.json": "[]", "extra.json": "[]"},
            id="unlisted sidecar",
        ),
        pytest.param(["events.json"], {"events.json": "not json"}, id="unparseable"),
        pytest.param(["events.json"], {"events.json": '{"a": 1}'}, id="not a list"),
        pytest.param(["events.json"], {"events.json": "[null]"}, id="non-dict entry"),
    ],
)
def test_load_baseline_rejects_an_incomplete_baseline(tmp_path, sidecars, files):
    # A partial baseline would read every lost finding as NEW on the PR.
    meta = {"toolshash": "h"}
    if sidecars is not None:
        meta["sidecars"] = sidecars
    write_text(tmp_path / META_FILENAME, json.dumps(meta))
    for name, content in files.items():
        write_text(tmp_path / name, content)

    assert load_baseline(str(tmp_path), "h") is None


@pytest.mark.parametrize(
    ("validators", "severities"),
    [
        pytest.param(None, ["error"], id="all validators"),
        pytest.param({"events"}, ["warning"], id="only what the PR ran"),
        pytest.param({"style"}, [], id="none of them"),
    ],
)
def test_load_baseline_dedupes_the_chosen_validators(tmp_path, validators, severities):
    # Main's dedupe raises a finding to the worst severity any validator gave
    # it, so a PR running only `events` must compare against `events` alone.
    _write_meta(tmp_path, sidecars=("events.json", "localisation.json"))
    _write_sidecar(tmp_path, "events", [_issue_dict("warning")])
    _write_sidecar(tmp_path, "localisation", [_issue_dict("error")])
    baseline = load_baseline(str(tmp_path), "h")
    assert baseline is not None
    assert [i.severity for i in baseline.issues(validators)] == severities
    assert baseline.meta["toolshash"] == "h"


@pytest.mark.parametrize(
    ("overrides", "keyed"),
    [
        pytest.param({}, True, id="located"),
        pytest.param({"file": "", "line": 0}, True, id="no file"),
        pytest.param({"category": ""}, False, id="no category"),
        pytest.param({"message": ""}, False, id="no message"),
    ],
)
def test_issue_key_needs_a_category_and_message(overrides, keyed):
    assert (issue_key(make_issue(**overrides)) is not None) is keyed


def test_classify_matches_a_finding_with_no_file(tmp_path):
    # Decision AI-cost findings name the decision and file in the message.
    message = "ABK_rebuild_the_power_grid Abkhazia.txt - ai_will_do ignores the cost"
    baseline = _baseline(
        tmp_path, [_issue_dict("warning", file="", line=0, message=message)]
    )
    issues = [
        make_issue(severity=Severity.WARNING, file="", line=0, message=message),
        make_issue(severity=Severity.WARNING, file="", line=0, message="added"),
    ]

    classify(issues, baseline)

    assert [i.baseline_status for i in issues] == ["existing", "new"]


@pytest.mark.parametrize(
    ("file", "message", "moved"),
    [
        pytest.param(
            "events/old.txt", "m", ("events/new.txt", "m"), id="finding in the file"
        ),
        pytest.param(
            "a.txt",
            "read at events/old.txt:#",
            ("a.txt", "read at events/new.txt:#"),
            id="path in the message",
        ),
        pytest.param("old.txt", "m", ("old.txt", "m"), id="basename only"),
        pytest.param("events/x.txt", "m", ("events/x.txt", "m"), id="unrelated"),
    ],
)
def test_rename_issues_moves_findings_to_the_new_path(tmp_path, file, message, moved):
    renames = tmp_path / "renames.txt"
    renames.write_text("events/old.txt\nevents/new.txt\n", encoding="utf-8")
    issue = make_issue(file=file, message=message)

    rename_issues([issue], load_renames(str(renames)))

    assert (issue.file, issue.message) == moved


def test_tool_effect_counts_what_the_pr_validators_change():
    main = Counter(
        {
            ("warning", "a", "f", "kept"): 1,
            ("warning", "a", "f", "old wording"): 1,
            ("warning", "b", "f", "dropped"): 2,
        }
    )
    pr = Counter(
        {
            ("warning", "a", "f", "kept"): 1,
            ("warning", "a", "f", "new wording"): 1,
            ("warning", "c", "f", "added"): 1,
        }
    )

    assert tool_effect(pr, main) == {"a": (1, 1), "b": (0, 2), "c": (1, 0)}


def test_classify_tags_new_and_existing(tmp_path):
    baseline = _baseline(
        tmp_path,
        [
            _issue_dict("error", file="old.txt", line=1, message="old finding"),
            _issue_dict("warning", file="warn.txt", line=3, message="known warning"),
        ],
    )

    issues = [
        make_issue(file="old.txt", line=1, message="old finding"),
        make_issue(file="new.txt", line=1, message="new finding"),
        make_issue(
            severity=Severity.WARNING,
            file="new.txt",
            line=2,
            message="new warning",
        ),
        make_issue(
            severity=Severity.WARNING,
            file="warn.txt",
            line=3,
            message="known warning",
        ),
    ]
    stats = classify(issues, baseline)

    assert [i.baseline_status for i in issues] == [
        "existing",
        "new",
        "new",
        "existing",
    ]
    assert stats.new_errors == 1
    assert stats.new_warnings == 1
    assert stats.existing_errors == 1
    assert stats.existing_warnings == 1
    assert stats.unclassified == 0
    assert stats.new_issues == issues[1:3]


@pytest.mark.parametrize(
    ("on_main", "on_pr", "status"),
    [
        pytest.param("warning", Severity.ERROR, "raised", id="raised"),
        pytest.param("error", Severity.WARNING, "lowered", id="lowered"),
    ],
)
def test_classify_reports_severity_changes(tmp_path, on_main, on_pr, status):
    baseline = _baseline(
        tmp_path, [_issue_dict(on_main, file="a.txt", line=1, message="same")]
    )
    issue = make_issue(severity=on_pr, file="a.txt", line=1, message="same")

    stats = classify([issue], baseline)

    assert issue.baseline_status == status
    assert getattr(stats, status) == [issue]
    assert (stats.new_errors, stats.new_warnings) == (0, 0)


@pytest.mark.parametrize("warning_first", [True, False])
def test_classify_exact_error_match_wins_over_a_lowered_warning(
    tmp_path, warning_first
):
    baseline = _baseline(
        tmp_path, [_issue_dict("error", file="a.txt", line=1, message="same")]
    )
    error = make_issue(file="a.txt", line=1, message="same")
    warning = make_issue(
        severity=Severity.WARNING, file="a.txt", line=2, message="same"
    )
    issues = [warning, error] if warning_first else [error, warning]

    stats = classify(issues, baseline)

    assert (error.baseline_status, warning.baseline_status) == ("existing", "new")
    assert (stats.new_errors, stats.new_warnings) == (0, 1)


def test_classify_line_shift_reads_existing(tmp_path):
    # An unrelated edit six lines up moves the anchor line and the read-site
    # lines inside the message; the finding still exists on main.
    def message(focus_line, event_line):
        return (
            "flag_x - set only by focus AST_x; replace 2 read(s) with "
            "`has_completed_focus = AST_x`: "
            f"common/national_focus/05_Australia.txt:{focus_line}, "
            f"events/05_australia_events.txt:{event_line}"
        )

    focus_file = "common/national_focus/05_Australia.txt"
    baseline = _baseline(
        tmp_path,
        [
            _issue_dict(
                "warning",
                file=focus_file,
                line=3112,
                message=message(1889, 8071),
                category="redundant-focus-flag",
            )
        ],
    )

    shifted = make_issue(
        severity=Severity.WARNING,
        file=focus_file,
        line=3106,
        message=message(1883, 8032),
        category="redundant-focus-flag",
    )
    stats = classify([shifted], baseline)

    assert shifted.baseline_status == "existing"
    assert stats.new_warnings == 0
    assert stats.existing_warnings == 1


def test_classify_masks_line_word_references(tmp_path):
    baseline = _baseline(
        tmp_path,
        [_issue_dict("error", line=10, message="X redefined (first at line 4)")],
    )

    moved = make_issue(file="a.txt", line=8, message="X redefined (first at line 2)")
    classify([moved], baseline)
    assert moved.baseline_status == "existing"


def test_classify_extra_instance_of_existing_finding_is_new(tmp_path):
    baseline = _baseline(
        tmp_path,
        [_issue_dict("error", file="a.txt", line=5, message="dup")],
    )

    issues = [
        make_issue(file="a.txt", line=5, message="dup"),
        make_issue(file="a.txt", line=40, message="dup"),
    ]
    stats = classify(issues, baseline)

    assert [i.baseline_status for i in issues] == ["existing", "new"]
    assert stats.existing_errors == 1
    assert stats.new_errors == 1


# The PR replaced line 10 of events/a.txt with lines 10-12, so lines below
# moved down by two.
_HUNKS = {"events/a.txt": [(10, 1, 10, 3)]}


@pytest.mark.parametrize(
    ("file", "main_lines", "pr_lines", "statuses"),
    [
        pytest.param("events/a.txt", [5], [5], ["existing"], id="above the edit"),
        pytest.param("events/a.txt", [20], [22], ["existing"], id="shifted below"),
        pytest.param("events/a.txt", [20], [20], ["new"], id="not where main's moved"),
        pytest.param("events/a.txt", [10], [11], ["existing"], id="same changed hunk"),
        pytest.param(
            "events/a.txt",
            [5, 30],
            [5, 11],
            ["existing", "new"],
            id="fixed one copy, added another",
        ),
        pytest.param("events/a.txt", [0], [0], ["existing"], id="no line"),
        pytest.param("a.txt", [20], [22], ["existing"], id="basename by count"),
    ],
)
def test_classify_places_findings_through_the_diff(
    tmp_path, file, main_lines, pr_lines, statuses
):
    baseline = _baseline(
        tmp_path,
        [
            _issue_dict("error", file=file, line=line, message="dup")
            for line in main_lines
        ],
    )
    issues = [make_issue(file=file, line=line, message="dup") for line in pr_lines]

    classify(issues, baseline, _HUNKS)

    assert [i.baseline_status for i in issues] == statuses


def test_load_hunks_reads_only_header_lines(tmp_path):
    hunks = tmp_path / "hunks.txt"
    hunks.write_text(
        "diff --git a/events/a b.txt b/events/a b.txt\n"
        "+++ b/events/a b.txt\t\n"
        "@@ -3 +3,2 @@ ctx\n"
        "+++ an added line, not a header\n"
        "@@ -9,0 +11 @@\n"
        "diff --git a/events/gone.txt b/events/gone.txt\n"
        "+++ /dev/null\n"
        "@@ -1,4 +0,0 @@\n",
        encoding="utf-8",
    )

    assert load_hunks(str(hunks)) == {"events/a b.txt": [(3, 1, 3, 2), (9, 0, 11, 1)]}


def test_classify_leaves_unkeyable_issues_untagged(tmp_path):
    baseline = _baseline(tmp_path)

    unkeyable = make_issue(category="", message="no category")
    stats = classify([unkeyable], baseline)

    assert unkeyable.baseline_status is None
    assert stats.unclassified == 1


def test_load_issues_names_the_malformed_sidecar(tmp_path):
    (tmp_path / "events.json").write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="events.json"):
        load_issues(str(tmp_path))


def test_from_dict_coerces_non_numeric_line_to_zero(tmp_path):
    from report_lib import Issue

    issue = Issue.from_dict(
        {
            "severity": "error",
            "category": "c",
            "message": "m",
            "file": "f.txt",
            "line": "abc",
        }
    )
    assert issue.line == 0
    assert issue.has_location is False


def test_load_baseline_returns_none_when_meta_not_a_dict(tmp_path):
    (tmp_path / META_FILENAME).write_text("[1, 2, 3]", encoding="utf-8")
    assert load_baseline(str(tmp_path), "h") is None


def test_load_baseline_returns_none_on_unreadable_meta(tmp_path):
    (tmp_path / META_FILENAME).write_text("{broken", encoding="utf-8")
    assert load_baseline(str(tmp_path), "h") is None


def test_classify_with_empty_baseline_marks_everything_new(tmp_path):
    # An all-clean main run stores empty sidecars: any PR finding is new by
    # definition.
    stats = classify(
        [
            make_issue(file="a.txt", line=1, message="first"),
            make_issue(
                severity=Severity.WARNING,
                file="b.txt",
                line=2,
                message="second",
            ),
        ],
        _baseline(tmp_path),
    )

    assert stats.new_errors == 1
    assert stats.new_warnings == 1
    assert stats.existing_errors == 0
    assert stats.unclassified == 0


def test_classify_counts_mixed_unclassified_and_new(tmp_path):
    stats = classify(
        [
            make_issue(file="a.txt", line=1, message="keyed"),
            make_issue(category="", message="no category"),
        ],
        _baseline(tmp_path),
    )

    assert stats.new_errors == 1
    assert stats.unclassified == 1
    assert len(stats.new_issues) == 1


def test_write_baseline_copies_sidecars_writes_meta_and_prunes(tmp_path):
    current = tmp_path / "current"
    current.mkdir()
    _write_sidecar(current, "events", [_issue_dict("error")])

    output = tmp_path / "baseline"
    output.mkdir()
    # A stale sidecar from a validator that no longer runs.
    _write_sidecar(output, "removed-validator", [_issue_dict("error")])

    write_baseline(str(current), str(output), {"toolshash": "h"})

    assert (output / "events.json").is_file()
    assert not (output / "removed-validator.json").exists()
    meta = json.loads((output / META_FILENAME).read_text(encoding="utf-8"))
    assert meta["toolshash"] == "h"
    assert meta["sidecars"] == ["events.json"]


def test_a_clean_run_round_trips_as_an_empty_baseline(tmp_path):
    # A clean validator writes an empty sidecar. That complete empty result
    # loads as the empty findings set, unlike a run with no output.
    current = tmp_path / "current"
    _write_sidecar(current, "events", [])
    output = tmp_path / "baseline"

    write_baseline(str(current), str(output), {"toolshash": "h"})

    baseline = load_baseline(str(output), "h")
    assert baseline is not None
    assert baseline.issues() == []


def test_build_report_annotates_new_vs_existing(tmp_path):
    # End-to-end wiring: the report generator classifies against a restored
    # baseline and both bodies carry the NEW/EXISTING signal.
    import generate_validation_report
    from report_lib import ReportContext

    results = tmp_path / "validation-results" / "validation-events-results"
    results.mkdir(parents=True)
    (results / "validation-events.log").write_text(
        "VALIDATION COMPLETE", encoding="utf-8"
    )
    (results / "validation-events.json").write_text(
        json.dumps(
            [
                _issue_dict("error", file="old.txt", message="old finding"),
                _issue_dict("error", file="new.txt", message="new finding"),
            ]
        ),
        encoding="utf-8",
    )

    _baseline(
        tmp_path / "baseline",
        [_issue_dict("error", file="old.txt", message="old finding")],
    )
    baseline = load_baseline(str(tmp_path / "baseline"), "h")

    ctx = ReportContext(
        pr_number="42",
        commit_sha="abc1234deadbeef",  # pragma: allowlist secret
        repo="MillenniumDawn/Millennium-Dawn",
    )
    body, step_body, _runs, deduped, _trunc, stats = (
        generate_validation_report.build_report(
            str(tmp_path / "validation-results"), ctx, baseline
        )
    )

    assert stats is not None
    assert stats.new_errors == 1
    assert stats.existing_errors == 1
    assert "1 new error against the main baseline" in body
    assert "## New Findings Introduced by this branch." in body
    assert "## New Findings Introduced by this branch." in step_body
    assert len(deduped) == 2


def test_tag_changed_files_sets_in_diff():
    issues = [
        make_issue(file="events/MD_x.txt"),
        make_issue(file="events/other.txt"),
        make_issue(file=""),
    ]
    tag_changed_files(issues, {"events/MD_x.txt"})
    assert issues[0].in_diff is True
    assert issues[1].in_diff is False
    assert issues[2].in_diff is False


def test_tag_changed_files_normalises_slashes():
    issue = make_issue(file="events\\MD_x.txt")
    tag_changed_files([issue], {"events/MD_x.txt"})
    assert issue.in_diff is True


def test_load_changed_files_skips_blank_lines(tmp_path):
    path = tmp_path / "changed-files.txt"
    path.write_text("a.txt\n\nb.txt\n", encoding="utf-8")
    assert load_changed_files(str(path)) == {"a.txt", "b.txt"}


def test_load_changed_files_missing_path_is_empty(tmp_path):
    assert load_changed_files(str(tmp_path / "missing.txt")) == set()


def test_classify_then_tag_marks_both_axes(tmp_path):
    baseline = _baseline(
        tmp_path,
        [_issue_dict("error", file="old.txt", line=1, message="old finding")],
    )
    issues = [
        make_issue(file="old.txt", line=1, message="old finding"),
        make_issue(file="new.txt", line=1, message="new finding"),
    ]
    classify(issues, baseline)
    tag_changed_files(issues, {"new.txt"})
    assert issues[0].baseline_status == "existing"
    assert issues[0].in_diff is False
    assert issues[1].baseline_status == "new"
    assert issues[1].in_diff is True
