#!/usr/bin/env python3
"""
Debug tool for DarijaLang parser
"""

import sys
from darija_parser import parse
from darija_lexer import tokenize

def debug_parse(filename):
    """Debug the parser by showing tokens and AST"""
    try:
        with open(filename, 'r') as f:
            source = f.read()
        
        print("\n=== TOKENS ===")
        for token in tokenize(source):
            print(f"{token.line}:{token.column} - {token.type}: {token.value!r}")
        
        print("\n=== PARSING ===")
        try:
            ast = parse(source)
            print("Parsing successful!")
            print("\n=== AST ===")
            print(ast)
            return 0
        except Exception as e:
            print(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_parser.py <filename>")
        sys.exit(1)
    
    sys.exit(debug_parse(sys.argv[1]))
