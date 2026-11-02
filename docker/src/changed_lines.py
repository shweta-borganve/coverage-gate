import re

 feature/add-coverage-report-parser

from src.logger_config import configure_logger

logger = configure_logger(__name__)

main
HUNK_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_changed_lines(diff_text: str) -> dict[str, set[int]]:
    """Return added line numbers grouped by file path."""
 feature/add-coverage-report-parser

    lines = diff_text.splitlines()

    logger.info("Parsing diff to identify changed lines.")
    logger.debug("Diff contains %d lines.", len(lines))

 main
    changed_lines = {}
    current_file = None
    current_line = None

 feature/add-coverage-report-parser
    for line in diff_text.splitlines():

    for line in lines:
 main
        if line.startswith("+++ "):
            file_path = line[4:].strip()

            if file_path == "/dev/null":
                current_file = None
 feature/add-coverage-report-parser

                logger.debug("Skipping deleted-file target: %s.", file_path)
main
            elif file_path.startswith("b/"):
                current_file = file_path[2:]
            else:
                current_file = file_path

            current_line = None
 feature/add-coverage-report-parser


            if current_file is not None:
                logger.debug("Processing diff for file: %s.", current_file)

main
            continue

        if line.startswith("@@ "):
            match = HUNK_PATTERN.match(line)

            if match is None or current_file is None:
 feature/add-coverage-report-parser

                logger.debug("Ignoring invalid or unsupported diff hunk: %s.", line)
 main
                current_line = None
                continue

            current_line = int(match.group(1))
            changed_lines.setdefault(current_file, set())
feature/add-coverage-report-parser


            logger.debug(
                "Started diff hunk for %s at new-file line %d.",
                current_file,
                current_line,
            )
 main
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

feature/add-coverage-report-parser

    total_changed_lines = sum(len(lines) for lines in changed_lines.values())

    logger.info(
        "Diff parsing completed: %d changed lines across %d files.",
        total_changed_lines,
        len(changed_lines),
    )

    logger.debug("Changed-line details: %s", changed_lines)

main
    return changed_lines
