# tests/test_lexer.py
from darija_lexer import tokenize, Token

sample = 'bool a = bssa7 && !machibssa7 || faragh;'

def test_logical_tokens():
    tokens = list(tokenize(sample))
    values = [t.value for t in tokens]

    # Quick sanity: the operator symbols must be present
    assert '&&' in values, 'AND operator missing'
    assert '!'  in values, 'NOT operator missing'
    assert '||' in values, 'OR operator missing'

    # Precise ordering check (keyword / ident / symbols)
    expected = [
        'bool', 'a', '=', True, '&&',
        '!', False, '||', 'faragh', ';'
    ]
    assert values == expected
