from dataclasses import dataclass
from typing import List

@dataclass
class Token:
    type: str
    value: str
    quantifier: str

@dataclass
class Group:
    type: str
    value: List[Token]
    quantifier: str

def getCharRange(start, end):
    # Get the range of characters between two end points
    return ''.join(list(map(chr, range(ord(start), ord(end)+1))))

def parse(re: str):
    """Regex Parser

    Limited support for different regex operators

    Supports wildcard(.), zeroOrOne(?), zeroOrMore(*), oneOrMore(+), groups(()), backslash(\\), 
             ranges([]), specific number of characters({m,n}), negation(^)

    Args:
        re (str): regular expression string

    Raises:
        ValueError: Expression is invalid and cannot be parsed

    Returns:
        List : state tree
    """
    stack = [[]]
    i = 0

    re = re.strip()

    while i < len(re):
        match re[i]:
            case '.':
                stack[-1].append(Token("wildcard", ".", "exactlyOne"))
                i += 1
            case '?':
                # if the last element of the stack is empty then it means there are no elements before it, so the syntax is incorrect
                if not stack[-1]:
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Get the last element from the last element of the stack
                last = stack[-1][-1]
                if (last.quantifier != 'exactlyOne'):
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Update quantifier
                last.quantifier = 'zeroOrOne'
                i += 1
            case '*':
                # if the last element of the stack is empty then it means there are no elements before it, so the syntax is incorrect
                if not stack[-1]:
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Get the last element from the last element of the stack
                last = stack[-1][-1]
                # If the element already has a quantifier then its a syntax error (In the case of this program)
                if (last.quantifier != 'exactlyOne'):
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Update quantifier
                last.quantifier = 'zeroOrMore'
                i += 1
            case '+':
                # if the last element of the stack is empty then it means there are no elements before it, so the syntax is incorrect
                if not stack[-1]:
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Get the last element from the last element of the stack
                last = stack[-1][-1]
                # If the element already has a quantifier then its a syntax error (In the case of this program)
                if (last.quantifier != 'exactlyOne'):
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # A trick to handle the one or more quantifier, by seperating it into an exactly one quantifier and a zero or more quantifier
                copy = Token(last.type, last.value, 'zeroOrMore')
                stack[-1].append(copy)
                i += 1
            case '{':
                # if the last element of the stack is empty then it means there are no elements before it, so the syntax is incorrects
                if not stack[-1]:
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Get the last element from the last element of the stack
                last = stack[-1][-1]
                # If the element already has a quantifier then its a syntax error (In the case of this program)
                if (last.quantifier != 'exactlyOne'):
                    raise ValueError("Quantifier must follow an unquantified element or group")
                # Get the text inside the {}
                ranges = ''
                i += 1
                while i < len(re) and re[i] != '}':
                    ranges += re[i]
                    i += 1
                # If there is not closing } then the syntax is wrong
                if i == len(re) - 1 and re[i] != '}':
                    raise ValueError(f"No brackets to close at index {i}")
                
                # Try to parse the string inside the quantifier
                try:
                    # Handle ranges
                    if ',' in ranges:
                        min = int(ranges.split(',')[0])
                        max = int(ranges.split(',')[1])
                        if max <= min:
                            raise ValueError()
                        if min >= 1:
                            # Use a trick to change the quantifier into a bunch of exactly one and zero or one quantifiers
                            while min > 1:
                                copy = Token(last.type, last.value, 'exactlyOne')
                                stack[-1].append(copy)
                                min -= 1
                                max -= 1
                            while max > 1:
                                copy = Token(last.type, last.value, 'zeroOrOne')
                                stack[-1].append(copy)
                                max -= 1
                        else:
                            last.quantifier = f"-{max}"
                    # Handle fixed number
                    else:
                        num = int(ranges)
                        if num >= 1:
                            # Use a trick to change the quantifier into a bunch of exactly one quantifiers
                            while num > 1:
                                copy = Token(last.type, last.value, 'exactlyOne')
                                stack[-1].append(copy)
                                num -= 1
                        else:
                            raise ValueError("Expecting >0 value in brackets")
                except:
                    raise ValueError("Quantifier not accepted")
                i += 1
            case '[':
                # Get the text inside []
                ranges = ''
                i += 1
                while i < len(re) and re[i] != ']':
                    ranges += re[i]
                    i += 1
                # If bracket is not closed then there is a syntax error
                if i == len(re) - 1 and re[i] != ']':
                    raise ValueError(f"No brackets to close at index {i}")
                # Check which type it is
                tokenType = "elements" if ranges[0] != "^" else "exclude"
                # If it is exclude type then remove the first character from the char ranges
                if ranges[0] == "^":
                    ranges = ranges[1:]
                # Parse the text
                if '-' in ranges and ranges[0] != '-':
                    charRanges = ''
                    # For each range (-), parse it and add the possible characters to a character range
                    indicies = [i for i, char in enumerate(ranges) if char == '-']
                    charRanges += ranges[:indicies[0] - 1]
                    for j in indicies:
                        # Getting start of range and end of range
                        start = ranges[j-1]
                        end = ranges[j+1]
                        # Checking if the syntax is allowed
                        if len(start) != 1 or len(end) != 1 or ord(start) >= ord(end):
                            raise ValueError("Quantifier not accepted")
                        if start.isdigit() and end.isdigit():
                            charRanges += getCharRange(start, end)
                        elif start.isupper() and end.isupper():
                            charRanges += getCharRange(start, end)
                        elif start.islower() and end.islower():
                            charRanges += getCharRange(start, end)
                        else:
                            raise ValueError("Range not accepted")
                    stack[-1].append(Token(tokenType, f"{charRanges}", "exactlyOne"))
                else:
                    # If there is no range(-), just use the text as the matching criterion
                    stack[-1].append(Token(tokenType, ranges, "exactlyOne"))
                i += 1
            case '(':
                # Append a new list to collect all the elements in the group
                stack.append([])
                i += 1
            case ')':
                # If the length of the stack is less than or equal to 1 then there is no groups, therefore there is a syntax error
                if len(stack) <= 1:
                    raise ValueError(f"No group to close at index {i}")
                # Pop the group from the stack and store it inside a group element
                states = stack.pop()
                stack[-1].append(Group("group", states, 'exactlyOne'))
                i += 1
            case '\\':
                # If there is no element after the \ then it's a syntax error
                if (i + 1 >= len(re)):
                    raise ValueError(f"Bad escape character at index {i}")
                stack[-1].append(Token("element", re[i+1], "exactlyOne"))
                i += 2
            case _:
                stack[-1].append(Token("element", re[i], "exactlyOne"))
                i += 1

    if (len(stack) != 1):
        raise ValueError('Unmatched groups in regular expression')
    
    return stack[0]
    


