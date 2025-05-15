from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any, Optional, Tuple

import darija_parser as ast # To reference AST node types

# --- IR Node Definitions ---
@dataclass
class IRNode:
    """Base class for all IR instructions."""
    pass

@dataclass
class IRLabel(IRNode):
    name: str  # e.g., L0, L1, func_start_main

@dataclass
class IRGoto(IRNode): # Unconditional jump
    label: str

@dataclass
class IRConditionalGoto(IRNode): # Conditional jump
    condition_var: str  # Variable holding the boolean result of the condition
    true_label: str
    false_label: str

# Operations that produce a value into a temporary variable
@dataclass
class IRBinOp(IRNode):
    target_temp_var: str
    op: str
    left_operand: Any  # Can be var name (str), temp name (str), or constant
    right_operand: Any # Can be var name (str), temp name (str), or constant

@dataclass
class IRUnaryOp(IRNode):
    target_temp_var: str
    op: str
    operand: Any # Can be var name (str), temp name (str), or constant

@dataclass
class IRCall(IRNode):
    func_name: str
    args: List[Any]  # List of var names (str), temp names (str), or constants
    target_temp_var: Optional[str] = None  # Temp variable to store the result, if any

# Operations that do not necessarily produce a value or store into program variables
@dataclass
class IRStore(IRNode):
    target_var: str  # Program variable name
    source_var_or_const: Any  # Temp/var name (str) or constant value to store

@dataclass
class IRReturn(IRNode):
    value_var_or_const: Optional[Any] = None  # Temp/var name (str) or constant value to return

# Add these IR node classes for exception handling
@dataclass
class IRTryCatch(IRNode):
    try_body: List[IRNode]
    catch_var: str  # Name of the exception variable
    catch_body: List[IRNode]

@dataclass
class IRThrow(IRNode):
    value_var_or_const: Any  # Expression to throw

# Function and Program Structure
@dataclass
class IRFuncDef(IRNode):
    name: str
    params: List[str]  # List of parameter names
    body: List[IRNode]  # Sequence of IR instructions for the function body

@dataclass
class IRProgram(IRNode):
    functions: List[IRFuncDef]

