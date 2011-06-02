# basicparser.py
#
# Sets up a reasonable parser for the game.
#
# Provides: global_parser, understand

from textadv.gamesystem import parser
import re

global_parser = parser.Parser()
global_parser.add_default_words()

def understand(command, action) :
    """Takes a textual form of a command and adds it to the parser so
    that action is executed.  The following is an example of the
    textual form:

    give [something y] to [something z]

    The understood nonterminals are [something varname] and [anything
    varname] where "something" refers to something the actor can
    immediately access, where "anything" refers to anything in the
    game world.

    Other nonterminals:
    - [direction x] for a cardinal direction
    
    - [text x] for taking some number of arbitrary words, and then
      binding x to the resulting string.

    - [object oid] for matching against a particular object.
    """

    parts = []
    lastindex = 0
    for match in re.finditer(r"\[([A-Za-z]+)\s+([A-Za-z0-9_]+)\]", command) :
        parts.extend(command[lastindex:match.start()].split())
        lastindex = match.end()
        if match.group(1).lower() == "something" :
            parts.append(parser.Something(match.group(2)))
        elif match.group(1).lower() == "anything" :
            parts.append(parser.Anything(match.group(2)))
        elif match.group(1).lower() == "direction" :
            parts.append(parser.Direction(match.group(2)))
        elif match.group(1).lower() == "text" :
            parts.append(parser.TextNonTerminal(match.group(2)))
        elif match.group(1).lower() == "object" :
            parts.append(parser.ObjectNonTerminal(match.group(2)))
        else :
            raise Exception("Bad form "+match.group(1))
    parts.extend(command[lastindex:].split())
    global_parser.add_sentence(parts, action)

def add_direction(direction, synonyms=None) :
    """Adds a direction to the parser for [direction x]."""
    direction = direction.lower()
    if synonyms == None :
        synonyms = [direction]
    global_parser.add_global_direction(direction, synonyms)

class ParseSomething(parser.NonTerminal) :
    """Tries to parse text which matches [something].  Can be given to
    a parser object.  Returns the actual objects themselves."""
    my_something = parser.Something("x")
    def parse(self, input, i, parser_obj, next) :
        def _next(input2, i2) :
            if len(input) == i2 :
                return parser.Possibilities([])
            else :
                return parser.Possibilities()
        return [m[0].obj for m in self.my_something.parse(input, i, parser_obj, _next)]

def parse_something(context, input) :
    """Helper to be able to parse an object name from some input."""
    res = context.parser.parse_all(input, grammar=ParseSomething())
    return [r[0] for r in res]
