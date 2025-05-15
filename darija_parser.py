#!/usr/bin/env python3
"""darija_parser.py  ▸ DarijaLang Parser (Phase 3)

Uses PLY (Python Lex‑Yacc) to transform the DarijaLang token stream
into an Abstract Syntax Tree (AST).

▸ Requirements
  pip install ply

▸ Design notes
  • The lexer from darija_lexer.py is imported and reused.
  • The AST is represented with simple @dataclass nodes for clarity.
  • Only a minimal C‑like subset is implemented: variable declarations,
    assignments, arithmetic expressions, function definitions, if/else,
    while, for, break/continue, return, and I/O calls.
  • A Program node wraps a list of top‑level declarations/definitions.

Feel free to extend grammar rules or AST node classes as you add
features (arrays, structs, etc.).
"""
from __future__ import annotations

import ply.yacc as yacc
from dataclasses import dataclass, field
from typing import List, Any

# ──────────────────────────────────────────────────────────────────────
# 1.  Re‑use lexer tokens
# ──────────────────────────────────────────────────────────────────────
import darija_lexer as lexmod

tokens = lexmod.tokens

# ──────────────────────────────────────────────────────────────────────
# 2.  AST Node definitions
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Node:
    line: int

@dataclass
class Program(Node):
    body: List[Node]

@dataclass
class VarDecl(Node):
    type_name: str
    identifier: str
    initializer: Any | None

@dataclass
class ConstLiteral(Node):
    value: Any

@dataclass
class Identifier(Node):
    name: str

@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class Assignment(Node):
    identifier: str
    value: Node

@dataclass
class IfStmt(Node):
    test: Node
    consequent: Node
    alternate: Node | None

@dataclass
class WhileStmt(Node):
    test: Node
    body: Node

@dataclass
class ForStmt(Node):
    init: Node | None
    test: Node | None
    update: Node | None
    body: Node

@dataclass
class BreakStmt(Node):
    pass

@dataclass
class ContinueStmt(Node):
    pass

@dataclass
class ReturnStmt(Node):
    value: Node | None

@dataclass
class Compound(Node):
    statements: List[Node]

@dataclass
class FuncCall(Node):
    name: str
    args: List[Node]

@dataclass
class FuncDef(Node):
    return_type: str
    name: str
    params: List[tuple]
    body: Compound

@dataclass
class ArrayExpr(Node):
    elements: List[Node]

@dataclass
class ArrayAccess(Node):
    array: Node
    index: Node

@dataclass
class DictExpr(Node):
    keys: List[Node]
    values: List[Node]

@dataclass
class DictAccess(Node):
    dict_expr: Node
    key: Node

@dataclass
class ClassDef(Node):
    name: str
    parent: str | None
    body: List[Node]

@dataclass
class MemberAccess(Node):
    object: Node
    member: str

@dataclass
class MethodCall(Node):
    object: Node
    method: str
    args: List[Node]

@dataclass
class Property(Node):
    type_name: str
    name: str
    access: str  # 'public' or 'private'
    initializer: Any | None

@dataclass
class Method(Node):
    return_type: str
    name: str
    params: List[tuple]
    body: Compound
    access: str  # 'public' or 'private'

@dataclass
class TryStmt(Node):
    body: Compound
    handlers: List[CatchClause]

@dataclass
class CatchClause(Node):
    param_type: str
    param_name: str
    body: Compound

@dataclass
class ThrowStmt(Node):
    expression: Node

# ──────────────────────────────────────────────────────────────────────
# 3.  Operator precedence
# ──────────────────────────────────────────────────────────────────────
precedence = (
    ('left', 'AWLA_LOGICAL'),      # Logical OR (||)
    ('left', 'OU'),                # Logical AND (&&)
    ('left', 'EQ', 'NE'),          # Equality operators (==, !=)
    ('left', 'LT', 'LE', 'GT', 'GE'), # Relational operators (<, <=, >, >=)
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS"),           # Unary minus
    ("right", "MACHI"),            # Logical NOT (!)
    ('nonassoc', 'ILA_IFX'),       # For if-then (dangling if) - lower precedence
    ('nonassoc', 'AWLA'),          # For if-else: AWLA token itself - higher precedence
    ("left", "DOT"),               # Member access has high precedence
)

# ──────────────────────────────────────────────────────────────────────
# 4.  Grammar rules (p_*)
# ──────────────────────────────────────────────────────────────────────

def p_program(p):
    """program : external_list"""
    p[0] = Program(body=p[1], line=1)


