#!/usr/bin/env python
#coding:utf-8
## Based on ecmavisitor.py from slimit:
## /usr/local/lib/python*/dist-packages/slimit-*/slimit/visitors/ecmavisitor.py

###############################################################################
#
# Copyright (c) 2011 Ruslan Spivak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from slimit import ast

class LabVisitor(object):

    def __init__(self):
        self.indent_level = 0
        #my code here
        self.blacklistGlobalName = ['document','eval','window','grader']
        self.dangerPropNames = ['__proto__','constructor','__defineGetter__']
        self.replaceSafePropName = '__invalid__'
        self.thischeck = 'this_check(this)'
        self.prefix = 'sandbox_'
        self.bracketIndexCheck = 'bracket_check'
        self.dangerObjPropNames = ['"toString"','"valueOf"']
        self.returnCheck = 'return_check'
        self.objcheck = 'objcheck'

    def _make_indent(self):
        return ' ' * self.indent_level

    def visit(self, node):
        #print "visit,node=%r" % node
        method = 'visit_%s' % node.__class__.__name__
        #print "================"
        #print "visit,method=",method
        return getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node):
        return 'GEN: %r' % node

    def visit_Program(self, node):
        s = '\n'.join(self.visit(child) for child in node)
        #print "visit_Program=%r" % s
        return s

    def visit_Block(self, node):
        s = '{\n'
        self.indent_level += 2
        s += '\n'.join(
            self._make_indent() + self.visit(child) for child in node)
        self.indent_level -= 2
        s += '\n' + self._make_indent() + '}'
        return s

    def visit_VarStatement(self, node):
        s = 'var %s;' % ', '.join(self.visit(child) for child in node)
        return s

    def visit_VarDecl(self, node):
        output = []
        output.append(self.visit(node.identifier))
        if node.initializer is not None:
            output.append(' = %s' % self.visit(node.initializer))
        return ''.join(output)

    def visit_Identifier(self, node):
        #把document等全局变量加上sandbox_前缀
        if getattr(node, '_in_expression', False) and getattr(node,'_mangle_candidate',False):
            if node._in_expression and node._mangle_candidate:
                #print "get Identifier=%s" % node.value
                #检查是否需要给变量名加上前缀
                for name in self.blacklistGlobalName:
                    if name == node.value:
                        #print "this Identifier is blacker"
                        node.value = self.prefix + node.value
        return node.value

    def visit_Assign(self, node):
        # Note: if node.op is ':' this "assignment" is actually a property in
        # an object literal, i.e. { foo: 1, "bar": 2 }. In that case, node.left
        # is either an ast.Identifier or an ast.String.
        if node.op == ':':
            template = '%s%s %s'
        else:
            template = '%s %s %s'
        if getattr(node, '_parens', False):
            template = '(%s)' % template
        return template % (
            self.visit(node.left), node.op, self.visit(node.right))

    def visit_Number(self, node):
        return node.value

    def visit_Comma(self, node):
        return '%s, %s' % (self.visit(node.left), self.visit(node.right))

    def visit_EmptyStatement(self, node):
        return node.value

    def visit_If(self, node):
        s = 'if ('
        if node.predicate is not None:
            s += self.visit(node.predicate)
        s += ') '
        s += self.visit(node.consequent)
        if node.alternative is not None:
            s += ' else '
            s += self.visit(node.alternative)
        return s

    def visit_Boolean(self, node):
        return node.value

    def visit_For(self, node):
        s = 'for ('
        if node.init is not None:
            s += self.visit(node.init)
        if node.init is None:
            s += ' ; '
        elif isinstance(node.init, (ast.Assign, ast.Comma)):
            s += '; '
        else:
            s += ' '
        if node.cond is not None:
            s += self.visit(node.cond)
        s += '; '
        if node.count is not None:
            s += self.visit(node.count)
        s += ') ' + self.visit(node.statement)
        return s

    def visit_ForIn(self, node):
        if isinstance(node.item, ast.VarDecl):
            template = 'for (var %s in %s) '
        else:
            template = 'for (%s in %s) '
        s = template % (self.visit(node.item), self.visit(node.iterable))
        s += self.visit(node.statement)
        return s

    def visit_BinOp(self, node):
        if getattr(node, '_parens', False):
            template = '(%s %s %s)'
        else:
            template = '%s %s %s'
        return template % (
            self.visit(node.left), node.op, self.visit(node.right))

    def visit_UnaryOp(self, node):
        s = self.visit(node.value)
        if node.postfix:
            s += node.op
        elif node.op in ('delete', 'void', 'typeof'):
            s = '%s %s' % (node.op, s)
        else:
            s = '%s%s' % (node.op, s)
        if getattr(node, '_parens', False):
            s = '(%s)' % s
        return s

    def visit_ExprStatement(self, node):
        return '%s;' % self.visit(node.expr)

    def visit_DoWhile(self, node):
        s = 'do '
        s += self.visit(node.statement)
        s += ' while (%s);' % self.visit(node.predicate)
        return s

    def visit_While(self, node):
        s = 'while (%s) ' % self.visit(node.predicate)
        s += self.visit(node.statement)
        return s

    def visit_Null(self, node):
        return 'null'

    def visit_String(self, node):
        return node.value

    def visit_Continue(self, node):
        if node.identifier is not None:
            s = 'continue %s;' % self.visit_Identifier(node.identifier)
        else:
            s = 'continue;'
        return s

    def visit_Break(self, node):
        if node.identifier is not None:
            s = 'break %s;' % self.visit_Identifier(node.identifier)
        else:
            s = 'break;'
        return s

    def visit_Return(self, node):
        if node.expr is None:
            return 'return;'
        else:
            if getattr(node,'felix_hook_tostring',False):
                tempalte = 'return '+self.returnCheck+'(%s);'
                return tempalte % self.visit(node.expr)
            return 'return %s;' % self.visit(node.expr)

    def visit_With(self, node):
        s = 'with (%s) ' % self.visit(node.expr)
        s += self.visit(node.statement)
        return s

    def visit_Label(self, node):
        s = '%s: %s' % (
            self.visit(node.identifier), self.visit(node.statement))
        return s

    def visit_Switch(self, node):
        s = 'switch (%s) {\n' % self.visit(node.expr)
        self.indent_level += 2
        for case in node.cases:
            s += self._make_indent() + self.visit_Case(case)
        if node.default is not None:
            s += self.visit_Default(node.default)
        self.indent_level -= 2
        s += self._make_indent() + '}'
        return s

    def visit_Case(self, node):
        s = 'case %s:\n' % self.visit(node.expr)
        self.indent_level += 2
        elements = '\n'.join(self._make_indent() + self.visit(element)
                             for element in node.elements)
        if elements:
            s += elements + '\n'
        self.indent_level -= 2
        return s

    def visit_Default(self, node):
        s = self._make_indent() + 'default:\n'
        self.indent_level += 2
        s += '\n'.join(self._make_indent() + self.visit(element)
                       for element in node.elements)
        if node.elements is not None:
            s += '\n'
        self.indent_level -= 2
        return s

    def visit_Throw(self, node):
        s = 'throw %s;' % self.visit(node.expr)
        return s

    def visit_Debugger(self, node):
        return '%s;' % node.value

    def visit_Try(self, node):
        s = 'try '
        s += self.visit(node.statements)
        if node.catch is not None:
            s += ' ' + self.visit(node.catch)
        if node.fin is not None:
            s += ' ' + self.visit(node.fin)
        return s

    def visit_Catch(self, node):
        s = 'catch (%s) %s' % (
            self.visit(node.identifier), self.visit(node.elements))
        return s

    def visit_Finally(self, node):
        s = 'finally %s' % self.visit(node.elements)
        return s

    def visit_FuncDecl(self, node):
        self.indent_level += 2
        elements = '\n'.join(self._make_indent() + self.visit(element)
                             for element in node.elements)
        self.indent_level -= 2

        s = 'function %s(%s) {\n%s' % (
            self.visit(node.identifier),
            ', '.join(self.visit(param) for param in node.parameters),
            elements,
            )
        s += '\n' + self._make_indent() + '}'
        return s

    def visit_FuncExpr(self, node):
        self.indent_level += 2
        elements = '\n'.join(self._make_indent() + self.visit(element)
                             for element in node.elements)
        self.indent_level -= 2

        ident = node.identifier
        ident = '' if ident is None else ' %s' % self.visit(ident)

        header = 'function%s(%s)'
        if getattr(node, '_parens', False):
            header = '(' + header
        s = (header + ' {\n%s') % (
            ident,
            ', '.join(self.visit(param) for param in node.parameters),
            elements,
            )
        s += '\n' + self._make_indent() + '}'
        if getattr(node, '_parens', False):
            s += ')'
        return s

    def visit_Conditional(self, node):
        if getattr(node, '_parens', False):
            template = '(%s ? %s : %s)'
        else:
            template = '%s ? %s : %s'

        s = template % (
            self.visit(node.predicate),
            self.visit(node.consequent), self.visit(node.alternative))
        return s

    def visit_Regex(self, node):
        if getattr(node, '_parens', False):
            return '(%s)' % node.value
        else:
            return node.value

    def visit_NewExpr(self, node):
        #mycode here
        if 'Function' == node.identifier.value:
            s = 'new %s()' % (self.visit(node.identifier))
        else:
            s = 'new %s(%s)' % (
                self.visit(node.identifier),
                ', '.join(self.visit(arg) for arg in node.args)
            )
        return s

    def visit_DotAccessor(self, node):
        #print "visit_DotAccessor(%r,%r)" % (node.node, node.identifier)

        #mycode here,运行时检查调用eval的函数的类型，如果是window就直接返回null
        needobjcheck = False
        #TODO 这样检查并不全面
        if node.identifier.value == 'eval':
            needobjcheck = True

        if getattr(node, '_parens', False):
            if needobjcheck:
                template = '('+self.objcheck+'(%s)'+'.%s)'
            else:
                template = '(%s.%s)'
        else:
            if needobjcheck:
                template = self.objcheck+'(%s)'+'.%s'
            else:
                template = '%s.%s'

        #replace the danerous propname to invalid name
        for propname in self.dangerPropNames:
            if propname == node.identifier.value:
                node.identifier.value = self.replaceSafePropName

        s = template % (self.visit(node.node), self.visit(node.identifier))
        return s

    def visit_BracketAccessor(self, node):
        #my code here
        template = '%s['+self.bracketIndexCheck+'(%s)]'
        #print "visit_BracketAccessor template=",template
        s = template % (self.visit(node.node), self.visit(node.expr))
        return s

    def visit_FunctionCall(self, node):
        #mycode here,并没有考虑很全面
        if getattr(node.identifier,"value",False):
            if node.identifier.value == 'setTimeout':
                if not node.args[0].__class__.__name__ == 'FuncExpr':
                    # 跳过第一个参数
                    s = '%s(%s)' % (self.visit(node.identifier),
                                    ', '.join(self.visit(arg) for arg in node.args[1:]))
                    return s

        s = '%s(%s)' % (self.visit(node.identifier),
                        ', '.join(self.visit(arg) for arg in node.args))
        return s

    def visit_Object(self, node):
        # This is an object literal with a list of properties. Each property
        # will be an ast.Assign with op = ':'. So { foo: 1, "bar": 2 } is
        #   Object([Assign(':', Identifier('foo'), Number('1')),
        #           Assign(':', String('"bar"'), Number('2'))])

        #TODO 遍历找到node.properties中为Assign的node，并且其right node为FuncExpr，并且其left node的value="toString"等，
        # 则找到FuncExpr中elements为Return的node，给它加上标志，在visit这个node时，加上动态检测
        for prop in node.properties:
            if "Assign" == prop.__class__.__name__:
                for black in self.dangerObjPropNames:
                    if prop.left.value == black:
                        if "FuncExpr" == prop.right.__class__.__name__:
                            for ele in prop.right.elements:
                                if "Return" == ele.__class__.__name__:
                                    # find it,and setattr a flag
                                    setattr(ele, 'felix_hook_tostring', True)

        s = '{\n'
        self.indent_level += 2
        s += ',\n'.join(self._make_indent() + self.visit(prop)
                        for prop in node.properties)
        self.indent_level -= 2
        if node.properties:
            s += '\n'
        s += self._make_indent() + '}'
        return s

    def visit_Array(self, node):
        s = '['
        length = len(node.items) - 1
        for index, item in enumerate(node.items):
            if isinstance(item, ast.Elision):
                s += ','
            elif index != length:
                s += self.visit(item) + ','
            else:
                s += self.visit(item)
        s += ']'
        return s

    def visit_This(self, node):
        # check this on runtime.
        return self.thischeck

