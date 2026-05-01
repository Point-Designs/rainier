import pytest
from rainier.parser import Parser
from rainier.interpreter import Interpreter


def run(source: str):
    program = Parser(source).parse()
    return Interpreter().eval(program)


def test_arithmetic_and_assignment():
    result = run("x = 2 + 3\nx")
    assert result == 5


def test_if_expression():
    result = run("if true\n  10\nelse\n  20\nend")
    assert result == 10


def test_class_and_method():
    source = "class Greeter\n  def greet\n    puts \"Hello\"\n  end\nend\ng = new Greeter\ng.greet"
    assert run(source) is None


def test_method_with_params():
    source = "def add(a, b)\n  a + b\nend\nadd(3, 4)"
    assert run(source) == 7