# --- AST to IR Visitor ---
class ASTtoIRVisitor:
    def __init__(self):
        self.ir_code_stream: List[IRNode] = [] # Current stream being built (e.g., for a function body)
        self.temp_var_count = 0
        self.label_count = 0
        self.current_function_params: List[str] = []
        self.loop_stack: List[Tuple[str, str]] = [] # Stack of (continue_label, break_label)

    def _new_temp(self) -> str:
        self.temp_var_count += 1
        return f"t{self.temp_var_count - 1}"

    def _new_label(self, prefix="L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count - 1}"

    def visit(self, node: ast.Node) -> Any:
        method_name = f'visit_{node.__class__.__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        # Expressions return a value/var_name, statements append to ir_code_stream and return None
        return visitor_method(node)

    def generic_visit(self, node: ast.Node):
        raise NotImplementedError(f"No visit_{node.__class__.__name__} method for {type(node)}")

    def visit_Program(self, node: ast.Program) -> IRProgram:
        ir_functions = []
        # Assuming global statements are not yet handled or are wrapped in a main by parser
        for item in node.body:
            if isinstance(item, ast.FuncDef):
                ir_functions.append(self.visit(item))
            else:
                # Handle global variable declarations or other top-level statements if necessary
                # For now, focusing on function definitions
                print(f"Warning: Skipping top-level AST node {type(item)} in IR generation.")
        return IRProgram(functions=ir_functions)

    def visit_FuncDef(self, node: ast.FuncDef) -> IRFuncDef:
        # Save and reset state for this function
        outer_ir_stream = self.ir_code_stream
        outer_temp_count = self.temp_var_count
        outer_params = self.current_function_params
        outer_loop_stack = self.loop_stack

        self.ir_code_stream = []
        self.temp_var_count = 0  # Temps are local to a function
        
        # Fix for params being None
        if node.params is None:
            self.current_function_params = []
        else:
            # Store parameter names correctly
            self.current_function_params = [p[1] for p in node.params]  # Extract param names
            
        self.loop_stack = []

        self.visit(node.body)  # Populates self.ir_code_stream

        func_ir_body = self.ir_code_stream
        func_params = list(self.current_function_params)  # Make a copy to preserve parameter list
        
        # Restore outer state
        self.ir_code_stream = outer_ir_stream
        self.temp_var_count = outer_temp_count
        self.current_function_params = outer_params
        self.loop_stack = outer_loop_stack
        
        return IRFuncDef(name=node.name, params=func_params, body=func_ir_body)

    def visit_Compound(self, node: ast.Compound) -> None:
        for stmt in node.statements:
            self.visit(stmt) # Statements append to self.ir_code_stream

    def visit_VarDecl(self, node: ast.VarDecl) -> None:
        if node.initializer:
            init_val_or_var = self.visit(node.initializer)
            self.ir_code_stream.append(IRStore(target_var=node.identifier, source_var_or_const=init_val_or_var))
        # If no initializer, variable is declared. Some IRs might have explicit declaration.
        # For now, first store implies declaration. Or it's considered uninitialized.

    def visit_Assignment(self, node: ast.Assignment) -> None:
        value_var_or_const = self.visit(node.value)
        self.ir_code_stream.append(IRStore(target_var=node.identifier, source_var_or_const=value_var_or_const))

    def visit_ConstLiteral(self, node: ast.ConstLiteral) -> Any:
        """Return the literal value directly."""
        return node.value

    def visit_Identifier(self, node: ast.Identifier) -> str:
        # When an identifier is visited in an expression context, it means its value is being used.
        # It could be a local variable, a temporary, or a function parameter.
        return node.name

    def visit_BinOp(self, node: ast.BinOp) -> str: # Returns temp var name holding the result
        left_val_or_var = self.visit(node.left)
        right_val_or_var = self.visit(node.right)
        result_temp = self._new_temp()
        self.ir_code_stream.append(IRBinOp(target_temp_var=result_temp, op=node.op,
                                           left_operand=left_val_or_var, right_operand=right_val_or_var))
        return result_temp

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str: # Returns temp var name holding the result
        operand_val_or_var = self.visit(node.operand)
        result_temp = self._new_temp()
        self.ir_code_stream.append(IRUnaryOp(target_temp_var=result_temp, op=node.op, operand=operand_val_or_var))
        return result_temp

    def visit_IfStmt(self, node: ast.IfStmt) -> None:
        cond_var = self.visit(node.test) # Should return var name holding boolean result

        then_label = self._new_label("then")
        else_label = self._new_label("else")
        end_if_label = self._new_label("endif")

        actual_false_label = else_label if node.alternate else end_if_label
        self.ir_code_stream.append(IRConditionalGoto(condition_var=cond_var, true_label=then_label, false_label=actual_false_label))

        self.ir_code_stream.append(IRLabel(name=then_label))
        self.visit(node.consequent)

        if node.alternate:
            self.ir_code_stream.append(IRGoto(label=end_if_label)) # Skip else block if then was executed
            self.ir_code_stream.append(IRLabel(name=else_label))
            self.visit(node.alternate)

        self.ir_code_stream.append(IRLabel(name=end_if_label))

    def visit_WhileStmt(self, node: ast.WhileStmt) -> None:
        loop_cond_label = self._new_label("while_cond")
        loop_body_label = self._new_label("while_body")
        loop_end_label = self._new_label("while_end")

        self.loop_stack.append((loop_cond_label, loop_end_label)) # Continue goes to cond, Break goes to end

        self.ir_code_stream.append(IRLabel(name=loop_cond_label))
        cond_var = self.visit(node.test)
        self.ir_code_stream.append(IRConditionalGoto(condition_var=cond_var, true_label=loop_body_label, false_label=loop_end_label))

        self.ir_code_stream.append(IRLabel(name=loop_body_label))
        self.visit(node.body)
        self.ir_code_stream.append(IRGoto(label=loop_cond_label)) # Jump back to condition check

        self.ir_code_stream.append(IRLabel(name=loop_end_label))
        self.loop_stack.pop()

    def visit_ForStmt(self, node: ast.ForStmt) -> None:
        loop_cond_label = self._new_label("for_cond")
        loop_body_label = self._new_label("for_body")
        loop_update_label = self._new_label("for_update")
        loop_end_label = self._new_label("for_end")

        self.loop_stack.append((loop_update_label, loop_end_label)) # Continue goes to update, Break to end

        if node.init:
            self.visit(node.init) # Init is a statement (VarDecl or Assignment or expr)

        self.ir_code_stream.append(IRLabel(name=loop_cond_label))
        if node.test:
            test_cond_var = self.visit(node.test)
            self.ir_code_stream.append(IRConditionalGoto(condition_var=test_cond_var, true_label=loop_body_label, false_label=loop_end_label))
        else: # No test means infinite loop (unless break)
            self.ir_code_stream.append(IRGoto(label=loop_body_label))

        self.ir_code_stream.append(IRLabel(name=loop_body_label))
        self.visit(node.body)

        self.ir_code_stream.append(IRLabel(name=loop_update_label))
        if node.update:
            self.visit(node.update) # Update is a statement

        self.ir_code_stream.append(IRGoto(label=loop_cond_label))
        self.ir_code_stream.append(IRLabel(name=loop_end_label))
        self.loop_stack.pop()

    def visit_FuncCall(self, node: ast.FuncCall) -> str:
        """Visit function call node and generate IR instructions."""
        arg_vars_or_consts = []
        for arg in node.args:
            arg_vars_or_consts.append(self.visit(arg))
        
        # Determine if the function call's result is used.
        # For simplicity, always assign to a temp. Can be optimized later.
        result_temp = self._new_temp()
        self.ir_code_stream.append(IRCall(func_name=node.name, args=arg_vars_or_consts, target_temp_var=result_temp))
        return result_temp

    def visit_ReturnStmt(self, node: ast.ReturnStmt) -> None:
        val_or_var = None
        if node.value:
            val_or_var = self.visit(node.value)
        self.ir_code_stream.append(IRReturn(value_var_or_const=val_or_var))

    def visit_BreakStmt(self, node: ast.BreakStmt) -> None:
        if not self.loop_stack:
            # This should ideally be caught by a semantic analysis phase or parser
            raise ValueError("Break statement outside of loop.")
        _ , break_label = self.loop_stack[-1]
        self.ir_code_stream.append(IRGoto(label=break_label))

    def visit_ContinueStmt(self, node: ast.ContinueStmt) -> None:
        if not self.loop_stack:
            raise ValueError("Continue statement outside of loop.")
        continue_label, _ = self.loop_stack[-1]
        self.ir_code_stream.append(IRGoto(label=continue_label))

    def visit_TryStmt(self, node: ast.TryStmt) -> None:
        # Create labels for try entry, catch handler, and after the whole try-catch
        try_label = self._new_label("try")
        catch_label = self._new_label("catch")
        end_label = self._new_label("try_end")
        
        # Save current code stream to restore after processing both bodies
        outer_ir_stream = self.ir_code_stream
        
        # Process try block
        try_body_stream = []
        self.ir_code_stream = try_body_stream
        self.visit(node.body)
        try_body = self.ir_code_stream
        
        # Process catch block
        catch_body_stream = []
        self.ir_code_stream = catch_body_stream
        # For each catch handler (we only support one for now)
        handler = node.handlers[0]  # Just handle the first one for simplicity
        catch_var = handler.param_name
        self.visit(handler.body)
        catch_body = self.ir_code_stream
        
        # Restore outer stream
        self.ir_code_stream = outer_ir_stream
        
        # Emit try-catch block instructions
        self.ir_code_stream.append(IRTryCatch(
            try_body=try_body,
            catch_var=catch_var,
            catch_body=catch_body
        ))

    def visit_ThrowStmt(self, node: ast.ThrowStmt) -> None:
        # Evaluate the expression to throw
        value_var_or_const = self.visit(node.expression)
        self.ir_code_stream.append(IRThrow(value_var_or_const=value_var_or_const))

# --- Main function to convert AST to IR ---
def generate_ir(ast_tree: ast.Program) -> IRProgram:
    visitor = ASTtoIRVisitor()
    ir_program = visitor.visit(ast_tree)
    return ir_program

