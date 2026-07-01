import difflib
import os
import re
import sys
from collections import defaultdict

# --- CONFIGURATION ---
LOG_FILE_PATH = "text.log"
LOCALIZATION_DIR = "."
REPLACE_DIR = os.path.join(LOCALIZATION_DIR, "localisation", "english", "replace")

# --- REGEX PATTERNS ---
LOG_PATTERN = re.compile(
    r"key:\s*(?P<key>[\w\.\-]+),\s*file:\s*(?P<file>[^,]+),\s*value:\s*(?P<value>.*)"
)
YML_LINE_PATTERN = re.compile(r"^\s*([\w\.\-]+):\d*\s*\"(.*)\"\s*$")

# --- TERMINAL STYLING (ANSI CODES) ---
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_UNDERLINE = "\033[4m"
CLR_MODDED = "\033[93m"  # Bright Yellow
CLR_VANILLA = "\033[96m"  # Bright Cyan
CLR_DIFF = "\033[92m"  # Bright Green for changes
CLR_TARGET = "\033[95m"  # Magenta for paths


def enable_windows_ansi():
    """Forces Windows CMD/PowerShell to support ANSI escape color codes."""
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        stdout_handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(stdout_handle, mode.value | 0x0004)


def clean_control_characters(text):
    """Replaces ancient ASCII Device Control characters (DC1-DC4) with HoI4's § symbol."""
    # \x11 = DC1, \x12 = DC2, \x13 = DC3, \x14 = DC4
    for dc_char in ["\x11", "\x12", "\x13", "\x14"]:
        text = text.replace(dc_char, "§")
    return text


