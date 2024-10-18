# ast_nodes.py

class ASTNode:
    """Base class for all AST nodes."""
    pass

class ClassNode(ASTNode):
    def __init__(self, class_name, lino, inherits, parent_type, parent_type_lino, featureList):
        self.class_name = class_name
        self.lino = lino
        self.tag = inherits
        self.parent_type = parent_type
        self.parent_type_lino = parent_type_lino
        self.featureList = featureList

class FormalNode(ASTNode):
    def __init__(self, arg_name_lino, arg_name, arg_type_lino, arg_type):
        self.arg_name_lino = arg_name_lino
        self.arg_name = arg_name
        self.arg_type_lino = arg_type_lino
        self.arg_type = arg_type


class FeatureNode(ASTNode):
    """Base class for features within a class."""
    pass

class MethodFeature(FeatureNode):
    def __init__(self, method_name_lino, method_name, formalsList, return_type, return_type_lino, body):
        self.feature_type = "method"
        self.method_name_lino = method_name_lino
        self.method_name = method_name
        self.formalsList = formalsList
        self.return_type = return_type
        self.return_type_lino = return_type_lino
        self.body = body

class AttributeInitFeature(FeatureNode):
    def __init__(self, attribute_name_lino, attribute_name, attribute_type_lino, attribute_type, init_expr):
        self.feature_type = "attribute_init"
        self.attribute_name_lino = attribute_name_lino
        self.attribute_name = attribute_name
        self.attribute_type_lino = attribute_type_lino
        self.attribute_type = attribute_type
        self.init_expr = init_expr

class AttributeNoInitFeature(FeatureNode):
    def __init__(self, attribute_name_lino, attribute_name, attribute_type_lino, attribute_type):
        self.feature_type = "attribute_no_init"
        self.attribute_name_lino = attribute_name_lino
        self.attribute_name = attribute_name
        self.attribute_type_lino = attribute_type_lino
        self.attribute_type = attribute_type





class ExprNode(ASTNode):
    """Base class for all expressions."""
    pass

class AssignExpr(ExprNode):
    def __init__(self, line, tag, var, rhs):
        self.line = line
        self.tag = tag
        self.var = var  # Tuple (line, id)
        self.rhs = rhs  # ExprNode

class DynamicDispatchExpr(ExprNode):
    def __init__(self, line, tag, exp, method, args):
        self.line = line
        self.tag = tag
        self.exp = exp  # ExprNode
        self.method = method  # Tuple (line, id)
        self.args = args  # List of ExprNode

class StaticDispatchExpr(ExprNode):
    def __init__(self, line, tag, exp, type, method, args):
        self.line = line
        self.tag = tag
        self.exp = exp  # ExprNode
        self.type = type  # Tuple (line, id)
        self.method = method  # Tuple (line, id)
        self.args = args  # List of ExprNode

class SelfDispatchExpr(ExprNode):
    def __init__(self, line, tag, method, args):
        self.line = line
        self.tag = tag
        self.method = method  # Tuple (line, id)
        self.args = args  # List of ExprNode

class IfExpr(ExprNode):
    def __init__(self, line, tag, predicate, thenExpr, elseExpr):
        self.line = line
        self.tag = tag
        self.predicate = predicate  # ExprNode
        self.thenExpr = thenExpr  # ExprNode
        self.elseExpr = elseExpr  # ExprNode

class WhileExpr(ExprNode):
    def __init__(self, line, tag, predicate, body):
        self.line = line
        self.tag = tag
        self.predicate = predicate  # ExprNode
        self.body = body  # ExprNode

class BlockExpr(ExprNode):
    def __init__(self, line, tag, body):
        self.line = line
        self.tag = tag
        self.body = body  # List of ExprNode

class SimpleExpr(ExprNode):
    def __init__(self, line, tag, name):
        self.line = line
        self.tag = tag
        self.name = name  # Tuple (line, id)

class LiteralExpr(ExprNode):
    def __init__(self, line, tag, value=None):
        self.line = line
        self.tag = tag
        self.value = value  # For integers and strings

class UnaryExpr(ExprNode):
    def __init__(self, line, tag, expr):
        self.line = line
        self.tag = tag
        self.expr = expr  # ExprNode

class BinaryExpr(ExprNode):
    def __init__(self, line, tag, expr1, expr2):
        self.line = line
        self.tag = tag
        self.expr1 = expr1  # ExprNode
        self.expr2 = expr2  # ExprNode

class LetExpr(ExprNode):
    def __init__(self, line, tag, bindings, body):
        self.line = line
        self.tag = tag
        self.bindings = bindings  # List of LetBinding
        self.body = body  # ExprNode

class Identifier(ExprNode):
    def __init__(self, line, ident_name):
        self.line = line
        self.ident_name = ident_name

class PlusExpr(ExprNode):
    def __init__(self, line, e1, e2):
        self.line = line
        self.e1 = e1  # ExprNode
        self.e2 = e2  # ExprNode

class Int(ExprNode):
    def __init__(self, line, int_val):
        self.line = line
        self.int_val = int_val


class String(ExprNode):
    def __init__(self, line, str_val):
        self.line = line
        self.str_val = str_val

class CaseExpr(ExprNode):
    def __init__(self, line, tag, expr, elementsList):
        self.line = line
        self.tag = tag
        self.expr = expr  # ExprNode
        self.elementsList = elementsList  # List of CaseElement

class LetBinding:
    def __init__(self, bind, var, type, expr=None):
        self.bind = bind
        self.var = var  # Tuple (line, id)
        self.type = type  # Tuple (line, id)
        self.expr = expr  # ExprNode or None

class CaseElement:
    def __init__(self, var, type, body):
        self.var = var  # Tuple (line, id)
        self.type = type  # Tuple (line, id)
        self.body = body  # ExprNode
