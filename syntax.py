#!/usr/bin/env python3

import ply.yacc
import ply.lex
import lexer # previous phase example snipped code

from syntax_common import treeprint

#tokens defined in lexer.py, needed for syntax rules
tokens = lexer.tokens

# Copy this class definition from the public_examples/simple-expression-example files
class ASTnode:
  def __init__(self, typestr):
    self.nodetype = typestr

def p_program(p): 
     '''program : definitions_multiple statement_list'''
     p[0] = ASTnode("program")
     p[0].children_statement = p[2]

def p_statement_list(p):
     '''statement_list : statement statement_list
                       | statement'''
     if len(p) == 3:
          p[0] = p[2]
          p[0].append(p[1])
     else:
          p[0] = [p[1]]

def p_definitions(p):
     '''definitions : function_definition
                    | procedure_definition
                    | variable_definition'''
     pass

def p_definitions_multiple(p):
     '''definitions_multiple : definitions definitions_multiple
                             | '''
     pass

def p_variable_definition(p):
     '''variable_definition : LET IDENT EQ rvalue
                            | CONST IDENT EQ expression'''
     pass

def p_variable_definition_multiple(p):
     '''variable_definition_multiple : variable_definition variable_definition_multiple
                                     | '''
     pass

def p_function_definition(p):
     '''function_definition : FUNC FUNC_IDENT LCURLY RCURLY RETURN IDENT variable_definition_multiple IS match_block ENDFUNC
                            | FUNC FUNC_IDENT LCURLY formals RCURLY RETURN IDENT variable_definition_multiple IS match_block ENDFUNC'''
     pass

def p_match_block(p): 
     '''match_block : match_item_multiple default_match'''
     pass

def p_match_item(p):
     '''match_item : expression LARROW rvalue COMMA'''
     pass

def p_match_item_multiple(p):
     '''match_item_multiple : match_item match_item_multiple
                            | '''
     pass

def p_default_match(p):
     '''default_match : LARROW rvalue
                      | DEFAULT LARROW rvalue'''
     pass

def p_procedure_definition(p): 
     '''procedure_definition : PROC PROC_IDENT LSQUARE RSQUARE variable_definition_multiple IS statement_list ENDPROC
                             | PROC PROC_IDENT LSQUARE formals RSQUARE variable_definition_multiple IS statement_list ENDPROC'''
     pass

def p_formals(p):
     '''formals : formal_arg
                | formal_arg SEMICOLON formals'''
     pass

def p_formal_arg(p):
     '''formal_arg : IDENT COLON IDENT'''
     pass

def p_statement(p):
     '''statement : statement_if
                  | statement_return
                  | statement_repeat
                  | print_statement
                  | assignment
                  | procedure_call'''
     p[0] = p[1]

def p_procedure_call(p):
     '''procedure_call : PROC_IDENT LPAREN RPAREN
                       | PROC_IDENT LPAREN arguments RPAREN'''
     p[0] = ASTnode("procedure_call")
     p[0].value = p[1]
     if len(p) == 5:
          p[0].children_arguments = p[3]
     p[0].lineno = p.lineno(1)


def p_arguments(p):
     '''arguments : expression
                  | expression COMMA arguments'''
     pass

def p_assignment(p):
     '''assignment : lvalue ASSIGN rvalue'''
     p[0] = ASTnode("assignment")
     p[0].child_target = p[1]
     p[0].child_expr = p[3]
     p[0].lineno = p.lineno(2)

def p_lvalue(p):
     '''lvalue : IDENT
               | IDENT DOT IDENT'''
     pass

def p_rvalue(p):
     '''rvalue : expression
               | if_expression
               | expression AMPERSAND expression'''
     pass

def p_print_statement(p):
     '''print_statement : PRINT print_item print_item_multiple'''
     p[0] = ASTnode("print")
     p[0].children_print_item = p[3]
     p[0].children_print_item.append(p[2])
     p[0].lineno = p.lineno(1)

def p_print_item(p):
     '''print_item : STRING
                   | expression'''
     p[0] = ASTnode("print_item")
     p[0].value = p[1]

def p_print_item_multiple(p):
     '''print_item_multiple : AMPERSAND print_item print_item_multiple
                            | '''
     if len(p) == 4:
          p[0] = p[3]
          p[0].append(p[2])
     else:
          p[0] = []

def p_statement_if(p):
     '''statement_if : IF expression THEN statement_list ENDIF
                     | IF expression THEN statement_list ELSE statement_list ENDIF'''
     p[0] = ASTnode("if")
     p[0].child_expression = p[2]

     p[0].children_statement_1 = p[4]

     if len(p) == 8:
          p[0].children_statement_2 = p[6]
     
     p[0].lineno = p.lineno(1)

def p_statement_repeat(p):
     '''statement_repeat : REPEAT statement_list UNTIL expression'''
     p[0] = ASTnode("repeat")
     p[0].children_statement = p[2]
     p[0].child_expression = p[4]
     p[0].lineno = p.lineno(1)

def p_statement_return(p):
     '''statement_return : RETURN expression'''
     p[0] = ASTnode("return")
     p[0].child_expression = p[2]
     p[0].lineno = p.lineno(1)

def p_expression(p):
     '''expression : simple_expr
                   | expression EQ simple_expr
                   | expression NOTEQ simple_expr
                   | expression LT simple_expr'''
     pass

def p_simple_expr(p):
     '''simple_expr : term
                    | simple_expr PLUS term
                    | simple_expr MINUS term'''
     pass

def p_term(p):
     '''term : factor
             | term MULT factor
             | term DIV factor'''
     pass

def p_factor(p):
     '''factor : atom
               | MINUS atom
               | PLUS atom'''
     pass

def p_atom(p):
     '''atom : IDENT
             | IDENT APOSTROPHE IDENT
             | INT_LITERAL
             | FRACTION_LITERAL
             | function_call
             | LPAREN expression RPAREN'''
     pass

def p_function_call(p):
     '''function_call : FUNC_IDENT LPAREN RPAREN
                      | FUNC_IDENT LPAREN arguments RPAREN'''
     pass

def p_if_expression(p):
     '''if_expression : IF expression THEN expression ELSE expression ENDIF'''
     pass

def p_error(p):
       print(f"Error found! {p.lineno}: Syntax Error (token:'{p.value}')")
       raise SystemExit

parser = ply.yacc.yacc()

if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-t', '--treetype', help='type of output tree (unicode/ascii/dot)')
    arg_parser.add_argument('inputfilename', help='filename to process')
    ns = arg_parser.parse_args()

    outformat="unicode"
    if ns.treetype:
      outformat = ns.treetype

    if ns.inputfilename is None:
        # user didn't provide input filename
        arg_parser.print_help()
    else:
        data = open( ns.inputfilename ).read()
        result = parser.parse(data, lexer=lexer.lexer, debug=False)
        # Pretty print the resulting tree
        treeprint(result, outformat)
        print("Program ok.")
