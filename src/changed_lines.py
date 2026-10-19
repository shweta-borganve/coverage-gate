import re

from src.logger_config import configure_logger

logger = configure_logger(__name__)

HUNK_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_changed_lines(diff_text: str) -> dict[str, set[int]]:
    """Return added line numbers grouped by file path."""
    logger.info("Parsing diff to identify changed lines.")
    logger.debug("Diff contains %d lines.", len(diff_text.splitlines()))

    changed_lines = {}
    current_file = None
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            file_path = line[4:].strip()

            if file_path == "/dev/null":
                current_file = None
                logger.debug("Skipping deleted-file target: %s.", file_path)
            elif file_path.startswith("b/"):
                current_file = file_path[2:]
            else:
                current_file = file_path

            current_line = None

            if current_file is not None:
                logger.debug("Processing diff for file: %s.", current_file)

            continue

        if line.startswith("@@ "):
            match = HUNK_PATTERN.match(line)

            if match is None or current_file is None:
                logger.debug("Ignoring invalid or unsupported diff hunk: %s.", line)
                current_line = None
                continue

            current_line = int(match.group(1))
            changed_lines.setdefault(current_file, set())

            logger.debug(
                "Started diff hunk for %s at new-file line %d.",
                current_file,
                current_line,
            )
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

    total_changed_lines = sum(len(lines) for lines in changed_lines.values())

    logger.info(
        "Diff parsing completed: %d changed lines across %d files.",
        total_changed_lines,
        len(changed_lines),
    )

    logger.debug("Changed-line details: %s", changed_lines)

    return changed_lines
