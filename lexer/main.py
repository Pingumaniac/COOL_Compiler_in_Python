import sys
import ply.lex as lex
from ply.lex import TOKEN

class CoolLexer(object):
    tokens = (
        "at", "case", "class", "colon", "comma", "divide", "dot", "else", "equals",
        "esac", "false", "fi", "identifier", "if", "in", "inherits", "integer",
        "isvoid", "larrow", "lbrace", "le", "let", "loop", "lparen", "lt",
        "minus", "new", "not", "of", "plus", "pool", "rarrow", "rbrace",
        "rparen", "semi", "string", "then", "tilde", "times", "true", "type", "while"
    )

    reserved = {
        "case": "case", "class": "class", "else": "else", "esac": "esac", "false": "false",
        "fi": "fi", "if": "if", "in": "in", "inherits": "inherits", "isvoid": "isvoid",
        "let": "let", "loop": "loop", "new": "new", "not": "not", "of": "of",
        "pool": "pool", "then": "then", "true": "true", "while": "while"
    }

    states = (
        ('comment', 'exclusive'),
    )

    t_lparen = r'\('
    t_rparen = r'\)'
    t_lbrace = r'\{'
    t_rbrace = r'\}'
    t_colon = r'\:'
    t_comma = r'\,'
    t_dot = r'\.'
    t_semi = r'\;'
    t_at = r'\@'
    t_times = r'\*'
    t_divide = r'\/'
    t_plus = r'\+'
    t_minus = r'\-'
    t_tilde = r'~'
    t_lt = r'\<'
    t_equals = r'\='
    t_le = r'\<\='
    t_larrow = r'\<\-'
    t_rarrow = r'\=\>'
    t_ignore = ' \t\r\f\v' # Include space to ignore
    t_comment_ignore = ' \t\r\f'

    def __init__(self, buildLexer=True, debug=False, lextab="pycoolc.lextab",
                 optimize=True, outputDir="", debugLog=None, errorLog=None):
        self.comment_lcount = 0
        self.lexer = None
        self.lastToken = None

        self._debug = debug
        self._lextab = lextab
        self._optimize = optimize
        self._outputDir = outputDir
        self._debugLog = debugLog
        self._errorLog = errorLog

        if buildLexer:
            self.build(debug=debug, lextab=lextab, optimize=optimize, outputDir=outputDir, debugLog=debugLog, errorLog=errorLog)

    @TOKEN(r"t[rR][uU][eE]|f[aA][lL][sS][eE]")
    def t_boolean(self, token):
        if token.value[0] == 't' or token.value[0] == 'f':
            token.type = self.reserved.get(token.value.lower())
        return token


    @TOKEN(r"\d+")
    def t_integer(self, token):
        token.value = int(token.value)
        if token.value > 2147483647:
            print(f"ERROR: {token.lineno}: Lexer: integer too large")
            sys.exit(1)
        return token


    @TOKEN(r"[A-Z][a-zA-Z_0-9]*")
    def t_type_identifier(self, token):
        if token.value.lower() =='true' or token.value.lower() == 'false':
            token.type = self.reserved.get(token.value, 'type')
        else:
            token.type = self.reserved.get(token.value.lower(), 'type')
        return token


    @TOKEN(r"[a-z][a-zA-Z_0-9]*")
    def t_object_identifier(self, token):
        lowervalue = token.value.lower()
        token.type = self.reserved.get(lowervalue, 'identifier')
        return token


    @TOKEN(r'\"([^\\\n]|(\\.))*?\"')
    def t_string(self, token):
        raw_string = token.value[1:-1]
        processed_string = []
        idx = 0

        while idx < len(raw_string):
            current_char = raw_string[idx]

            if current_char == '\\':
                if idx + 1 >= len(raw_string):
                    print(f"ERROR: {token.lineno}: Lexer: unterminated string with backslash")
                    sys.exit(1)
                next_char = raw_string[idx + 1]
                processed_string.append("\\" + next_char)
                idx += 1
            elif current_char == '\x00': # NUL character (ASCII 0)
                print(f"ERROR: {token.lineno}: Lexer: a string may not contain NUL, the character with ASCII value 0")
            else:
                processed_string.append(current_char)

            idx += 1

        final_string = ''.join(processed_string)

        if len(final_string) > 1024:
            print(f"ERROR: {token.lineno}: Lexer: string length exceeds 1024 characters")
            sys.exit(1)

        token.value = final_string
        return token


    @TOKEN(r"\n+")
    def t_newline(self, token):
        token.lexer.lineno += len(token.value)

    def t_single_line_comment(self, t):
        r'\-\-[^\n]*'
        pass

    @TOKEN(r"\n+")
    def t_single_line_comment_newline(self, token):
        token.lexer.lineno += len(token.value)

    def t_multi_line_comment(self, t):
        r'\(\*'
        t.lexer.push_state('comment')
        self.comment_lcount = 1

    def t_comment_open(self, t):
        r'\(\*'
        self.comment_lcount += 1

    def t_comment_close(self, t):
        r'\*\)'
        self.comment_lcount -= 1
        if self.comment_lcount == 0:
            t.lexer.pop_state()

    def t_comment_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)


    def t_comment_error(self, t):
        t.lexer.skip(1)


    def t_error(self, token):
        if token.value[0] == '"':
            print(f"ERROR: {token.lineno}: Lexer: unterminated string")
        else:
            print("ERROR: %d: Lexer: illegal character: %s" % (token.lineno, token.value[0]))
        sys.exit(1)


    def build(self, **kwargs):
        debug = kwargs.get("debug", self._debug)
        lextab = kwargs.get("lextab", self._lextab)
        optimize = kwargs.get("optimize", self._optimize)
        outputDir = kwargs.get("outputDir", self._outputDir)
        debugLog = kwargs.get("debugLog", self._debugLog)
        errorLog = kwargs.get("errorLog", self._errorLog)

        self.tokens = self.tokens + tuple(self.reserved.values())

        self.lexer = lex.lex(module=self, lextab=lextab, debug=debug, optimize=optimize, outputdir=outputDir,
                             debuglog=debugLog, errorlog=errorLog)


    def input(self, coolProgramSourceCode: str):
        if self.lexer is None:
            raise Exception("Lexer was not built. Try calling the build() method first.")
        self.lexer.input(coolProgramSourceCode)

    def token(self):
        if self.lexer is None:
            raise Exception("Lexer was not built. Try building the lexer with the build() method.")
        self.lastToken = self.lexer.token()
        return self.lastToken

    def __iter__(self):
        return self

    def __next__(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t

def main():
    if len(sys.argv) != 2:
        print("Usage: ./lexer.py file.cl")
        sys.exit(1)

    inputFile = sys.argv[1]

    if not inputFile.endswith(".cl"):
        print("Cool program source code files must end with .cl extension.")
        sys.exit(1)

    try:
        with open(inputFile, encoding="utf-8") as file:
            coolCode = file.read()
    except IOError:
        print(f"ERROR: Could not open file {inputFile}")
        sys.exit(1)

    coolLexer = CoolLexer()
    coolLexer.build()

    coolLexer.input(coolCode)

    outputFile = inputFile + "-lex"

    try:
        with open(outputFile, "w") as out:
            for token in coolLexer:
                out.write("%d\n" % token.lineno)
                out.write("%s\n" % token.type)
                if token.type in ['identifier', 'integer', 'string', 'type']:
                    out.write("%s\n" % token.value)

            if coolLexer.comment_lcount > 0:
                print(f"ERROR: {coolLexer.lexer.lineno}: Lexer: unterminated comment")
                sys.exit(1)

    except IOError:
        print(f"ERROR: Could not write to file {outputFile}")
        sys.exit(1)

if __name__ == "__main__":
    main()

