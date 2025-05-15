#!/usr/bin/env python3
"""darija_c_emitter.py - DarijaLang Code Generator (Phase 5)

Converts DarijaLang IR to C source code for compilation by gcc/clang.
"""

import os
import tempfile
import subprocess
import sys
from typing import List, Dict, Set, Optional

from darija_ir import (
    IRProgram, IRFuncDef, IRNode, IRLabel, IRGoto, IRConditionalGoto,
    IRBinOp, IRUnaryOp, IRCall, IRStore, IRReturn
)

class CEmitter:
    """Converts IR code to C source code."""

    def __init__(self):
        self.c_keywords = {
            "auto", "break", "case", "char", "const", "continue", "default", "do", "double", 
            "else", "enum", "extern", "float", "for", "goto", "if", "int", "long", "register", 
            "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", 
            "union", "unsigned", "void", "volatile", "while"
        }
        self.used_identifiers: Set[str] = set()
        
    def safe_identifier(self, name: str) -> str:
        """Ensure identifier doesn't clash with C keywords."""
        if name in self.c_keywords:
            return f"__d_{name}"
        return name
    
    def emit(self, ir_program: IRProgram) -> str:
        """Generate C code from IR program."""
        result = [
            '#include "darija_runtime.h"\n\n',
            '/* Generated C code from DarijaLang */\n\n'
        ]
        
        # Generate function definitions
        for func in ir_program.functions:
            result.append(self._emit_function(func))
            
        # Add main function stub if not defined
        if not any(f.name == "main" for f in ir_program.functions):
            # Get the first function or a default function name
            entry_func = ir_program.functions[0].name if ir_program.functions else "bda"
            result.append(f"\n/* Main stub for program entry */\n")
            result.append(f"int main(void) {{\n")
            result.append(f"    return {self.safe_identifier(entry_func)}();\n")
            result.append("}\n")
            
        return "".join(result)
    
    def _emit_function(self, func: IRFuncDef) -> str:
        """Generate C code for a function definition."""
        # For simplicity, all functions return int
        # In a full implementation, we'd map DarijaLang types to C types
        func_name = self.safe_identifier(func.name)
        
        # Format parameters
        params = []
        for param in func.params:
            safe_param = self.safe_identifier(param)
            params.append(f"int {safe_param}")
        params_str = ", ".join(params) if params else "void"
        
        result = [f"int {func_name}({params_str}) {{\n"]
        
        # Find all variables to declare at the beginning
        all_vars = self._collect_variables(func)
        
        # Declare all variables at the beginning of the function
        for var in all_vars:
            result.append(f"    int {self.safe_identifier(var)};\n")
        
        if all_vars:
            result.append("\n")
        
        # Emit function body
        for instr in func.body:
            result.append(self._emit_instruction(instr))
            
        result.append("}\n\n")
        return "".join(result)

    def _collect_variables(self, func: IRFuncDef) -> Set[str]:
        """Collect all variables used in a function."""
        all_vars = set()
        
        # Process each instruction to find variables
        for instr in func.body:
            # For binary operations, the target is a temp variable
            if isinstance(instr, IRBinOp):
                all_vars.add(instr.target_temp_var)
                if isinstance(instr.left_operand, str):
                    all_vars.add(instr.left_operand)
                if isinstance(instr.right_operand, str):
                    all_vars.add(instr.right_operand)
                    
            # For unary operations, the target is a temp variable
            elif isinstance(instr, IRUnaryOp):
                all_vars.add(instr.target_temp_var)
                if isinstance(instr.operand, str):
                    all_vars.add(instr.operand)
                    
            # For function calls with return value
            elif isinstance(instr, IRCall):
                if instr.target_temp_var:
                    all_vars.add(instr.target_temp_var)
                for arg in instr.args:
                    if isinstance(arg, str):
                        all_vars.add(arg)
                        
            # For assignments
            elif isinstance(instr, IRStore):
                all_vars.add(instr.target_var)
                if isinstance(instr.source_var_or_const, str):
                    all_vars.add(instr.source_var_or_const)
                    
            # For conditional jumps
            elif isinstance(instr, IRConditionalGoto):
                if isinstance(instr.condition_var, str):
                    all_vars.add(instr.condition_var)
                    
            # For returns
            elif isinstance(instr, IRReturn):
                if isinstance(instr.value_var_or_const, str):
                    all_vars.add(instr.value_var_or_const)
        
        # Remove parameter names since they're already declared
        for param in func.params:
            if param in all_vars:
                all_vars.remove(param)
                
        return all_vars
    
    def _emit_instruction(self, instr: IRNode) -> str:
        """Generate C code for an IR instruction."""
        if isinstance(instr, IRLabel):
            # In C, labels can't directly precede declarations - add a dummy statement
            return f"{instr.name}: ;\n"
        elif isinstance(instr, IRGoto):
            return f"    goto {instr.label};\n"
        elif isinstance(instr, IRConditionalGoto):
            # Note: C uses ! for negation
            cond_var = self.safe_identifier(instr.condition_var)
            return f"    if (!{cond_var}) goto {instr.false_label};\n"
        elif isinstance(instr, IRBinOp):
            target = self.safe_identifier(instr.target_temp_var)
            left = self._format_operand(instr.left_operand)
            right = self._format_operand(instr.right_operand)
            return f"    {target} = {left} {instr.op} {right};\n"
        elif isinstance(instr, IRUnaryOp):
            target = self.safe_identifier(instr.target_temp_var)
            operand = self._format_operand(instr.operand)
            # Map DarijaLang unary ops to C
            op_map = {'-': '-', '!': '!'}
            c_op = op_map.get(instr.op, instr.op)
            return f"    {target} = {c_op}{operand};\n"
        elif isinstance(instr, IRCall):
            func_name = self.safe_identifier(instr.func_name)
            args = [self._format_operand(arg) for arg in instr.args]
            args_str = ", ".join(args)
            
            # Special handling for void functions
            if func_name in ["tba3", "tba3_str"]:
                return f"    {func_name}({args_str});\n"
                
            if instr.target_temp_var:
                target = self.safe_identifier(instr.target_temp_var)
                return f"    {target} = {func_name}({args_str});\n"
            else:
                return f"    {func_name}({args_str});\n"
        elif isinstance(instr, IRStore):
            target = self.safe_identifier(instr.target_var)
            source = self._format_operand(instr.source_var_or_const)
            # All variables are already declared at the beginning, so just assign
            return f"    {target} = {source};\n"
        elif isinstance(instr, IRReturn):
            if instr.value_var_or_const is None:
                return "    return 0;\n"
            value = self._format_operand(instr.value_var_or_const)
            return f"    return {value};\n"
        else:
            return f"    /* Unhandled IR instruction: {type(instr).__name__} */\n"
    
    def _format_operand(self, operand) -> str:
        """Format an operand (variable, literal, etc.) for C code."""
        if isinstance(operand, str):  # Variable name
            return self.safe_identifier(operand)
        elif operand is True:
            return "1"  # C doesn't have 'true' in C89/C90
        elif operand is False:
            return "0"  # C doesn't have 'false' in C89/C90
        elif operand is None:
            return "0"  # Represent null as 0 for simplicity
        else:  # Numeric or other literal
            return str(operand)

