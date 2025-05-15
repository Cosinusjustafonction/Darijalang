#!/usr/bin/env python3
"""
Test script for string handling in DarijaLang
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from darija_parser import parse
from darija_ir import generate_ir
from darija_c_emitter import CEmitter

def test_string_handling():
    # Very simple test program with string
    test_code = '''
    int bda() {
        tba3_str("Hello, DarijaLang!");
        rj3 0;
    }
    '''
    
    # Parse and generate IR
    ast = parse(test_code)
    ir = generate_ir(ast)
    
    # Generate C code
    emitter = CEmitter()
    c_code = emitter.emit(ir)
    
    print("Generated C code:")
    print("=" * 40)
    print(c_code)
    
    # Save for debug purposes
    with open("string_test_output.c", "w") as f:
        f.write(c_code)
    print("C code saved to string_test_output.c")

if __name__ == "__main__":
    test_string_handling()
