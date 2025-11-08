#!/usr/bin/env python3

import ply.yacc
import ply.lex
import lexer # previous phase example snipped code

from syntax_common import treeprint, get_childvars
from semantics_common import SemData, SymbolData, visit_tree
from fractions import Fraction

#tokens defined in lexer.py, needed for syntax rules
tokens = lexer.tokens

# Copy this class definition from the public_examples/simple-expression-example files
class ASTnode:
  def __init__(self, typestr):
    self.nodetype = typestr

def p_program(p): 
     '''program : definitions_multiple statement_list'''
     p[0] = ASTnode("program")
     p[0].children_definitions = p[1]
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
     p[0] = [p[1]]

def p_definitions_multiple(p):
     '''definitions_multiple : definitions definitions_multiple
                             | '''
     if len(p) == 3:
        p[0] = p[1] + p[2]
     else:
        p[0] = []

def p_variable_definition(p):
     '''variable_definition : LET IDENT EQ rvalue
                            | CONST IDENT EQ expression'''
     p[0] = ASTnode("variable_definition")
     p[0].value = p[2]
     p[0].child_expression = p[4]
     p[0].lineno = p.lineno(1)

     p[0].decltype = p[1]

def p_variable_definition_multiple(p):
     '''variable_definition_multiple : variable_definition variable_definition_multiple
                                     | '''
     if len(p) == 3:
        p[0] = p[2]
        p[0].insert(0, p[1])
     else:
        p[0] = []

def p_function_definition(p):
     '''function_definition : FUNC FUNC_IDENT LCURLY RCURLY RETURN IDENT variable_definition_multiple IS match_block ENDFUNC
                            | FUNC FUNC_IDENT LCURLY formals RCURLY RETURN IDENT variable_definition_multiple IS match_block ENDFUNC'''
     p[0] = ASTnode("function_definition")
     p[0].value = p[2]  # function name
     if len(p) == 11:
        p[0].children_formals = []
        p[0].child_return_name = ASTnode("return_variable")
        p[0].child_return_name.value = p[6]
        p[0].children_locals = p[7]
        p[0].children_match = p[9]
     else:
        p[0].children_formals = p[4]
        p[0].child_return_name = ASTnode("return_variable")
        p[0].child_return_name.value = p[7]
        p[0].children_locals = p[8]
        p[0].children_match = p[10]
     p[0].lineno = p.lineno(1)

def p_match_block(p): 
     '''match_block : match_item_multiple default_match'''
     p[0] = [*p[1], p[2]]

def p_match_item(p):
     '''match_item : expression LARROW rvalue COMMA'''
     node = ASTnode("match_item")
     node.child_expression = p[1]
     node.child_result = p[3]
     node.lineno = p.lineno(2)
     p[0] = node

def p_match_item_multiple(p):
     '''match_item_multiple : match_item match_item_multiple
                            | '''
     if len(p) == 3:
        p[0] = p[2]
        p[0].insert(0, p[1])
     else:
        p[0] = []

def p_default_match(p):
     '''default_match : LARROW rvalue
                      | DEFAULT LARROW rvalue'''
     p[0] = ASTnode("default_match")
     p[0].child_result = p[len(p)-1]
     p[0].lineno = p.lineno(1)

def p_procedure_definition(p): 
     '''procedure_definition : PROC PROC_IDENT LSQUARE RSQUARE variable_definition_multiple IS statement_list ENDPROC
                             | PROC PROC_IDENT LSQUARE formals RSQUARE variable_definition_multiple IS statement_list ENDPROC'''
     p[0] = ASTnode("procedure_definition")
     p[0].value = p[2]
     if len(p) == 9:
        p[0].children_formals = []
        p[0].children_locals = p[5]
        p[0].children_body = p[7]
     else:
        p[0].children_formals = p[4]
        p[0].children_locals = p[6]
        p[0].children_body = p[8]
     p[0].lineno = p.lineno(1)

def p_formals(p):
     '''formals : formal_arg
                | formal_arg SEMICOLON formals'''
     if len(p) == 2:
        p[0] = [p[1]]
     else:
        p[0] = [p[1]] + p[3]

def p_formal_arg(p):
     '''formal_arg : IDENT COLON IDENT'''
     node = ASTnode("formal_arg")
     node.value = p[1]
     node.child_type = ASTnode("type")
     node.child_type.value = p[3]
     node.lineno = p.lineno(1)
     p[0] = node

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
     if len(p) == 2:
        p[0] = [p[1]]
     else:
        p[0] = [p[1]] + p[3]

