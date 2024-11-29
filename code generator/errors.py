# errors.py

class RuntimeErrorHandler:
    def __init__(self, asm):
        self.asm = asm
        self.error_labels = {
            'dispatch_void': "ERROR_dispatch_void",
            'division_zero': "ERROR_division_zero",
            'case_error': "ERROR_case_error"
        }
        self.define_error_messages()

    def define_error_messages(self):
        for error, label in self.error_labels.items():
            self.asm(f"{label}:","")
            # Define the error message with a placeholder for the line number
            # Example: "ERROR: 42: Exception: dispatch void"
            self.asm(f'    .byte ' + ', '.join(f"'{c}'" for c in f'ERROR: %d: Exception: {error.replace("_", " ")}') + ', 10, 0')

    def handle_error(self, error_type, line_number):
        label = self.error_labels.get(error_type)
        if label:
            # Move the line number into `rsi`
            self.asm(f"    movq ${line_number}, %rsi", f"Load line number {line_number} into rsi")

            # Use `lea` with the correct syntax to load the label address into `rdi`
            self.asm(f"    lea {label}(%rip), %rdi", f"Load address of {error_type} error message into rdi")

            # Clear `rax` (no floating-point arguments for `printf`)
            self.asm("    xorq %rax, %rax", "No floating-point arguments for printf")

            # Call `printf`
            self.asm("    call printf", "Call printf to print the error message")

            # Set exit status to 1 and exit the program
            self.asm("    movq $1, %rdi", "Set exit status to 1")
            self.asm("    call exit", "Exit the program")
        else:
            print(f"Unhandled error type: {error_type}")
            exit(1)

