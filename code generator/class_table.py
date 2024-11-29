# class_table.py

class ClassTable:
    def __init__(self):
        self.data = {}
        # Initialize predefined classes
        self.data['Object'] = {
            'parent': None,
            'attribs': [],
            'methods': [
                ('abort', [], ('0','Object'), ('0','Object','internal','Object.abort'), 'Object'),
                ('copy', [], ('0','SELF_TYPE'), ('0','SELF_TYPE','internal','Object.copy'), 'Object'),
                ('type_name', [], ('0','String'), ('0','String', 'internal','Object.type_name'), 'Object')]}
        self.data['Bool'] = {
            'parent': 'Object',
            'attribs': [],
            'methods': []}
        self.data['Int'] = {
            'parent': 'Object',
            'attribs': [],
            'methods': []}
        self.data['IO'] = {
            'parent': 'Object',
            'attribs': [],
            'methods': [
                ('in_int', [], ('0','IO'), ('0','Int','internal','IO.in_int'), 'IO'),
                ('in_string', [], ('0','IO'), ('0','String','internal','IO.in_string'), 'IO'),
                ('out_int', [('x','Int')], ('0','IO'), ('0','SELF_TYPE','internal','IO.out_int'), 'IO'),
                ('out_string', [('x','String')], ('0','IO'), ('0','SELF_TYPE','internal','IO.out_string'), 'IO')]}
        self.data['String'] = {
            'parent': 'Object',
            'attribs': [],
            'methods': [
                ('concat', [('s','String')], ('0','String'), ('0','String','internal','String.concat'), 'String'),
                ('length', [], ('0','Int'), ('0','Int','internal','String.length'), 'String'),
                ('substr', [('i','Int'),('l','Int')], ('0','String'), ('0','String','internal','String.substr'), 'String')]}

    def add_class(self, name, parent_name):
        if name in self.data:
            pass
        if parent_name is None:
            parent_name = 'Object'
        self.data[name] = { 'parent': parent_name, 'attribs': [], 'methods': [] }

    def get_class(self, name):
        return name if name in self.data else None

    def get_parent(self, name):
        return self.data[name]['parent'] if name in self.data else None

    def all_classes(self):
        return sorted(self.data.keys())

    def add_attribute(self, cname, aname, type_, init):
        if cname not in self.data:
            print(f"Error: Class {cname} not defined.")
            exit()
        self.data[cname]['attribs'].append((aname, type_, init))

    def get_attribute(self, cname, aname):
        for a in self.data[cname]['attribs']:
            if a[0][1] == aname:
                return a
        return None

    def find_attribute(self, cname, aname):
        if cname is None:
            return None
        a = self.get_attribute(cname, aname)
        if a is not None:
            return a
        return self.find_attribute(self.get_parent(cname), aname)

    def all_attributes(self, name):
        if name is None:
            return []
        alist = self.all_attributes(self.get_parent(name))
        overrides = {a[0][1]: True for a in self.data[name]['attribs']}
        # Remove overridden attributes
        alist = [a for a in alist if a[0][1] not in overrides]
        # Add current class's attributes
        alist += self.data[name]['attribs']
        return alist

    def inherited_attributes(self, name):
        return self.all_attributes(self.get_parent(name))

    def add_method(self, cname, mname, args, type_, body):
        if cname not in self.data:
            print(f"Error: Class {cname} not defined.")
            exit()
        self.data[cname]['methods'].append((mname, args, type_, body, cname))

    def get_method(self, cname, mname):
        for m in self.data[cname]['methods']:
            if m[0] == mname:
                return m
        return None

    def find_method(self, cname, mname):
        if cname is None:
            return None
        m = self.get_method(cname, mname)
        if m is not None:
            return m
        return self.find_method(self.get_parent(cname), mname)

    def all_methods(self, name):
        if name is None:
            return []
        mlist = self.all_methods(self.get_parent(name))
        overrides = {m[0]: True for m in self.data[name]['methods']}
        # Remove overridden methods
        mlist = [m for m in mlist if m[0] not in overrides]
        # Add current class's methods
        mlist += self.data[name]['methods']
        return mlist

    def declared_methods(self, name):
        return self.data[name]['methods']

    def inherited_methods(self, name):
        return self.all_methods(self.get_parent(name))
    
    def get_method_index(self, class_name, method_name):
        """
        Get the index of a method in the vtable of a class.

        Parameters:
            class_name (str): The name of the class where the dispatch occurs.
            method_name (str): The name of the method being called.

        Returns:
            int: The index of the method in the vtable, or -1 if the method is not found.
        """
        # Retrieve all methods in vtable order
        methods = self.all_methods(class_name)
        # Find the index of the method
        for index, method in enumerate(methods):
            if method[0] == method_name:  # Compare method names
                return index

        # Method not found
        return -1
    

    