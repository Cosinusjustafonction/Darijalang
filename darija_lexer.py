#!/usr/bin/env python3
"""darija_lexer.py  ▸ DarijaLang Lexer (Phase 2)

▶ Revision 2 – handles:
   • HTML tags correctly BEFORE treating '<' / '>' as symbols
   • C‑style escaped strings like \"Salam!\"  ➜ token STRING("Salam!")
   • Interactive mode + clearer lexer errors

Usage
-----
    python darija_lexer.py hello.darija
    # or just run without args and paste code
"""
from __future__ import annotations
import re, sys
from typing import List, Iterator, Optional, Any

class Token:
    def __init__(self, type: str, value: Any, line: int, column: int, lexpos: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.lexpos = lexpos

    def __repr__(self):
        return f"Token(type='{self.type}', value={self.value!r}, line={self.line}, column={self.column}, lexpos={self.lexpos})"

# Define token types for PLY. This list must include all terminals used by the parser.
tokens = (
    # Literals
    'ID', 'NUMBER', 'STRING',
    'BOOL',  # For true/false literals: bssa7, machibssa7
    'NULL',  # For null literal: walou

    # Type Keyword (generic)
    'TYPE',  # For "int", "float", "char", "bool", "string", "faragh"

    # Control flow & other specific Keywords
    'ILA', 'AWLA', 'MNINTCHOUF', 'KOULLA', 'HRASS', 'KML', 'RJ3',

    # OOP Keywords
    'CLASS', 'EXTENDS', 'PUBLIC', 'PRIVATE',
    
    # Data structure Keywords
    'DICT', 'KEY',

    # Error handling keywords
    'TRY', 'CATCH', 'THROW', 'EXCEPTION',

    # Symbols / Operators
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET', 'COMMA', 'SEMI', 'DOT', 'COLON',
    'ASSIGN',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'UMINUS',  # Token for unary minus precedence

    # Logical Operators
    'OU',             # && (AND)
    'AWLA_LOGICAL',   # || (OR)
    'MACHI',          # !  (NOT)

    # Relational Operators
    'LT',             # <
    'GT',             # >
    'LE',             # <=
    'GE',             # >=
    'EQ',             # ==
    'NE',             # !=

    # Dummy token for if/else precedence
    'ILA_IFX',
)

# Keyword and Symbol Mapping
_TYPE_KEYWORDS = {"int", "float", "char", "bool", "string", "faragh", "list", "ktab"}
_CONTROL_KEYWORDS_MAP = {
    "ila": "ILA", "awla": "AWLA", "mnintchouf": "MNINTCHOUF",
    "koulla": "KOULLA", "hrass": "HRASS", "kml": "KML", "rj3": "RJ3",
    # Add logical operator keywords here
    "ou": "OU",          # Keyword for logical AND
    "machi": "MACHI",    # Keyword for logical NOT
    # OOP keywords
    "9ism": "CLASS",      # Class definition
    "kikml": "EXTENDS",   # Inheritance
    "m3rof": "PUBLIC",    # Public access
    "mkhabi": "PRIVATE",  # Private access
    # Data structure keywords
    "sarout": "KEY",      # Dictionary key
    # Error handling keywords
    "7awl": "TRY",        # Try block
    "chd": "CATCH",       # Catch block
    "lou7": "THROW",      # Throw statement
    "3ajib": "EXCEPTION", # Exception
    # Note: AWLA_LOGICAL for '||' is distinct from AWLA for 'else'
}
_LITERAL_KEYWORDS_MAP = {
    "bssa7": ("BOOL", True),
    "machibssa7": ("BOOL", False),
    "walou": ("NULL", "walou"),
}
_SYMBOLS_MAP = {
    '(': 'LPAREN', ')': 'RPAREN', '{': 'LBRACE', '}': 'RBRACE',
    '[': 'LBRACKET', ']': 'RBRACKET', ',': 'COMMA', ';': 'SEMI',
    '.': 'DOT', ':': 'COLON', '=': 'ASSIGN',
    '+': 'PLUS', '-': 'MINUS', '*': 'TIMES', '/': 'DIVIDE',
}

# Add special handling for Arabic-numeral-containing keywords
_SPECIAL_KEYWORDS = {
    "7awl": "TRY",       # Try block
    "3ajib": "EXCEPTION"  # Exception type
}

# Regex patterns --------------------------------------------------------------
TAG_RE      = re.compile(r"<[^>]+>")                             # HTML‑style tag
# ESC_STRING  = re.compile(r'"((?:\\.|[^"\\])*)"')               # Old regex, kept for reference
NUMBER_RE   = re.compile(r"\d+(?:\.\d+)?")
ID_RE       = re.compile(r"[A-Za-z_][\w]*")
SPECIAL_ID_RE = re.compile(r"[0-9][A-Za-z_]+")  # For identifiers starting with numbers
WHITESPACE  = re.compile(r"[ \t\r]+")
COMMENT_RE  = re.compile(r"//[^\n]*")

# ─── Core lexer ─────────────────────────────────────────────────────────────

def tokenize(code: str) -> Iterator[Token]:
    line = 1
    col0 = 0  # index of line start in code
    i = 0
    n = len(code)

    def column(pos: int) -> int:
        return pos - col0 + 1

    while i < n:
        char_i = code[i]

        # Handle newlines fast
        if char_i == "\n":
            line += 1
            i += 1
            col0 = i
            continue

        # Skip whitespace
        m = WHITESPACE.match(code, i)
        if m:
            i = m.end()
            continue

        # Skip comments
        m = COMMENT_RE.match(code, i)
        if m:
            i = m.end()
            continue

        # Skip HTML‑style tags <...>
        if char_i == "<":
            tag_match = TAG_RE.match(code, i)
            if tag_match:
                i = tag_match.end()
                continue

        # Check for multi-character operators first (logical and relational)
        # Relational
        if code[i:i+2] == '<=':
            yield Token('LE', '<=', line, column(i), i)
            i += 2
            continue
        if code[i:i+2] == '>=':
            yield Token('GE', '>=', line, column(i), i)
            i += 2
            continue
        if code[i:i+2] == '==':
            yield Token('EQ', '==', line, column(i), i)
            i += 2
            continue
        if code[i:i+2] == '!=':
            yield Token('NE', '!=', line, column(i), i)
            i += 2
            continue
        # Logical Symbols (still support && and || if desired, keywords will take precedence for "ou", "machi")
        if code[i:i+2] == '&&':
            yield Token('OU', '&&', line, column(i), i) # Symbol for AND
            i += 2
            continue
        if code[i:i+2] == '||':
            yield Token('AWLA_LOGICAL', '||', line, column(i), i) # Symbol for OR
            i += 2
            continue
        
        # Check for single-character operators (logical NOT symbol)
        # Note: 'machi' keyword for NOT is handled by _CONTROL_KEYWORDS_MAP
        if char_i == '!': # Symbol for NOT
            yield Token('MACHI', '!', line, column(i), i)
            i += 1
            continue
        if char_i == '<':
            yield Token('LT', '<', line, column(i), i)
            i += 1
            continue
        if char_i == '>':
            yield Token('GT', '>', line, column(i), i)
            i += 1
            continue

        # Single-character symbols
        if char_i in _SYMBOLS_MAP:
            op_val = char_i
            op_type = _SYMBOLS_MAP[op_val]
            yield Token(op_type, op_val, line, column(i), i)
            i += 1
            continue

        # String literal - Manual parsing logic
        if char_i == '"':
            start_pos = i
            start_line = line
            start_col = column(i)
            
            i += 1 # Move past the opening quote
            str_content_chars = []
            # print(f"DEBUG: Entered string parsing at line {start_line}, col {start_col}") # Optional: debug entry
            
            while i < n:
                current_char_in_string = code[i]
                # print(f"DEBUG: String char: {current_char_in_string!r}, i={i}, line={line}") # DEBUG PRINT
                
                if current_char_in_string == '"': # Closing quote
                    i += 1 # Move past the closing quote
                    # print(f"DEBUG: Found closing quote. Content: {''.join(str_content_chars)}") # Optional: debug exit
                    yield Token("STRING", "".join(str_content_chars), start_line, start_col, start_pos)
                    break # String tokenized successfully
                elif current_char_in_string == '\\': # Escape sequence
                    i += 1 # Move past backslash
                    if i < n:
                        escaped_char = code[i]
                        if escaped_char == 'n':
                            str_content_chars.append('\n')
                        elif escaped_char == '"':
                            str_content_chars.append('"')
                        elif escaped_char == '\\':
                            str_content_chars.append('\\')
                        # Add other common escapes if needed, e.g., \t for tab
                        else:
                            # If not a recognized escape, treat as literal backslash followed by the character
                            str_content_chars.append('\\')
                            str_content_chars.append(escaped_char) 
                        i += 1 # Move past the escaped character
                    else: # EOF after backslash - unterminated string
                        break # Break to outer loop's EOF check for unterminated string
                elif current_char_in_string == '\n':
                    # Handling of unescaped newlines in strings:
                    # Option 1: Disallow (raise error)
                    # Option 2: Allow (as done here, for simplicity or multiline strings)
                    str_content_chars.append(current_char_in_string)
                    line += 1
                    col0 = i + 1
                    i += 1
                else: # Regular character in string (like a period)
                    # print(f"DEBUG: Appending regular char: {current_char_in_string!r}") # Optional: debug append
                    str_content_chars.append(current_char_in_string)
                    i += 1
            else: # Outer while loop finished because i >= n (EOF)
                if start_pos < n and code[start_pos] == '"': # Check if we actually started parsing a string
                    # This means an unterminated string literal
                    context_char_at_start = code[start_pos]
                    error_message_unterminated = (
                        f"Unterminated string literal starting at line {start_line} col {start_col} (pos {start_pos}).\n"
                        f"String began with: {context_char_at_start}"
                    )
                    raise SyntaxError(error_message_unterminated)
            continue # Continue to the next tokenization attempt from the main loop

        # Check for special keywords that start with numbers (like 7awl, 3ajib)
        if char_i.isdigit():
            m = SPECIAL_ID_RE.match(code, i)
            if m:
                lexeme = m.group(0)
                tok_line = line
                tok_col = column(i)
                tok_lexpos = i
                i = m.end()
                
                # Check if it's a special keyword
                if lexeme in _SPECIAL_KEYWORDS:
                    yield Token(_SPECIAL_KEYWORDS[lexeme], lexeme, tok_line, tok_col, tok_lexpos)
                    continue
                # If not a special keyword, fall through to number handling

        # Number literal
        m = NUMBER_RE.match(code, i)
        if m:
            num_str = m.group(0)
            try:
                val = int(num_str) if '.' not in num_str else float(num_str)
            except ValueError:
                val = num_str
            yield Token("NUMBER", val, line, column(i), i)
            i = m.end()
            continue

        # Identifier / keyword
        m = ID_RE.match(code, i)
        if m:
            lexeme = m.group(0)
            tok_line = line
            tok_col = column(i)
            tok_lexpos = i
            i = m.end()

            if lexeme in _TYPE_KEYWORDS:
                yield Token("TYPE", lexeme, tok_line, tok_col, tok_lexpos)
            elif lexeme in _CONTROL_KEYWORDS_MAP:
                yield Token(_CONTROL_KEYWORDS_MAP[lexeme], lexeme, tok_line, tok_col, tok_lexpos)
            elif lexeme in _LITERAL_KEYWORDS_MAP:
                tok_type, tok_val = _LITERAL_KEYWORDS_MAP[lexeme]
                yield Token(tok_type, tok_val, tok_line, tok_col, tok_lexpos)
            else:
                yield Token("ID", lexeme, tok_line, tok_col, tok_lexpos)
            continue

        # If nothing matched
        # More detailed error context:
        context_before = code[max(0, i-30):i]
        context_after = code[i+1:i+31]
        error_message = (
            f"Unexpected character {code[i]!r} at line {line} col {column(i)} (pos {i}).\n"
            f"Context: ...'{context_before}' [ERROR_CHAR:'{code[i]}'] '{context_after}'..."
        )
        raise SyntaxError(error_message)

# ─── PLY Lexer Wrapper ───────────────────────────────────────────────────────

class LexerWrapper:
    def __init__(self, tokenizer_func):
        self.tokenizer_func = tokenizer_func
        self.token_stream = iter([])
        self._lineno = 1

    def input(self, data: str):
        processed_data = data.replace("<br>", "\n")
        self.token_stream = self.tokenizer_func(processed_data)
        self._lineno = 1

    def token(self) -> Optional[Token]:
        try:
            tok = next(self.token_stream)
            self._lineno = tok.line
            return tok
        except StopIteration:
            return None

    @property
    def lineno(self):
        return self._lineno

    @lineno.setter
    def lineno(self, value):
        self._lineno = value

# Instantiate the lexer for PLY parser to use via "lexmod.lexer"
lexer = LexerWrapper(tokenize)

# ─── CLI helper ──────────────────────────────────────────────────────────────

def _read_source(path: Optional[str]) -> str:
    if path:
        try:
            with open(path, "r", encoding="utf‑8") as f:
                content = f.read()
                content = content.replace("<br>", "\n")
                return content
        except FileNotFoundError:
            print(f"⚠️  File not found: {path}\nSwitching to interactive mode. Paste code then Ctrl‑D / Ctrl‑Z.\n", file=sys.stderr)
    print(">>> DarijaLang interactive input <<<", file=sys.stderr)
    return sys.stdin.read()

def main(argv: List[str]) -> None:
    src = _read_source(argv[1] if len(argv) > 1 else None)
    try:
        for tok in tokenize(src):
            print(tok)
    except SyntaxError as e:
        print(f"Lexer error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)