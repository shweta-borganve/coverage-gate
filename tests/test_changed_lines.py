from src.changed_lines import parse_changed_lines


def test_parse_added_line_numbers():
    diff_text = """\
diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,2 +1,3 @@
 first_line
+new_line
 second_line
"""

    assert parse_changed_lines(diff_text) == {"example.py": {2}}


def test_parse_added_line_numbers_with_deleted_lines():
    diff_text = """\
diff --git a/src/example.py b/src/example.py
--- a/src/example.py
+++ b/src/example.py
@@ -1,4 +1,4 @@
 first_line
-old_line
+new_line
+another_new_line
 last_line
"""

    assert parse_changed_lines(diff_text) == {
        "src/example.py": {2, 3},
    }


def test_parse_added_line_numbers_in_multiple_files():
    diff_text = """\
diff --git a/src/parser.py b/src/parser.py
--- a/src/parser.py
+++ b/src/parser.py
@@ -9,0 +10,1 @@
+new_parser_line
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -9,0 +10,1 @@
+new_main_line
"""

    assert parse_changed_lines(diff_text) == {
        "src/parser.py": {10},
        "src/main.py": {10},
    }


def test_parse_added_lines_from_multiple_hunks():
    diff_text = """\
diff --git a/src/example.py b/src/example.py
--- a/src/example.py
+++ b/src/example.py
@@ -1,2 +1,3 @@
 first_line
+added_near_top
 second_line
@@ -19,2 +20,3 @@
 twentieth_line
+added_near_bottom
 twenty_first_line
"""

    assert parse_changed_lines(diff_text) == {
        "src/example.py": {2, 21},
    }


def test_parse_deleted_file():
    diff_text = """\
diff --git a/src/old_file.py b/src/old_file.py
deleted file mode 100644
--- a/src/old_file.py
+++ /dev/null
@@ -1,2 +0,0 @@
-old_line_one
-old_line_two
"""

    assert parse_changed_lines(diff_text) == {}


def test_parse_new_file():
    diff_text = """\
diff --git a/src/new_file.py b/src/new_file.py
new file mode 100644
--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,2 @@
+first_line
+second_line
"""

    assert parse_changed_lines(diff_text) == {
        "src/new_file.py": {1, 2},
    }


def test_parse_changed_lines_in_renamed_file():
    diff_text = """\
diff --git a/src/old_parser.py b/src/parser.py
similarity index 90%
rename from src/old_parser.py
rename to src/parser.py
--- a/src/old_parser.py
+++ b/src/parser.py
@@ -9,2 +9,3 @@
 existing_line
+new_parser_line
 another_existing_line
"""

    assert parse_changed_lines(diff_text) == {
        "src/parser.py": {10},
    }
