import ply.yacc as yacc
import sys
from output_ast import OutputAST
from lexer_cl import DummyLexer

class CoolParser:
    # Should be uppercase for ply tokens, thus have more token types than lexer
    tokens = (
        'LBRACE',
        'RBRACE',
        'LPAREN',
        'RPAREN',
        'INTEGER',
        'CLASS',
        'ELSE',
        'FALSE',
        'FI',
        'IF',
        'IN',
        'INHERITS',
        'ISVOID',
        'LET',
        'LOOP',
        'POOL',
        'THEN',
        'WHILE',
        'CASE',
        'ESAC',
        'NEW',
        'OF',
        'NOT',
        'TRUE',
        'AT',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'RARROW',
        'LARROW',
        'LE',
        'LT',
        'EQUALS',
        'COLON',
        'COMMA',
        'SEMI',
        'TILDE',
        'DOT',
        'IDENTIFIER',
        'TYPE',
        'STRING'
    )

    precedence = (
        ('nonassoc', 'LARROW'),
        ('right', 'TILDE'),
        ('left', 'NOT'),
        ('nonassoc', 'LE', 'LT', 'EQUALS'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'DOT'),
        ('left', 'AT'),
        ('left', 'ISVOID')
    )


    def __init__(self, lexer):
        self.lexer = lexer
        self.parser = yacc.yacc(module=self)
        self.ast = None

    def parse(self):
        self.ast = self.parser.parse(lexer=self.lexer)
        return self.ast

    # Grammar Rules

    def p_program_classlist(self, p):
        'program : classlist'
        p[0] = p[1]

    def p_classlist_one(self, p):
        'classlist : class SEMI'
        p[0] = [p[1]]

    def p_classlist_some(self, p):
        'classlist : class SEMI classlist'
        p[0] = [p[1]] + p[3]

    def p_class_noinherit(self, p):
        'class : CLASS type LBRACE featurelist RBRACE'
        p[0] = (p.lineno(1), 'class_noinherit', p[2], p[4])

    def p_class_inherit(self, p):
        'class : CLASS type INHERITS type LBRACE featurelist RBRACE'
        p[0] = (p.lineno(1), 'class_inherit', p[2], p[4], p[6])

    def p_type(self, p):
        'type : TYPE'
        p[0] = (p.lineno(1), p[1])

    def p_identifier(self, p):
        'identifier : IDENTIFIER'
        p[0] = (p.lineno(1), p[1])

    def p_formallist_some(self, p):
        'formallist : formal COMMA formallist'
        p[0] = [p[1]] + p[3]

    def p_formallist_one(self, p):
        'formallist : formal'
        p[0] = [p[1]]

    def p_formal(self, p):
        'formal : identifier COLON type'
        p[0] = (p[1][0], p[1], p[3])

    def p_featurelist_none(self, p):
        'featurelist : '
        p[0] = []

    def p_featurelist_some(self, p):
        'featurelist : feature SEMI featurelist'
        p[0] = [p[1]] + p[3]

    def p_feature_attribute(self, p):
        'feature : attribute'
        p[0] = p[1]

    def p_attributenoinit(self, p):
        'attribute : identifier COLON type'
        p[0] = (p[1][0], 'attribute_no_init', p[1], p[3])

    def p_attributeinit(self, p):
        'attribute : identifier COLON type LARROW exp'
        p[0] = (p[1][0], 'attribute_init', p[1], p[3], p[5])

    def p_feature_method_withformals(self, p):
        'feature : identifier LPAREN formallist RPAREN COLON type LBRACE exp RBRACE'
        p[0] = (p[1][0], 'method', p[1], p[3], p[6], p[8])

    def p_feature_method_noformals(self, p):
        'feature : identifier LPAREN RPAREN COLON type LBRACE exp RBRACE'
        p[0] = (p[1][0], 'method', p[1], [], p[5], p[7])

    def p_explist_semi_one(self, p):
        'explist_semi : exp SEMI'
        p[0] = [p[1]]

    def p_explist_semi_some(self, p):
        'explist_semi : exp SEMI explist_semi'
        p[0] = [p[1]] + p[3]

    def p_explist_comma_one(self, p):
        'explist_comma : exp'
        p[0] = [p[1]]

    def p_explist_comma_some(self, p):
        'explist_comma : exp COMMA explist_comma'
        p[0] = [p[1]] + p[3]

    def p_exp_assign(self, p):
        'exp : identifier LARROW exp'
        p[0] = (p[1][0], 'assign', p[1], p[3])

    def p_exp_dynamicdispatch_withexp(self, p):
        'exp : exp DOT identifier LPAREN explist_comma RPAREN'
        p[0] = (p[1][0], 'dynamic_dispatch', p[1], p[3], p[5])

    def p_exp_dynamicdispatch_noexp(self, p):
        'exp : exp DOT identifier LPAREN RPAREN'
        p[0] = (p[1][0], 'dynamic_dispatch', p[1], p[3], [])

    def p_exp_staticdispatch_withexp(self, p):
        'exp : exp AT type DOT identifier LPAREN explist_comma RPAREN'
        p[0] = (p[1][0], 'static_dispatch', p[1], p[3], p[5], p[7])

    def p_exp_staticdispatch_noexp(self, p):
        'exp : exp AT type DOT identifier LPAREN RPAREN'
        p[0] = (p[1][0], 'static_dispatch', p[1], p[3], p[5], [])

    def p_exp_selfdispatch_withexp(self, p):
        'exp : identifier LPAREN explist_comma RPAREN'
        p[0] = (p[1][0], 'self_dispatch', p[1], p[3])

    def p_exp_selfdispatch_noexp(self, p):
        'exp : identifier LPAREN RPAREN'
        p[0] = (p[1][0], 'self_dispatch', p[1], [])

    def p_exp_if(self, p):
        'exp : IF exp THEN exp ELSE exp FI'
        p[0] = (p.lineno(1), 'if', p[2], p[4], p[6])

    def p_exp_while(self, p):
        'exp : WHILE exp LOOP exp POOL'
        p[0] = (p.lineno(1), 'while', p[2], p[4])

    def p_exp_block(self, p):
        'exp : LBRACE explist_semi RBRACE'
        p[0] = (p.lineno(1), 'block', p[2])

    def p_exp_new(self, p):
        'exp : NEW type'
        p[0] = (p.lineno(1), 'new', p[2])

    def p_exp_isvoid(self, p):
        'exp : ISVOID exp'
        p[0] = (p.lineno(1), 'isvoid', p[2])

    def p_exp_plus(self, p):
        'exp : exp PLUS exp'
        p[0] = (p[1][0], 'plus', p[1], p[3])

    def p_exp_minus(self, p):
        'exp : exp MINUS exp'
        p[0] = (p[1][0], 'minus', p[1], p[3])

    def p_exp_times(self, p):
        'exp : exp TIMES exp'
        p[0] = (p[1][0], 'times', p[1], p[3])

    def p_exp_divide(self, p):
        'exp : exp DIVIDE exp'
        p[0] = (p[1][0], 'divide', p[1], p[3])

    def p_exp_not(self, p):
        'exp : NOT exp'
        p[0] = (p.lineno(1), 'not', p[2])

    def p_exp_negate(self, p):
        'exp : TILDE exp'
        p[0] = (p.lineno(1), 'negate', p[2])

    def p_exp_parenexp(self, p):
        'exp : LPAREN exp RPAREN'
        p[0] = (p.lineno(1), 'paren_exp', p[2])

    def p_exp_identifier(self, p):
        'exp : identifier'
        p[0] = (p[1][0], 'identifier', p[1])

    def p_exp_integer(self, p):
        'exp : INTEGER'
        p[0] = (p.lineno(1), 'integer', p[1])

    def p_exp_string(self, p):
        'exp : STRING'
        p[0] = (p.lineno(1), 'string', p[1])

    def p_exp_true(self, p):
        'exp : TRUE'
        p[0] = (p.lineno(1), 'true')

    def p_exp_false(self, p):
        'exp : FALSE'
        p[0] = (p.lineno(1), 'false')

    def p_exp_let(self, p):
        'exp : LET attribute attributelist IN exp'
        p[0] = (p.lineno(1), 'let', [p[2]] + p[3], p[5])

    def p_let_attributelist_none(self, p):
        'attributelist : '
        p[0] = []

    def p_let_attributelist_some(self, p):
        'attributelist : COMMA attribute attributelist'
        p[0] = [p[2]] + p[3]

    def p_exp_case(self, p):
        'exp : CASE exp OF elementlist ESAC'
        p[0] = (p.lineno(1), 'case', p[2], p[4])

    def p_case_element(self, p):
        'element : identifier COLON type RARROW exp'
        p[0] = (p[1][0], p[1], p[3], p[5])

    def p_case_elementlist_one(self, p):
        'elementlist : element SEMI'
        p[0] = [p[1]]

    def p_case_elementlist_some(self, p):
        'elementlist : element SEMI elementlist'
        p[0] = [p[1]] + p[3]

    def p_exp_lt(self, p):
        'exp : exp LT exp'
        p[0] = (p[1][0], 'lt', p[1], p[3])

    def p_exp_le(self, p):
        'exp : exp LE exp'
        p[0] = (p[1][0], 'le', p[1], p[3])

    def p_exp_eq(self, p):
        'exp : exp EQUALS exp'
        p[0] = (p[1][0], 'eq', p[1], p[3])

    def p_error(self, p):
        if p:
            print("ERROR:", p.lineno, ": Parser: parse error near", p.value)
            sys.exit(1)
        else:
            print("ERROR: Syntax error at EOF")
            sys.exit(1)

def main():

    if len(sys.argv) < 2:
        print("Usage: python parser.py <tokens_filename>")
        sys.exit(1)

    tokens_filename = sys.argv[1]
    lexer = DummyLexer(tokens_filename)
    parser = CoolParser(lexer)
    ast = parser.parse()

    ast_filename = tokens_filename[:-3] + "ast"
    output = OutputAST(ast, ast_filename)
    output.output_ast_file()


if __name__ == "__main__":
    main()
