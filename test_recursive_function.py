#!/usr/bin/env python3
"""
Test script for recursive function handling
"""

import sys
import os
from darija_parser import parse
from darija_ir import generate_ir
from darija_c_emitter import CEmitter

def test_recursive_function():
    # Simple test with a recursive function
    test_code = '''
    int factorial(int n) {
        ila (n <= 1) {
            rj3 1;
        }
        rj3 n * factorial(n - 1);
    }
    
    int bda() {
        int result = factorial(5);
        tba3(result);
        rj3 0;
    }
    '''
    
    # Parse and generate IR
    ast = parse(test_code)
    ir = generate_ir(ast)
    
    # Generate C code and print it
    emitter = CEmitter()
    c_code = emitter.emit(ir)
    
    print("\n=== Generated C Code ===")
    print(c_code)
    
    # Check if parameters are handled correctly
    expected_signature = "int factorial(int n)"
    if expected_signature in c_code:
        print("\nSUCCESS: Function parameters are correctly emitted!")
    else:
        print("\nFAILURE: Function parameters are missing in the C code")
        print(f"Expected '{expected_signature}' in the generated code")

if __name__ == "__main__":
    test_recursive_function()
