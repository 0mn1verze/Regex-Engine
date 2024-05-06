from parse import Token, Group
from typing import List
from dataclasses import dataclass

@dataclass
class StackState:
    isBacktrackable: bool
    state: Token | Group
    consumptions: List[int]

def stateMatchesStringAtIndex(state : Token | Group, s : str, i : int) -> List[bool|int]:
    """Matches string at a particular index to a particular state

    Args:
        state (Token | Group): state
        s (str): string
        i (int): index

    Raises:
        ValueError: If the type is not supported then there will be an error

    Returns:
        List[bool, int]: Returns whether or not the string matched and how many characters are in the match
    """
    # If out of bounds then there is nothing to match
    if i >= len(s):
        return [False, 0]

    # If wildcard then anything matches
    if state.type == 'wildcard':
        return [True, 1]

    # If it's just one element then match it
    if state.type == 'element':
        isMatch = state.value == s[i]
        return [isMatch, 1 if isMatch else 0]
    
    # If there are multiple elements, check if one of them matches
    if state.type == 'elements':
        isMatch = s[i] in state.value
        return [isMatch, 1 if isMatch else 0]
    
    # If the type is exclude, check if none of them matches
    if state.type == "exclude":
        isMatch = s[i] not in state.value
        return [isMatch, 1 if isMatch else 0]
    
    # If it is a group then call the test function for the group for the remaining part of the string
    if state.type == 'group':
        return test(state.value, s[i:])
    
    raise ValueError("Unsupported Element Type")



def test(states : List[Token | Group], s : str) -> List[bool|int]:
    """Test the string

    Args:
        states (List[Token  |  Group]): states from the parser
        s (str): string

    Raises:
        ValueError: raises error if there is an unsupported quantifier

    Returns:
        List[bool, int]: Returns whether or not the string matched and how many characters are in the match
    """
    # Stack for back tracking
    backtrackStack = []

    # Shallow copy queue to use for looping
    queue = states[:]
    i = 0

    # Get current state
    currentState = queue.pop(0)

    # Back tracking function
    def backtrack():
        nonlocal currentState, i

        # Insert the current state back into the queue because we are backtracking
        queue.insert(0, currentState)

        # Assume we could not backtrack at first
        couldBacktrack = False

        # Loop through the entire backtrack stack to see if there are elements that can be backtracked, and start there from scratch
        while len(backtrackStack):

            # Pop element from the backtrack stack
            item = backtrackStack.pop()
            isBacktrackable = item.isBacktrackable
            state = item.state
            consumptions = item.consumptions

            # If there is an element for us to backtrack then reverse its state
            if isBacktrackable:
                # If the element does not consume anything then we cannot backtrack (Should be redundant)
                if len(consumptions) == 0:
                    queue.insert(0, currentState)
                    continue
                # Restore the previous state
                n = consumptions.pop()
                i -= n
                # There may be multiple consumption stages, like from (b.*)+, so we add back the current stack state but without the newest consumption
                backtrackStack.append(StackState(isBacktrackable, state, consumptions))
                couldBacktrack = True
                break
                
            # If the element is non backtrackable then we can just reverse it and try an even earlier state
            queue.insert(0, state)
            i -= sum(consumptions)

        # If backtracking is successful then the new current state should be the first element of the queue
        if couldBacktrack:
            currentState = queue.pop(0)
        
        return couldBacktrack

    # While there are current states, we test them
    while currentState:
        match currentState.quantifier:
            case 'exactlyOne':
                # Matches the string at index i
                isMatch, consumed = stateMatchesStringAtIndex(currentState, s, i)

                # If it does not match, try backtracking and if that does not work then return false
                if not isMatch: 
                    # Keep track of the index as the backtracking function changes it
                    indexBeforeBacktracking = i
                    couldBacktrack = backtrack()
                    if not couldBacktrack:
                        return [False, indexBeforeBacktracking]
                    continue
                
                # Append the state to the backtracking stack
                backtrackStack.append(StackState(False, currentState, [consumed]))

                # Skip the consumed characters
                i += consumed
                # If the queue is empty then break out
                if not queue:
                    break
                # Get new current state
                currentState = queue.pop(0)
            case 'zeroOrOne':
                if i >= len(s):
                    backtrackStack.append(StackState(False, currentState, [0]))
                    # If the queue is empty then break out
                    if not queue:
                        break
                    # Get new current state
                    currentState = queue.pop(0)
                    continue
                # Matches the string at index i
                isMatch, consumed = stateMatchesStringAtIndex(currentState, s, i)
                # Append the state to the backtracking stack
                backtrackStack.append(StackState(isMatch and consumed > 0, currentState, [consumed]))
                # Skip the consumed characters
                i += consumed
                # If the queue is empty then break out
                if not queue:
                    break
                # Get new current state
                currentState = queue.pop(0)
            case 'zeroOrMore':
                backtrackState = StackState(True, currentState, [])

                while True:
                    if i >= len(s):
                        # If the state has not consumed any characters then its not backtrackable
                        if len(backtrackState.consumptions) == 0:
                            backtrackState.isBacktrackable = False
                            backtrackState.consumptions.append(0)
                        backtrackStack.append(backtrackState)
                        # If the queue is empty then break out
                        if not queue:
                            break
                        # Get new current state
                        currentState = queue.pop(0)
                        break
                    # Matches the string at index i
                    isMatch, consumed = stateMatchesStringAtIndex(currentState, s, i)

                    # If the string does not match then it either means the state matches partially or not at all
                    if not isMatch or consumed == 0:
                        # If the state has not consumed any characters then its not backtrackable
                        if len(backtrackState.consumptions) == 0:
                            backtrackState.isBacktrackable = False
                            backtrackState.consumptions.append(0)
                        backtrackStack.append(backtrackState)
                        # If the queue is empty then break out
                        if not queue:
                            break
                        # Get new current state
                        currentState = queue.pop(0)
                        break
                    # Add the number of consumed characters to the list
                    backtrackState.consumptions.append(consumed)
                    # Skip the consumed characters
                    i += consumed
                if not queue:
                    break
            # Raise error for unsupported operation
            case _:
                    raise ValueError("Unsupported Operation")
    return [True, i]
            
