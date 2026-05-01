import argparse
from .parser import Parser
from .interpreter import Interpreter

BANNER = "Rainier 0.1.0 - Ruby-inspired scripting language"


def run_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as infile:
        source = infile.read()
    program = Parser(source).parse()
    interpreter = Interpreter()
    interpreter.eval(program)


def repl() -> None:
    interpreter = Interpreter()
    print(BANNER)
    while True:
        try:
            line = input("rainier> ")
        except EOFError:
            break
        if not line.strip():
            continue
        try:
            program = Parser(line).parse()
            result = interpreter.eval(program)
            if result is not None:
                print(result)
        except Exception as exc:
            print(f"Error: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rainier Ruby-inspired interpreter")
    parser.add_argument("path", nargs="?", help="Source file to run")
    args = parser.parse_args()
    if args.path:
        run_file(args.path)
    else:
        repl()


if __name__ == "__main__":
    main()
