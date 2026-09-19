"""Guard against the deprecated Buffer() constructor (Node DEP0005, #3947).

The deprecation warning in CI's artifact step comes from upstream action
bundles, not mod code: docs/src only uses Buffer as a type and consumes
fs.readFileSync results via Buffer.from-safe methods. This pins that no
constructor call (new Buffer( / Buffer() as a function) creeps back in.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_ROOTS = (REPO_ROOT / "docs" / "src", REPO_ROOT / "docs" / "scripts")
_EXTENSIONS = {".ts", ".mts", ".js", ".mjs", ".cjs"}
_DEPRECATED_CALL = re.compile(r"(?<![\w$.])Buffer\s*\(")


def _code_line(line: str) -> str:
    return line.split("//", 1)[0]


def _has_deprecated_call(line: str) -> bool:
    return _DEPRECATED_CALL.search(_code_line(line)) is not None


def test_no_deprecated_buffer_constructor_in_docs_source():
    offenders = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*")):
            if path.suffix not in _EXTENSIONS or not path.is_file():
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if _has_deprecated_call(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}")
    assert (
        not offenders
    ), "deprecated Buffer() constructor calls (DEP0005): " + ", ".join(offenders)


def test_detector_spots_calls_but_not_types_or_methods():
    assert _has_deprecated_call("const b = new Buffer(4);")
    assert _has_deprecated_call("const b = Buffer('x');")
    assert not _has_deprecated_call(
        "function toArrayBuffer(buffer: Buffer): ArrayBuffer {"
    )
    assert not _has_deprecated_call("const data = toArrayBuffer(buf);")
    assert not _has_deprecated_call("return buf.toString('base64');")
    assert not _has_deprecated_call("const b = Buffer.from('x');")
    assert not _has_deprecated_call("const b = Buffer.alloc(4);")