def p_external_list(p):
    """external_list : external external_list
                     | empty"""
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else: # empty
        p[0] = []


def p_external(p):
    """external : function_def
                 | statement
                 | class_def"""
    p[0] = p[1]

# Function definition
def p_function_def(p):
    """function_def : TYPE ID LPAREN param_list RPAREN compound"""
    p[0] = FuncDef(return_type=p[1], name=p[2], params=p[4], body=p[6], line=p.slice[1].line)

def p_param_list(p):
    """param_list : param_list_nonempty
                  | empty"""
    p[0] = p[1]

def p_param_list_nonempty(p):
    """param_list_nonempty : TYPE ID
                            | TYPE ID COMMA param_list_nonempty"""
    if len(p) == 3:
        p[0] = [(p[1], p[2])]
    else:
        p[0] = [(p[1], p[2])] + p[4]

# Function call and argument list rules
def p_func_call(p):
    """func_call : ID LPAREN arg_list RPAREN"""
    p[0] = FuncCall(name=p[1], args=p[3], line=p.slice[1].line)

def p_arg_list(p):
    """arg_list : arg_list_nonempty
                | empty"""
    if p[1] is None:  # empty case
        p[0] = []
    else:  # non-empty case
        p[0] = p[1]

def p_arg_list_nonempty(p):
    """arg_list_nonempty : expression
                          | expression COMMA arg_list_nonempty"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

# Compound block
def p_compound(p):
    """compound : LBRACE stmt_list RBRACE"""
    p[0] = Compound(statements=p[2], line=p.slice[1].line)

# Fix the statement list handling to be more robust
def p_stmt_list(p):
    """stmt_list : statement stmt_list
                 | empty"""
    if len(p) == 3:
        if p[2] is None:
            p[0] = [p[1]]  # Single statement case
        else:
            p[0] = [p[1]] + p[2]  # Multiple statements case
    else:
        p[0] = []  # Empty case

# Statements umbrella
def p_statement(p):
    """statement : declaration_stmt
                 | expression_stmt
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | return_stmt
                 | break_stmt
                 | continue_stmt
                 | compound
                 | try_stmt
                 | throw_stmt"""
    p[0] = p[1]

# Declaration
def p_declaration_stmt(p):
    """declaration_stmt : TYPE ID SEMI
                         | TYPE ID ASSIGN expression SEMI"""
    if len(p) == 4:
        p[0] = VarDecl(type_name=p[1], identifier=p[2], initializer=None, line=p.slice[1].line)
    else:
        p[0] = VarDecl(type_name=p[1], identifier=p[2], initializer=p[4], line=p.slice[1].line)

# Add proper array declaration support
def p_declaration_stmt_array(p):
    """declaration_stmt : TYPE ID LBRACKET NUMBER RBRACKET SEMI"""
    line_num = getattr(p.lexer, "lineno", 0)
    # Create a VarDecl with special array type notation
    p[0] = VarDecl(type_name=f"{p[1]}[]", identifier=p[2], initializer=None, line=line_num)

# Expression statement
def p_expression_stmt(p):
    """expression_stmt : expression SEMI"""
    p[0] = p[1]

# Add explicit rule for function calls in expression statements
def p_expression_stmt_func_call(p):
    """expression_stmt : func_call SEMI"""
    p[0] = p[1]

# Expressions with assignment
def p_expression(p):
    """expression : assignment
                  | binary_expr"""
    p[0] = p[1]

def p_assignment(p):
    """assignment : ID ASSIGN expression"""
    p[0] = Assignment(identifier=p[1], value=p[3], line=p.slice[1].line)

# Add array element assignment support
def p_assignment_array_element(p):
    """assignment : ID LBRACKET expression RBRACKET ASSIGN expression"""
    line_num = getattr(p.lexer, "lineno", 0)
    # Create an array access identifier first
    array_access = ArrayAccess(array=Identifier(name=p[1], line=line_num), index=p[3], line=line_num)
    # Then create an assignment to this array element
    p[0] = Assignment(identifier=f"{p[1]}[{p[3]}]", value=p[6], line=line_num)

# Binary arithmetic
def p_binary_expr(p):
    """binary_expr : binary_expr PLUS binary_expr
                   | binary_expr MINUS binary_expr
                   | binary_expr TIMES binary_expr
                   | binary_expr DIVIDE binary_expr
                   | binary_expr OU binary_expr
                   | binary_expr AWLA_LOGICAL binary_expr
                   | binary_expr LT binary_expr
                   | binary_expr LE binary_expr
                   | binary_expr GT binary_expr
                   | binary_expr GE binary_expr
                   | binary_expr EQ binary_expr
                   | binary_expr NE binary_expr"""
    p[0] = BinOp(op=p[2], left=p[1], right=p[3], line=p.slice[2].line)

def p_binary_expr_uminus(p):
    """binary_expr : MINUS binary_expr %prec UMINUS"""
    p[0] = UnaryOp(op='-', operand=p[2], line=p.slice[1].line)

def p_binary_expr_machi(p):
    """binary_expr : MACHI binary_expr"""
    p[0] = UnaryOp(op='!', operand=p[2], line=p.slice[1].line)

# Fix the binary_expr_factor function to properly handle literals and function calls
def p_binary_expr_factor(p):
    """binary_expr : LPAREN expression RPAREN
                   | NUMBER
                   | STRING
                   | BOOL
                   | NULL
                   | ID
                   | func_call"""
    if len(p) == 2:
        tok = p.slice[1]
        if tok.type == "NUMBER":
            p[0] = ConstLiteral(value=p[1], line=tok.line)
        elif tok.type == "STRING":
            p[0] = ConstLiteral(value=p[1], line=tok.line)
        elif tok.type == "BOOL":
            p[0] = ConstLiteral(value=p[1], line=tok.line)
        elif tok.type == "NULL":
            p[0] = ConstLiteral(value=p[1], line=tok.line)
        elif tok.type == "ID":
            p[0] = Identifier(name=p[1], line=tok.line)
        else:  # func_call already built
            p[0] = p[1]
    else:
        p[0] = p[2]  # For parenthesized expressions

# If / else
def p_if_stmt(p):
    """if_stmt : ILA LPAREN expression RPAREN statement AWLA statement
               | ILA LPAREN expression RPAREN statement %prec ILA_IFX"""
    if len(p) == 8: # ILA ... AWLA ...
        p[0] = IfStmt(test=p[3], consequent=p[5], alternate=p[7], line=p.slice[1].line)
    else: # ILA ... (no AWLA)
        p[0] = IfStmt(test=p[3], consequent=p[5], alternate=None, line=p.slice[1].line)

# While
def p_while_stmt(p):
    """while_stmt : MNINTCHOUF LPAREN expression RPAREN statement"""
    p[0] = WhileStmt(test=p[3], body=p[5], line=p.slice[1].line)

# For
def p_for_stmt(p):
    """for_stmt : KOULLA LPAREN expression SEMI expression SEMI expression RPAREN statement"""
    p[0] = ForStmt(init=p[3], test=p[5], update=p[7], body=p[9], line=p.slice[1].line)

# Make the opt_expr rule more robust
def p_opt_expr(p):
    """opt_expr : expression
                | empty"""
    p[0] = p[1]

# Break / Continue / Return
def p_break_stmt(p):
    """break_stmt : HRASS SEMI"""
    p[0] = BreakStmt(line=p.slice[1].line)

def p_continue_stmt(p):
    """continue_stmt : KML SEMI"""
    p[0] = ContinueStmt(line=p.slice[1].line)

def p_return_stmt(p):
    """return_stmt : RJ3 opt_expr SEMI"""
    p[0] = ReturnStmt(value=p[2], line=p.slice[1].line)

# Array/List related rules
def p_binary_expr_array(p):
    """binary_expr : LBRACKET arg_list RBRACKET"""
    p[0] = ArrayExpr(elements=p[2], line=p.slice[1].line)

# Fix the array access expression to handle line information correctly
def p_binary_expr_array_access(p):
    """binary_expr : binary_expr LBRACKET expression RBRACKET"""
    # Use p.lineno instead of p.slice[1].line if available, otherwise default to 0
    line_num = getattr(p.lexer, "lineno", 0)
    p[0] = ArrayAccess(array=p[1], index=p[3], line=line_num)

# Dictionary related rules
def p_binary_expr_dict(p):
    """binary_expr : LBRACE dict_items RBRACE"""
    keys, values = p[2] if p[2] else ([], [])
    p[0] = DictExpr(keys=keys, values=values, line=p.slice[1].line)

def p_dict_items(p):
    """dict_items : dict_item_list
                  | empty"""
    if p[1] is None:
        p[0] = ([], [])
    else:
        p[0] = p[1]

def p_dict_item_list(p):
    """dict_item_list : dict_item
                      | dict_item COMMA dict_item_list"""
    if len(p) == 2:
        key, value = p[1]
        p[0] = ([key], [value])
    else:
        key, value = p[1]
        keys, values = p[3]
        p[0] = ([key] + keys, [value] + values)

def p_dict_item(p):
    """dict_item : expression COLON expression"""
    p[0] = (p[1], p[3])

# Class related rules
def p_class_def(p):
    """class_def : CLASS ID class_inheritance LBRACE class_body RBRACE"""
    p[0] = ClassDef(name=p[2], parent=p[3], body=p[5], line=p.slice[1].line)

def p_class_inheritance(p):
    """class_inheritance : EXTENDS ID
                         | empty"""
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

def p_class_body(p):
    """class_body : class_member class_body
                  | empty"""
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_class_member(p):
    """class_member : property_decl
                    | method_decl"""
    p[0] = p[1]

def p_property_decl(p):
    """property_decl : access_modifier TYPE ID SEMI
                     | access_modifier TYPE ID ASSIGN expression SEMI"""
    if len(p) == 5:
        p[0] = Property(type_name=p[2], name=p[3], access=p[1], initializer=None, line=p.slice[2].line)
    else:
        p[0] = Property(type_name=p[2], name=p[3], access=p[1], initializer=p[5], line=p.slice[2].line)

def p_method_decl(p):
    """method_decl : access_modifier TYPE ID LPAREN param_list RPAREN compound"""
    p[0] = Method(return_type=p[2], name=p[3], params=p[5], body=p[7], access=p[1], line=p.slice[2].line)

def p_access_modifier(p):
    """access_modifier : PUBLIC
                       | PRIVATE
                       | empty"""
    if p[1] == 'm3rof':
        p[0] = 'public'
    elif p[1] == 'mkhabi':
        p[0] = 'private'
    else:
        p[0] = 'public'  # Default to public

def p_binary_expr_member_access(p):
    """binary_expr : binary_expr DOT ID"""
    p[0] = MemberAccess(object=p[1], member=p[3], line=p.slice[2].line)

def p_binary_expr_method_call(p):
    """binary_expr : binary_expr DOT ID LPAREN arg_list RPAREN"""
    p[0] = MethodCall(object=p[1], method=p[3], args=p[5], line=p.slice[2].line)

# Try-catch statement
def p_try_stmt(p):
    """try_stmt : TRY compound catch_clauses"""
    p[0] = TryStmt(body=p[2], handlers=p[3], line=p.slice[1].line)

def p_catch_clauses(p):
    """catch_clauses : catch_clause catch_clauses
                     | catch_clause"""
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

# Update catch clause to fix syntax:
def p_catch_clause(p):
    """catch_clause : CATCH LPAREN EXCEPTION ID RPAREN compound"""
    p[0] = CatchClause(param_type='exception', param_name=p[4], body=p[6], line=p.slice[1].line)

# Throw statement
def p_throw_stmt(p):
    """throw_stmt : THROW expression SEMI"""
    p[0] = ThrowStmt(expression=p[2], line=p.slice[1].line)

# Empty production
def p_empty(p):
    """empty :"""
    p[0] = None

# Fix the error handling function
def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' (line {p.line}, type {p.type})")
        
        # Try to provide more context about the error
        expected = []
        
        # Check what state we're in
        state = parser.statestack[-1] if hasattr(parser, 'statestack') and parser.statestack else None
        if state is not None:
            # Get the valid tokens that could appear next
            try:
                for token_idx in parser.action[state].keys():
                    if isinstance(token_idx, int) and token_idx > 0:
                        token_name = parser.symtab[token_idx]
                        if token_name not in expected:
                            expected.append(token_name)
            except (KeyError, AttributeError, TypeError) as e:
                print(f"Error while getting expected tokens: {e}")
            
            if expected:
                print(f"Expected one of: {', '.join(expected)}")
    else:
        print("Syntax error at EOF")

# ──────────────────────────────────────────────────────────────────────
# 5.  Build parser entry‑point
# ──────────────────────────────────────────────────────────────────────

parser = yacc.yacc(start="program", debug=True)

def parse(src: str) -> Program:
    lexmod.lexer.lineno = 1
    return parser.parse(src, lexer=lexmod.lexer)

# ──────────────────────────────────────────────────────────────────────
# 6.  CLI for quick testing
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        source_path = sys.argv[1]
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                code = f.read()
            ast = parse(code)
            print("Parsed AST:\n", ast)
        except FileNotFoundError:
            print(f"File not found: {source_path}")
            sys.exit(1)
    else:
        print("Paste DarijaLang program (Ctrl‑D/Ctrl‑Z to finish):")
        code = sys.stdin.read()
        ast = parse(code)
        print("Parsed AST:\n", ast)