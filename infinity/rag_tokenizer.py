import re
from collections import Counter


def is_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value or ""))


def is_number(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value or ""))


def is_alphabet(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]+", value or ""))


def naive_qie(text: str) -> list[str]:
    return _tokens(text)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\s]", text or "")


class RagTokenizer:
    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()

    def tokenize(self, line: str) -> str:
        tokens = _tokens(line)
        self._counter.update(tokens)
        return " ".join(tokens)

    def fine_grained_tokenize(self, tokens: str) -> str:
        return tokens

    def tag(self, token: str) -> str:
        if is_number(token):
            return "m"
        if is_alphabet(token):
            return "eng"
        if is_chinese(token):
            return "n"
        return "x"

    def freq(self, token: str) -> int:
        return self._counter[token]

    def _tradi2simp(self, text: str) -> str:
        return text

    def _strQ2B(self, text: str) -> str:
        return text
