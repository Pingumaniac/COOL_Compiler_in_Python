import ply.lex as lex
import sys

class DummyLexer:
    def __init__(self, tokens_filename):
        self.tokens = []
        self._read_tokens(tokens_filename)

    def _read_tokens(self, tokens_filename):
        try:
            with open(tokens_filename, 'r') as f:
                tokens_lines = [line.rstrip('\n') for line in f.readlines()]
        except FileNotFoundError:
            print(f"ERROR: File '{tokens_filename}' not found.")
            sys.exit(1)

        while tokens_lines:
            line_number = self._get_token_line(tokens_lines)
            token_type = self._get_token_line(tokens_lines)
            if token_type in ['identifier', 'integer', 'type', 'string']:
                token_lexeme = self._get_token_line(tokens_lines)
            else:
                token_lexeme = token_type
            self.tokens.append((line_number, token_type.upper(), token_lexeme))

    def _get_token_line(self, tokens_lines):
        return tokens_lines.pop(0) if tokens_lines else ''

    def token(self):
        if not self.tokens:
            return None
        line, token_type, lexeme = self.tokens.pop(0)
        tok = lex.LexToken()
        tok.type = token_type
        tok.value = lexeme
        tok.lineno = int(line)
        tok.lexpos = 0
        return tok