def p_assignment(p):
     '''assignment : lvalue ASSIGN rvalue'''
     p[0] = ASTnode("assignment")
     p[0].child_target = p[1]
     p[0].child_expr = p[3]
     p[0].lineno = p.lineno(2)

def p_lvalue(p):
     '''lvalue : IDENT
               | IDENT DOT IDENT'''
     node = ASTnode("lvalue")
     if len(p) == 2:
        node.value = p[1]
     else:
        node.value = f"{p[1]}.{p[3]}"
     node.lineno = p.lineno(1)
     p[0] = node

def p_rvalue(p):
     '''rvalue : expression
               | if_expression
               | expression AMPERSAND expression'''
     if len(p) == 2:
        p[0] = p[1]
     else:
        node = ASTnode("concat_expression")
        node.child_left = p[1]
        node.child_right = p[3]
        node.lineno = p.lineno(2)
        p[0] = node

def p_print_statement(p):
     '''print_statement : PRINT print_item print_item_multiple'''
     p[0] = ASTnode("print")
     p[0].children_print_item = [p[2]] + p[3]
     p[0].lineno = p.lineno(1)

def p_print_item(p):
     '''print_item : STRING
                   | expression'''
     p[0] = ASTnode("print_item")
     if isinstance(p[1], str):
        p[0].value = p[1]         # it's a STRING
     else:
        p[0].child_expr = p[1]    # it's an expression node

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
     if len(p) == 2:
        p[0] = p[1]
     else:
        node = ASTnode("binary_expression")
        node.value = p[2]
        node.child_left = p[1]
        node.child_right = p[3]
        node.lineno = p.lineno(2)
        p[0] = node

def p_simple_expr(p):
     '''simple_expr : term
                    | simple_expr PLUS term
                    | simple_expr MINUS term'''
     if len(p) == 2:
        p[0] = p[1]
     else:
        node = ASTnode("binary_expression")
        node.value = p[2]
        node.child_left = p[1]
        node.child_right = p[3]
        node.lineno = p.lineno(2)
        p[0] = node

def p_term(p):
     '''term : factor
             | term MULT factor
             | term DIV factor
             | term MOD factor'''
     if len(p) == 2:
        p[0] = p[1]
     else:
        node = ASTnode("binary_expression")
        node.value = p[2]
        node.child_left = p[1]
        node.child_right = p[3]
        node.lineno = p.lineno(2)
        p[0] = node

def p_factor(p):
     '''factor : atom
               | MINUS atom
               | PLUS atom'''
     if len(p) == 2:
        p[0] = p[1]
     else:
        node = ASTnode("unary_expression")
        node.value = p[1]
        node.child_expr = p[2]
        node.lineno = p.lineno(1)
        p[0] = node

def p_atom(p):
     '''atom : IDENT
             | IDENT APOSTROPHE IDENT
             | INT_LITERAL
             | FRACTION_LITERAL
             | function_call
             | LPAREN expression RPAREN'''
     if len(p) == 2:
        if isinstance(p[1], ASTnode):
            p[0] = p[1]
        else:
            node = ASTnode("literal" if isinstance(p[1], (int, float, Fraction)) else "identifier")
            node.value = p[1]
            node.lineno = p.lineno(1)
            p[0] = node
     elif len(p) == 4 and p[2] == "'":
        node = ASTnode("qualified_identifier")
        node.value = f"{p[1]}'{p[3]}"
        node.lineno = p.lineno(1)
        p[0] = node
     else:
        p[0] = p[2]  # parentheses

def p_function_call(p):
     '''function_call : FUNC_IDENT LPAREN RPAREN
                      | FUNC_IDENT LPAREN arguments RPAREN'''
     node = ASTnode("function_call")
     node.value = p[1]
     node.children_arguments = [] if len(p) == 4 else p[3]
     node.lineno = p.lineno(1)
     p[0] = node

def p_if_expression(p):
     '''if_expression : IF expression THEN expression ELSE expression ENDIF'''
     node = ASTnode("if_expression")
     node.child_condition = p[2]
     node.child_then = p[4]
     node.child_else = p[6]
     node.lineno = p.lineno(1)
     p[0] = node

def p_error(p):
    if p:
        print(f"Error found! {p.lineno}: Syntax Error (token:'{p.value}')")
    else:
        print("Error found! Unexpected end of input.")
    raise SystemExit

class SemanticContext:
    def __init__(self):
        self.inside_repeat = False
        self.inside_function = None
        self.declared_symbols = set()
        self.local_symbols = set()

