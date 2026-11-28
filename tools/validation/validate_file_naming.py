"""Check the file naming convention for scripted localisation."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared_utils import COUNTRY_TAG_ASSIGNMENT_LINE_RE, strip_comments  # noqa: E402
from validator_common import BaseValidator, run_validator_main  # noqa: E402

SCRIPTED_LOC_DIR = "common/scripted_localisation"
COUNTRY_TAG_DIR = "common/country_tags"
_SCRIPTED_LOC_NAME = re.compile(
    r"(?:(?!99)[0-9]{2}_(?:[A-Za-z0-9_]+_)?|99_(?P<tag>[A-Z0-9]{3})_(?:[A-Za-z0-9_]+_)?)"
    r"scripted_localisation\.txt"
)


class Validator(BaseValidator):
    TITLE = "FILE NAMING VALIDATION"
    STAGED_EXTENSIONS = [".txt"]
    STAGED_INCLUDE_MISSING = True

    def validate_scripted_loc_file_names(self):
        if self.staged_only and not self.staged_touches(
            (SCRIPTED_LOC_DIR, COUNTRY_TAG_DIR)
        ):
            return
        root = Path(self.mod_path)
        tag_files = self._collect_files(
            [f"{COUNTRY_TAG_DIR}/*.txt"], ignore_staged=True
        )
        tags = {
            tag
            for path in tag_files
            for tag in COUNTRY_TAG_ASSIGNMENT_LINE_RE.findall(
                strip_comments(Path(path).read_text(encoding="utf-8-sig"))
            )
        }
        for path in sorted((root / SCRIPTED_LOC_DIR).glob("*.txt")):
            if not path.is_file() or path.name.endswith("_FR_loc.txt"):
                continue
            rel = path.relative_to(root).as_posix()
            match = _SCRIPTED_LOC_NAME.fullmatch(path.name)
            if not match:
                self.add_warning(
                    "scripted-loc-file-name",
                    "Use NN_<system>_scripted_localisation.txt or "
                    "99_<TAG>[_<topic>]_scripted_localisation.txt",
                    rel,
                )
            elif (tag := match["tag"]) and tag not in tags:
                self.add_warning(
                    "scripted-loc-file-tag",
                    f"Country tag '{tag}' is not declared in {COUNTRY_TAG_DIR}/; "
                    "use a shared-system prefix for non-country files",
                    rel,
                )

    def run_validations(self):
        self.validate_scripted_loc_file_names()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate scripted localisation file naming")
