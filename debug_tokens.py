#!/usr/bin/env python3
"""Debug tool to print tokens from DarijaLang lexer"""

import sys
from darija_lexer import tokenize

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_tokens.py <filename>")
        return
        
    try:
        with open(sys.argv[1], 'r') as f:
            source = f.read()
            
        print("Tokens from", sys.argv[1])
        print("=" * 40)
        for token in tokenize(source):
            print(f"Line {token.line}: {token.type} = {token.value!r}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
