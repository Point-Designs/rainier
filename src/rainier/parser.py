from __future__ import annotations
from .lexer import Lexer
from .ast import *

class Parser:
    def __init__(self, source: str):
        self.lexer = Lexer(source)

    def parse(self) -> Program:
        self.lexer.skip_newlines()
        statements = []
        while self.lexer.peek()[0] != "EOF":
            statements.append(self.parse_statement())
            self.lexer.skip_newlines()
        return Program(statements)

    def parse_statement(self) -> Node:
        tok = self.lexer.peek()
        if tok[0] == "def":
            return self.parse_def()
        if tok[0] == "class":
            return self.parse_class()
        if tok[0] == "if":
            return self.parse_if()
        if tok[0] == "while":
            return self.parse_while()
        if tok[0] == "return":
            self.lexer.next()
            expr = None
            if self.lexer.peek()[0] != "NEWLINE" and self.lexer.peek()[0] != "EOF" and self.lexer.peek()[0] != "end":
                expr = self.parse_expression()
            return Return(expr)
        expr = self.parse_expression()
        if isinstance(expr, Variable) and self.lexer.peek()[0] == "=":
            self.lexer.next()
            value = self.parse_expression()
            return Assignment(expr.name, value)
        return ExpressionStatement(expr)

    def parse_def(self) -> Def:
        self.lexer.expect("def")
        name = self.expect_ident()
        params = []
        if self.lexer.peek()[0] == "(":
            self.lexer.next()
            while self.lexer.peek()[0] != ")":
                params.append(self.expect_ident())
                if self.lexer.peek()[0] == ",":
                    self.lexer.next()
            self.lexer.next()
        while self.lexer.peek()[0] == "NEWLINE":
            self.lexer.next()
        body = self.parse_block_body()
        self.lexer.expect("end")
        return Def(name, params, body)

    def parse_class(self) -> ClassDef:
        self.lexer.expect("class")
        name = self.expect_ident()
        while self.lexer.peek()[0] == "NEWLINE":
            self.lexer.next()
        body = self.parse_block_body()
        self.lexer.expect("end")
        return ClassDef(name, body)

    def parse_if(self) -> If:
        self.lexer.expect("if")
        condition = self.parse_expression()
        self.lexer.skip_newlines()
        then_branch = self.parse_block_body(until_keywords={"elsif", "else", "end"})
        else_branch = None
        if self.lexer.peek()[0] == "elsif":
            else_branch = [self.parse_if()]
        elif self.lexer.peek()[0] == "else":
            self.lexer.next()
            self.lexer.skip_newlines()
            else_branch = self.parse_block_body()
        self.lexer.expect("end")
        return If(condition, then_branch, else_branch)

    def parse_while(self) -> While:
        self.lexer.expect("while")
        condition = self.parse_expression()
        self.lexer.skip_newlines()
        body = self.parse_block_body()
        self.lexer.expect("end")
        return While(condition, body)

    def parse_block_body(self, until_keywords: set[str] | None = None) -> list[Node]:
        statements: list[Node] = []
        while self.lexer.peek()[0] not in {"EOF", "end", "else", "elsif"} if until_keywords is None else self.lexer.peek()[0] not in until_keywords:
            statements.append(self.parse_statement())
            self.lexer.skip_newlines()
        return statements

    def parse_expression(self) -> Node:
        return self.parse_assignment()

    def parse_assignment(self) -> Node:
        expr = self.parse_or()
        return expr

    def parse_or(self) -> Node:
        expr = self.parse_and()
        while self.lexer.peek()[0] == "or":
            self.lexer.next()
            expr = BinaryOp("or", expr, self.parse_and())
        return expr

    def parse_and(self) -> Node:
        expr = self.parse_equality()
        while self.lexer.peek()[0] == "and":
            self.lexer.next()
            expr = BinaryOp("and", expr, self.parse_equality())
        return expr

    def parse_equality(self) -> Node:
        expr = self.parse_comparison()
        while self.lexer.peek()[0] in {"==", "!="}:
            op = self.lexer.next()[0]
            expr = BinaryOp(op, expr, self.parse_comparison())
        return expr

    def parse_comparison(self) -> Node:
        expr = self.parse_term()
        while self.lexer.peek()[0] in {"<", ">", "<=", ">="}:
            op = self.lexer.next()[0]
            expr = BinaryOp(op, expr, self.parse_term())
        return expr

    def parse_term(self) -> Node:
        expr = self.parse_factor()
        while self.lexer.peek()[0] in {"+", "-"}:
            op = self.lexer.next()[0]
            expr = BinaryOp(op, expr, self.parse_factor())
        return expr

    def parse_factor(self) -> Node:
        expr = self.parse_unary()
        while self.lexer.peek()[0] in {"*", "/"}:
            op = self.lexer.next()[0]
            expr = BinaryOp(op, expr, self.parse_unary())
        return expr

    def parse_unary(self) -> Node:
        if self.lexer.peek()[0] in {"-", "!"}:
            op = self.lexer.next()[0]
            return UnaryOp(op, self.parse_unary())
        return self.parse_call()

    def parse_call(self) -> Node:
        expr = self.parse_primary()
        while True:
            if self.lexer.peek()[0] == ".":
                self.lexer.next()
                name = self.expect_ident()
                expr = MemberAccess(expr, name)
                continue
            if self.lexer.peek()[0] == "(":
                self.lexer.next()
                args = []
                while self.lexer.peek()[0] != ")":
                    args.append(self.parse_expression())
                    if self.lexer.peek()[0] == ",":
                        self.lexer.next()
                self.lexer.next()
                expr = Call(expr, args)
                continue
            if self.lexer.peek()[0] not in {"EOF", "NEWLINE", ";", "end", "else", "elsif", "then", ")"}:
                if isinstance(expr, Variable) or isinstance(expr, MemberAccess) or isinstance(expr, Call):
                    next_expr = self.parse_primary()
                    expr = Call(expr, [next_expr])
                    continue
            break
        return expr

    def parse_primary(self) -> Node:
        tok = self.lexer.peek()
        if tok[0] == "NUMBER":
            self.lexer.next()
            if "." in tok[1]:
                return Literal(float(tok[1]))
            return Literal(int(tok[1]))
        if tok[0] == "STRING":
            self.lexer.next()
            return Literal(tok[1])
        if tok[0] == "true":
            self.lexer.next()
            return Literal(True)
        if tok[0] == "false":
            self.lexer.next()
            return Literal(False)
        if tok[0] == "nil":
            self.lexer.next()
            return Literal(None)
        if tok[0] == "self":
            self.lexer.next()
            return Self()
        if tok[0] == "INSTANCE_VAR":
            self.lexer.next()
            return InstanceVar(tok[1])
        if tok[0] == "new":
            self.lexer.next()
            class_name = self.expect_ident()
            args = []
            if self.lexer.peek()[0] == "(":
                self.lexer.next()
                while self.lexer.peek()[0] != ")":
                    args.append(self.parse_expression())
                    if self.lexer.peek()[0] == ",":
                        self.lexer.next()
                self.lexer.next()
            return NewExpr(class_name, args)
        if tok[0] == "(":
            self.lexer.next()
            expr = self.parse_expression()
            self.lexer.expect(")")
            return expr
        if tok[0] == "IDENT":
            self.lexer.next()
            return Variable(tok[1])
        raise SyntaxError(f"Unexpected token: {tok}")

    def expect_ident(self) -> str:
        tok = self.lexer.next()
        if tok[0] != "IDENT":
            raise SyntaxError(f"Expected identifier, got {tok}")
        return tok[1]
