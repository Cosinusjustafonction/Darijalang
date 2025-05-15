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
    IRBinOp, IRUnaryOp, IRCall, IRStore, IRReturn, IRTryCatch, IRThrow
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
            # Look for bda function (our conventional entry point)
            entry_func = next((f.name for f in ir_program.functions if f.name == "bda"), 
                             ir_program.functions[0].name if ir_program.functions else "bda")
            
            # Determine if the entry function needs parameters
            entry_params_str = ""
            for func in ir_program.functions:
                if func.name == entry_func and func.params:
                    entry_params_str = ", ".join(["5"] * len(func.params))  # Default args
            
            result.append(f"\n/* Main stub for program entry */\n")
            result.append(f"int main(void) {{\n")
            result.append(f"    return {self.safe_identifier(entry_func)}({entry_params_str});\n")
            result.append("}\n")
            
        return "".join(result)
    
    def _emit_function(self, func: IRFuncDef) -> str:
        """Generate C code for a function definition."""
        # For simplicity, all functions return int
        # In a full implementation, we'd map DarijaLang types to C types
        func_name = self.safe_identifier(func.name)
        
        # Format parameters
        params = []
        if func.params:  # Make sure params exists and isn't None
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
        
        # Helper function to process instruction and collect variables
        def process_instruction(instr):
            if isinstance(instr, IRBinOp):
                all_vars.add(instr.target_temp_var)
                if isinstance(instr.left_operand, str) and instr.left_operand.isidentifier():
                    all_vars.add(instr.left_operand)
                if isinstance(instr.right_operand, str) and instr.right_operand.isidentifier():
                    all_vars.add(instr.right_operand)
                    
            elif isinstance(instr, IRUnaryOp):
                all_vars.add(instr.target_temp_var)
                if isinstance(instr.operand, str) and instr.operand.isidentifier():
                    all_vars.add(instr.operand)
                    
            elif isinstance(instr, IRCall):
                if instr.target_temp_var:
                    all_vars.add(instr.target_temp_var)
                for arg in instr.args:
                    if isinstance(arg, str) and arg.isidentifier():
                        all_vars.add(arg)
                        
            elif isinstance(instr, IRStore):
                all_vars.add(instr.target_var)
                if isinstance(instr.source_var_or_const, str) and instr.source_var_or_const.isidentifier():
                    all_vars.add(instr.source_var_or_const)
                    
            elif isinstance(instr, IRConditionalGoto):
                if isinstance(instr.condition_var, str) and instr.condition_var.isidentifier():
                    all_vars.add(instr.condition_var)
                    
            elif isinstance(instr, IRReturn):
                if isinstance(instr.value_var_or_const, str) and instr.value_var_or_const.isidentifier():
                    all_vars.add(instr.value_var_or_const)
                    
            # Handle try-catch blocks recursively
            elif isinstance(instr, IRTryCatch):
                # Process try body
                for try_instr in instr.try_body:
                    process_instruction(try_instr)
                    
                # Add catch variable
                all_vars.add(instr.catch_var)
                    
                # Process catch body
                for catch_instr in instr.catch_body:
                    process_instruction(catch_instr)
                    
            elif isinstance(instr, IRThrow):
                if isinstance(instr.value_var_or_const, str) and instr.value_var_or_const.isidentifier():
                    all_vars.add(instr.value_var_or_const)
        
        # Process each instruction in the function body
        for instr in func.body:
            process_instruction(instr)
        
        # Remove parameter names since they're already declared
        if func.params:
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
        elif isinstance(instr, IRTryCatch):
            # Generate C code for try-catch using setjmp/longjmp
            try_id = self._new_jmp_id()
            result = []
            
            # Setup try block with setjmp
            result.append(f"    /* Begin try-catch block {try_id} */\n")
            result.append(f"    __darija_push_handler({try_id});\n")
            result.append(f"    if (setjmp(__darija_jmp_buf[__darija_handler_idx - 1]) == 0) {{\n")
            
            # Emit try body
            for try_instr in instr.try_body:
                # Indent one level more
                try_code = self._emit_instruction(try_instr).replace("\n", "\n    ")
                result.append(try_code)
            
            # After try body completes normally, skip the catch
            result.append(f"        /* Try completed normally - pop handler and skip catch */\n")
            result.append(f"        __darija_pop_handler();\n")
            result.append(f"    }} else {{\n")
            result.append(f"        /* Exception caught - execute catch block */\n")
            
            # Store exception in catch variable
            catch_var = self.safe_identifier(instr.catch_var)
            result.append(f"        char* {catch_var} = __darija_current_exception;\n")
            
            # Emit catch body
            for catch_instr in instr.catch_body:
                catch_code = self._emit_instruction(catch_instr).replace("\n", "\n        ")
                result.append(catch_code)
                
            result.append(f"    }}\n")
            result.append(f"    /* End try-catch block {try_id} */\n")
            return "".join(result)
        elif isinstance(instr, IRThrow):
            value = self._format_operand(instr.value_var_or_const)
            return f"    __darija_throw({value});\n"
        else:
            return f"    /* Unhandled IR instruction: {type(instr).__name__} */\n"
    
    def _new_jmp_id(self):
        """Generate a new unique ID for jump buffers."""
        if not hasattr(self, '_jmp_counter'):
            self._jmp_counter = 0
        self._jmp_counter += 1
        return self._jmp_counter - 1

    def _format_operand(self, operand) -> str:
        """Format an operand (variable, literal, etc.) for C code."""
        if isinstance(operand, str):
            # If it's definitely a string literal (not an identifier), ensure it's quoted
            if not operand.isidentifier() and not operand.startswith('"'):
                # Don't double-quote strings that are already quoted
                return f'"{operand}"'
            # For variable names or already quoted strings, return as is
            return self.safe_identifier(operand)
        elif isinstance(operand, (int, float)):
            return str(operand)
        elif operand is True:
            return "1"
        elif operand is False:
            return "0"
        elif operand is None:
            return "0"
        else:
            # For any other type, convert to string and handle with care
            return f'"{str(operand)}"'

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
    
    # Always save debug output during development
    debug_c_path = "debug_output.c"
    with open(debug_c_path, "w") as f:
        f.write(c_code)
    print(f"Generated C code saved to: {debug_c_path}")
    
    # Include more verbose debug info
    print("\nAST structure:")
    print(ast)
    
    print("\nIR structure:")
    for func in ir.functions:
        print(f"Function: {func.name}")
        for i, instr in enumerate(func.body):
            print(f"  [{i}] {type(instr).__name__}: {instr}")
    
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