def parse_log(log_path):
    """Parses text.log and groups duplicates by localization key."""
    duplicates = defaultdict(list)
    if not os.path.exists(log_path):
        print(f"Error: Log file not found at {log_path}")
        return duplicates

    with open(log_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            # Fix any hidden DC characters directly at the source log line
            line = clean_control_characters(line)
            match = LOG_PATTERN.search(line)
            if match:
                data = match.groupdict()
                duplicates[data["key"]].append(
                    {"file": data["file"].strip(), "value": data["value"].strip()}
                )
    return {k: v for k, v in duplicates.items() if len(v) > 1}


def remove_key_from_file(file_path, key_to_remove):
    """Removes a specific localization key from a target YML file."""
    if not os.path.exists(file_path):
        print(f"Warning: File to edit not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    new_lines = []
    removed = False
    for line in lines:
        match = YML_LINE_PATTERN.match(line)
        if match and match.group(1) == key_to_remove:
            removed = True
            continue
        new_lines.append(line)

    if removed:
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.writelines(new_lines)
        return True
    return False


def get_target_replace_info(vanilla_file_name):
    """Determines what the target replace file will be and if it already exists."""
    base_name = os.path.basename(vanilla_file_name).replace("_l_english.yml", "")
    pref_name = f"replaced_from_{base_name}_l_english.yml"
    vanilla_pref_name = f"replaced_from_vanilla_{base_name}_l_english.yml"

    pref_path = os.path.join(REPLACE_DIR, pref_name)
    vanilla_pref_path = os.path.join(REPLACE_DIR, vanilla_pref_name)

    if os.path.exists(pref_path):
        return pref_name, "Appended (File Exists)"
    elif os.path.exists(vanilla_pref_path):
        return vanilla_pref_name, "Appended (File Exists)"
    else:
        return pref_name, "Created (New File)"


def add_key_to_replace_folder(key, value, target_file_name):
    """Writes the key to the approved target file in the replace folder."""
    target_path = os.path.join(REPLACE_DIR, target_file_name)
    os.makedirs(REPLACE_DIR, exist_ok=True)
    file_exists = os.path.exists(target_path)

    # Sanity clean strings before finalizing output file writing
    clean_key = clean_control_characters(key)
    clean_value = clean_control_characters(value)

    # Formatted explicitly to:  key: "value"
    loc_line = f' {clean_key}: "{clean_value}"\n'

    if not file_exists:
        with open(target_path, "w", encoding="utf-8-sig") as f:
            f.write("l_english:\n")
            f.write(loc_line)
    else:
        with open(target_path, "a", encoding="utf-8-sig") as f:
            f.write(loc_line)


def generate_diff_string(str1, str2):
    """Highlights character-level differences using color and underlines."""
    result1, result2 = [], []
    matcher = difflib.SequenceMatcher(None, str1, str2)

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result1.append(str1[i1:i2])
            result2.append(str2[j1:j2])
        elif op == "replace":
            result1.append(
                f"{CLR_UNDERLINE}{CLR_DIFF}{str1[i1:i2]}{CLR_RESET}{CLR_MODDED}"
            )
            result2.append(
                f"{CLR_UNDERLINE}{CLR_DIFF}{str2[j1:j2]}{CLR_RESET}{CLR_VANILLA}"
            )
        elif op == "delete":
            result1.append(
                f"{CLR_UNDERLINE}{CLR_DIFF}{str1[i1:i2]}{CLR_RESET}{CLR_MODDED}"
            )
        elif op == "insert":
            result2.append(
                f"{CLR_UNDERLINE}{CLR_DIFF}{str2[j1:j2]}{CLR_RESET}{CLR_VANILLA}"
            )

    return "".join(result1), "".join(result2)


def main():
    enable_windows_ansi()

    print("Parsing text.log...")
    duplicates = parse_log(LOG_FILE_PATH)

    if not duplicates:
        print("No duplicates found to process. Make sure 'text.log' is in this folder.")
        return

    total_keys = len(duplicates)
    print(f"Found {total_keys} unique duplicate keys. Starting review process...\n")

    processed_count = 0
    approved_count = 0

    for key, entries in duplicates.items():
        processed_count += 1
        md_entry = None
        vanilla_entry = None

        for entry in entries:
            filename = os.path.basename(entry["file"])
            if filename.startswith("MD"):
                md_entry = entry
            else:
                vanilla_entry = entry

        if md_entry and vanilla_entry:
            target_file, status = get_target_replace_info(vanilla_entry["file"])

            highlighted_md, highlighted_vanilla = generate_diff_string(
                md_entry["value"], vanilla_entry["value"]
            )

            # --- INTERACTIVE PROMPT INTERFACE ---
            print("=" * 70)
            print(f"{CLR_BOLD}KEY [{processed_count}/{total_keys}]: {key}{CLR_RESET}")
            print("-" * 70)
            print(f"  * Modded File (Delete From):  {md_entry['file']}")
            print(f"    Value: {CLR_MODDED}{highlighted_md}{CLR_RESET}")
            print(f"  * Vanilla File (Reference):   {vanilla_entry['file']}")
            print(f"    Value: {CLR_VANILLA}{highlighted_vanilla}{CLR_RESET}")
            print(
                f"  * Target Replace File:        {CLR_TARGET}localisation/english/replace/{target_file}{CLR_RESET} ({status})"
            )
            print("-" * 70)

            while True:
                choice = (
                    input("Approve this migration? (y/n) or 'q' to quit: ")
                    .strip()
                    .lower()
                )
                if choice in ["y", "n", "q"]:
                    break
                print(
                    "Invalid input. Please enter 'y' for yes, 'n' for no, or 'q' to quit."
                )

            if choice == "q":
                print("\nExiting script. No further changes made.")
                break
            elif choice == "y":
                md_file_path = os.path.join(LOCALIZATION_DIR, md_entry["file"])
                if remove_key_from_file(md_file_path, key):
                    add_key_to_replace_folder(key, md_entry["value"], target_file)
                    print(f"--> [SUCCESS] Successfully migrated: {key}\n")
                    approved_count += 1
                else:
                    print(
                        "--> [ERROR] Could not find the key in the file to delete it.\n"
                    )
            else:
                print(f"--> [SKIPPED] Skipped key: {key}\n")
        else:
            pass

    print("=" * 70)
    print(
        f"Process complete. Reviewed {processed_count}/{total_keys} keys. Approved & migrated {approved_count}."
    )


if __name__ == "__main__":
    main()
