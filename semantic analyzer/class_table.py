# class_table.py

from formatter import ASTFormatter
import sys
from ast_nodes import ExprNode, LetExpr, CaseExpr, LetBinding, AssignExpr, \
    DynamicDispatchExpr, StaticDispatchExpr, SelfDispatchExpr, IfExpr, \
    BlockExpr, SimpleExpr, LiteralExpr, UnaryExpr, BinaryExpr, WhileExpr, FormalNode

class ClassTable:
    def __init__(self):
        self.data = {}
        self.initializeBuiltInClasses()

    def initializeBuiltInClasses(self):
        # Initialize built-in classes: Object, Bool, Int, IO, String
        self.data['Object'] = {
            'parent': None,
            'attributes': [],
            'methods': [
                ('abort', [], ('0', 'Object'), ('0', 'Object', 'internal', 'Object.abort'), 'Object'),
                ('copy', [], ('0', 'SELF_TYPE'), ('0', 'SELF_TYPE', 'internal', 'Object.copy'), 'Object'),
                ('type_name', [], ('0', 'String'), ('0', 'String', 'internal', 'Object.type_name'), 'Object')
            ]
        }
        self.data['Bool'] = {
            'parent': 'Object',
            'attributes': [],
            'methods': []
        }
        self.data['Int'] = {
            'parent': 'Object',
            'attributes': [],
            'methods': []
        }
        self.data['IO'] = {
            'parent': 'Object',
            'attributes': [],
            'methods': [
                ('in_int', [], ('0', 'Int'), ('0', 'Int', 'internal', 'IO.in_int'), 'IO'),
                ('in_string', [], ('0', 'String'), ('0', 'String', 'internal', 'IO.in_string'), 'IO'),
                ('out_int', [('x', 'Int')], ('0', 'SELF_TYPE'), ('0', 'SELF_TYPE', 'internal', 'IO.out_int'), 'IO'),
                ('out_string', [('x', 'String')], ('0', 'SELF_TYPE'), ('0', 'SELF_TYPE', 'internal', 'IO.out_string'), 'IO')
            ]
        }
        self.data['String'] = {
            'parent': 'Object',
            'attributes': [],
            'methods': [
                ('concat', [('s', 'String')], ('0', 'String'), ('0', 'String', 'internal', 'String.concat'), 'String'),
                ('length', [], ('0', 'Int'), ('0', 'Int', 'internal', 'String.length'), 'String'),
                ('substr', [('i', 'Int'), ('l', 'Int')], ('0', 'String'), ('0', 'String', 'internal', 'String.substr'), 'String')
            ]
        }

    def completeClassTable(self, ast):
        for c in self.data:
            parent = self.data[c]['parent']
            if parent != None and parent in self.data:
                parent_attributes = self.data[parent]['attributes'].copy()
                parent_methods = self.data[parent]['methods'].copy()
                self.data[c]['attributes'] += parent_attributes
                self.data[c]['methods'] += parent_methods

        for c in ast:
            if c.class_name == 'SELFTYPE':
                print(f"ERROR: {f.lino}: Type-Check: SELF_TYPE cannot be a class name")
                sys.exit(1)
            self.addClass(c.class_name, c.parent_type, c.lino, c.parent_type_lino)
            for f in c.featureList:
                if f.feature_type == "method":
                    self.addMethod(c.class_name, f)
                elif f.feature_type == "attribute_init" or f.feature_type == "attribute_no_init":
                    self.addAttribute(c.class_name, f)
                else:
                    print(f"ERROR: {f.lino}: Type-Check: feature", f.feature_type, "not found")
                    sys.exit(1)
        self.validateParents()
        if "Main" not in self.data:
            print("ERROR: 0: Type-Check: Main class not found")
            sys.exit(1)
        
        has_main_method = False
        for m in self.data['Main']['methods']:
            if m[0] == 'main' and m[1] == []:
                has_main_method = True
        
        if not has_main_method:
            print("ERROR: 0: Type-Check: main method with 0 param in Main class not found")
            sys.exit(1)
        
        self.addinheritedAttributes()
    

    def validateParents(self):
        for c in self.data:
            parent = self.data[c]['parent']
            if parent != None:
                if parent not in self.data:
                    print("ERROR:", self.data[c]["line"], f": Type-Check: class {c}'s parent {parent} not defined")
                    sys.exit(1)

    def addinheritedAttributes(self):
        for c in self.data:
            parentList = []
            parent = self.data[c]['parent']
            while parent != None:
                parentList.append(parent)
                parent = self.data[parent]['parent']
            for parent in parentList:
                for attribute in self.data[parent]['attributes']:
                    if self.getAttribute(c, attribute[0]) == None:
                        self.data[c]['attributes'].append(attribute)
                for method in self.data[parent]['methods']:
                    if self.getMethod(c, method[0]) == None:
                        self.data[c]['methods'].append(method)
                    

    def addClass(self, namee, parenttName, lino, parent_type_lino):
        if namee in self.data:
            print(f"ERROR: {lino}: Type-Check: class {namee} redefined")
            sys.exit(1)
        if namee == 'SELF_TYPE':
            print(f"ERROR: {lino}: Type-Check: class named SELF_TYPE")
            sys.exit(1)
        if parenttName in ["Bool", "String", "Integer"]:
            print(f"ERROR: {lino}: Type-Check: class {namee} inherits from unsupported Primitive type")
            sys.exit(1)
        if parenttName in self.data:
            self.data[namee] = {'parent': parenttName, 'attributes': self.data[parenttName]['attributes'].copy(), 'methods': self.data[parenttName]['methods'].copy()}
        else:
            self.data[namee] = {'parent': parenttName, 'attributes': [], 'methods': [], "line": parent_type_lino}
        (isCircular, cycle_class) = self.checkCircularInheritance(namee, set(), None)
        if isCircular:
            print("ERROR: 0: Type-Check: inheritance cycle:", cycle_class, namee)
            sys.exit(1)

        return self
    
    def checkCircularInheritance(self, name, visited, lastclass):
        if name in visited:
            return (True, lastclass)
        visited.add(name)
        parent = self.getParent(name)
        if parent is None or parent not in self.data:
            return (False, None)
        return self.checkCircularInheritance(parent, visited, name)

    def getClass(self, name):
        return name if name in self.data else None

    def getParent(self, name):
        return self.data[name]['parent'] if name in self.data else None

    def allClasses(self):
        return sorted(self.data.keys())

    def addAttribute(self, className, feature):
        for a in self.data[className]['attributes']:
            if a[0] == feature.attribute_name:
                print("ERROR:", feature.attribute_name_lino, ": Type-Check: class", className, "redefines attribute", feature.attribute_name)
                sys.exit(1)
        if feature.attribute_name == 'self':
            print(f"ERROR: {feature.attribute_name_lino}: Type-Check: cann't name an attribute self")
            sys.exit(1)

        if feature.feature_type == "attribute_init":
            self.data[className]['attributes'].append((feature.attribute_name, feature.attribute_type, feature.init_expr))
        elif feature.feature_type == "attribute_no_init":
            self.data[className]['attributes'].append((feature.attribute_name, feature.attribute_type, None))
        return self


    def getAttribute(self, className, attributeName):
        for a in self.data[className]['attributes']:
            if a[0] == attributeName:
                return a
        return None

    def findAttribute(self, className, attributeName):
        if className is None:
            return None
        a = self.getAttribute(className, attributeName)
        if a is not None:
            return a
        return self.findAttribute(self.getParent(className), attributeName)

    def allAttributes(self, name):
        if name is None:
            return []
        overrides = {}
        alist = []
        inheritedAttributes = self.allAttributes(self.getParent(name))
        for i in inheritedAttributes:
            x = self.getAttribute(name, i[0])
            if x is None:
                alist.append(i)
            else:
                alist.append(x)
                overrides[x[0]] = True
        for a in self.data[name]['attributes']:
            if a[0] in overrides:
                continue
            alist.append(a)
        return alist

    def inheritedAttributes(self, name):
        if name is None:
            return []
        return self.allAttributes(self.getParent(name))
    
    def formalEquals(self,formalList1, formalList2):
        if len(formalList1) != len(formalList2):
            return False
        
        for i in range(len(formalList1)):
            f1 = formalList1[i]
            if isinstance(f1, FormalNode):
                f1_type = f1.arg_type
                f1_name = f1.arg_name
            else:
                f1_type = f1[1]
                f1_name = f1[0]
            f2 = formalList2[i]
            if isinstance(f2, FormalNode):
                f2_type = f2.arg_type
                f2_name = f2.arg_name
            else:
                f2_type = f2[1]
                f2_name = f2[0]
            if f1_name != f2_name or f1_type!=f2_type:
                return False
        return True

    def addMethod(self, className, feature):
        overiding = False
        method_to_overide = None
        for methodd in self.data[className]['methods']:
            inherited_method_name = methodd[0]
            if inherited_method_name == feature.method_name:
                inherited_method_formals = methodd[1]
                overriding_method_formals = feature.formalsList
                if not self.formalEquals(inherited_method_formals,overriding_method_formals):
                    print(f"ERROR: {feature.method_name_lino}: Type-Check: Overiding function have different formals")
                    exit(1)
                if methodd[2][1] != feature.return_type:
                    print(f"ERROR: {feature.return_type_lino}: Type-Check: Overiding function have different return types")
                    exit(1)
                overiding = True
                method_to_overide = methodd
        
        if overiding:
            self.data[className]['methods'].remove(method_to_overide)

        self.data[className]['methods'].append((feature.method_name, feature.formalsList, (feature.return_type_lino ,feature.return_type), feature.body, className))
        return self

    def getMethod(self, className, methodName):
        for m in self.data[className]['methods']:
            if m[0] == methodName:
                return m
        return None

    def findMethod(self, className, methodName):
        if className is None:
            return None
        m = self.getMethod(className, methodName)
        if m is not None:
            return m
        return self.findMethod(self.getParent(className), methodName)

    def allMethods(self, name):
        if name is None:
            return []
        overrides = {}
        mlist = []
        inheritedMethods = self.allMethods(self.getParent(name))
        for i in inheritedMethods:
            x = self.getMethod(name, i[0])
            if x is None:
                mlist.append(i)
            else:
                mlist.append(x)
                overrides[x[0]] = True
        for m in self.data[name]['methods']:
            if m[0] in overrides:
                continue
            mlist.append(m)
        return mlist

    def inheritedMethods(self, name):
        if name is None:
            return []
        return self.allMethods(self.getParent(name))

    def parentMap(self):
        text = ['parent_map', str(len(self.data) - 1)]  # Exclude Object
        for cls in sorted(self.data.keys()):
            if cls == 'Object':
                continue
            text.append(cls)
            text.append(self.data[cls]['parent'])
        return "\n".join(text)

    def classMap(self, formatter: ASTFormatter):
        text = ['class_map', str(len(self.data))]
        for cls in sorted(self.data.keys()):
            text.append(cls)
            attributes = self.allAttributes(cls)
            text.append(str(len(attributes)))
            for attr in attributes:
                if attr[2] is None:
                    text.append("no_initializer")
                else:
                    text.append("initializer")
                text.append(attr[0])
                text.append(attr[1])
                if attr[2] is not None:
                    text.append(formatter.formatExpr(attr[2]).rstrip("\n"))
        return "\n".join(text)

    def implementationMap(self, formatter: ASTFormatter):
        text = ['implementation_map', str(len(self.data))]
        for cls in sorted(self.data.keys()):
            text.append(cls)
            methods = self.allMethods(cls)
            text.append(str(len(methods)))
            for m in methods:
                
                text.append(m[0])
                text.append(str(len(m[1])))
                for f in m[1]:
                    if isinstance(f, FormalNode):
                        text.append(f.arg_name)
                    else:
                        text.append(f[0])
                
                text.append(m[4])  # Defining class

                
                if isinstance(m[3], ExprNode):
                    # text.append(formatter.formatExpr(m[3]).rstrip("\n"))
                    text.append(formatter.formatExpr(m[3])[:-1])
                else:
                    if len(m[3]) == 4 and m[3][0] == '0' and m[3][2] == 'internal':
                        text.extend(m[3])
                    else:
                        # text.append(formatter.formatExpr(m[3]).rstrip("\n"))
                        text.append(formatter.formatExpr(m[3]))
                


        return "\n".join(text)
