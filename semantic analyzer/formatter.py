# formatter.py

from ast_nodes import (
    ClassNode, MethodFeature, AttributeInitFeature, AssignExpr,
    DynamicDispatchExpr, StaticDispatchExpr, SelfDispatchExpr,
    IfExpr, BlockExpr, SimpleExpr, LiteralExpr, UnaryExpr,
    BinaryExpr, LetExpr, CaseExpr, LetBinding, CaseElement,FormalNode, WhileExpr
)

class ASTFormatter:
    def formatProgram(self, program):
        return self.formatList(program, self.formatClass)

    def formatList(self, items, formatFunction):
        text = f"{len(items)}\n"
        for item in items:
            text += formatFunction(item)
        return text

    def formatId(self, idTuple):
        return f"{idTuple[0]}\n{idTuple[1]}\n"

    def formatFormal(self, formal):
        if isinstance(formal, FormalNode):
            nameFormatted = f"{formal.arg_name_lino}\n{formal.arg_name}\n"
            typeFormatted = f"{formal.arg_type_lino}\n{formal.arg_type}\n"
        else:
            nameFormatted = self.formatId(formal[0])
            typeFormatted = self.formatId(formal[1])
        return nameFormatted + typeFormatted

    def formatExpr(self, expr):
        if not expr:
            return ""
        text = f"{expr.line}\n"
        if isinstance(expr, SimpleExpr):
            if expr.name[1] == 'self':
                text += f"SELF_TYPE\n"
            else:
                text += f"{expr.annotatedType}\n"
        # elif isinstance(expr, BlockExpr):
        #     text += f"{expr.sharedType}\n"
        elif isinstance(expr, WhileExpr):
            text += f"Object\n"
        else:
            text += f"{expr.annotatedType}\n"
        
        if hasattr(expr, 'parent') and expr.parent:
            text += f"{expr.parent}\n"
        text += f"{expr.tag}\n"

        if isinstance(expr, AssignExpr):
            text += self.formatId(expr.var) + self.formatExpr(expr.rhs)
        elif isinstance(expr, DynamicDispatchExpr):
            text += self.formatExpr(expr.exp) + self.formatId(expr.method)
            text += self.formatList(expr.args, self.formatExpr)
        elif isinstance(expr, StaticDispatchExpr):
            text += self.formatExpr(expr.exp) + self.formatId(expr.type)
            text += self.formatId(expr.method) + self.formatList(expr.args, self.formatExpr)
        elif isinstance(expr, SelfDispatchExpr):
            text += self.formatId(expr.method) + self.formatList(expr.args, self.formatExpr)
        elif isinstance(expr, IfExpr):
            text += self.formatExpr(expr.predicate) + self.formatExpr(expr.thenExpr) + self.formatExpr(expr.elseExpr)
        elif isinstance(expr, BlockExpr):
            text += self.formatList(expr.body, self.formatExpr)
        elif isinstance(expr, SimpleExpr):
            text += self.formatId(expr.name)
        elif isinstance(expr, LiteralExpr):
            if expr.value or expr.value == "":
                text += f"{expr.value}\n"
        elif isinstance(expr, UnaryExpr):
            text += self.formatExpr(expr.expr)
        elif isinstance(expr, BinaryExpr):
            text += self.formatExpr(expr.expr1) + self.formatExpr(expr.expr2)
        elif isinstance(expr, LetExpr):
            text += self.formatList(expr.bindings, self.formatLetBinding) + self.formatExpr(expr.body)
        elif isinstance(expr, CaseExpr):
            text += self.formatExpr(expr.expr) + self.formatList(expr.elementsList, self.formatCaseElement)
        elif isinstance(expr, WhileExpr):
            text += self.formatExpr(expr.predicate) + self.formatExpr(expr.body)
        else:
            raise ValueError(f'Unrecognized expression: {expr}')
        return text

    def formatLetBinding(self, binding):
        text = f"{binding.bind}\n" + self.formatId(binding.var) + self.formatId(binding.type)
        if binding.bind == 'let_binding_init' and binding.expr:
            text += self.formatExpr(binding.expr)
        return text

    def formatCaseElement(self, element):
        return self.formatId(element.var) + self.formatId(element.type) + self.formatExpr(element.body)

    def formatFeature(self, feature):
        # print(feature)
        text = f"{feature.feature_type}\n"

        if isinstance(feature, MethodFeature):
            text += f"{feature.method_name_lino}\n{feature.method_name}\n"
            text += self.formatList(feature.formalsList, self.formatFormal)
            text += f"{feature.return_type_lino}\n{feature.return_type}\n"
            text += self.formatExpr(feature.body)
        else:
            # text += self.formatId(feature.type)
            text += f"{feature.attribute_name_lino}\n{feature.attribute_name}\n{feature.attribute_type_lino}\n{feature.attribute_type}\n"
            if isinstance(feature, AttributeInitFeature):
                text += self.formatExpr(feature.init_expr)
        # elif isinstance(feature, AttributeInitFeature):
        #     text += self.formatId(feature.type)
        #     if feature.init:
        #         text += self.formatExpr(feature.init)
        return text

    def formatClass(self, classNode):
        text= f"{classNode.lino}\n{classNode.class_name}\n{classNode.tag}\n"
        if classNode.tag == 'inherits' and classNode.parent_type:
            text += f"{classNode.parent_type_lino}\n{classNode.parent_type}\n"

        text += self.formatList(classNode.featureList, self.formatFeature)

        # text = self.formatId(classNode.class_name) + f"{classNode.tag}\n"
        # if classNode.tag == 'inherits' and classNode.parent:
        #     text += self.formatId(classNode.parent)
        # text += self.formatList(classNode.features, self.formatFeature)
        return text
