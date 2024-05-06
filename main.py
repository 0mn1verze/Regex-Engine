from parse import parse
from test import test

# Regex expression
regex = 'a*\.*.*[b-d]{3,4}'

# Parsing the expression into a state tree
states = parse(regex)

print(states)


# Example string
example = 'aaaa....ccccc'

# Test string
result = test(states, example)

print(result)