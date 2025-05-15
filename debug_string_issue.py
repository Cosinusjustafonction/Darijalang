#!/usr/bin/env python3
"""
Debug script for string handling issues
"""

import os
import sys
from darija_parser import parse
from darija_ir import generate_ir
from darija_c_emitter import CEmitter

def debug_string_handling(source_code):
    print("==== Parsing Source ====")
    ast = parse(source_code)
    
    print("\n==== Generating IR ====")
    ir = generate_ir(ast)
    
    print("\n==== IR for Function Body ====")
    if ir.functions:
        for i, instr in enumerate(ir.functions[0].body):
            print(f"[{i}] {type(instr).__name__}: {instr}")
            if hasattr(instr, 'args'):
                print(f"    Args: {instr.args} (types: {[type(arg) for arg in instr.args]})")
    
    print("\n==== Generating C Code ====")
    emitter = CEmitter()
    c_code = emitter.emit(ir)
    
    print("\n==== Generated C Code ====")
    print(c_code)
    
    # Save to debug file
    with open("debug_c_output.c", "w") as f:
        f.write(c_code)
    print("\nC code saved to debug_c_output.c")

if __name__ == "__main__":
    test_code = """
    int bda() {
        tba3_str("Hello, World!");
        rj3 0;
    }
    """
    debug_string_handling(test_code)
