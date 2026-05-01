from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Node:
    pass

@dataclass
class Program(Node):
    statements: list[Node]

@dataclass
class ExpressionStatement(Node):
    expression: Node

@dataclass
class Assignment(Node):
    name: str
    expression: Node

@dataclass
class If(Node):
    condition: Node
    then_branch: list[Node]
    else_branch: list[Node] | None

@dataclass
class While(Node):
    condition: Node
    body: list[Node]

@dataclass
class Def(Node):
    name: str
    params: list[str]
    body: list[Node]

@dataclass
class ClassDef(Node):
    name: str
    body: list[Node]

@dataclass
class Return(Node):
    expression: Node | None

@dataclass
class BinaryOp(Node):
    operator: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    operator: str
    operand: Node

@dataclass
class Literal(Node):
    value: Any

@dataclass
class Variable(Node):
    name: str

@dataclass
class InstanceVar(Node):
    name: str

@dataclass
class Call(Node):
    callee: Node
    args: list[Node]
    block: Block | None = None

@dataclass
class Block(Node):
    params: list[str]
    body: list[Node]

@dataclass
class MemberAccess(Node):
    receiver: Node
    name: str

@dataclass
class Self(Node):
    pass

@dataclass
class NewExpr(Node):
    class_name: str
    args: list[Node]