def compile_and_run(source: str, keep_c: bool = False, output_path: Optional[str] = None) -> int:
    """
    Compile DarijaLang source to C, then compile and run the C code.
    
    Args:
        source: DarijaLang source code
        keep_c: Whether to keep generated C files
        output_path: Optional path for the output executable
        
    Returns:
        The exit code from running the compiled program
    """
    from darija_parser import parse
    from darija_ir import generate_ir
    
    # Parse source to AST
    ast = parse(source)
    
    # Generate IR
    ir = generate_ir(ast)
    
    # Generate C code
    emitter = CEmitter()
    c_code = emitter.emit(ir)
    
    # Create temporary directory for build artifacts
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write generated C code to file
        c_file_path = os.path.join(temp_dir, "prog.c")
        with open(c_file_path, "w") as f:
            f.write(c_code)
        
        # Copy runtime files to the temporary directory
        runtime_dir = os.path.dirname(os.path.abspath(__file__))
        runtime_h = os.path.join(runtime_dir, "darija_runtime.h")
        runtime_c = os.path.join(runtime_dir, "darija_runtime.c")
        
        # Copy header to temp dir
        temp_runtime_h = os.path.join(temp_dir, "darija_runtime.h")
        with open(runtime_h, "r") as src, open(temp_runtime_h, "w") as dst:
            dst.write(src.read())
        
        # Copy implementation to temp dir
        temp_runtime_c = os.path.join(temp_dir, "darija_runtime.c") 
        with open(runtime_c, "r") as src, open(temp_runtime_c, "w") as dst:
            dst.write(src.read())
        
        # Default output path if not specified
        if not output_path:
            output_path = os.path.join(temp_dir, "prog.out")
        
        # Compile with gcc - now using the copied runtime files
        compile_cmd = [
            "gcc", "-std=c11", "-O2", c_file_path, temp_runtime_c,
            "-o", output_path
        ]
        
        try:
            subprocess.run(compile_cmd, check=True)
            
            # Keep generated C files if requested
            if keep_c:
                kept_c_path = f"{output_path}.c"
                with open(c_file_path, "r") as src, open(kept_c_path, "w") as dst:
                    dst.write(src.read())
                print(f"Generated C code saved to: {kept_c_path}")
            
            # Run the compiled program
            run_result = subprocess.run([output_path], capture_output=True)
            print(run_result.stdout.decode('utf-8'))  # Print program output
            if run_result.stderr:
                print("Error output:", file=sys.stderr)
                print(run_result.stderr.decode('utf-8'), file=sys.stderr)
            return run_result.returncode
            
        except subprocess.CalledProcessError as e:
            print(f"Compilation error: {e}", file=sys.stderr)
            return 1

if __name__ == "__main__":
    # CLI for testing the emitter
    if len(sys.argv) < 2:
        print("Usage: python darija_c_emitter.py <darija_source_file> [--keep-c] [--output <path>]")
        sys.exit(1)
    
    source_path = sys.argv[1]
    keep_c = "--keep-c" in sys.argv
    
    output_idx = -1
    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output")
    
    output_path = None
    if output_idx >= 0 and output_idx + 1 < len(sys.argv):
        output_path = output_idx + 1
    
    try:
        with open(source_path, "r") as f:
            source = f.read()
        exit_code = compile_and_run(source, keep_c, output_path)
        sys.exit(exit_code)
    except FileNotFoundError:
        print(f"File not found: {source_path}")
        sys.exit(1)
