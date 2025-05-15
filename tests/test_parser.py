# tests/test_parser.py
from darija_parser import parse
from darija_parser import BinOp, UnaryOp, Identifier, ConstLiteral
code = """
faragh check() {
    bool a = bssa7;
    bool b = machibssa7;
    ila (a && !b || 1 == 0) {
        hrass;
    }
}
"""

def test_logical_ast_shape():
    ast = parse(code)        # returns Program(AST)

    # Program->FuncDef->Body->If
    func_def_node = ast.body[0]      # Program.body contains top-level nodes
    if_stmt = func_def_node.body.statements[2]   # FuncDef.body is Compound, access its statements list

    # The condition should be BinOp('||')
    assert isinstance(if_stmt.test, BinOp)
    assert if_stmt.test.op == '||'

    # Left child should be BinOp('&&')
    left = if_stmt.test.left
    assert isinstance(left, BinOp) and left.op == '&&'

    # Ensure NOT captured as UnaryOp
    assert isinstance(left.right, UnaryOp) and left.right.op == '!'

    # Right side of top OR: equality check -> BinOp('==')
    right = if_stmt.test.right
    assert isinstance(right, BinOp) and right.op == '=='

def test_parser_no_syntax_error():
    # The same code should round-trip without throwing
    parse(code)
