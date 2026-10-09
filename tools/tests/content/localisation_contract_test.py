"""Contract fixtures for English localisation edits (#5101).

Static checks cannot prove a string renders correctly in game, but they can pin
what a text-only edit must not change and which scope each role resolves to.
Markup fixtures report lost or duplicated keys and changed substitutions, color
codes, icons, escaped quotes, and newlines; an intentional correction passes only
when its exact token change is declared. Scope fixtures pin FROM/PREV roles to
the on_action or event that actually fires the string. Formatting fixtures pin
percentage points against fractions and money against icon tokens. Native
rendering is checked by hand: .claude/docs/loc-smoke-checklist.md.
"""

import re
from collections import Counter
from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import extract_block_from_text, strip_comments
from validate_localisation import _parse_loc_keys_from_text

REPO = Path(__file__).resolve().parents[3]
ENGLISH = REPO / "localisation" / "english"

_LOC_LINE_RE = re.compile(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*$')
_MARKUP_RE = re.compile(r'\$\$|\$[^$\s"]+\$|§.|£[\w.@\-]*|\[[^\[\]]*\]|\\"|\\n')
_COLOR_RE = re.compile(r"§.")


def _loc(filename):
    values = {}
    for line in read_text(ENGLISH / filename).split("\n"):
        match = _LOC_LINE_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _file(*lines):
    return "l_english:\n" + "".join(f" {line}\n" for line in lines)


# ---------------------------------------------------------------------------
# Key and markup contract
# ---------------------------------------------------------------------------


def markup(value):
    return Counter(_MARKUP_RE.findall(value))


def contract_changes(before, after):
    """Key and markup differences between two versions of one English file."""
    before_pairs = _parse_loc_keys_from_text(before)
    after_pairs = _parse_loc_keys_from_text(after)
    before_values, after_values = dict(before_pairs), dict(after_pairs)
    changes = {("lost", key, "") for key in before_values.keys() - after_values}
    changes |= {("added", key, "") for key in after_values.keys() - before_values}
    before_counts = Counter(key for key, _ in before_pairs)
    after_counts = Counter(key for key, _ in after_pairs)
    changes |= {
        ("duplicated", key, "")
        for key, count in after_counts.items()
        if count > 1 and count > before_counts[key]
    }
    for key in before_values.keys() & after_values.keys():
        old, new = markup(before_values[key]), markup(after_values[key])
        changes |= {("-", key, token) for token in old - new}
        changes |= {("+", key, token) for token in new - old}
    return changes


def unexpected_changes(before, after, expected=frozenset()):
    return contract_changes(before, after) - set(expected)


BLR_MILITIA_BEFORE = (
    r'BLR_people_militia_desc: "But the situation is not easy. Many people understand'
    r' this,\" Alexander Lukashenko stressed."'
)
BLR_MILITIA_AFTER = (
    r'BLR_people_militia_desc: "\"But the situation is not easy. Many people'
    r' understand this,\" Alexander Lukashenko stressed."'
)
COM_FEDERALIST_BEFORE = (
    r'COM_change_federalist_constitutionalist_support_effect_tt: "Change the'
    r" §YFederalist Constitution§! Support by §Y[temp_change|Y%0]§!. (Current Support:"
    r' [?COM_federalist_constitutional_support|Y0]%)\n"'
)
COM_FEDERALIST_AFTER = (
    r'COM_change_federalist_constitutionalist_support_effect_tt: "Change the'
    r" §YFederalist Constitution§! Support by §Y[?temp_change|Y0]%§!. (Current Support:"
    r' [?COM_federalist_constitutional_support|Y0]%)\n"'
)
COM_MAYOTTE_BEFORE = (
    r'COM_mayotte_referendum_independence_effect_tt: "Change the §Y[MTE.GetAdjective]§!'
    r" Support by §Y[?temp_change|Y0]%§!. (Current Support:"
    r' §Y[?COM.mayotte_referendum_comoros|Y0]%§!)\n"'
)
COM_MAYOTTE_AFTER = (
    r'COM_mayotte_referendum_independence_effect_tt: "Change the §Y[MTE.GetAdjective]§!'
    r" Support by §Y[?temp_change|Y0]%§!. (Current Support:"
    r' §Y[?COM.mayotte_referendum_independence|Y0]%§!)\n"'
)
FUEL_BUTTON = (
    r'buy_fuel_for_money_button_delayed_tt: "§YPrerequisites:§!\n'
    r"[!buy_fuel_for_money_button_click_enabled]\n§YEffects:§!\n"
    r"[!buy_fuel_for_money_button_click]\n£key_shift + £click_left §YShift L Click§!"
    r' to set up an automatic purchase of §YFuel§!"'
)


def test_text_only_edit_keeps_the_contract():
    before = _file(
        'BLR_people_militia: "People \'s Militia"',
        FUEL_BUTTON.replace("to set up", "To setup"),
    )
    after = _file('BLR_people_militia: "People\'s Militia"', FUEL_BUTTON)
    assert contract_changes(before, after) == set()


@pytest.mark.parametrize(
    "before, after, expected",
    [
        # #5091: the missing opening quote of a cited speech.
        (
            BLR_MILITIA_BEFORE,
            BLR_MILITIA_AFTER,
            {("+", "BLR_people_militia_desc", r"\"")},
        ),
        # #5090: a variable read without `?` and a percentage format on points.
        (
            COM_FEDERALIST_BEFORE,
            COM_FEDERALIST_AFTER,
            {
                (
                    "-",
                    "COM_change_federalist_constitutionalist_support_effect_tt",
                    "[temp_change|Y%0]",
                ),
                (
                    "+",
                    "COM_change_federalist_constitutionalist_support_effect_tt",
                    "[?temp_change|Y0]",
                ),
            },
        ),
        # #5090: the independence tooltip read the Comoros-side variable.
        (
            COM_MAYOTTE_BEFORE,
            COM_MAYOTTE_AFTER,
            {
                (
                    "-",
                    "COM_mayotte_referendum_independence_effect_tt",
                    "[?COM.mayotte_referendum_comoros|Y0]",
                ),
                (
                    "+",
                    "COM_mayotte_referendum_independence_effect_tt",
                    "[?COM.mayotte_referendum_independence|Y0]",
                ),
            },
        ),
    ],
)
def test_intentional_correction_passes_only_when_declared(before, after, expected):
    before, after = _file(before), _file(after)
    assert contract_changes(before, after) == expected
    assert unexpected_changes(before, after, expected) == set()


@pytest.mark.parametrize(
    "mutation, change",
    [
        (lambda v: v.replace("§!", "", 1), ("-", "§!")),
        (lambda v: v.replace(r"\n", " ", 1), ("-", r"\n")),
        (lambda v: v.replace("£key_shift + ", ""), ("-", "£key_shift")),
        (
            lambda v: v.replace("[!buy_fuel_for_money_button_click]", ""),
            ("-", "[!buy_fuel_for_money_button_click]"),
        ),
        (lambda v: v.replace("§YFuel", "§GFuel"), ("+", "§G")),
        (lambda v: v.replace("purchase", r"\"purchase\""), ("+", r"\"")),
    ],
)
def test_accidental_markup_change_is_reported(mutation, change):
    kind, token = change
    found = unexpected_changes(_file(FUEL_BUTTON), _file(mutation(FUEL_BUTTON)))
    assert (kind, "buy_fuel_for_money_button_delayed_tt", token) in found


def test_changed_substitution_is_reported():
    before = _file(r'GER_footer: "Removed by §Y$GER_focus_a$§!."')
    after = _file(r'GER_footer: "Removed by §Y$GER_focus_b$§!."')
    assert contract_changes(before, after) == {
        ("-", "GER_footer", "$GER_focus_a$"),
        ("+", "GER_footer", "$GER_focus_b$"),
    }


def test_lost_and_duplicated_keys_are_reported():
    before = _file('a: "One"', 'b: "Two"', 'c: "Three"')
    after = _file('a: "One"', 'c: "Three"', 'c: "Three again"')
    assert contract_changes(before, after) == {
        ("lost", "b", ""),
        ("duplicated", "c", ""),
    }


# ---------------------------------------------------------------------------
# Scope roles pinned to the consumer that fires the string
# ---------------------------------------------------------------------------


def _block_after(text, pattern):
    match = re.search(pattern, text)
    assert match, pattern
    body, end = extract_block_from_text(text, match.start())
    assert end > 0, pattern
    return body


def _event_block(text, event_id):
    match = re.search(rf"\bid\s*=\s*{re.escape(event_id)}\s", text)
    assert match, event_id
    start = text.rfind("country_event", 0, match.start())
    return _block_after(text[start:], r"country_event\s*=\s*\{")


def role_violations(value, anchors, roles):
    """Anchors whose named scope groups do not resolve to the role's scope."""
    problems = []
    for anchor in anchors:
        match = re.search(anchor, value)
        if not match:
            problems.append(f"anchor not found: {anchor}")
            continue
        for role, scope in match.groupdict().items():
            expected = roles[role.rstrip("0123456789")]
            if scope.upper() != expected:
                problems.append(f"{role} uses {scope}, expected {expected}")
    return problems


ON_ACTIONS = read_text(REPO / "common" / "on_actions" / "00_on_actions.txt")
ACE_EVENTS = strip_comments(read_text(REPO / "events" / "AcePilots.txt"))
ACES = _loc("MD_aces_l_english.yml")

W, F = r"(?P<winner{}>\w+)", r"(?P<fallen{}>\w+)"

# on_action -> (event, scope of the ace that died, scope of the ace that won)
ACE_CONSUMERS = {
    "on_ace_killed_by_ace": ("MD_ace_killed_by_ace.1", "FROM", "PREV"),
    "on_ace_killed_other_ace": ("MD_ace_killed_other_ace.1", "PREV", "FROM"),
}
ACE_ANCHORS = {
    "MD_ace_killed_by_ace.1.t": [
        rf"^\[{F.format(1)}\.GetFullName\] Shot Down By \[{W.format(1)}\.GetCallsign\]$"
    ],
    "MD_ace_killed_by_ace.1.d": [
        rf"led by the infamous \[{W.format(1)}\.GetCallsign\]",
        rf"chasing down \[{F.format(1)}\.GetCallsign\]",
        rf"overwhelmed by \[{W.format(1)}\.GetCallsign\] in \[{W.format(2)}\.GetHerHis\]"
        rf" \[{W.format(3)}\.GetWingShort\]",
        rf"outmaneuvered \[{F.format(1)}\.GetHerHim\]",
        rf"\[{F.format(1)}\.GetName\] \[{F.format(2)}\.GetSurname\]'s"
        rf" \[{F.format(3)}\.GetWingShort\] caught fire",
        rf"celebrating \[{W.format(1)}\.GetFullName\] as a hero",
    ],
    "MD_ace_killed_other_ace.1.t": [
        rf"^\[{W.format(1)}\.GetFullName\] Shot Down \[{F.format(1)}\.GetCallsign\]$"
    ],
    "MD_ace_killed_other_ace.1.d": [
        rf"highlighting \[{W.format(1)}\.GetFullName\]'s heroic deed",
        rf"pilot, \[{F.format(1)}\.GetName\] \[{F.format(2)}\.GetSurname\],"
        rf" known as \[{F.format(3)}\.GetCallsign\]",
        rf"\[{F.format(1)}\.GetFullName\] was a feared pilot",
        rf"on \[{F.format(1)}\.GetHerHis\] conscience",
    ],
}


@pytest.mark.parametrize("on_action", sorted(ACE_CONSUMERS))
def test_ace_event_roles_match_the_on_action_scopes(on_action):
    event_id, fallen, winner = ACE_CONSUMERS[on_action]
    match = re.search(rf"((?:\t#[^\n]*\n)+)\t{on_action}\s*=\s*\{{", ON_ACTIONS)
    assert match, on_action
    documented = " ".join(match.group(1).split())
    assert "FROM = our ace" in documented and "PREV = enemy ace" in documented
    assert event_id in _block_after(ON_ACTIONS, rf"\b{on_action}\s*=\s*\{{")

    event = _event_block(ACE_EVENTS, event_id)
    roles = {"fallen": fallen, "winner": winner}
    for field in ("title", "desc"):
        key = re.search(rf"\b{field}\s*=\s*(\S+)", event).group(1)
        assert role_violations(ACES[key], ACE_ANCHORS[key], roles) == [], key


def test_swapped_ace_roles_are_reported():
    killed = ACES["MD_ace_killed_by_ace.1.d"]
    roles = {"fallen": "FROM", "winner": "PREV"}
    anchors = ACE_ANCHORS["MD_ace_killed_by_ace.1.d"]
    swapped = killed.replace("in [Prev.GetHerHis]", "in [From.GetHerHis]")
    assert role_violations(swapped, anchors, roles) == [
        "winner2 uses From, expected PREV"
    ]
    # Before #5092 the winner's pronoun was a hardcoded "his".
    before = killed.replace("in [Prev.GetHerHis] [Prev", "in his [Prev")
    assert len(role_violations(before, anchors, roles)) == 1


GENERIC_EVENTS = strip_comments(read_text(REPO / "events" / "Generic.txt"))
EVENTS = _loc("events_l_english.yml")

S, R = r"(?P<sender{}>\w+)", r"(?P<recipient{}>\w+)"
# md4.14 reaches the target with FROM = the demanding country; each answer is
# sent back with FROM = the target, so FROM flips sides between the two events.
SUBMISSION_ANCHORS = {
    "md4.14.t": rf"^\[{S.format(1)}\.GetName\] Demands Submission$",
    "md4.14.d": rf"Government of \[{S.format(1)}\.GetName\] have demanded",
    "md4.15.t": rf"^\[{R.format(1)}\.GetName\] Submits$",
    "md4.15.d": rf"Government of \[{R.format(1)}\.GetName\] have agreed",
    "md4.16.t": rf"^\[{R.format(1)}\.GetName\] Resists$",
    "md4.16.d": rf"Government of \[{R.format(1)}\.GetName\] have rejected",
}


def test_submission_answers_are_sent_back_to_the_sender():
    demand = _event_block(GENERIC_EVENTS, "md4.14")
    options = [
        _block_after(demand[match.start() :], r"option\s*=\s*\{")
        for match in re.finditer(r"\boption\s*=\s*\{", demand)
    ]
    assert len(options) == 2
    for option, answer in zip(options, ("md4.15", "md4.16")):
        assert re.search(
            rf"FROM\s*=\s*\{{\s*country_event\s*=\s*\{{\s*id\s*=\s*{answer}\b", option
        )


@pytest.mark.parametrize("key", sorted(SUBMISSION_ANCHORS))
def test_submission_strings_name_the_other_side(key):
    roles = {"sender": "FROM", "recipient": "FROM"}
    assert role_violations(EVENTS[key], [SUBMISSION_ANCHORS[key]], roles) == []


def test_answer_that_names_itself_is_reported():
    anchors = [SUBMISSION_ANCHORS["md4.15.t"]]
    roles = {"recipient": "FROM"}
    assert role_violations("[ROOT.GetName] Submits", anchors, roles) == [
        "recipient1 uses ROOT, expected FROM"
    ]


# ---------------------------------------------------------------------------
# Percentage points, fractions, money, and icons
# ---------------------------------------------------------------------------

_FORMAT_FLAGS_RE = re.compile(r"[0-9.%A-Z]*")


def format_number(value, flags):
    """HOI4 `[?var|flags]`: a digit sets decimals; `%` multiplies by 100 and
    appends %; `%%` appends % without multiplying; letters only pick a color."""
    assert _FORMAT_FLAGS_RE.fullmatch(flags), f"unsupported flags: {flags}"
    digits = re.findall(r"\d", flags)
    decimals = int(digits[0]) if digits else 0
    percent = "%" in flags
    number = value * 100 if percent and "%%" not in flags else value
    return f"{number:.{decimals}f}" + ("%" if percent else "")


def displayed(value_text, variable, value):
    """What the player reads for one variable, including a literal % after it."""
    match = re.search(rf"\[\?{re.escape(variable)}\|([^\]]*)\](%?)", value_text)
    if not match:
        return None
    return format_number(value, match.group(1)) + match.group(2)


COM = _loc("MD_focus_COM_l_english.yml")
POLITICAL = _loc("0_political_system_l_english.yml")

# Points: temp_change is set to 4, 5, 6, -2, or -3 before each Comoros effect,
# and France sets COM.mayotte_referendum_independence to 15.
POINTS = [
    (COM, "COM_change_federalist_constitutionalist_support_effect_tt", "temp_change"),
    (
        COM,
        "COM_change_anti_federalist_constitutionalist_support_effect_tt",
        "temp_change",
    ),
    (COM, "COM_mayotte_referendum_independence_effect_tt", "temp_change"),
    (
        COM,
        "COM_mayotte_referendum_independence_effect_tt",
        "COM.mayotte_referendum_independence",
    ),
]
# Fractions: election_threshold is set to 0.01 to 0.10.
FRACTIONS = [
    (POLITICAL, "party_0_greater_than_election_threshold_tt", "election_threshold"),
]
SCALE = [(0, "0%"), (50, "50%"), (100, "100%")]


@pytest.mark.parametrize("values, key, variable", POINTS)
@pytest.mark.parametrize("points, shown", SCALE)
def test_percentage_points_render_unscaled(values, key, variable, points, shown):
    assert displayed(values[key], variable, points) == shown


@pytest.mark.parametrize("values, key, variable", FRACTIONS)
@pytest.mark.parametrize("points, shown", SCALE)
def test_fractions_render_scaled(values, key, variable, points, shown):
    assert displayed(values[key], variable, points / 100) == shown


def test_wrong_percentage_scale_is_reported():
    # Before #5090: no `?`, so the engine never reads the variable.
    assert displayed(COM_FEDERALIST_BEFORE, "temp_change", 50) is None
    # With `?` but still `%`: points are multiplied by 100 a second time.
    assert displayed("[?temp_change|Y%0]", "temp_change", 50) == "5000%"
    # A fraction shown as points rounds to nothing.
    assert displayed("[?election_threshold|0]%", "election_threshold", 0.5) == "0%"
    assert format_number(0.5, ".2%%") == "0.50%"


def currency_problems(value):
    """`£` always opens an icon name; a literal dollar is written `$$`."""
    problems = [
        f"icon without a name at {m.start()}" for m in re.finditer(r"£(?!\w)", value)
    ]
    rest = re.sub(r"\$\$|\$[A-Za-z0-9_.@|\-]+\$", "", value)
    problems += [f"lone $ at {m.start()}" for m in re.finditer(r"\$", rest)]
    return problems


def test_money_uses_dollars_not_an_icon_token():
    peace = _loc("conditional_peace_deals_l_english.yml")
    assert currency_problems(peace["CPD_reparations_preview_TT"]) == []
    # Before #5092 the amounts opened an icon token instead of printing money.
    before = (
        "Projected transfer for this deal: §Y£[?CPD_rep_preview_temp|.2]B per week§!"
        " (~§Y£[?CPD_rep_preview_total_temp|.0]B§! over the year)"
    )
    assert len(currency_problems(before)) == 2
    assert currency_problems("Costs $5 and $GER_focus$") == ["lone $ at 6"]
    assert currency_problems(_COLOR_RE.sub("", FUEL_BUTTON)) == []
