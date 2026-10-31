import re

HUNK_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_changed_lines(diff_text: str) -> dict[str, set[int]]:
    """Return added line numbers grouped by file path."""
    changed_lines = {}
    current_file = None
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            file_path = line[4:].strip()

            if file_path == "/dev/null":
                current_file = None
            elif file_path.startswith("b/"):
                current_file = file_path[2:]
            else:
                current_file = file_path

            current_line = None
            continue

        if line.startswith("@@ "):
            match = HUNK_PATTERN.match(line)

            if match is None or current_file is None:
                current_line = None
                continue

            current_line = int(match.group(1))
            changed_lines.setdefault(current_file, set())
            continue

        if current_line is None:
            continue

        if line.startswith("+"):
            changed_lines[current_file].add(current_line)
            current_line += 1
        elif line.startswith(("-", "\\")):
            continue
        else:
            current_line += 1

    return changed_lines
