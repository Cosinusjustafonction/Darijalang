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
    # Corrected precedence for if-else:
    # ILA_IFX (if-without-else) should have lower precedence
    # AWLA (else token) should have higher precedence to bind to the nearest if
    ('nonassoc', 'ILA_IFX'),       # For if-then (dangling if) - lower precedence
    ('nonassoc', 'AWLA'),          # For if-else: AWLA token itself - higher precedence
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
                 | statement"""
    p[0] = p[1]

# Function definition
def p_function_def(p):
    """function_def : TYPE ID LPAREN param_list RPAREN compound"""
    p[0] = FuncDef(return_type=p[1], name=p[2], params=p[4], body=p[6], line=p.slice[1].line)


# Refactored p_param_list
def p_param_list_production1(p):
    """param_list : param_list_nonempty"""
    p[0] = p[1]

def p_param_list_production2(p):
    """param_list : empty"""
    p[0] = []


def p_param_list_nonempty(p):
    """param_list_nonempty : TYPE ID
                            | TYPE ID COMMA param_list_nonempty"""
    if len(p) == 3:
        p[0] = [(p[1], p[2])]
    else:
        p[0] = [(p[1], p[2])] + p[4]

# Compound block
def p_compound(p):
    """compound : LBRACE stmt_list RBRACE"""
    p[0] = Compound(statements=p[2], line=p.slice[1].line)


def p_stmt_list(p):
    """stmt_list : stmt_list statement
                 | empty"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

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
                 | compound"""
    p[0] = p[1]

# Declaration

def p_declaration_stmt(p):
    """declaration_stmt : TYPE ID SEMI
                         | TYPE ID ASSIGN expression SEMI"""
    if len(p) == 4:
        p[0] = VarDecl(type_name=p[1], identifier=p[2], initializer=None, line=p.slice[1].line)
    else:
        p[0] = VarDecl(type_name=p[1], identifier=p[2], initializer=p[4], line=p.slice[1].line)

# Expression statement

def p_expression_stmt(p):
    """expression_stmt : expression SEMI"""
    p[0] = p[1]

# Expressions with assignment

def p_expression(p):
    """expression : assignment
                  | binary_expr"""
    p[0] = p[1]


def p_assignment(p):
    """assignment : ID ASSIGN expression"""
    p[0] = Assignment(identifier=p[1], value=p[3], line=p.slice[1].line)

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

# Unary minus rule
def p_binary_expr_uminus(p):
    """binary_expr : MINUS binary_expr %prec UMINUS"""
    p[0] = UnaryOp(op='-', operand=p[2], line=p.slice[1].line)

# Unary NOT rule
def p_binary_expr_machi(p):
    """binary_expr : MACHI binary_expr"""
    p[0] = UnaryOp(op=p[1], operand=p[2], line=p.slice[1].line)

# Parentheses and literals

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
        if tok.type == "NUMBER" or tok.type == "STRING" or tok.type == "BOOL" or tok.type == "NULL":
            p[0] = ConstLiteral(value=p[1], line=tok.line)
        elif tok.type == "ID":
            p[0] = Identifier(name=p[1], line=tok.line)
        else:  # func_call already built
            p[0] = p[1]
    else:
        p[0] = p[2]

# Function call

def p_func_call(p):
    """func_call : ID LPAREN arg_list RPAREN"""
    p[0] = FuncCall(name=p[1], args=p[3], line=p.slice[1].line)


def p_arg_list_production1(p):
    """arg_list : arg_list_nonempty"""
    p[0] = p[1]

def p_arg_list_production2(p):
    """arg_list : empty"""
    p[0] = []


def p_arg_list_nonempty(p):
    """arg_list_nonempty : expression
                          | expression COMMA arg_list_nonempty"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

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
    """for_stmt : KOULLA LPAREN opt_expr SEMI opt_expr SEMI opt_expr RPAREN statement"""
    p[0] = ForStmt(init=p[3], test=p[5], update=p[7], body=p[9], line=p.slice[1].line)


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

# Empty production

def p_empty(p):
    """empty :"""
    p[0] = None

# Error rule

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' (line {p.line}, type {p.type})")  # Added p.type
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
        except FileNotFoundError:
            print(f"File not found: {source_path}")
            sys.exit(1)
    else:
        print("Paste DarijaLang program (Ctrl‑D/Ctrl‑Z to finish):")
        code = sys.stdin.read()

    ast = parse(code)
    print("Parsed AST:\n", ast)
