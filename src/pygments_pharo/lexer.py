"""Pygments lexer for Pharo Smalltalk."""

from typing import Iterator, Tuple

from pygments.lexer import Lexer
from pygments.token import Comment, Error, Name, Number, Operator, Punctuation, String, Text

TokenTriplet = Tuple[int, object, str]  # (position, token type, value)


class PharoLexer(Lexer):
    """
    For Pharo Smalltalk syntax.

    Mostly follows the OCScanner rules from Pharo 13.
    Written by Kilian Kier.
    """

    name = "Pharo"
    url = "https://pharo.org/"
    filenames = ["*.st"]
    aliases = ["pharo"]
    mimetypes = ["text/x-pharo", "text/x-smalltalk"]

    tokens = {}

    reserved_words = {
        "nil",
        "true",
        "false",
        "self",
        "super",
        "thisContext",
    }
    binary_character = set("+-/\\*~<>=@,%|&?!·÷±×")
    special_punctuation = set("()[]{}.;!:")
    return_character = "^"

    def get_tokens_unprocessed(self, text: str) -> Iterator[TokenTriplet]:
        length = len(text)
        pos = 0

        while pos < length:
            char = text[pos]
            start = pos

            if char.isspace():
                pos = self._scan_whitespace(text, pos)
                yield start, Text.Whitespace, text[start:pos]
                continue

            if char == '"':
                token, pos, ok = self._scan_comment(text, pos)
                yield start, Comment if ok else Error, token
                continue

            if char == "'":
                token, pos, ok = self._scan_string_literal(text, pos)
                yield start, String if ok else Error, token
                continue

            if char == "$":
                token, pos, ok = self._scan_character_literal(text, pos)
                yield start, String.Char if ok else Error, token
                continue

            if char == "#":
                token, pos, tok = self._scan_hash_literal(text, pos)
                yield start, tok, token
                continue

            if self._starts_number(text, pos):
                token, pos, ok = self._scan_number(text, pos)
                yield start, Number if ok else Error, token
                continue

            if self._is_binary_char(char):
                token, pos = self._scan_binary_selector(text, pos)
                yield start, Operator, token
                continue

            if self._is_identifier_start(char):
                token, pos, tok = self._scan_identifier_or_keyword(text, pos)
                yield start, tok, token
                continue

            if char == ":" and pos + 1 < length and text[pos + 1] == "=":
                yield start, Operator, ":="
                pos += 2
                continue

            if char in self.special_punctuation:
                yield start, Punctuation, char
                pos += 1
                continue

            if char == self.return_character:
                yield start, Operator, char
                pos += 1
                continue

            yield start, Error, char
            pos += 1

        if not text.endswith("\n"):
            yield length, Text.Whitespace, "\n"

    @staticmethod
    def _scan_whitespace(text: str, pos: int) -> int:
        while pos < len(text) and text[pos].isspace():
            pos += 1
        return pos

    @staticmethod
    def _scan_comment(text: str, pos: int) -> Tuple[str, int, bool]:
        start = pos
        pos += 1
        while pos < len(text):
            char = text[pos]
            if char == '"':
                if pos + 1 < len(text) and text[pos + 1] == '"':
                    pos += 2
                    continue
                pos += 1
                return text[start:pos], pos, True
            pos += 1
        return text[start:], len(text), False

    @staticmethod
    def _scan_string_literal(text: str, pos: int) -> Tuple[str, int, bool]:
        start = pos
        pos += 1
        while pos < len(text):
            char = text[pos]
            if char == "'":
                if pos + 1 < len(text) and text[pos + 1] == "'":
                    pos += 2
                    continue
                pos += 1
                return text[start:pos], pos, True
            pos += 1
        return text[start:], len(text), False

    @staticmethod
    def _scan_character_literal(text: str, pos: int) -> Tuple[str, int, bool]:
        start = pos
        pos += 1
        if pos >= len(text) or (text[pos] == "\n" and pos == len(text) - 1):
            return text[start:pos], pos, False
        return text[start : pos + 1], pos + 1, True

    def _scan_hash_literal(self, text: str, pos: int) -> Tuple[str, int, object]:
        start = pos
        pos += 1
        while pos < len(text) and text[pos] == "#":
            pos += 1
        if pos >= len(text):
            return text[start:], pos, Error

        char = text[pos]

        if char in "([":
            pos += 1
            return text[start:pos], pos, String.Symbol

        if char == "'":
            token, pos, ok = self._scan_string_literal(text, pos)
            return text[start:pos], pos, String.Symbol if ok else Error

        if self._is_identifier_start(char):
            end = self._scan_symbol_name(text, pos)
            return text[start:end], end, String.Symbol

        if self._is_binary_char(char):
            end = self._scan_binary_selector(text, pos)[1]
            return text[start:end], end, String.Symbol

        return text[start:pos], pos, Error

    def _scan_symbol_name(self, text: str, pos: int) -> int:
        pos = self._scan_name(text, pos)
        while pos < len(text) and text[pos] == ":":
            pos += 1
            pos = self._scan_name(text, pos)
        return pos

    def _scan_binary_selector(self, text: str, pos: int) -> Tuple[str, int]:
        start = pos
        while pos < len(text) and self._is_binary_char(text[pos]):
            pos += 1
        return text[start:pos], pos

    def _scan_identifier_or_keyword(self, text: str, pos: int) -> Tuple[str, int, object]:
        start = pos
        pos = self._scan_name(text, pos)
        token_text = text[start:pos]
        token_type = self._classify_identifier(token_text)

        if (
            pos < len(text)
            and text[pos] == ":"
            and not (pos + 1 < len(text) and text[pos + 1] == "=")
        ):
            pos += 1
            token_text = text[start:pos]
            token_type = Name.Function

        return token_text, pos, token_type

    def _scan_name(self, text: str, pos: int) -> int:
        while pos < len(text) and self._is_identifier_part(text[pos]):
            pos += 1
        return pos

    def _scan_number(self, text: str, pos: int) -> Tuple[str, int, bool]:
        start = pos

        if text[pos] == "-":
            pos += 1

        radix_start = pos
        pos = self._consume_digits(text, pos)

        if len(text) > pos > radix_start and text[pos] in "rR":
            base = int(text[radix_start:pos])
            pos += 1
            if base <= 1:
                pos = self._consume_literal_tail(text, pos)
                return text[start:pos], pos, False
            digits_consumed, pos = self._consume_radix_digits(text, pos, base)
            if not digits_consumed:
                return text[start:pos], pos, False
            return text[start:pos], pos, True

        if pos == radix_start:
            return text[start : start + 1], start + 1, False

        if (
            pos < len(text)
            and text[pos] == "."
            and pos + 1 < len(text)
            and text[pos + 1].isdigit()
        ):
            pos += 1
            pos = self._consume_digits(text, pos)

        if pos < len(text) and text[pos] in "eEdD":
            exp_pos = pos + 1
            if exp_pos < len(text) and text[exp_pos] in "+-":
                exp_pos += 1
            if exp_pos < len(text) and text[exp_pos].isdigit():
                pos = self._consume_digits(text, exp_pos)

        return text[start:pos], pos, True

    @staticmethod
    def _consume_digits(text: str, pos: int) -> int:
        while pos < len(text) and text[pos].isdigit():
            pos += 1
        return pos

    @staticmethod
    def _consume_literal_tail(text: str, pos: int) -> int:
        while pos < len(text) and (text[pos].isalnum() or text[pos] == "."):
            pos += 1
        return pos

    def _consume_radix_digits(self, text: str, pos: int, base: int) -> Tuple[bool, int]:
        consumed = False
        has_fraction = False
        length = len(text)

        while pos < length:
            char = text[pos]
            if char == ".":
                if has_fraction:
                    break
                if pos + 1 < length and self._radix_digit_value(text[pos + 1]) < base:
                    has_fraction = True
                    pos += 1
                    continue
                break

            value = self._radix_digit_value(char)
            if 0 <= value < base:
                consumed = True
                pos += 1
                continue
            break
        return consumed, pos

    @staticmethod
    def _radix_digit_value(char: str) -> int:
        if char.isdigit():
            return ord(char) - ord("0")
        lower = char.lower()
        if "a" <= lower <= "z":
            return ord(lower) - ord("a") + 10
        return -1

    @staticmethod
    def _starts_number(text: str, pos: int) -> bool:
        if text[pos].isdigit():
            return True
        return text[pos] == "-" and pos + 1 < len(text) and text[pos + 1].isdigit()

    @staticmethod
    def _is_identifier_start(char: str) -> bool:
        return char.isalpha() or char == "_"

    @staticmethod
    def _is_identifier_part(char: str) -> bool:
        return char.isalnum() or char == "_"

    def _is_binary_char(self, char: str) -> bool:
        return char in self.binary_character

    def _classify_identifier(self, value: str) -> object:
        if value in self.reserved_words:
            return Name.Builtin.Pseudo
        if value and value[0].isupper():
            return Name.Class
        return Name.Variable
