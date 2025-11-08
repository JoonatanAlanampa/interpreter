import sys, ply.lex
from fractions import Fraction

tokens = (
    'LPAREN', 'RPAREN',
    'LSQUARE', 'RSQUARE',
    'LCURLY', 'RCURLY',

    'LARROW', 'ASSIGN',
    'APOSTROPHE', 'AMPERSAND',
    'COMMA', 'COLON', 'SEMICOLON',
    'DOT', 'EQ', 'NOTEQ',
    'LT', 'PLUS', 'MINUS',
    'MULT', 'DIV', 
    
    'STRING', 'FRACTION_LITERAL',
    'INT_LITERAL', 'IDENT', 'FUNC_IDENT', 'PROC_IDENT',
    
    'LET', 'CONST', 'PROC', 'FUNC', 'ENDPROC', 'ENDFUNC',
    'RETURN', 'IS', 'REPEAT', 'UNTIL', 'IF', 'THEN',
    'ELSE', 'ENDIF', 'PRINT', 'DEFAULT', 'MOD'
)

# Tokens
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LSQUARE = r'\['
t_RSQUARE = r'\]'
t_LCURLY = r'\{'
t_RCURLY = r'\}'

t_LARROW = r'<-'
t_ASSIGN = r':='
t_APOSTROPHE = r"'"
t_AMPERSAND = r'&'
t_COMMA  = r','
t_COLON = r':'
t_SEMICOLON = r';'
t_DOT = r'\.'
t_EQ = r'='
t_NOTEQ = r'/='
t_LT = r'<'
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_MOD = r'%'

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_FRACTION_LITERAL(t):
    r'[0-9]+_[0-9]+'
    try:
        t.value = Fraction(t.value.replace("_", "/"))
    except ZeroDivisionError:
        raise Exception("Error found! Denominator 0.")
    return t

def t_INT_LITERAL(t):
    r'-?[0-9]+'
    t.value = int(t.value)
    if t.value >= 1000000000:
        raise Exception("Error found! Integer value too large", t.value)
    return t

def t_FUNC_IDENT(t):
    r'[A-Z][a-z0-9_]+'
    return t

def t_PROC_IDENT(t):
    r'[A-Z][A-Z][A-Z0-9_]*'
    return t

def t_IDENT(t):
    r'[a-z][a-zA-Z0-9_]+'
    if t.value == 'let':
        t.type = 'LET'
    if t.value == 'const':
        t.type = 'CONST'
    if t.value == 'proc':
        t.type = 'PROC'
    if t.value == 'func':
        t.type = 'FUNC'
    if t.value == 'endProc':
        t.type = 'ENDPROC'
    if t.value == 'endFunc':
        t.type = 'ENDFUNC'
    if t.value == 'return':
        t.type = 'RETURN'
    if t.value == 'is':
        t.type = 'IS'
    if t.value == 'repeat':
        t.type = 'REPEAT'
    if t.value == 'until':
        t.type = 'UNTIL'
    if t.value == 'if':
        t.type = 'IF'
    if t.value == 'then':
        t.type = 'THEN'
    if t.value == 'else':
        t.type = 'ELSE'
    if t.value == 'endif':
        t.type = 'ENDIF'
    if t.value == 'print':
        t.type = 'PRINT'
    if t.value == 'default':
        t.type = 'DEFAULT'
        
    return t

# Ignored characters
t_ignore = " \r\t"

def t_COMMENT(t):
    r'---[\s\S]*?---'
    return None

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    raise Exception("Error found! Illegal character '{}' at line {}".format(
        t.value[0], t.lexer.lineno ) )

# define lexer in module level so it can be used after
# importing this module:
lexer = ply.lex.lex()

# if this module/file is the first one started (the main module)
# then run:
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'usage: {sys.argv[0]} <filename>', file=sys.stderr )
        raise SystemExit
    else:
        with open( sys.argv[1], 'r' ) as INFILE:
            # blindly read all to memory (what if that is a 42Gb file?)
            data = INFILE.read()

        lexer.input( data )

        while True:
            token = lexer.token()
            if token is None:
                break
            print( token )
        print("Program ok.")
