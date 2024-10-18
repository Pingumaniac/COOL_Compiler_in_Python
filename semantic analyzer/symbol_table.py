# symbol_table.py

class SymbolTable:
    """A simple symbol table to manage scopes and symbols."""
    def __init__(self):
        self.class_data = []
        self.types = []
        self.scope_data =[]
        # self.class_methods = []

    def addClassSymbol(self, name, type):
        self.class_data.append((name, type))

    def defining_types(self, type_list):
        self.types = type_list
        self.types.append("SELF_TYPE")

    def defining_methods(self, method_list):
        self.methods = method_list

    def clearSymbolTable(self):
        self.class_data = []
        self.scope_data = []

    def clearScopeData(self):
        self.scope_data = []
        
    def recognize_type(self, type):
        if type in self.types:
            return True
        return False
    
    def retrieve_identifier_type(self, identifier):
        for scope in self.scope_data:
            for (name, type) in scope:
                if name == identifier:
                    return type
        for (name, type) in self.class_data:
            if name == identifier:
                return type
        return None

    def enter_scope(self, scope_data):
        new_scope = []
        for name, type in scope_data:
            new_scope.append((name, type))
        self.scope_data.append(new_scope)

    def exit_scope(self):
        self.scope_data.pop()

    # def startScope(self):
    #     self.data.append(("SCOPE", None))

    # def clearScope(self):
    #     i = len(self.data) - 1
    #     while i > 0 and self.data[i][0] != "SCOPE":
    #         i -= 1
    #     self.data = self.data[:i]

    def findSymbol(self, name):
        for scope in self.scope_data:
            for (n, t) in scope:
                if name == n:
                    return (n, t)
        for (n, t) in self.class_data:
            if name == n:
                return (n, t)
        return None
    # def isInScope(self, name):
    #     for (n, d) in reversed(self.data):
    #         if n == name:
    #             return (n, d)
    #         if n == "SCOPE":
    #             return None
    #     return None
