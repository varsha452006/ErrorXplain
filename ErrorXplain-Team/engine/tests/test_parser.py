"""Tests for the C error parser - real gcc-style multi-line errors."""

from parser.error_parser import parse_c_error


def test_single_line_error_extracts_file_and_line():
    result = parse_c_error("main.c:5:9: error: expected ';' before 'return'")
    assert result.file == "main.c"
    assert result.line == 5
    assert result.level == "error"
    assert "expected" in result.raw_message


def test_multiline_error_ignores_notes():
    raw = (
        "main.c: In function 'main':\n"
        "main.c:7:5: error: 'x' undeclared (first use in this function)\n"
        "main.c:7:5: note: each undeclared identifier is reported only once\n"
    )
    result = parse_c_error(raw)
    assert result.level == "error"
    assert result.line == 7
    assert "note" not in result.raw_message.lower()


def test_warning_used_when_no_error_present():
    raw = (
        "main.c: In function 'foo':\n"
        "main.c:10:5: warning: implicit declaration of function 'bar'\n"
        "main.c:10:5: note: include the header that defines 'bar'\n"
    )
    result = parse_c_error(raw)
    assert result.level == "warning"
    assert result.line == 10


def test_error_wins_even_if_it_appears_after_a_warning():
    raw = (
        "main.c:3:1: warning: unused variable 'y'\n"
        "main.c:5:9: error: expected ';' before 'return'\n"
    )
    result = parse_c_error(raw)
    assert result.level == "error"
    assert result.line == 5


def test_unparseable_text_falls_back_to_raw():
    text = "some completely unrelated text with no gcc format"
    result = parse_c_error(text)
    assert result.file is None
    assert result.line is None
    assert result.raw_message == text
