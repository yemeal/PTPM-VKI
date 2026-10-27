import pytest

from app.domain.exceptions.comments import (
    InvalidMessageTextError,
    InvalidUsernameError,
)
from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH, MAX_USERNAME_LENGTH
from app.domain.value_objects.message_text import MessageText
from app.domain.value_objects.username import Username


def test_username_valid() -> None:
    u = Username.from_str("  john_doe  ")
    assert u.value == "john_doe"
    assert str(u) == "john_doe"
    assert repr(u) == "Username('john_doe')"
    assert len(u) == 8
    assert hash(u) == hash("john_doe")
    assert u == Username.from_str("john_doe")
    assert u != "john_doe"


@pytest.mark.parametrize(
    "invalid_input",
    ["", "   ", "\t", "\n", " \t \n "],
    ids=["empty", "spaces", "tab", "newline", "mixed_whitespace"],
)
def test_username_rejects_empty_or_whitespace(invalid_input: str) -> None:
    with pytest.raises(InvalidUsernameError):
        Username.from_str(invalid_input)


def test_username_rejects_non_string() -> None:
    with pytest.raises(InvalidUsernameError):
        Username.model_validate({"value": 123})


def test_username_rejects_too_long() -> None:
    too_long = "a" * (MAX_USERNAME_LENGTH + 1)
    with pytest.raises(InvalidUsernameError):
        Username.from_str(too_long)

    valid_edge = "a" * MAX_USERNAME_LENGTH
    u = Username.from_str(valid_edge)
    assert len(u) == MAX_USERNAME_LENGTH


def test_message_text_valid() -> None:
    m = MessageText.from_str("  Hello \r\n World!  ")
    assert m.value == "Hello \n World!"
    assert str(m) == "Hello \n World!"
    assert repr(m) == "MessageText('Hello \\n World!')"
    assert len(m) == len("Hello \n World!")
    assert hash(m) == hash("Hello \n World!")
    assert m == MessageText.from_str("Hello \n World!")
    assert m != "Hello \n World!"


def test_message_text_nfc_normalization() -> None:
    # 'e' + combining acute accent -> single code point 'é' in NFC
    decomposed = "e\u0301"
    composed = "\u00e9"
    m = MessageText.from_str(decomposed)
    assert m.value == composed


@pytest.mark.parametrize(
    "invalid_input",
    ["", "   ", "\t", "\n\r", "   \n\r\t  "],
    ids=["empty", "spaces", "tab", "crlf", "mixed_whitespace"],
)
def test_message_text_rejects_empty_or_whitespace(invalid_input: str) -> None:
    with pytest.raises(InvalidMessageTextError):
        MessageText.from_str(invalid_input)


def test_message_text_rejects_non_string() -> None:
    with pytest.raises(InvalidMessageTextError):
        MessageText.model_validate({"value": 12345})


def test_message_text_rejects_too_long() -> None:
    too_long = "b" * (MAX_MESSAGE_TEXT_LENGTH + 1)
    with pytest.raises(InvalidMessageTextError):
        MessageText.from_str(too_long)

    valid_edge = "b" * MAX_MESSAGE_TEXT_LENGTH
    m = MessageText.from_str(valid_edge)
    assert len(m) == MAX_MESSAGE_TEXT_LENGTH
