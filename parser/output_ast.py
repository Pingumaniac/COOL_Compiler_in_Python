import sys

class OutputAST:
    def __init__(self, ast, output_filename):
        self.ast = ast
        self.fout = open(output_filename, 'w')

    def print_list(self, lst, print_element_function):
        self.fout.write(str(len(lst)) + "\n")
        for elem in lst:
            print_element_function(elem)

    def print_identifier(self, identifier_tuple):
        # identifier_tuple = (lineno, name)
        self.fout.write(str(identifier_tuple[0]) + "\n")
        self.fout.write(identifier_tuple[1] + "\n")

    def print_exp(self, exp_tuple):
        # print(exp_tuple)
        lineno, exp_type = exp_tuple[0], exp_tuple[1]

        # added to skip printing paren_exp
        if exp_type != 'paren_exp':
            self.fout.write(str(lineno) + "\n")
            self.fout.write(exp_type + "\n")


        if exp_type in ['plus', 'minus', 'times', 'divide', 'lt', 'le', 'eq', 'while']:
            # (lineno, type, left, right)
            self.print_exp(exp_tuple[2])
            self.print_exp(exp_tuple[3])

        elif exp_type == 'if':
            # (lineno, 'if', cond, then, else)
            self.print_exp(exp_tuple[2])
            self.print_exp(exp_tuple[3])
            self.print_exp(exp_tuple[4])

        elif exp_type == 'assign':
            # (lineno, 'assign', identifier, expr)
            self.print_identifier(exp_tuple[2])
            self.print_exp(exp_tuple[3])

        elif exp_type == 'block':
            # (lineno, 'block', explist_semi)
            self.print_list(exp_tuple[2], self.print_exp)

        elif exp_type == 'dynamic_dispatch':
            # (lineno, 'dynamic_dispatch', expr, identifier, explist_comma)
            self.print_exp(exp_tuple[2])
            self.print_identifier(exp_tuple[3])
            self.print_list(exp_tuple[4], self.print_exp)

        elif exp_type == 'static_dispatch':
            # (lineno, 'static_dispatch', expr, type, identifier, explist_comma)
            self.print_exp(exp_tuple[2])
            self.print_identifier(exp_tuple[3])
            self.print_identifier(exp_tuple[4])
            self.print_list(exp_tuple[5], self.print_exp)

        elif exp_type == 'self_dispatch':
            # (lineno, 'self_dispatch', identifier, explist_comma)
            self.print_identifier(exp_tuple[2])
            self.print_list(exp_tuple[3], self.print_exp)

        elif exp_type in ['integer', 'string']:
            # (lineno, 'integer', value) or (lineno, 'string', value)
            self.fout.write(str(exp_tuple[2]) + "\n")

        elif exp_type in ['isvoid', 'not', 'negate']:
            # (lineno, 'isvoid', expr) etc.
            self.print_exp(exp_tuple[2])

        elif exp_type in ['new', 'identifier']:
            # (lineno, 'new', type) or (lineno, 'identifier', identifier)
            if exp_type == 'new':
                self.print_identifier(exp_tuple[2])
            else:
                self.print_identifier(exp_tuple[2])

        elif exp_type == 'let':
            # (lineno, 'let', bindings, expr)
            self.print_list(exp_tuple[2], self.print_binding)
            self.print_exp(exp_tuple[3])

        elif exp_type == 'case':
            # (lineno, 'case', expr, elementlist)
            self.print_exp(exp_tuple[2])
            self.print_list(exp_tuple[3], self.print_element)

        elif exp_type == 'paren_exp':
            self.print_exp(exp_tuple[2])

        elif exp_type == 'true':
            pass

        elif exp_type == 'false':
            pass
        
        else:
            print("unhandled expression type: ", exp_type)
            print(exp_tuple)
            sys.exit(1)

    def print_element(self, element_tuple):
        # element_tuple = (lineno, identifier, type, expr)
        self.print_identifier(element_tuple[1])
        self.print_identifier(element_tuple[2])
        self.print_exp(element_tuple[3])

    def print_binding(self, binding_tuple):
        # binding_tuple = (lineno, 'attribute_no_init'/'attribute_init', identifier, type, [expr])
        binding_type = binding_tuple[1]
        if binding_type == 'attribute_no_init':
            self.fout.write("let_binding_no_init\n")
            self.print_identifier(binding_tuple[2])
            self.print_identifier(binding_tuple[3])
        elif binding_type == 'attribute_init':
            self.fout.write("let_binding_init\n")
            self.print_identifier(binding_tuple[2])
            self.print_identifier(binding_tuple[3])
            self.print_exp(binding_tuple[4])
        else:
            print("unhandled binding")
            sys.exit(1)

    def print_feature(self, feature_tuple):
        # feature_tuple = (lineno, 'attribute_no_init'/'attribute_init'/'method', ...)
        # print("feature_tuple:")
        # print(feature_tuple)
        feature_type = feature_tuple[1]
        if feature_type == 'attribute_no_init':
            self.fout.write("attribute_no_init\n")
            self.print_identifier(feature_tuple[2])
            self.print_identifier(feature_tuple[3])
        elif feature_type == 'attribute_init':
            self.fout.write("attribute_init\n")
            self.print_identifier(feature_tuple[2])
            self.print_identifier(feature_tuple[3])
            self.print_exp(feature_tuple[4])
        elif feature_type == 'method':
            self.fout.write("method\n")
            self.print_identifier(feature_tuple[2])
            self.print_list(feature_tuple[3], self.print_formal)
            self.print_identifier(feature_tuple[4])
            self.print_exp(feature_tuple[5])
        else:
            print("unhandled feature")
            sys.exit(1)

    def print_class(self, class_tuple):
        # class_tuple = (lineno, 'class_noinherit'/'class_inherit', ...)
        class_type = class_tuple[1]
        if class_type == 'class_noinherit':
            self.print_identifier(class_tuple[2])
            self.fout.write("no_inherits\n")
            self.print_list(class_tuple[3], self.print_feature)
        elif class_type == 'class_inherit':
            self.print_identifier(class_tuple[2])
            self.fout.write("inherits\n")
            self.print_identifier(class_tuple[3])
            self.print_list(class_tuple[4], self.print_feature)
        else:
            print("unhandled class")
            sys.exit(1)

    def print_formal(self, formal_tuple):
        # formal_tuple = (lineno, identifier, type)
        self.print_identifier(formal_tuple[1])
        self.print_identifier(formal_tuple[2])

    def print_program(self, program_ast):
        self.print_list(program_ast, self.print_class)

    def output_ast_file(self):
        self.print_program(self.ast)
        self.fout.close()
