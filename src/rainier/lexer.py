import re

Token = tuple[str, str]

TOKEN_SPECIFICATION = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r'"([^"\\]*(?:\\.[^"\\]*)*)"'),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*[!?]?"),
    ("OP", r"<=|>=|==|!=|\+|\-|\*|/|<|>|=|\.|,|\(|\)|\||;"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t]+"),
    ("COMMENT", r"#.*"),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION))
KEYWORDS = {
    "def", "end", "class", "if", "else", "elsif", "then", "do", "while", "return", "true", "false", "nil", "self", "puts", "and", "or", "new"
}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.pos = 0
        self._tokenize()

    def _tokenize(self):
        for match in TOKEN_RE.finditer(self.source):
            kind = match.lastgroup
            value = match.group(kind)
            if kind == "NUMBER":
                self.tokens.append((kind, value))
            elif kind == "STRING":
                self.tokens.append((kind, bytes(value[1:-1], "utf-8").decode("unicode_escape")))
            elif kind == "IDENT":
                if value in KEYWORDS:
                    self.tokens.append((value, value))
                else:
                    self.tokens.append((kind, value))
            elif kind == "OP":
                self.tokens.append((value, value))
            elif kind == "NEWLINE":
                self.tokens.append(("NEWLINE", value))
            elif kind == "SKIP" or kind == "COMMENT":
                continue
            else:
                raise SyntaxError(f"Unknown token: {value}")
        self.tokens.append(("EOF", ""))

    def peek(self, offset=0) -> Token:
        return self.tokens[self.pos + offset]

    def next(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, expected: str) -> Token:
        tok = self.next()
        if tok[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {tok}")
        return tok

    def skip_newlines(self):
        while self.peek()[0] == "NEWLINE":
            self.next()