def before_check(node, semdata):
    ctx = semdata.context

    # Validating qualified identifiers
    if node.nodetype == "qualified_identifier":
        parts = node.value.split("'")
        if len(parts) == 2:
            base, attr = parts
            if attr not in ("num", "den", "int"):
                return f"Invalid attribute '{attr}' in qualified identifier."

    # Validating lvalue attributes (modifiable only num/den)
    if node.nodetype == "lvalue" and '.' in node.value:
        base, attr = node.value.split('.')
        if attr not in ("num", "den"):
            return f"Invalid modifiable attribute '{attr}' in lvalue."

    # Track we're inside repeat
    if node.nodetype == "repeat":
        ctx.inside_repeat = True

    # Error: return outside repeat
    if node.nodetype == "return" and not ctx.inside_repeat:
        return "Return statement only allowed inside repeat block."

    # Function/procedure definition
    if node.nodetype in ("function_definition", "procedure_definition"):
        ctx.inside_function = node.value
        ctx.local_symbols = set()
        seen_names = set()

        # Parameters
        for arg in node.children_formals:
            if arg.child_type.value not in ("integer", "fraction"):
                return f"Parameter '{arg.value}' has invalid type '{arg.child_type.value}'"
            if arg.value in seen_names:
                return f"Duplicate parameter name '{arg.value}'"
            seen_names.add(arg.value)
            ctx.local_symbols.add(arg.value)
            _add_symbol(semdata, arg.value, arg.child_type.value, arg)

        # Return variable (functions only)
        if node.nodetype == "function_definition":
            if node.child_return_name.value in seen_names:
                return f"Return variable '{node.child_return_name.value}' is already used as a parameter"
            seen_names.add(node.child_return_name.value)
            ctx.local_symbols.add(node.child_return_name.value)
            _add_symbol(semdata, node.child_return_name.value, "fraction", node.child_return_name)

        # Local variable names (shadowing allowed, no global collision check)
        for local in node.children_locals:
            if local.value in seen_names:
                return f"Duplicate local variable '{local.value}'"
            seen_names.add(local.value)
            ctx.local_symbols.add(local.value)
            # Do not add local variable to global symbol table

    # Global variable definition
    if node.nodetype == "variable_definition":
        if ctx.inside_function is None:
            if node.value in ctx.declared_symbols:
                return f"Variable '{node.value}' defined more than once"
            ctx.declared_symbols.add(node.value)
            symtype = getattr(node, "decltype", "let")
            _add_symbol(semdata, node.value, symtype, node)

    # Assignment to const check (only globals matter)
    if node.nodetype == "assignment":
        if hasattr(node.child_target, "value"):
            varname = node.child_target.value.split('.')[0]
            if varname in semdata.symtbl and varname not in ctx.local_symbols:
                if semdata.symtbl[varname].symtype == "const":
                    return f"Cannot assign to const variable '{varname}'"

    return None

def after_check(node, semdata):
    if node.nodetype == "repeat":
        semdata.context.inside_repeat = False
    if node.nodetype in ("function_definition", "procedure_definition"):
        semdata.context.inside_function = None
        semdata.context.local_symbols = set()

    if node.nodetype in ("function_call", "procedure_call"):
        name = node.value
        if name not in semdata.symtbl:
            return f"{node.nodetype.replace('_', ' ').capitalize()} '{name}' not defined"
        expected_args = _get_function_arg_count(semdata.symtbl[name].defnode)
        actual_args = len(getattr(node, "children_arguments", []))
        if actual_args != expected_args:
            return f"{node.nodetype.replace('_', ' ').capitalize()} '{name}' expects {expected_args} arguments, got {actual_args}"

    if node.nodetype == "identifier":
        if (
            node.value not in semdata.symtbl and
            node.value not in semdata.context.local_symbols
        ):
            return f"Use of undefined identifier '{node.value}'"

    return None

def _add_symbol(semdata, name, symtype, defnode):
    if name in semdata.symtbl:
        raise Exception(f"Internal error: symbol '{name}' already in symbol table.")
    semdata.symtbl[name] = SymbolData(symtype, defnode)

def _get_function_arg_count(defnode):
    return len(getattr(defnode, "children_formals", []))

def run_semantic_checks(ast_root):
    semdata = SemData()
    semdata.context = SemanticContext()
    visit_tree(ast_root, before_func=before_check, after_func=after_check, semdata=semdata)
    print("Semantic checks passed.")

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
        run_semantic_checks(result)
        print("Program ok.")
