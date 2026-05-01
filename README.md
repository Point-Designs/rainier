# Rainier

Rainier is a minimal Ruby-inspired scripting language with:

- dynamic typing
- method calls without parentheses
- class definitions and object creation
- basic control flow (`if`, `while`)
- simple built-in `puts`

## Getting started

Run Rainier scripts with Python:

```bash
python -m rainier examples/hello.rnr
```

Or start the interactive REPL:

```bash
python -m rainier
```

## Example

```ruby
class Greeter
  def initialize(name)
    @name = name
  end

  def greet
    puts "Hello #{@name}"
  end
end

g = new Greeter("World")
g.greet
```

## Project structure

- `src/rainier/` — language implementation
- `examples/` — sample Rainier scripts
- `tests/` — unit tests
