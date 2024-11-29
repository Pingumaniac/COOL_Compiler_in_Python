# code_generator.py

from helpers import LabelGenerator, StringCache
from errors import RuntimeErrorHandler

class CodeGenerator:
    def __init__(self, class_table, ast, symbol_table, filename):
        self.ctab = class_table
        self.ast = ast
        self.stab = symbol_table
        self.filename = filename
        self.output_file = f"{filename.split('.')[0]}.s"
        self.f = open(self.output_file, 'w')
        self.label_gen = LabelGenerator()
        self.string_cache = StringCache()
        self.error_handler = RuntimeErrorHandler(self.asm)
        self.current_class = None
        self.current_method = None
        self.reverse_class_name_mapping = {}

    def close(self):
        self.f.close()

    def asm(self, instr, comment=""):
        if instr.endswith(":"):
            self.f.write(f"{instr}\t# {comment}\n")
        else:
            self.f.write(f"    {instr}\t# {comment}\n")


    def asm_2(self, instr):
        self.f.write(f"{instr}\n")

    def generate(self):
        self.asm("# Generated x86-64 Assembly for COOL Program", "")
        self.asm(".section .data", "# Data section for constants and vtables")
        self.define_strings()
        # self.define_error_messages()
        self.define_vtables()
        self.generate_class_name_lookup()
        self.generate_abort_message()

        self.asm(".section .text", "# Code section")
        self.asm(".globl main", "# Define main as global entry point")
        self.asm(".extern malloc", "# Extern malloc from libc")
        self.asm(".extern printf", "# Extern printf for error handling")
        self.asm(".extern exit", "# Extern exit for terminating the program")

        self.generate_constructors()
        self.generate_methods()
        self.generate_main()
        self.generate_footer()
        self.add_string_literal_labels()

        self.close()


    def add_string_literal_labels(self):
        for string in self.string_cache.string_table:
            string_label = self.string_cache.string_table[string]
            self.asm(f".globl {string_label}", "")
            self.asm(f"{string_label}:", f'String literal: "{string}"')
            # Emit .byte directives for each character in the string
            for char in string:
                self.asm(f"    .byte {ord(char)}", f"'{char}'")
            
            # Add the null terminator
            self.asm("    .byte 0", "Null terminator")

    def generate_abort_message(self):
        """
        Adds the `string00` label with the abort message to the assembly output.
        """
        self.asm(".section .rodata", "Switch to read-only data section")
        self.asm(".globl string00", "Declare string00 as global")
        self.asm("string00:", "Abort message")
        self.asm('    .string "abort\\n"', "Define abort message with null terminator")

    def define_strings(self):
        self.asm("# String literals", "")
        for string, label in self.string_cache.string_table.items():
            escaped_string = string.replace('\\', '\\\\').replace('"', '\\"')
            self.asm(f"{label}:", f'.string "{escaped_string}"')

    # def define_error_messages(self):
    #     self.asm("# Runtime Error Messages", "")

    def generate_class_name_lookup(self):
        self.asm("# Class Name Mapping", "")
        self.asm("class_name_lookup:", "# Mapping of obj_id to class name")
        obj_id = 1
        for cname in sorted(self.ctab.all_classes()):
            class_name_label = f"{cname}_name"
            self.asm(f".quad {class_name_label}", f"# Class name for obj_id {obj_id}")
            self.asm(f"{class_name_label}: .string \"{cname}\"", f"# String for {cname}")
            self.reverse_class_name_mapping[cname] = obj_id
            obj_id += 1


    def define_vtables(self):
        self.asm_2("# VTables")
        for cname in sorted(self.ctab.all_classes()):
            vtable_label = f"{cname}..vtable"
            self.asm_2(f".globl {vtable_label}")
            self.asm(f"{vtable_label}:", f"# VTable for {cname}")
            constructor_label = f"{cname}..new"
            self.asm(f"    .quad {constructor_label}", f"# Constructor for {cname}")
            methods = self.ctab.all_methods(cname)
            for method in methods:
                method_label = f"{method[4]}.{method[0]}"
                self.asm(f"    .quad {method_label}", f"# Method {method[0]} for {cname}")

    def generate_constructors(self):
        self.asm("# Constructors", "")
        for cname in sorted(self.ctab.all_classes()):
            obj_id = self.reverse_class_name_mapping[cname]
            constructor_label = f"{cname}..new"
            self.asm_2(f".globl {constructor_label}")
            self.asm(f"{constructor_label}:", f"# Constructor for {cname}")

            # Function Prologue
            self.asm("    pushq %rbp", "# Save base pointer")
            self.asm("    movq %rsp, %rbp", "# Set base pointer")
            self.asm("    pushq %rbx", "# Save %rbx (callee-saved register)")
            # Stack is now aligned (pushed two 8-byte values)

            # Determine object size
            if cname == "String":
                object_size = 40
            elif cname in ["Int", "Bool"]:
                object_size = 32
            else:
                num_attrs = len(self.ctab.all_attributes(cname))
                object_size = 24 + 8 * num_attrs

            # Allocate memory for the object
            total_size = object_size
            self.asm(f"    movq ${total_size // 8}, %rdi", "# Number of elements for calloc")
            self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
            self.asm("    call calloc", "# Allocate memory")
            self.asm("    movq %rax, %rbx", "# Store allocated address in %rbx")

            # Initialize object metadata
            self.asm(f"    movq ${obj_id}, (%rbx)", "# Set object ID")
            self.asm(f"    movq ${object_size}, 8(%rbx)", "# Set object size")
            vtable_label = f"{cname}..vtable"
            self.asm(f"    leaq {vtable_label}(%rip), %rcx", "# Load vtable address")
            self.asm("    movq %rcx, 16(%rbx)", "# Set vtable pointer")

            # Initialize attributes
            attributes = self.ctab.all_attributes(cname)
            for idx, (aname, atype, ainit) in enumerate(attributes):
                offset = 24 + 8 * idx
                if ainit is not None:
                    # Before calling generate_expression, ensure %rbx is preserved
                    # Since %rbx is callee-saved and we're in the same function, it's safe
                    self.generate_expression(ainit, target_reg='%rax')
                    self.asm(f"    movq %rax, {offset}(%rbx)", f"# Store initialized attribute {aname}")
                else:
                    self.initialize_default(atype, offset, "%rbx", aname)

            # Function Epilogue
            self.asm("    movq %rbx, %rax", "# Return object pointer")
            self.asm("    popq %rbx", "# Restore %rbx")
            self.asm("    popq %rbp", "# Restore base pointer")
            self.asm("    ret", "# Return from constructor")




            
    def generate_methods(self):
        # Generate all methods for all classes
        self.asm("# Methods", "")
        for cname in sorted(self.ctab.all_classes()):
            self.current_class = cname
            methods = self.ctab.declared_methods(cname)
            for method in methods:
                mname, args, mtype, body, defining_class = method
                method_label = f"{defining_class}.{mname}"
                self.asm_2(f".globl {method_label}")
                self.asm(f"{method_label}:", f"# Method {mname} of {defining_class}")
                self.asm("    pushq %rbp", "# Save base pointer")
                self.asm("    movq %rsp, %rbp", "# Set base pointer")

                # Enter method scope
                self.stab.enter_scope()
                self.stab.add_symbol("self", "%rdi")  # 'self' is in %rdi

                # Save %rbx and 'self'
                self.asm("    pushq %rbx", "# Save %rbx on the stack")
                self.asm("    movq %rdi, %rbx", "# Save 'self' in %rbx")

                # Add class attributes to the symbol table
                attributes = self.ctab.all_attributes(self.current_class)
                for idx, (aname, atype, _) in enumerate(attributes):
                    offset = 24 + 8 * idx  # Attribute offset within the object
                    self.stab.add_symbol(aname[1], f"{offset}(%rbx)")  # Use %rbx instead of %rdi

                # Map arguments to stack
                for idx, pname in enumerate(args):
                    stack_offset = 16 + 8 * idx  # Stack offsets start at +16(%rbp) for arguments
                    self.stab.add_symbol(pname, f"{stack_offset}(%rbp)")

                # Generate code for method body
                self.generate_expression(body, target_reg='%rax')

                # Restore %rbx
                self.asm("    popq %rbx", "# Restore %rbx")

                # Exit method scope
                self.stab.exit_scope()

                # Restore base pointer and return
                self.asm("    popq %rbp", "# Restore base pointer")
                self.asm("    ret", "# Return from method")


    def generate_main(self):
        self.asm(".globl start", "# Define program entry point")
        self.asm("start:", "# Actual entry point")
        self.asm("    jmp main", "# Jump to main function")

        self.asm("# Main Function", "")
        self.asm("main:", "# Entry point")
        self.asm("    pushq %rbp", "# Save base pointer")
        self.asm("    movq %rsp, %rbp", "# Set base pointer")

        self.asm("    call Main..new", "# Create Main class instance")
        self.asm("    movq %rax, %rdi", "# Move Main object to rdi")

        self.asm("    movq 16(%rdi), %rsi", "# Load vtable pointer")
        self.asm("    call Main.main", "# Invoke Main.main method")

        self.asm("    movq $0, %rdi", "# Exit status 0")
        self.asm("    call exit", "# Exit the program")


    def generate_expression(self, expr, target_reg='%rax'):
        # Recursively generate code for an expression.
        expr_type = expr[1]
        tag = expr[2]
        line_number = int(expr[0])

        if tag == 'assign':
            var_name = expr[3][1]
            rhs = expr[4]
            self.generate_expression(rhs, target_reg='%rax')
            var_address = self.stab.find_symbol(var_name)
            if var_address is None:
                print(f"Error: Variable '{var_name}' not found at line {line_number}.")
                exit()
            self.asm(f"    movq %rax, {var_address}", f"# Assign to variable '{var_name}'")
            self.asm(f"    movq %rax, {target_reg}", f"# Result of assignment to '{var_name}'")
        elif tag == 'static_dispatch':
            self.generate_static_dispatch(expr, line_number, target_reg)
        elif tag == 'dynamic_dispatch':
            self.generate_dynamic_dispatch(expr, line_number, target_reg)
        elif tag == 'self_dispatch':
            self.generate_self_dispatch(expr, line_number, target_reg)
        elif tag == 'if':
            self.generate_if(expr, line_number, target_reg)
        elif tag == 'block':
            self.generate_block(expr, line_number, target_reg)
        elif tag == 'while':
            self.generate_while(expr, line_number, target_reg)
        elif tag == 'let':
            self.generate_let(expr, line_number, target_reg)
        elif tag == 'case':
            self.generate_case(expr, line_number, target_reg)
        elif tag == 'new':
            self.generate_new(expr, target_reg)
        elif tag == 'isvoid':
            self.generate_isvoid(expr, target_reg)
        elif tag == 'negate':
            self.generate_negate(expr, target_reg)
        elif tag == 'not':
            self.generate_not(expr, target_reg)
        elif tag in ['plus', 'minus', 'times', 'divide']:
            self.generate_arithmetic(expr, tag, line_number, target_reg)
        elif tag in ['lt', 'le', 'eq']:
            self.generate_comparison(expr, tag, line_number, target_reg)
        elif tag == 'internal':
            self.generate_internal(expr, target_reg)
        elif tag == 'integer':
            self.generate_integer(expr, target_reg)
        elif tag == 'string':
            self.generate_string(expr, target_reg)
        elif tag == 'true':
            self.generate_true(expr, target_reg)
        elif tag == 'false':
            self.generate_false(expr, target_reg)
        elif tag == 'identifier':
            self.generate_identifier(expr, target_reg)
        else:
            print(f"ERROR: Unhandled expression tag '{tag}' at line {line_number}.")
            exit()

    def generate_static_dispatch(self, expr, line_number, target_reg='%rax'):
        # Generate code for static dispatch.
        dispatch_exp = expr[3]
        dispatch_type = expr[4][1]
        method_name = expr[5][1]
        args = expr[6]

        # Evaluate the dispatch expression
        self.generate_expression(dispatch_exp, target_reg='%rax')  # Object in %rax

        # Check for dispatch on void
        self.error_handler.handle_error("dispatch_void", line_number)  # Before dispatch

        # Continue if not void
        label_continue = self.label_gen.new_label("dispatch_static_continue")
        self.asm(f"    cmpq $0, %rax", "# Check if object is void")
        self.asm(f"    jne {label_continue}", "# If not void, continue dispatch")
        self.asm(f"{label_continue}:", "")

        # Load vtable pointer (offset +16 in object layout)
        self.asm("    movq 16(%rax), %rsi", "# Load vtable pointer into %rsi")

        # Calculate method offset in vtable
        method_index = self.ctab.get_method_index(dispatch_type, method_name)
        if method_index == -1:
            print(f"Error: Method '{method_name}' not found in class '{dispatch_type}' at line {line_number}.")
            exit(1)
        offset = (method_index + 1) * 8  # New is the first entry in vtable

        # Load method address into %rdx (caller-saved register)
        self.asm(f"    movq {offset}(%rsi), %rdx", f"# Load address of method '{method_name}' from vtable into %rdx")

        # Save method address in %r12 (callee-saved register)
        self.asm("    movq %rdx, %r12", "# Save method address in %r12")

        # Move the dispatch object to %rdi (as per calling convention)
        self.asm("    movq %rax, %rdi", "# Move dispatch object to %rdi")

        # Evaluate arguments and push onto the stack
        for arg in reversed(args):
            self.generate_expression(arg, target_reg='%rax')
            self.asm("    pushq %rax", f"# Push argument for method '{method_name}'")

        # Call the method
        self.asm("    call *%r12", f"# Call method '{method_name}'")

        # Clean up the stack
        total_args = len(args)
        if total_args > 0:
            self.asm(f"    addq ${8 * total_args}, %rsp", "# Clean up stack after method call")

        # Restore 'self' into %rdi from %rbx
        self.asm("    movq %rbx, %rdi", "# Restore 'self' into %rdi")

        # Move result to target register
        self.asm(f"    movq %rax, {target_reg}", f"# Move result to {target_reg}")



    def generate_dynamic_dispatch(self, expr, line_number, target_reg='%rax'):
        # Generate code for dynamic dispatch.
        dispatch_exp = expr[3]
        static_type = expr[3][1]
        method_name = expr[5][1]
        args = expr[6]

        # Evaluate the dispatch expression
        self.generate_expression(dispatch_exp, target_reg='%rax')  # Object in %rax

        # Check for dispatch on void
        self.error_handler.handle_error("dispatch_void", line_number)  # Before dispatch

        # Continue if not void
        label_continue = self.label_gen.new_label("dispatch_dynamic_continue")
        self.asm(f"    cmpq $0, %rax", "# Check if object is void")
        self.asm(f"    jne {label_continue}", "# If not void, continue dispatch")
        self.asm(f"{label_continue}:", "")

        # Load vtable pointer (offset +16 in object layout)
        self.asm("    movq 16(%rax), %rsi", "# Load vtable pointer into %rsi")

        # Get method index using static type
        method_index = self.ctab.get_method_index(static_type, method_name)
        if method_index == -1:
            print(f"Error: Method '{method_name}' not found in class '{static_type}' at line {line_number}.")
            exit(1)

        # Calculate method offset in vtable
        offset = (method_index + 1) * 8
        # Load method address into %rdx
        self.asm(f"    movq {offset}(%rsi), %rdx", f"# Load address of method '{method_name}' from vtable into %rdx")

        # Save method address in %r12
        self.asm("    movq %rdx, %r12", "# Save method address in %r12")

        # Move the dispatch object to %rdi
        self.asm("    movq %rax, %rdi", "# Move dispatch object to %rdi")

        # Evaluate arguments and push onto the stack
        for arg in reversed(args):
            self.generate_expression(arg, target_reg='%rax')
            self.asm("    pushq %rax", f"# Push argument for method '{method_name}'")

        # Call the method
        self.asm("    call *%r12", f"# Call method '{method_name}'")

        # Clean up the stack
        total_args = len(args)
        if total_args > 0:
            self.asm(f"    addq ${8 * total_args}, %rsp", "# Clean up stack after method call")

        # Restore 'self' into %rdi from %rbx
        self.asm("    movq %rbx, %rdi", "# Restore 'self' into %rdi")

        # Move result to target register
        self.asm(f"    movq %rax, {target_reg}", f"# Move result to {target_reg}")



    def generate_self_dispatch(self, expr, line_number, target_reg='%rax'):
        # Generate code for self dispatch.
        method_name = expr[5][1]
        args = expr[6]

        # 'self' is in %rbx; move it to %rdi
        self.asm("    movq %rbx, %rdi", "# Move 'self' to %rdi")
        self.asm("    movq 16(%rbx), %rsi", "# Load vtable pointer of 'self' into %rsi")

        # Calculate method offset in vtable
        method_index = self.ctab.get_method_index(self.current_class, method_name)
        if method_index == -1:
            print(f"Error: Method '{method_name}' not found in class '{self.current_class}' at line {line_number}.")
            exit(1)

        # The first function of the vtable is the new method which is not in ctab
        offset = (method_index + 1) * 8
        # Load method address into %rdx
        self.asm(f"    movq {offset}(%rsi), %rdx", f"# Load address of method '{method_name}' from vtable into %rdx")

        # Save method address in %r12
        self.asm("    movq %rdx, %r12", "# Save method address in %r12")

        # Evaluate arguments and push onto the stack
        for arg in reversed(args):
            self.generate_expression(arg, target_reg='%rax')
            self.asm("    pushq %rax", f"# Push argument for method '{method_name}'")

        # Call the method
        self.asm("    call *%r12", f"# Call method '{method_name}'")

        # Clean up the stack
        total_args = len(args)
        if total_args > 0:
            self.asm(f"    addq ${8 * total_args}, %rsp", "# Clean up stack after method call")

        # Restore 'self' into %rdi from %rbx
        self.asm("    movq %rbx, %rdi", "# Restore 'self' into %rdi")

        # Move result to target register
        self.asm(f"    movq %rax, {target_reg}", f"# Move result to {target_reg}")





    def generate_if(self, expr, line_number, target_reg='%rax'):
        # Generate code for if-then-else expressions.
        cond = expr[3]
        then_exp = expr[4]
        else_exp = expr[5]

        label_else = self.label_gen.new_label("if_else")
        label_end = self.label_gen.new_label("if_end")

        # Evaluate condition
        self.generate_expression(cond, target_reg='%rax')
        self.asm("    movq 24(%rax), %rcx", "# Load Bool value into %rcx")
        self.asm("    cmpq $1, %rcx", "# Compare Bool value to true (1)")
        self.asm(f"    jne {label_else}", "# Jump to else if not true")

        # Then branch
        self.generate_expression(then_exp, target_reg='%rax')
        self.asm(f"    jmp {label_end}", "# Jump to end after then branch")

        # Else branch
        self.asm(f"{label_else}:")
        self.generate_expression(else_exp, target_reg='%rax')

        # End
        self.asm(f"{label_end}:")

    def generate_block(self, expr, line_number, target_reg='%rax'):
        # Generate code for block expressions.
        expressions = expr[3]
        for sub_expr in expressions:
            self.generate_expression(sub_expr, target_reg='%rax')

    def generate_while(self, expr, line_number, target_reg='%rax'):
        # Generate code for while loops.
        cond = expr[3]
        body = expr[4]

        label_start = self.label_gen.new_label("while_start")
        label_body = self.label_gen.new_label("while_body")
        label_end = self.label_gen.new_label("while_end")

        self.asm(f"{label_start}:", "# Start of while loop condition")
        # Evaluate condition
        self.generate_expression(cond, target_reg='%rax')
        self.asm("    movq 24(%rax), %rcx", "# Load Bool value into %rcx")
        self.asm("    cmpq $1, %rcx", "# Compare Bool value to true (1)")
        self.asm(f"    jne {label_end}", "# Exit loop if condition is false")

        # Body of the loop
        self.asm(f"{label_body}:")
        self.generate_expression(body, target_reg='%rax')

        # Jump back to condition
        self.asm(f"    jmp {label_start}", "# Jump back to condition check")

        # End of loop
        self.asm(f"{label_end}:", "# End of while loop")


    def generate_let(self, expr, line_number, target_reg='%rax'):
        # Generate code for let expressions.
        bindings = expr[3]
        body = expr[4]

        # Enter new scope
        self.stab.enter_scope()

        # Stack offset for variables
        offset = -8

        # Initialize bindings
        for bind in bindings:
            _, var, var_type, init = bind
            var_name = var[1]
            if init is not None:
                # Initialize with expression
                self.generate_expression(init, target_reg='%rax')
            else:
                # Default initialization
                if var_type[1] == 'Int':
                    self.asm("    movq $4, %rdi", "# Number of elements for Int object")
                    self.asm("    movq $8, %rsi", "# Size of each element for Int object")
                    self.asm("    call calloc", "# Allocate Int object with calloc")
                    self.asm("    movq $1, (%rax)", "# Set Int object ID")
                    self.asm("    movq $32, 8(%rax)", "# Set Int object size")
                    self.asm("    leaq Int..vtable(%rip), %rcx", "# Load Int vtable address")
                    self.asm("    movq %rcx, 16(%rax)", "# Set Int vtable pointer")
                    self.asm("    movq $0, 24(%rax)", "# Initialize Int value to 0")
                elif var_type[1] == 'Bool':
                    self.asm("    movq $4, %rdi", "# Number of elements for Bool object")
                    self.asm("    movq $8, %rsi", "# Size of each element for Bool object")
                    self.asm("    call calloc", "# Allocate Bool object with calloc")
                    self.asm("    movq $3, (%rax)", "# Set Bool object ID")
                    self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
                    self.asm("    leaq Bool..vtable(%rip), %rcx", "# Load Bool vtable address")
                    self.asm("    movq %rcx, 16(%rax)", "# Set Bool vtable pointer")
                    self.asm("    movb $0, 24(%rax)", "# Initialize Bool value to false")
                elif var_type[1] == 'String':
                    empty_string_label = self.string_cache.cache_string("")
                    self.asm("    movq $5, %rdi", "# Number of elements for String object")
                    self.asm("    movq $8, %rsi", "# Size of each element for String object")
                    self.asm("    call calloc", "# Allocate String object with calloc")
                    self.asm("    movq $2, (%rax)", "# Set String object ID")
                    self.asm("    movq $40, 8(%rax)", "# Set String object size")
                    self.asm("    leaq String..vtable(%rip), %rcx", "# Load String vtable address")
                    self.asm("    movq %rcx, 16(%rax)", "# Set String vtable pointer")
                    self.asm(f"    leaq {empty_string_label}(%rip), %rcx", "# Load empty string address")
                    self.asm("    movq %rcx, 24(%rax)", "# Set String pointer")
                    self.asm("    movq $0, 32(%rax)", "# Set String length to 0 (empty string)")
                else:
                    # For other classes, call their constructor
                    constructor = f"{var_type[1]}..new"
                    self.asm(f"    call {constructor}", f"# Call constructor for {var_type[1]} object")

            # Bind variable to stack and adjust offset
            self.stab.add_symbol(var_name, f"{offset}(%rbp)")
            self.asm(f"    movq %rax, {offset}(%rbp)", f"# Let binding '{var_name}'")
            offset -= 8  # Adjust stack offset for the next variable

        # Generate body expression
        self.generate_expression(body, target_reg='%rax')

        # Exit scope
        self.stab.exit_scope()

    def generate_case(self, expr, line_number, target_reg='%rax'):
        # Extract case elements
        case_expr = expr[3]       # Expression being matched
        case_elements = expr[4]   # List of (var, type_, body) tuples

        # Generate code for the case expression
        self.generate_expression(case_expr, target_reg=target_reg)

        # Load the type of the case expression into a temporary register (e.g., %rcx)
        TYPE_OFFSET = 0  # Adjust based on your object layout
        self.asm(f"    movq {TYPE_OFFSET}(%{target_reg}), %rcx", f"# Load type of case expression into %rcx")

        # Compare with 'Void' type address
        VOID_TYPE_ADDRESS = self.ctab.get_type_address("Void")
        if VOID_TYPE_ADDRESS is None:
            self.error_handler.handle_error("type_not_found", line_number)

        self.asm(f"    cmpq ${VOID_TYPE_ADDRESS}, %rcx", "# Compare case expression type with Void")
        self.asm(f"    je handle_case_error_{line_number}", "# Jump to error handler if case expression is Void")

        # Continue with type checking for each case branch
        label_end = f"case_end_{line_number}"
        labels = []  # Track labels for each case branch

        for i, (var, type_, body) in enumerate(case_elements):
            # Generate unique label for this case branch
            label_case = f"case_branch_{line_number}_{i}"
            labels.append(label_case)

            # Get the type address for the current case branch
            type_address = self.ctab.get_type_address(type_)
            if type_address is None:
                self.error_handler.handle_error("type_not_found", line_number)

            # Compare the case expression type with the current branch type
            self.asm(f"    cmpq ${type_address}, %rcx", f"# Check if case expression matches type '{type_}'")
            self.asm(f"    je {label_case}", "# Jump to this branch if types match")

        # If no branch matches, handle the 'case_no_match' error
        self.error_handler.handle_error("case_no_match", line_number)
        self.asm(f"    jmp {label_end}", "# Jump to end after handling no match")

        # Generate code for each case branch
        for i, (var, type_, body) in enumerate(case_elements):
            label_case = labels[i]
            self.asm(f"{label_case}:", f"# Case branch {i} for type '{type_}'")

            # Enter a new scope for the case branch
            self.stab.enter_scope()
            self.stab.add_symbol(var, target_reg)  # Bind case variable to target_reg (e.g., %rax)

            # Generate code for the branch body
            self.generate_expression(body, target_reg=target_reg)

            # Exit the scope and jump to the end of the case statement
            self.stab.exit_scope()
            self.asm(f"    jmp {label_end}", "# Jump to end after handling this branch")

        # Handle case expression being Void
        self.asm(f"handle_case_error_{line_number}:", f"# Handle case expression being Void")
        self.error_handler.handle_error("case_error", line_number)
        self.asm(f"    jmp {label_end}", "# Jump to end after handling case error")

        # End of case statement
        self.asm(f"{label_end}:", "# End of case statement")




    def generate_new(self, expr, target_reg='%rax'):
        # Generate code for object creation using 'new'.
        class_name = expr[3][1]
        constructor_label = f"{class_name}..new"
        self.asm(f"    call {constructor_label}", f"# Create new {class_name} object")
        self.asm(f"    movq %rax, {target_reg}", f"# Move new object to {target_reg}")

    def generate_isvoid(self, expr, target_reg='%rax'):
        # Generate code for isvoid expressions.
        exp = expr[3]
        self.generate_expression(exp, target_reg='%rax')
        self.asm("    cmpq $0, %rax", "# Check if expression is void")
        
        label_true = self.label_gen.new_label("isvoid_true")
        label_end = self.label_gen.new_label("isvoid_end")
        
        self.asm(f"    je {label_true}", "# If void, jump to true label")
        self.asm("    movq $0, %rcx", "# Set rcx to false")
        self.asm(f"    jmp {label_end}", "# Jump to end label")
        
        self.asm(f"{label_true}:", "# True label")
        self.asm("    movq $1, %rcx", "# Set rcx to true")
        
        self.asm(f"{label_end}:", "# End label")

        # Box the result into a Bool object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Bool object using calloc")
        self.asm("    movq $3, (%rax)", "# Set Bool object ID (3 for Bool)")
        self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
        self.asm("    leaq Bool..vtable(%rip), %rsi", "# Load Bool vtable pointer")
        self.asm("    movq %rsi, 16(%rax)", "# Set Bool vtable pointer")
        self.asm("    movb %cl, 24(%rax)", "# Set Bool value (attribute at offset 24)")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Bool object to {target_reg}")

    def generate_negate(self, expr, target_reg='%rax'):
        # Generate code for negate expressions (applies to integers).
        exp = expr[3]
        self.generate_expression(exp, target_reg='%rax')

        # Load Int value based on the object layout
        self.asm("    movq 24(%rax), %rcx", "# Load Int value into rcx (attribute at offset 24)")
        self.asm("    negq %rcx", "# Negate the Int value")

        # Box the result into a new Int object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Int object using calloc")
        self.asm("    movq $1, (%rax)", "# Set Int object ID (1 for Int)")
        self.asm("    movq $32, 8(%rax)", "# Set Int object size")
        self.asm("    leaq Int..vtable(%rip), %rcx", "# Load Int vtable pointer")
        self.asm("    movq %rcx, 16(%rax)", "# Set Int vtable pointer")
        self.asm("    movq %rcx, 24(%rax)", "# Set negated Int value at offset 24")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Int object to {target_reg}")



    def generate_not(self, expr, target_reg='%rax'):
        # Generate code for 'not' expressions (applies to booleans).
        exp = expr[3]
        self.generate_expression(exp, target_reg='%rax')

        # Load Bool value based on the object layout
        self.asm("    movb 24(%rax), %cl", "# Load Bool value into cl (attribute at offset 24)")
        self.asm("    xorb $1, %cl", "# Logical NOT operation")

        # Box the result into a new Bool object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Bool object using calloc")
        self.asm("    movq $3, (%rax)", "# Set Bool object ID (3 for Bool)")
        self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
        self.asm("    leaq Bool..vtable(%rip), %rcx", "# Load Bool vtable pointer")
        self.asm("    movq %rcx, 16(%rax)", "# Set Bool vtable pointer")
        self.asm("    movb %cl, 24(%rax)", "# Set Bool value at offset 24")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Bool object to {target_reg}")

    def generate_arithmetic(self, expr, op, line_number, target_reg='%rax'):
        # Generate code for arithmetic operations.
        left = expr[3]
        right = expr[4]

        # Evaluate left expression
        self.generate_expression(left, target_reg='%rsi')
        self.asm("    movq 24(%rsi), %rcx", "# Load left Int value into rcx (attribute at offset 24)")

        # Evaluate right expression
        self.generate_expression(right, target_reg='%rdx')
        self.asm("    movq 24(%rdx), %rdx", "# Load right Int value into rdx (attribute at offset 24)")

        # Perform the operation
        if op == 'plus':
            self.asm("    addq %rdx, %rcx", "# Perform addition")
        elif op == 'minus':
            self.asm("    subq %rdx, %rcx", "# Perform subtraction")
        elif op == 'times':
            self.asm("    imulq %rdx, %rcx", "# Perform multiplication")
        elif op == 'divide':
            # Check for division by zero
            self.asm("    cmpq $0, %rdx", "# Check if divisor is zero")
            label_continue = self.label_gen.new_label("div_continue")
            self.asm(f"    jne {label_continue}", "# If not zero, continue division")
            # Division by zero detected; handle the error
            self.error_handler.handle_error("division_zero", line_number)
            # Label to continue division
            self.asm(f"{label_continue}:", "")
            self.asm("    movq %rcx, %rax", "# Move dividend to rax")
            self.asm("    cqo", "# Sign extend rax to rdx:rax")
            self.asm("    idivq %rdx", "# Perform division")
            self.asm("    movq %rax, %rcx", "# Move quotient to rcx")


        # Box the result into a new Int object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Int object using calloc")
        self.asm("    movq $1, (%rax)", "# Set Int object ID (1 for Int)")
        self.asm("    movq $32, 8(%rax)", "# Set Int object size")
        self.asm("    leaq Int..vtable(%rip), %rsi", "# Load Int vtable pointer")
        self.asm("    movq %rsi, 16(%rax)", "# Set Int vtable pointer")
        self.asm("    movq %rcx, 24(%rax)", "# Set Int value (attribute at offset 24)")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Int object to {target_reg}")

    def generate_comparison(self, expr, comp_type, line_number, target_reg='%rax'):
        # Generate code for comparison operations (lt, le, eq).
        left = expr[3]
        right = expr[4]

        # Evaluate left expression
        self.generate_expression(left, target_reg='%rsi')
        self.asm("    movq 24(%rsi), %rcx", "# Load left value into rcx (attribute at offset 24)")

        # Evaluate right expression
        self.generate_expression(right, target_reg='%rdx')
        self.asm("    movq 24(%rdx), %rdx", "# Load right value into rdx (attribute at offset 24)")

        # Perform the comparison
        if comp_type == 'lt':
            self.asm("    cmpq %rdx, %rcx", "# Compare rcx < rdx")
            self.asm("    setl %cl", "# Set cl to 1 if rcx < rdx, else 0")
        elif comp_type == 'le':
            self.asm("    cmpq %rdx, %rcx", "# Compare rcx <= rdx")
            self.asm("    setle %cl", "# Set cl to 1 if rcx <= rdx, else 0")
        elif comp_type == 'eq':
            self.asm("    cmpq %rdx, %rcx", "# Compare rcx == rdx")
            self.asm("    sete %cl", "# Set cl to 1 if rcx == rdx")

        # Box the result into a new Bool object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Bool object using calloc")
        self.asm("    movq $3, (%rax)", "# Set Bool object ID (3 for Bool)")
        self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
        self.asm("    leaq Bool..vtable(%rip), %rsi", "# Load Bool vtable pointer")
        self.asm("    movq %rsi, 16(%rax)", "# Set Bool vtable pointer")
        self.asm("    movb %cl, 24(%rax)", "# Set Bool value (attribute at offset 24)")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Bool object to {target_reg}")



    def generate_internal(self, expr, target_reg):
        # Generate code for internal methods like IO.out_string, IO.out_int, etc.
        internal_method = expr[3]
        if internal_method == 'IO.out_int':
            # rax contains the Int object
            self.asm("    movq 24(%rax), %rsi", "Load Int value from the object into rsi")
            self.asm("    leaq percent.d(%rip), %rdi", "Load format string for int")
            self.asm("    movl %esi, %eax", "Move lower 32 bits of rsi to eax (sign-extend)")
            self.asm("    cdqe", "Convert dword to qword in rax")
            self.asm("    movq %rax, %rsi", "Move extended value into rsi")
            self.asm("    movl $0, %eax", "No floating-point arguments")
            self.asm("    call printf", "Call printf to print Int")
            self.asm(f"    movq %rax, {target_reg}", "Move result to target register")

        elif internal_method == 'IO.out_string':
            self.asm("    movq 16(%rbp), %rsi", "# Load String object into %rsi")
            self.asm("    movq 24(%rbp), %rdi", "# Load self object %rdi")

            self.asm("    movq 24(%rsi), %rdx", "Load String pointer into %rdx")
            self.asm("    movq %rdx, %rdi", "Move string pointer to %rdi for cooloutstr")
            self.asm("    call cooloutstr", "Call cooloutstr")
            # self.asm("    movq 24(%rsi), %rdx", "Load string pointer from the object into rsi")

            # # Pass the string pointer to cooloutstr
            # self.asm("    movq %rdx, %rdi", "Move string pointer to rdi for cooloutstr")
            # self.asm("    call cooloutstr", "Call cooloutstr to output the string")

            # # Return the result
            # self.asm(f"    movq %rax, {target_reg}", "Move result to target register")

        elif internal_method == 'IO.in_int':
            # Allocate memory for the input string
            self.asm("    movl $1, %esi", "Number of elements")
            self.asm("    movl $4096, %edi", "Allocate 4096 bytes")
            self.asm("    call calloc", "Call calloc")
            self.asm("    pushq %rax", "Save the buffer pointer on the stack")

            # Read the input from stdin
            self.asm("    movq %rax, %rdi", "Pass buffer pointer to fgets")
            self.asm("    movq $4096, %rsi", "Size of buffer")
            self.asm("    movq stdin(%rip), %rdx", "File pointer (stdin)")
            self.asm("    call fgets", "Read the string into buffer")
            self.asm("    popq %rdi", "Restore the buffer pointer")

            # Parse the integer from the string
            self.asm("    movl $0, %eax", "Clear %eax")
            self.asm("    pushq %rax", "Save space for sscanf result")
            self.asm("    movq %rsp, %rdx", "Address to store parsed integer")
            self.asm("    movq $percent.ld, %rsi", "Format string")
            self.asm("    call sscanf", "Call sscanf")
            self.asm("    popq %rax", "Retrieve the result")

            # Clamp the integer value to 32-bit range
            self.asm("    movq $0, %rsi", "Default to 0")
            self.asm("    cmpq $2147483647, %rax", "Check if > max int")
            self.asm("    cmovg %rsi, %rax", "Clamp to 0 if out of bounds")
            self.asm("    cmpq $-2147483648, %rax", "Check if < min int")
            self.asm("    cmovl %rsi, %rax", "Clamp to 0 if out of bounds")

            # Create a new Int object
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq $32, %rsi", "Size of each element (Int object)")
            self.asm("    call calloc", "Allocate Int object")
            self.asm("    movq $1, (%rax)", "Set Int object ID")
            self.asm("    movq $32, 8(%rax)", "Set Int object size")
            self.asm("    leaq Int..vtable(%rip), %rdx", "Load Int vtable address")
            self.asm("    movq %rdx, 16(%rax)", "Set Int vtable pointer")
            self.asm("    movq %rdi, 24(%rax)", "Store parsed integer value as attribute")

            # Return the Int object
            self.asm("    movq %rax, %rax", "Move Int object to target register")
        elif internal_method == 'IO.in_string':
            
            # Generate a new String object
            self.asm("    movq $String..new, %r14", "Load address of String constructor")
            self.asm("    call *%r14", "Call the String constructor")
            self.asm("    movq %rax, %rbx", "Store pointer to the new String object in rbx")

            # Allocate memory for the input buffer
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq $4096, %rsi", "Allocate 4096 bytes for the input buffer")
            self.asm("    call calloc", "Call calloc to allocate buffer")
            self.asm("    movq %rax, %r13", "Store buffer pointer in r13")

            # Call coolgetstr to populate the input buffer
            self.asm("    movq %r13, %rdi", "Pass buffer pointer to coolgetstr")
            self.asm("    call coolgetstr", "Call coolgetstr to read user input")

            # Calculate the length of the input string
            self.asm("    xorq %rcx, %rcx", "Set length counter (rcx) to 0")
            self.asm("    movq %r13, %rdi", "Set rdi to the start of the input buffer")
            self.asm("calculate_length_loop:", "")
            self.asm("    movb (%rdi), %al", "Load the current character")
            self.asm("    cmpb $0, %al", "Check if it is the null terminator")
            self.asm("    je calculate_length_done", "Jump to end if null terminator")
            self.asm("    incq %rcx", "Increment length counter")
            self.asm("    incq %rdi", "Move to the next character")
            self.asm("    jmp calculate_length_loop", "Repeat the loop")
            self.asm("calculate_length_done:", "# Length calculation complete")

            # Set String object's fields
            self.asm("    movq $2, (%rbx)", "Set String object ID")
            self.asm("    movq $40, 8(%rbx)", "Set String object size")
            self.asm("    leaq String..vtable(%rip), %rdx", "Load String vtable address")
            self.asm("    movq %rdx, 16(%rbx)", "Set vtable pointer")
            self.asm("    movq %r13, 24(%rbx)", "Set string pointer to input buffer")
            self.asm("    movq %rcx, 32(%rbx)", "Set string length")

            # Return the String object
            self.asm(f"    movq %rbx, {target_reg}", "Move String object to target register")

        elif internal_method == 'Object.abort':
            self.asm("    movq $string00, %r13", "Load abort message into r13")
            self.asm("    movq %r13, %rdi", "Move abort message pointer to rdi for cooloutstr")

            # Call cooloutstr to print the abort message
            self.asm("    call cooloutstr", "Call cooloutstr to output the abort message")

            # Set exit status to 0 and call exit
            self.asm("    movl $0, %edi", "Set exit status to 0")
            self.asm("    call exit", "Call exit to terminate the program")
        elif internal_method == 'Object.copy':
            # Allocate memory for the new object
            self.asm("    movq 8(%rax), %rcx", "Load size of the object from the second field")
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq %rcx, %rsi", "Size of each element")
            self.asm("    call calloc", "Allocate memory for the new object")
            self.asm("    movq %rax, %rbx", "Store the new object pointer in rbx")

            # Copy metadata (ID, size, vtable pointer)
            self.asm("    movq (%rax), %rsi", "Load ID from original object")
            self.asm("    movq %rsi, (%rbx)", "Copy ID to the new object")
            self.asm("    movq 8(%rax), %rsi", "Load size from original object")
            self.asm("    movq %rsi, 8(%rbx)", "Copy size to the new object")
            self.asm("    movq 16(%rax), %rsi", "Load vtable pointer from original object")
            self.asm("    movq %rsi, 16(%rbx)", "Copy vtable pointer to the new object")

            # Initialize attribute copying loop
            self.asm("    movq $24, %rcx", "Start copying attributes (offset 24)")
            self.asm("copy_loop_start:", "# Label for copy loop")
            self.asm("    cmpq %rcx, 8(%rax)", "Check if we've reached the object's size")
            self.asm("    jge copy_done", "Exit loop if all fields are copied")
            self.asm("    movq (%rax,%rcx), %rsi", "Load attribute from original object")
            self.asm("    movq %rsi, (%rbx,%rcx)", "Copy attribute to the new object")
            self.asm("    addq $8, %rcx", "Move to the next attribute (8 bytes each)")
            self.asm("    jmp copy_loop_start", "Continue copying")
            self.asm("copy_done:", "# End of copy loop")

            # Return the new object
            self.asm("    movq %rbx, %rax", "Return the new object in the target register")

        elif internal_method == 'Object.type_name':
            # The object ID pointer is in rdi
            self.asm("# Generate type_name", "")
            self.asm("    movq (%rdi), %rax", "Load obj_id from object")
            self.asm("    subq $1, %rax", "Convert obj_id to zero-based index")
            self.asm("    leaq class_name_lookup(%rip), %rcx", "Load address of the class_name_lookup table")
            self.asm("    movq (%rcx, %rax, 8), %rax", "Get pointer to class name string")
            self.asm(f"    movq %rax, {target_reg}", "Store the result in target register")
    
        elif internal_method == 'String.concat':
            # Load pointers and lengths of the two strings
            self.asm("    movq 24(%rdi), %rdx", "Load pointer to first string")
            self.asm("    movq 32(%rdi), %rcx", "Load length of first string")
            self.asm("    movq 24(%rsi), %r8", "Load pointer to second string")
            self.asm("    movq 32(%rsi), %r9", "Load length of second string")

            # Calculate total length of the concatenated string
            self.asm("    addq %r9, %rcx", "Total length of concatenated string")

            # Allocate memory for the concatenated string
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq %rcx, %rsi", "Size for concatenated string")
            self.asm("    call calloc", "Allocate memory for concatenated string")
            self.asm("    movq %rax, %rbx", "Store address of allocated memory in rbx")

            # Copy the first string into the concatenated string
            self.asm("    movq %rbx, %rdi", "Destination pointer for first string")
            self.asm("    movq %rdx, %rsi", "Source pointer for first string")
            self.asm("    movq 32(%rdi), %rdx", "Length of first string")
            self.asm("    call memcpy", "Copy first string")

            # Copy the second string into the concatenated string
            self.asm("    addq 32(%rdi), %rdi", "Adjust destination pointer for second string")
            self.asm("    movq 24(%rsi), %rsi", "Source pointer for second string")
            self.asm("    movq 32(%rsi), %rdx", "Length of second string")
            self.asm("    call memcpy", "Copy second string")

            # Allocate a new String object
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq $40, %rsi", "Size for String object")
            self.asm("    call calloc", "Allocate memory for new String object")

            # Set fields of the new String object
            self.asm("    movq $6, (%rax)", "Set object ID for String")
            self.asm("    movq $40, 8(%rax)", "Set String object size")
            self.asm("    leaq String..vtable(%rip), %rcx", "Load String vtable address")
            self.asm("    movq %rcx, 16(%rax)", "Set vtable pointer for String")
            self.asm("    movq %rbx, 24(%rax)", "Set pointer to concatenated string")
            self.asm("    movq %rcx, 32(%rax)", "Set length of concatenated string")

            # Return the new String object
            self.asm(f"    movq %rax, {target_reg}", "Move new String object to target register")

        elif internal_method == 'String.length':
            # String.length: Return the length of the string as an Int object
            # rdi = pointer to the String object
            self.asm("    movq 32(%rdi), %rsi", "Load string length into rsi")
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq $32, %rsi", "Size for Int object")
            self.asm("    call calloc", "Allocate memory for Int object")
            self.asm(f"    movq ${self.reverse_class_name_mapping['Int']}, (%rax)", "Set Int object ID")
            self.asm("    movq $32, 8(%rax)", "Set Int object size")
            self.asm("    leaq Int..vtable(%rip), %rcx", "Load Int vtable address")
            self.asm("    movq %rcx, 16(%rax)", "Set Int vtable pointer")
            self.asm("    movq 32(%rdi), %r10", "Load value into a temporary register")
            self.asm("    movq %r10, 24(%rax)", "Store value from temporary register")
            # self.asm("    movq 32(%rdi), 24(%rax)", "Store string length as Int value")
            self.asm(f"    movq %rax, {target_reg}", "Move Int object to target register")

        elif internal_method == 'String.substr':
            # Arguments:
            # rdi = Pointer to the original String object (invocant)
            # rsi = Start index (must be Int object)
            # rdx = Length (must be Int object)

            # Load original string pointer and length
            self.asm("    movq 24(%rdi), %rcx", "Load original string pointer into rcx")
            self.asm("    movq 32(%rdi), %r8", "Load original string length into r8")

            # Load start index and length values
            self.asm("    movq 24(%rsi), %rsi", "Load start index from Int object")
            self.asm("    movq 24(%rdx), %rdx", "Load length from Int object")

            # Adjust negative start index
            self.asm("    cmpq $0, %rsi", "Check if start index is negative")
            self.asm("    jge substr_start_positive", "Jump if start index is positive")
            self.asm("    addq %r8, %rsi", "Add string length to start index (negative to positive)")
            self.asm("    cmpq $0, %rsi", "Check if adjusted start index is still negative")
            self.asm("    jl substr_empty", "Return empty string if start index is out of bounds")
            self.asm("substr_start_positive:", "")

            # Handle length <= 0 (return empty string)
            self.asm("    cmpq $0, %rdx", "Check if length is <= 0")
            self.asm("    jle substr_empty", "Return empty string if length <= 0")

            # Adjust length if exceeding original string length
            self.asm("    addq %rsi, %rdx", "Compute (start index + length)")
            self.asm("    cmpq %r8, %rdx", "Check if (start index + length) > string length")
            self.asm("    jle substr_valid_length_end", "Jump if within bounds")
            self.asm("    subq %rdx, %rsi", "Restore start index")
            self.asm("substr_valid_length_end:", "")

            # Compute substring pointer
            self.asm("    leaq (%rcx, %rsi), %rcx", "Calculate pointer to substring start")

            # Allocate memory for the substring data
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq %rdx, %rsi", "Size of substring")
            self.asm("    call calloc", "Allocate memory for substring data")
            self.asm("    movq %rax, %rbx", "Store allocated memory address in rbx")

            # Copy substring data
            self.asm("    movq %rbx, %rdi", "Destination pointer for substring data")
            self.asm("    movq %rcx, %rsi", "Source pointer for substring data")
            self.asm("    movq %rdx, %rdx", "Number of bytes to copy (length)")
            self.asm("    call memcpy", "Copy substring data to allocated memory")

            # Create a new String object
            self.asm("    movq $1, %rdi", "Number of elements for calloc")
            self.asm("    movq $40, %rsi", "Size for String object")
            self.asm("    call calloc", "Allocate memory for new String object")
            self.asm(f"    movq ${self.reverse_class_name_mapping['String']}, (%rax)", "Set object ID for String")
            self.asm("    movq $40, 8(%rax)", "Set String object size")
            self.asm("    leaq String..vtable(%rip), %rcx", "Load String vtable address")
            self.asm("    movq %rcx, 16(%rax)", "Set vtable pointer")
            self.asm("    movq %rbx, 24(%rax)", "Set pointer to substring data")
            self.asm("    movq %rdx, 32(%rax)", "Set length of the substring")

            # Return the new String object
            self.asm(f"    movq %rax, {target_reg}", "Move new String object to target register")

        else:
            print(f"ERROR: Internal method '{internal_method}' not implemented.")
            exit()




    def generate_integer(self, expr, target_reg='%rax'):
        # Generate code for integer literals.
        value = expr[3]  # Extract the integer value from the expression

        # Load the integer literal into %rcx
        self.asm(f"    movq ${value}, %rcx", "# Load integer literal into %rcx")

        # Allocate 32 bytes for Int object (ID + size + vtable + value)
        self.asm("    movq $1, %rdi", "# Number of elements for Int object")
        self.asm("    movq $32, %rsi", "# Size of each element for Int object (ID + size + vtable + value)")
        self.asm("    call calloc", "# Allocate Int object with zero-initialization")
        self.asm("    movq $1, (%rax)", "# Set Int object ID")
        self.asm("    movq $32, 8(%rax)", "# Set Int object size")


        # Load Int vtable address into %rdx and set it in the Int object
        self.asm("    leaq Int..vtable(%rip), %rdx", "# Load Int vtable address")
        self.asm("    movq %rdx, 16(%rax)", "# Set Int vtable pointer")

        # Set the value of the Int object at offset 24
        self.asm("    movq %rcx, 24(%rax)", "# Set Int value (attribute at offset 24)")

        # Move the address of the Int object to the target register
        self.asm(f"    movq %rax, {target_reg}", f"# Move Int object to {target_reg}")

    def generate_string(self, expr, target_reg='%rax'):
        # Generate code for string literals.
        string_value = expr[3]
        string_label = self.string_cache.cache_string(string_value)
        # print(self.string_cache.string_table)
        # print(string_label)
        # Load string literal address into %rcx
        self.asm(f"    leaq {string_label}(%rip), %rcx", "# Load string literal address into %rcx")

        # Calculate length of the string (number of characters)
        string_length = len(string_value)

        # Allocate 40 bytes for String object (ID + size + vtable + pointer + length)
        self.asm("    movq $5, %rdi", "# Number of elements (5: ID, size, vtable, pointer, length)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate String object using calloc")
        self.asm("    movq $2, (%rax)", "# Set String object ID")
        self.asm("    movq $40, 8(%rax)", "# Set String object size")
        self.asm("    leaq String..vtable(%rip), %rdx", "# Load String vtable address")
        self.asm("    movq %rdx, 16(%rax)", "# Set String vtable pointer")
        self.asm("    movq %rcx, 24(%rax)", "# Set String pointer (attribute at offset 24)")
        self.asm(f"    movq ${string_length}, 32(%rax)", "# Set String length at offset 32")
        self.asm(f"    movq %rax, {target_reg}", f"# Move String object to {target_reg}")


    def generate_true(self, expr, target_reg='%rax'):
        # Generate code for 'true' boolean literal.
        self.asm("    movb $1, %cl", "# Set %cl to 1 for true")

        # Box into Bool object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Bool object using calloc")
        self.asm("    movq $3, (%rax)", "# Set Bool object ID (3 for Bool)")
        self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
        self.asm("    leaq Bool..vtable(%rip), %rcx", "# Load vtable address for Bool")
        self.asm("    movq %rcx, 16(%rax)", "# Set Bool vtable pointer")
        self.asm("    movb %cl, 24(%rax)", "# Set Bool value to true (attribute at offset 24)")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Bool object to {target_reg}")


    def generate_false(self, expr, target_reg='%rax'):
        # Generate code for 'false' boolean literal.
        self.asm("    movb $0, %cl", "# Set %cl to 0 for false")

        # Box into Bool object
        self.asm("    movq $4, %rdi", "# Number of elements (4: ID, size, vtable, value)")
        self.asm("    movq $8, %rsi", "# Size of each element (8 bytes)")
        self.asm("    call calloc", "# Allocate Bool object using calloc")
        self.asm("    movq $3, (%rax)", "# Set Bool object ID (3 for Bool)")
        self.asm("    movq $32, 8(%rax)", "# Set Bool object size")
        self.asm("    leaq Bool..vtable(%rip), %rcx", "# Load vtable address for Bool")
        self.asm("    movq %rcx, 16(%rax)", "# Set Bool vtable pointer")
        self.asm("    movb %cl, 24(%rax)", "# Set Bool value to false (attribute at offset 24)")
        self.asm(f"    movq %rax, {target_reg}", f"# Move Bool object to {target_reg}")

    def generate_identifier(self, expr, target_reg='%rax'):
        # Generate code for variable identifiers.
        var_name = expr[3][1]
        if var_name == 'self':
            self.asm(f"    movq %rbx, {target_reg}", "# Load 'self' into target register")
            return
        var_address = self.stab.find_symbol(var_name)
        if var_address is None:
            print(f"Error: Variable '{var_name}' not found.")
            exit()
        self.asm(f"    movq {var_address}, {target_reg}", f"# Load variable '{var_name}' into {target_reg}")


    def initialize_default(self, atype, offset, base_reg='%rbx', attribute_name=""):
        """
        Generates assembly code to initialize an attribute to its default value.

        Parameters:
            atype (str): The type of the attribute (e.g., Int, Bool, String, or a user-defined class).
            offset (int): The memory offset where the attribute is stored within the object.
            base_reg (str): The base register holding the object's memory address (e.g., %rbx).
            attribute_name (str): The name of the attribute being initialized.
        """
        if atype == "Int":
            # Default value for Int is 0
            self.asm(f"    movq $0, {offset}({base_reg})", f"# Set attribute {attribute_name} (Int) to 0")
        elif atype == "Bool":
            # Default value for Bool is false (0)
            self.asm(f"    movq $0, {offset}({base_reg})", f"# Set attribute {attribute_name} (Bool) to false")
        elif atype == "String":
            # Default value for String is null
            self.asm(f"    movq $0, {offset}({base_reg})", f"# Set attribute {attribute_name} (String) to null")
        else:
            # Default value for user-defined types is void (null)
            self.asm(f"    movq $0, {offset}({base_reg})", f"# Set attribute {attribute_name} (User-defined) to void")

    def generate_footer(self):
        # Define the.empty.string
        self.asm(".globl the.empty.string", "Declare the.empty.string as global")
        self.asm("the.empty.string:", 'The empty string ""')
        self.asm("    .byte 0", "Null terminator")

        # Define percent.d
        self.asm(".globl percent.d", "Declare percent.d as global")
        self.asm("percent.d:", 'String "%ld"')
        self.asm("    .byte  37", "'%'")
        self.asm("    .byte 108", "'l'")
        self.asm("    .byte 100", "'d'")
        self.asm("    .byte 0", "Null terminator")

        # Define percent.ld
        self.asm(".globl percent.ld", "Declare percent.ld as global")
        self.asm("percent.ld:", 'String " %ld"')
        self.asm("    .byte  32", "' '")
        self.asm("    .byte  37", "'%'")
        self.asm("    .byte 108", "'l'")
        self.asm("    .byte 100", "'d'")
        self.asm("    .byte 0", "Null terminator")

        # Start the substr_empty label
        self.asm(".globl substr_empty", "Declare substr_empty as global")
        self.asm("substr_empty:", "Label for returning an empty string object")
        
        # Allocate memory for the String object
        self.asm("    movq $1, %rdi", "Number of elements for calloc")
        self.asm("    movq $40, %rsi", "Size for String object (40 bytes)")
        self.asm("    call calloc", "Allocate memory for String object")
        self.asm("    movq %rax, %rbx", "Store allocated memory address in rbx")
        
        # Set String object fields
        self.asm("    movq $6, (%rbx)", "Set object ID for String")
        self.asm("    movq $40, 8(%rbx)", "Set String object size")
        self.asm("    leaq String..vtable(%rip), %rcx", "Load String vtable address")
        self.asm("    movq %rcx, 16(%rbx)", "Set vtable pointer")
        
        # Set string data to the.empty.string
        self.asm("    movq $the.empty.string, %rcx", "Load pointer to the.empty.string")
        self.asm("    movq %rcx, 24(%rbx)", "Set pointer to empty string")
        self.asm("    movq $0, 32(%rbx)", "Set string length to 0")
        
        # Return the empty String object
        self.asm("    movq %rbx, %rax", "Move String object to rax for return")
        self.asm("    ret", "Return from substr_empty")

        # Define .LC1 for empty string
        self.asm(".section .rodata", "Switch to read-only data section")
        self.asm(".LC1:", "Label for empty string")
        self.asm('    .string ""', "Empty string with null terminator")
        self.asm(".text", "Switch back to code section")

         # Define coolstrlen function
        self.asm(".globl coolstrlen", "Declare coolstrlen as global")
        self.asm(".type coolstrlen, @function", "Declare coolstrlen as a function")
        self.asm("coolstrlen:", "Function coolstrlen")
        self.asm(".LFB1:", "Function begin frame")
        self.asm("    .cfi_startproc", "Start Call Frame Information")
        self.asm("    pushq %rbp", "Save base pointer")
        self.asm("    .cfi_def_cfa_offset 16", "Update CFI offset")
        self.asm("    .cfi_offset 6, -16", "Save return address in CFI")
        self.asm("    movq %rsp, %rbp", "Set base pointer")
        self.asm("    .cfi_def_cfa_register 6", "Define CFI register")
        self.asm("    movq %rdi, -24(%rbp)", "Save input string pointer")
        self.asm("    movl $0, -4(%rbp)", "Initialize string length to 0")
        self.asm("    jmp .L7", "Jump to loop condition")
        # Loop logic
        self.asm(".L8:", "Loop body start")
        self.asm("    movl -4(%rbp), %eax", "Load current length")
        self.asm("    addl $1, %eax", "Increment length")
        self.asm("    movl %eax, -4(%rbp)", "Store updated length")
        self.asm(".L7:", "Loop condition")
        self.asm("    movl -4(%rbp), %eax", "Load current length")
        self.asm("    mov %eax, %eax", "Zero-extend eax")
        self.asm("    addq -24(%rbp), %rax", "Calculate character address")
        self.asm("    movzbl (%rax), %eax", "Load current character")
        self.asm("    testb %al, %al", "Check for null terminator")
        self.asm("    jne .L8", "Continue loop if not null")
        # Return length
        self.asm("    movl -4(%rbp), %eax", "Move final length to eax")
        self.asm("    leave", "Restore stack and base pointer")
        self.asm("    .cfi_def_cfa 7, 8", "Restore CFI")
        self.asm("    ret", "Return from function")
        self.asm("    .cfi_endproc", "End Call Frame Information")
        self.asm(".LFE1:", "Function end")
        self.asm("    .size coolstrlen, .-coolstrlen", "Define function size")

        # Define cooloutstr function
        self.asm(".globl cooloutstr", "Declare cooloutstr as global")
        self.asm(".type cooloutstr, @function", "Declare cooloutstr as a function")
        self.asm("cooloutstr:", "Function cooloutstr")
        self.asm(".LFB0:", "Function begin frame")
        self.asm("    pushq %rbp", "Save base pointer")
        self.asm("    movq %rsp, %rbp", "Set base pointer")
        self.asm("    subq $32, %rsp", "Allocate stack space")
        self.asm("    movq %rdi, -24(%rbp)", "Save argument (string pointer)")
        self.asm("    movl $0, -4(%rbp)", "Initialize index to 0")
        self.asm("    jmp .L2", "Jump to loop start")
        # Loop and output logic
        self.asm(".L5:", "Loop body start")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq -24(%rbp), %rax", "Calculate current char address")
        self.asm("    movzbl (%rax), %eax", "Load current character")
        self.asm("    cmpb $92, %al", "Check for backslash")
        self.asm("    jne .L3", "Jump if not a backslash")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq $1, %rax", "Advance to next character")
        self.asm("    addq -24(%rbp), %rax", "Calculate next char address")
        self.asm("    movzbl (%rax), %eax", "Load next character")
        self.asm("    cmpb $110, %al", "Check for newline")
        self.asm("    jne .L3", "Jump if not newline")
        self.asm("    movq stdout(%rip), %rax", "Load stdout")
        self.asm("    movq %rax, %rsi", "Set file handle")
        self.asm("    movl $10, %edi", "Set newline character")
        self.asm("    call fputc", "Write newline")
        self.asm("    addl $2, -4(%rbp)", "Increment index by 2")
        self.asm("    jmp .L2", "Jump to loop start")
        # More conditions
        self.asm(".L3:", "Check for tab")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq -24(%rbp), %rax", "Calculate char address")
        self.asm("    movzbl (%rax), %eax", "Load current character")
        self.asm("    cmpb $92, %al", "Check for backslash")
        self.asm("    jne .L4", "Jump if not a backslash")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq $1, %rax", "Advance to next character")
        self.asm("    addq -24(%rbp), %rax", "Calculate next char address")
        self.asm("    movzbl (%rax), %eax", "Load next character")
        self.asm("    cmpb $116, %al", "Check for tab")
        self.asm("    jne .L4", "Jump if not tab")
        self.asm("    movq stdout(%rip), %rax", "Load stdout")
        self.asm("    movq %rax, %rsi", "Set file handle")
        self.asm("    movl $9, %edi", "Set tab character")
        self.asm("    call fputc", "Write tab")
        self.asm("    addl $2, -4(%rbp)", "Increment index by 2")
        self.asm("    jmp .L2", "Jump to loop start")
        # Handle other cases
        self.asm(".L4:", "Write other characters")
        self.asm("    movq stdout(%rip), %rdx", "Load stdout")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq -24(%rbp), %rax", "Calculate char address")
        self.asm("    movzbl (%rax), %eax", "Load current character")
        self.asm("    movsbl %al, %eax", "Sign-extend char")
        self.asm("    movq %rdx, %rsi", "Set file handle")
        self.asm("    movl %eax, %edi", "Set character")
        self.asm("    call fputc", "Write character")
        self.asm("    addl $1, -4(%rbp)", "Increment index")
        self.asm(".L2:", "Check loop condition")
        self.asm("    movl -4(%rbp), %eax", "Load index")
        self.asm("    cltq", "Sign-extend index")
        self.asm("    addq -24(%rbp), %rax", "Calculate char address")
        self.asm("    movzbl (%rax), %eax", "Load current character")
        self.asm("    testb %al, %al", "Check if null terminator")
        self.asm("    jne .L5", "Repeat loop if not null terminator")
        self.asm("    movq stdout(%rip), %rax", "Load stdout")
        self.asm("    movq %rax, %rdi", "Flush stdout")
        self.asm("    call fflush", "Flush buffer")
        self.asm("    leave", "Restore stack")
        self.asm("    ret", "Return from function")

        # Define coolgetstr function

        self.asm(".globl coolgetstr", "Declare coolgetstr as global")
        self.asm(".type coolgetstr, @function", "Declare coolgetstr as a function")
        self.asm("coolgetstr:", "Function coolgetstr")
        self.asm(".LFB3:", "Function begin frame")
        self.asm("    pushq %rbp", "Save base pointer")
        self.asm("    movq %rsp, %rbp", "Set base pointer")
        self.asm("    subq $32, %rsp", "Allocate stack space")
        self.asm("    movl $1, %esi", "Set calloc multiplier to 1")
        self.asm("    movl $40960, %edi", "Set calloc size")
        self.asm("    call calloc", "Allocate memory for string")
        self.asm("    movq %rax, -16(%rbp)", "Store pointer to allocated memory")
        self.asm("    movl $0, -4(%rbp)", "Initialize a flag to 0")
        self.asm(".L20:", "Start input loop")
        self.asm("    movq stdin(%rip), %rax", "Load stdin into rax")
        self.asm("    movq %rax, %rdi", "Set stdin as input")
        self.asm("    call fgetc", "Read a character from stdin")
        self.asm("    movl %eax, -20(%rbp)", "Store the character")
        self.asm("    cmpl $-1, -20(%rbp)", "Check for EOF")
        self.asm("    je .L14", "Exit loop if EOF")
        self.asm("    cmpl $10, -20(%rbp)", "Check for newline")
        self.asm("    jne .L15", "Continue if not newline")
        self.asm(".L14:", "Handle newline or EOF")
        self.asm("    cmpl $0, -4(%rbp)", "Check if string is empty")
        self.asm("    je .L16", "Jump if empty")
        self.asm("    movl $.LC1, %eax", "Return empty string")
        self.asm("    jmp .L17", "End")
        self.asm(".L16:", "Return the allocated string")
        self.asm("    movq -16(%rbp), %rax", "Load string pointer into rax")
        self.asm("    jmp .L17", "End")
        self.asm(".L15:", "Handle normal characters")
        self.asm("    movq -16(%rbp), %rax", "Load string pointer")
        self.asm("    movq %rax, %rdi", "Set pointer for strlen")
        self.asm("    call coolstrlen", "Get string length")
        self.asm("    mov %eax, %eax", "Ensure result is in eax")
        self.asm("    addq -16(%rbp), %rax", "Calculate destination address")
        self.asm("    movl -20(%rbp), %edx", "Load character")
        self.asm("    movb %dl, (%rax)", "Store character at destination")
        self.asm("    jmp .L20", "Repeat loop")
        self.asm(".L17:", "End")
        self.asm("    leave", "Restore stack and base pointer")
        self.asm("    ret", "Return from function")
        self.asm(".LFE3:", "Function end")
        self.asm("    .size coolgetstr, .-coolgetstr", "Define size of coolgetstr")
