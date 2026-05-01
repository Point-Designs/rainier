from __future__ import annotations
from .ast import *

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class RubyObject:
    def __init__(self, klass: "RubyClass"):
        self.klass = klass
        self.instance_vars: dict[str, object] = {}

    def get(self, name: str):
        if name in self.instance_vars:
            return self.instance_vars[name]
        return self.klass.lookup_method(name)

    def set(self, name: str, value: object):
        self.instance_vars[name] = value

class RubyClass:
    def __init__(self, name: str, parent: "RubyClass" | None = None):
        self.name = name
        self.parent = parent
        self.methods: dict[str, Def] = {}

    def lookup_method(self, name: str):
        if name in self.methods:
            return self.methods[name]
        if self.parent:
            return self.parent.lookup_method(name)
        raise NameError(f"Undefined method '{name}' for class {self.name}")

class Environment:
    def __init__(self, parent: "Environment" | None = None):
        self.vars: dict[str, object] = {}
        self.parent = parent

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined variable '{name}'")

    def set(self, name: str, value: object):
        self.vars[name] = value

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.classes: dict[str, RubyClass] = {}
        self.setup_builtins()

    def setup_builtins(self):
        self.classes["Object"] = RubyClass("Object")
        self.globals.set("self", self)
        self.globals.set("puts", lambda *args: print(*args))
        self.globals.set("print", lambda *args: print(*args, end=""))
        self.globals.set("p", lambda *args: print(*[repr(arg) for arg in args]))

    def eval(self, node: Node, env: Environment | None = None, self_obj: RubyObject | None = None):
        if env is None:
            env = self.globals
        method = getattr(self, f"eval_{type(node).__name__}", None)
        if method is None:
            raise NotImplementedError(type(node).__name__)
        return method(node, env, self_obj)

    def eval_Program(self, node: Program, env: Environment | None, self_obj: RubyObject | None):
        value = None
        for stmt in node.statements:
            value = self.eval(stmt, env, self_obj)
        return value

    def eval_ExpressionStatement(self, node: ExpressionStatement, env: Environment, self_obj: RubyObject | None):
        return self.eval(node.expression, env, self_obj)

    def eval_Assignment(self, node: Assignment, env: Environment, self_obj: RubyObject | None):
        value = self.eval(node.expression, env, self_obj)
        if isinstance(node.target, InstanceVar):
            if self_obj is None:
                raise NameError("@ instance variable used outside of an object")
            self_obj.set(node.target.name, value)
        else:
            env.set(node.target.name, value)
        return value

    def eval_If(self, node: If, env: Environment, self_obj: RubyObject | None):
        condition = self.eval(node.condition, env, self_obj)
        branch = node.then_branch if condition else node.else_branch or []
        value = None
        for stmt in branch:
            value = self.eval(stmt, env, self_obj)
        return value

    def eval_While(self, node: While, env: Environment, self_obj: RubyObject | None):
        value = None
        while self.eval(node.condition, env, self_obj):
            for stmt in node.body:
                value = self.eval(stmt, env, self_obj)
        return value

    def eval_Def(self, node: Def, env: Environment, self_obj: RubyObject | None):
        env.set(node.name, node)
        return node

    def eval_ClassDef(self, node: ClassDef, env: Environment, self_obj: RubyObject | None):
        klass = RubyClass(node.name, self.classes.get("Object"))
        self.classes[node.name] = klass
        class_env = Environment(env)
        for stmt in node.body:
            if isinstance(stmt, Def):
                klass.methods[stmt.name] = stmt
            else:
                self.eval(stmt, class_env)
        return klass

    def eval_Return(self, node: Return, env: Environment, self_obj: RubyObject | None):
        raise ReturnSignal(self.eval(node.expression, env, self_obj) if node.expression else None)

    def eval_BinaryOp(self, node: BinaryOp, env: Environment, self_obj: RubyObject | None):
        left = self.eval(node.left, env, self_obj)
        right = self.eval(node.right, env, self_obj)
        if node.operator == "+":
            return left + right
        if node.operator == "-":
            return left - right
        if node.operator == "*":
            return left * right
        if node.operator == "/":
            return left / right
        if node.operator == "==":
            return left == right
        if node.operator == "!=":
            return left != right
        if node.operator == "<":
            return left < right
        if node.operator == ">":
            return left > right
        if node.operator == "<=":
            return left <= right
        if node.operator == ">=":
            return left >= right
        if node.operator == "and":
            return left and right
        if node.operator == "or":
            return left or right
        raise NotImplementedError(node.operator)

    def eval_UnaryOp(self, node: UnaryOp, env: Environment, self_obj: RubyObject | None):
        value = self.eval(node.operand, env, self_obj)
        if node.operator == "-":
            return -value
        if node.operator == "!":
            return not value
        raise NotImplementedError(node.operator)

    def eval_Literal(self, node: Literal, env: Environment, self_obj: RubyObject | None):
        return node.value

    def eval_Variable(self, node: Variable, env: Environment, self_obj: RubyObject | None):
        if node.name == "self":
            return self_obj or self
        return env.get(node.name)

    def eval_InstanceVar(self, node: InstanceVar, env: Environment, self_obj: RubyObject | None):
        if self_obj is None:
            raise NameError("@ instance variable used outside of an object")
        return self_obj.get(node.name)

    def eval_Self(self, node: Self, env: Environment, self_obj: RubyObject | None):
        return self_obj or self

    def eval_Call(self, node: Call, env: Environment, self_obj: RubyObject | None):
        callee = self.eval(node.callee, env, self_obj)
        args = [self.eval(arg, env, self_obj) for arg in node.args]
        if callable(callee):
            return callee(*args)
        if isinstance(callee, RubyObject):
            raise TypeError("Cannot call object directly")
        if isinstance(node.callee, MemberAccess):
            receiver = self.eval(node.callee.receiver, env, self_obj)
            method_name = node.callee.name
            if isinstance(receiver, RubyObject):
                method_def = receiver.klass.lookup_method(method_name)
                return self.call_method(receiver, method_def, args)
        if isinstance(node.callee, Variable):
            target = env.get(node.callee.name)
            if isinstance(target, Def):
                return self.call_function(target, args)
        raise NameError(f"Undefined callable: {node.callee}")

    def eval_MemberAccess(self, node: MemberAccess, env: Environment, self_obj: RubyObject | None):
        receiver = self.eval(node.receiver, env, self_obj)
        if isinstance(receiver, RubyObject):
            if node.name in receiver.instance_vars:
                return receiver.instance_vars[node.name]
            method_def = receiver.klass.lookup_method(node.name)
            return self.call_method(receiver, method_def, [])
        if isinstance(receiver, RubyClass):
            return receiver.lookup_method(node.name)
        raise NameError(f"Member access on non-object: {receiver}")

    def eval_NewExpr(self, node: NewExpr, env: Environment, self_obj: RubyObject | None):
        klass = self.classes.get(node.class_name)
        if klass is None:
            raise NameError(f"Undefined class '{node.class_name}'")
        obj = RubyObject(klass)
        init = klass.methods.get("initialize")
        if init:
            self.call_method(obj, init, [self.eval(arg, env, self_obj) for arg in node.args])
        return obj

    def call_function(self, function: Def, args: list[object]):
        call_env = Environment(self.globals)
        for name, value in zip(function.params, args):
            call_env.set(name, value)
        try:
            for stmt in function.body:
                self.eval(stmt, call_env)
        except ReturnSignal as signal:
            return signal.value
        return None

    def call_method(self, receiver: RubyObject, method: Def, args: list[object]):
        call_env = Environment(self.globals)
        call_env.set("self", receiver)
        for name, value in zip(method.params, args):
            call_env.set(name, value)
        try:
            for stmt in method.body:
                self.eval(stmt, call_env, receiver)
        except ReturnSignal as signal:
            return signal.value
        return None
