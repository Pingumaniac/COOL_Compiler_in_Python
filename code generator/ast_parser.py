# ast_parser.py

from class_table import ClassTable

class ASTParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        with open(self.filename, 'r') as file:
            self.file = file
            self.get_line = self._get_line
            self.get_list = self._get_list
            self.get_id = self._get_id
            self.get_formal = self._get_formal
            self.get_expr = self._get_expr
            self.get_let_binding = self._get_let_binding
            self.get_case_element = self._get_case_element
            self.get_feature = self._get_feature
            self.get_class = self._get_class
            self.get_class_map_attrib = self._get_class_map_attrib
            self.get_class_map = self._get_class_map
            self.get_implementation_map_method = self._get_implementation_map_method
            self.get_implementation_map = self._get_implementation_map
            self.get_parent_map = self._get_parent_map

            # Read sections
            self.get_line()  # Skip header
            class_map = self.get_list(self.get_class_map)
            self.get_line()  # Skip separator
            implementation_map = self.get_list(self.get_implementation_map)
            self.get_line()  # Skip separator
            parent_map = self.get_list(self.get_parent_map)
            program_classlist = self.get_list(self.get_class)

        # Build Class Table
        ctab = ClassTable()
        for (cname, parent) in parent_map:
            ctab.add_class(cname, parent)
        for (cname, attrs) in class_map:
            for a in attrs:
                ctab.add_attribute(cname, a[1], a[2], a[3])
        for (cname, methods) in implementation_map:
            for m in methods:
                if not ctab.find_method(cname, m[0]):
                    ctab.add_method(cname, m[0], m[1], m[2], m[3])

        return ctab, program_classlist

    def _get_line(self):
        return self.file.readline().rstrip("\n\r")

    def _get_list(self, get_function):
        count = int(self.get_line())
        return [get_function() for _ in range(count)]

    def _get_id(self):
        line = self.get_line()
        identifier = self.get_line()
        return (line, identifier)

    def _get_formal(self):
        name = self.get_id()
        type_ = self.get_id()
        return (name, type_)

    def _get_expr(self):
        line = self.get_line()
        type_ = self.get_line()
        tag = self.get_line()

        if tag == 'assign':
            var = self.get_id()
            rhs = self.get_expr()
            return [line, type_, tag, var, rhs]
        elif tag == 'dynamic_dispatch':
            exp = self.get_expr()
            method = self.get_id()
            args = self.get_list(self.get_expr)
            return [line, type_, tag, exp, None, method, args]
        elif tag == 'static_dispatch':
            exp = self.get_expr()
            type_ = self.get_id()
            method = self.get_id()
            args = self.get_list(self.get_expr)
            return [line, type_, tag, exp, type_, method, args]
        elif tag == 'self_dispatch':
            method = self.get_id()
            args = self.get_list(self.get_expr)
            return [line, type_, tag, None, None, method, args]
        elif tag == 'if':
            prd = self.get_expr()
            thn = self.get_expr()
            els = self.get_expr()
            return [line, type_, tag, prd, thn, els]
        elif tag == 'block':
            body = self.get_list(self.get_expr)
            return [line, type_, tag, body]
        elif tag in ['new', 'identifier']:
            name = self.get_id()
            return [line, type_, tag, name]
        elif tag in ['integer', 'string']:
            value = self.get_line()
            return [line, type_, tag, value]
        elif tag in ['true', 'false']:
            return [line, type_, tag]
        elif tag in ['negate', 'not', 'isvoid']:
            exp = self.get_expr()
            return [line, type_, tag, exp]
        elif tag in ['while','plus','minus','times','divide','lt','le','eq']:
            exp1 = self.get_expr()
            exp2 = self.get_expr()
            return [line, type_, tag, exp1, exp2]
        elif tag == 'let':
            binding = self.get_list(self.get_let_binding)
            body = self.get_expr()
            return [line, type_, tag, binding, body]
        elif tag == 'case':
            exp = self.get_expr()
            elementslist = self.get_list(self.get_case_element)
            return [line, type_, tag, exp, elementslist]
        elif tag == 'internal':
            parent = self.get_line()
            return [line, type_, tag, parent]
        else:
            print('Unrecognized expression', line, tag)
            exit()

    def _get_let_binding(self):
        bind = self.get_line()
        var = self.get_id()
        type_ = self.get_id()
        exp = None
        if bind == 'let_binding_init':
            exp = self.get_expr()
        return (bind, var, type_, exp)

    def _get_case_element(self):
        var = self.get_id()
        type_ = self.get_id()
        body = self.get_expr()
        return (var, type_, body)

    def _get_feature(self):
        tag = self.get_line()
        name = self.get_id()
        if tag == 'method':
            formalslist = self.get_list(self.get_formal)
            type_ = self.get_id()
            body = self.get_expr()
            return (tag, name, formalslist, type_, body)
        else:
            type_ = self.get_id()
            init = None
            if tag == 'attribute_init':
                init = self.get_expr()
            return (tag, name, type_, init)

    def _get_class(self):
        name = self.get_id()
        tag = self.get_line()
        parent = None
        if tag == 'inherits':
            parent = self.get_id()
        featurelist = self.get_list(self.get_feature)
        return (name, tag, parent, featurelist)

    def _get_class_map_attrib(self):
        tag = self.get_line()
        name = self.get_line()
        type_ = self.get_line()
        init = None
        if tag == "initializer":
            init = self.get_expr()
        return (tag, (0,name), (0,type_), init)

    def _get_class_map(self):
        name = self.get_line()
        attribs = self.get_list(self.get_class_map_attrib)
        return (name, attribs)

    def _get_implementation_map_method(self):
        name = self.get_line()
        formals = self.get_list(self.get_line)
        type_ = self.get_line()
        body = self.get_expr()
        return (name, formals, type_, body)

    def _get_implementation_map(self):
        name = self.get_line()
        methods = self.get_list(self.get_implementation_map_method)
        return (name, methods)

    def _get_parent_map(self):
        name = self.get_line()
        parent = self.get_line()
        return (name, parent)
