class SymbolTable:
    def __init__(self):
        # Initialize with a global scope
        self.scopes = [{}]

    def add_symbol(self, name, data):
        # Adds a symbol to the current (innermost) scope.
        self.scopes[-1][name] = data

    def enter_scope(self):
        # Enters a new scope by pushing a new dictionary onto the scope stack.
        self.scopes.append({})

    def exit_scope(self):
        # Exits the current scope by popping the top dictionary off the scope stack.
        # Raises an error if attempting to exit the global scope.
        if len(self.scopes) == 1:
            raise RuntimeError("Cannot exit the global scope.")
        self.scopes.pop()

    def find_symbol(self, name):
        # Searches for a symbol starting from the innermost scope to the outermost.
        # Returns the associated data if found, else returns None.
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_in_current_scope(self, name):
        # Checks if a symbol exists in the current (innermost) scope.
        # Returns the associated data if found, else returns None.
        return self.scopes[-1].get(name, None)
