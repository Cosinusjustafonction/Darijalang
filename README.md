# This is a project for the Language Theory class Professor Youness Moukafih
# DarijaLang: A Comprehensive Guide

DarijaLang is a compiled programming language with syntax inspired by Darija, the Arabic dialect spoken in Morocco. It combines traditional programming constructs with culturally-relevant keywords to create a unique language that serves both as an educational tool and a practical programming language.

## Table of Contents
1. [Introduction](#introduction)
2. [Compiler Architecture](#compiler-architecture)
3. [Lexical Analysis](#lexical-analysis)
4. [Syntax Analysis](#syntax-analysis)
5. [Intermediate Representation](#intermediate-representation)
6. [Code Generation](#code-generation)
7. [Runtime Support](#runtime-support)
8. [Language Features](#language-features)
9. [Error Handling](#error-handling)
10. [Testing and Development](#testing-and-development)
11. [Usage Guide](#usage-guide)

## Introduction

The DarijaLang compiler translates source code into C, which is then compiled to machine code using a standard C compiler (gcc/clang). This approach, known as source-to-source compilation or "transpilation," allows DarijaLang to leverage the optimization capabilities and cross-platform support of existing C compilers while maintaining its own unique syntax and features.

### Key Features

- **Culturally-relevant keywords**: Control structures and concepts use Darija-based terminology
    - Example: `ila` (if), `awla` (else), `mnintchouf` (while), `koulla` (for), `7awl` (try), `chd` (catch)
- **C-like core syntax**: Familiar programming paradigm with enhanced readability
- **Strong type system**: Static typing with clear type declarations
    - Supported types: `int`, `float`, `string`, `bool`, and others
- **Rich control flow**: If/else statements, loops, and functions
- **Error handling**: Try-catch-throw mechanism using culturally-relevant keywords (7awl/chd/lou7)
- **Data structures**: Support for arrays and dictionaries
- **Object-oriented features**: Classes, inheritance, and access modifiers (m3rof/mkhabi)

### Example: Hello World in DarijaLang

```
tba3("Salam Darija!");
```

### Example: Variable Declaration and Control Flow

```
int x = 10;
string name = "Ahmed";

ila (x > 5) {
        tba3("X kbir men 5: " + x);
} awla {
        tba3("X sghir men wla equal l 5: " + x);
}
```

## Compiler Architecture

The DarijaLang compiler follows a traditional multi-phase compiler design:

1. **Lexical Analysis**: Source code → Tokens
2. **Syntax Analysis**: Tokens → Abstract Syntax Tree (AST)
3. **Intermediate Representation**: AST → IR Code
4. **Code Generation**: IR → C Code
5. **Compilation**: C Code → Machine Code

This design separates concerns and makes the compiler more maintainable and extensible. Each phase has a specific role and communicates with subsequent phases through well-defined interfaces.

### Phases in Detail

1. **Lexical Analysis (Lexer)**: This first phase breaks down the source code into a series of tokens. Tokens represent the smallest meaningful units in a programming language, like keywords, identifiers, operators, and literals.

     **Example:** The code `int x = 5;` would be tokenized as:
     ```
     [TOKEN(TYPE, "int"), TOKEN(ID, "x"), TOKEN(ASSIGN, "="), TOKEN(NUMBER, 5), TOKEN(SEMICOLON, ";")]
     ```

2. **Syntax Analysis (Parser)**: This phase takes the token stream and organizes it into a hierarchical structure called an Abstract Syntax Tree (AST). The AST represents the grammatical structure of the program.

     **Example AST** for `int x = 5;`:
     ```
     VarDecl(
         type_name="int",
         identifier="x",
         initializer=NumberLiteral(value=5),
         line=1
     )
     ```

3. **Intermediate Representation (IR)**: The AST is transformed into a lower-level representation that's closer to the target language. This simplifies code generation and enables optimization.

     **Example IR** for `int x = 5;`:
     ```
     IRVarDecl(name="x", type="int")
     IRAssign(target="x", value=5)
     ```

4. **Code Generation (Emitter)**: This phase converts the IR into C code that can be compiled by a standard C compiler.

     **Example C code** generated from IR:
     ```c
     int x;
     x = 5;
     ```

5. **Compilation**: The generated C code is compiled to machine code using gcc/clang.

     **Example command**:
     ```bash
     gcc -o program program.c
     ```

### Visual Representation of the Compilation Pipeline

```
Source Code → [Lexer] → Tokens → [Parser] → AST → [IR Generator] → IR → [C Emitter] → C Code → [GCC/Clang] → Executable
```

## Lexical Analysis

The lexical analyzer (`darija_lexer.py`) transforms source code into tokens using regular expressions and pattern matching. It's the first phase of compilation and serves as the interface between raw text and structured compiler data.

### Key Components

#### Token Definition
A `Token` is defined as a Python class with five fields:
- `type`: The category of the token (e.g., "ID", "NUMBER", "LPAREN")
- `value`: The actual value of the token (e.g., "x", 42, "(")
- `line`: Line number where the token appears
- `column`: Column number where the token starts
- `lexpos`: Character offset in the input string

```python
@dataclass
class Token:
        type: str
        value: Any
        line: int
        column: int
        lexpos: int
        
        def __repr__(self):
                return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.column})"
```

#### Language Specification 

The lexer defines several mappings and patterns to recognize different types of tokens:

1. **Token Types**: A tuple listing all valid token type names

     ```python
     _TOKEN_TYPES = (
             'ID', 'NUMBER', 'STRING', 'TYPE', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
             'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMICOLON', 'ASSIGN',
             'EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'ILA', 'AWLA', 'KHDEM', 'MA7ED',
             # ... more token types ...
     )
     ```

2. **Keyword Maps**:
     - `_TYPE_KEYWORDS`: Type keywords like "int" (int), "3ayan" (float), "string" (string)
     
     ```python
     _TYPE_KEYWORDS = {
             'int': 'int',      # Integer type
             '3ayan': 'float',    # Float type
             'string': 'string',   # String type
             'logic': 'bool',     # Boolean type
             # ... other types ...
     }
     ```
     
     - `_CONTROL_KEYWORDS_MAP`: Control flow keywords mapped to token types
     
     ```python
     _CONTROL_KEYWORDS_MAP = {
             'ila': 'ILA',        # if
             'awla': 'AWLA',      # else
             'ma7ed': 'MA7ED',    # while
             '7awl': 'HAWL',      # try
             'chd': 'CHD',        # catch
             # ... other control keywords ...
     }
     ```
     
     - `_LITERAL_KEYWORDS_MAP`: Literal keywords mapped to their values
     
     ```python
     _LITERAL_KEYWORDS_MAP = {
             'bssa7': ('BOOL_LITERAL', True),     # true
             'machibssa7': ('BOOL_LITERAL', False), # false
             # ... other literals ...
     }
     ```
     
     - `_SPECIAL_KEYWORDS`: Special keywords containing Arabic numerals (e.g., "7awl", "3ajib")
     
     ```python
     _SPECIAL_KEYWORDS = {
             '7awl': 'HAWL',   # try
             '3ajib': 'AJIB',  # exception
             # ... other special keywords ...
     }
     ```

3. **Symbol Map (`_SYMBOLS_MAP`)**: Maps characters to token types

     ```python
     _SYMBOLS_MAP = {
             '+': 'PLUS',
             '-': 'MINUS',
             '*': 'TIMES',
             '/': 'DIVIDE',
             '(': 'LPAREN',
             ')': 'RPAREN',
             '{': 'LBRACE',
             '}': 'RBRACE',
             ';': 'SEMICOLON',
             '=': 'ASSIGN',
             # ... other symbols ...
     }
     ```

#### Tokenization Process

The core `tokenize` function iterates through the input code character by character:

```python
def tokenize(code: str) -> List[Token]:
        tokens = []
        i = 0
        line = 1
        column = 1
        
        while i < len(code):
                # Skip whitespace
                if code[i].isspace():
                        if code[i] == '\n':
                                line += 1
                                column = 1
                        else:
                                column += 1
                        i += 1
                        continue
                        
                # Skip comments
                if code[i:i+2] == '//':
                        i = code.find('\n', i)
                        if i == -1:
                                break
                        continue
                        
                # Example: Handle string literals
                if code[i] == '"':
                        start_pos = i
                        i += 1  # Skip the opening quote
                        start_col = column
                        column += 1
                        string_value = ""
                        
                        while i < len(code) and code[i] != '"':
                                if code[i] == '\\' and i + 1 < len(code):
                                        # Handle escape sequences
                                        i += 1
                                        column += 1
                                        if code[i] == 'n':
                                                string_value += '\n'
                                        elif code[i] == 't':
                                                string_value += '\t'
                                        # ... other escape sequences ...
                                        else:
                                                string_value += code[i]
                                else:
                                        string_value += code[i]
                                
                                i += 1
                                column += 1
                                
                        if i >= len(code):
                                raise SyntaxError(f"Unterminated string at line {line}, column {start_col}")
                                
                        tokens.append(Token("STRING", string_value, line, start_col, start_pos))
                        i += 1  # Skip the closing quote
                        column += 1
                        continue
                        
                # Handle other token types...
                
        return tokens
```

### Example: Tokenization of a Simple Program

For the following DarijaLang code:

```
int x = 5;
ila (x > 3) {
        tba3("x kbir men 3");
}
```

The tokenization would produce:

```
[Token(TYPE, "int", line=1, col=1),
 Token(ID, "x", line=1, col=7),
 Token(ASSIGN, "=", line=1, col=9),
 Token(NUMBER, 5, line=1, col=11),
 Token(SEMICOLON, ";", line=1, col=12),
 Token(ILA, "ila", line=2, col=1),
 Token(LPAREN, "(", line=2, col=5),
 Token(ID, "x", line=2, col=6),
 Token(GT, ">", line=2, col=8),
 Token(NUMBER, 3, line=2, col=10),
 Token(RPAREN, ")", line=2, col=11),
 Token(LBRACE, "{", line=2, col=13),
 Token(ID, "tba3", line=3, col=5),
 Token(LPAREN, "(", line=3, col=10),
 Token(STRING, "x kbir men 3", line=3, col=11),
 Token(RPAREN, ")", line=3, col=25),
 Token(SEMICOLON, ";", line=3, col=26),
 Token(RBRACE, "}", line=4, col=1)]
```

### Special Handling for Arabic Numeral Keywords

DarijaLang features a unique characteristic where some keywords contain numbers (e.g., "7awl" for "try", "3ajib" for "exception"). The lexer contains special logic to correctly tokenize these.

```python
# Special handling for Arabic numeral keywords
if i < len(code) and code[i].isalpha() or code[i] in ['7', '3', '9']:
        start_pos = i
        start_col = column
        identifier = ""
        
        while i < len(code) and (code[i].isalnum() or code[i] == '_' or code[i] in ['7', '3', '9']):
                identifier += code[i]
                i += 1
                column += 1
                
        # Check special keywords first (like 7awl, 3ajib)
        if identifier in _SPECIAL_KEYWORDS:
                tokens.append(Token(_SPECIAL_KEYWORDS[identifier], identifier, line, start_col, start_pos))
                continue
                
        # Check regular keywords and identifiers
        # ...
```

## Syntax Analysis

The parser (`darija_parser.py`) transforms the token stream into an Abstract Syntax Tree (AST) using the PLY (Python Lex-Yacc) library. It defines the grammar of DarijaLang and builds a structured representation of the program.

### AST Node Definitions

The AST consists of node classes defined using Python's `@dataclass` decorator. Each node represents a specific syntactic construct:

```python
@dataclass
class Node:
        line: int  # Base class with line number for error reporting

@dataclass
class Program(Node):
        body: List[Node]  # Top-level container for the program

@dataclass
class VarDecl(Node):
        type_name: str
        identifier: str
        initializer: Any | None
        
@dataclass
class FunctionDecl(Node):
        return_type: str
        name: str
        params: List[tuple]  # List of (type, name) tuples
        body: 'Block'
        
@dataclass
class IfStmt(Node):
        test: 'Expression'
        consequent: 'Statement'
        alternate: 'Statement' | None
        
@dataclass
class WhileStmt(Node):
        test: 'Expression'
        body: 'Statement'
        
@dataclass
class Block(Node):
        statements: List['Statement']
        
@dataclass
class BinaryOp(Node):
        left: 'Expression'
        op: str
        right: 'Expression'
        
@dataclass
class CallExpr(Node):
        function: str
        arguments: List['Expression']
        
# ... many more node types for different language constructs ...
```

### Operator Precedence

The parser defines operator precedence to correctly handle expressions with multiple operators:

```python
precedence = (
        ('left', 'AWLA_LOGICAL'),      # Logical OR (||)
        ('left', 'OU'),                # Logical AND (&&)
        ('left', 'EQ', 'NE'),          # Equality operators (==, !=)
        ('left', 'LT', 'LE', 'GT', 'GE'), # Relational operators (<, <=, >, >=)
        ("left", "PLUS", "MINUS"),     # Addition and subtraction (+, -)
        ("left", "TIMES", "DIVIDE"),   # Multiplication and division (*, /)
        ("right", "UMINUS"),           # Unary minus (-x)
        ("right", "MACHI"),            # Logical NOT (!)
```

