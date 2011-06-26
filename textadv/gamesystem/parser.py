# parser.py
#
# a parser engine for interactive fiction

# Interface:
# class: Parser, Something, Anything
# exceptions: NoSuchWord, NoUnderstand

# kinds of things we want to parse:
# "inventory"
# "examine [something]"
# "go [direction]"
# "unlock [something] with [something]"
# "debug_dump [anything]"
# "tell [someone] to [action]"
# "give [someone] [something]"
# "give [something] to [someone]"

# where [something] is a noun form: [art]? [adj]* [noun]?

import string
import re
import itertools
from textadv.core.patterns import VarPattern
from textadv.core.rulesystem import ActionTable, ActionHandled

###
### Parser exceptions
###

class NoSuchWord(Exception) :
    def __init__(self, word) :
        self.word = word

class NoUnderstand(Exception) :
    pass

class NoInput(Exception) :
    pass

class Ambiguous(Exception) :
    """Options is a list of lists of object ids."""
    def __init__(self, options=[]) :
        self.options = options

###
### Useful functions
###

def append(xs) :
    return [a for x in xs for a in x]

def product(xs, ys) :
    out = []
    for x in xs :
        for y in ys :
            out.append(x+y)
    return out

def separate_object_words(words) :
    """Takes a list of words as returned by Words(ob), and segments
    them into the adjs and nouns.  Returns (adjs, nouns)."""
    adjs = []
    nouns = []
    for w in words :
        if w[0] == "@" :
            nouns.append(w[1:])
        else :
            adjs.append(w)
    return (adjs,nouns)

def parser_valid_description(myadjs, mynouns, objadjs, objnouns) :
    """Checks whether (myadjs, mynouns) is a valid description for
    (objadjs,objnouns)."""
    if not myadjs and not mynouns :
        return False
    for madj in myadjs :
        if madj not in objadjs :
            return False
    for mnoun in mynouns :
        if mnoun not in objnouns :
            return False
    return True

###
### Basically constant constants
###

PARSER_ARTICLES = ["a", "an", "the"]

###
### Matched objects
###

class MatchedObject(object) :
    def __init__(self, words, name, score, var=None) :
        self.words = words
        self.name = name
        self.score = score
        self.var = var
    def __repr__(self) :
        return "MatchedObject(%r,%r,%r,%r)" % (self.words, self.name, self.score, self.var)

###
### Basic thing parser
###

parse_thing = ActionTable(accumulator=append)
@parse_thing.add_handler
def default_parse_thing(name, words, input, i, ctxt, next) :
    def match_adjs_nouns(curr_adjs, i2) :
        poss = []
        if i2 < len(input) :
            # try adding another adjective
            if input[i2] in adjs :
                new_adjs = curr_adjs + [input[i2]]
                if parser_valid_description(new_adjs, [], adjs, nouns) :
                    poss.extend(match_adjs_nouns(new_adjs, i2+1))
            # or try concluding with a noun
            if input[i2] in nouns :
                # already a match
                poss.extend(product([[MatchedObject(input[i:i2+1], name, 2)]],
                                    next(input, i2+1)))
        # or just try concluding
        if len(curr_adjs) > 0 :
            # already a match
            poss.extend(product([[MatchedObject(input[i:i2], name, 1)]],
                                next(input, i2)))
        return poss
    adjs,nouns = words
    poss = []
    if i < len(input) :
        i2 = i
        # skip over articles
        if input[i] in PARSER_ARTICLES :
            i2 += 1
        poss.extend(match_adjs_nouns([], i2))
    return poss


###
### Parser action tables
###

parse_something = ActionTable(accumulator=append)
@parse_something.add_handler
def default_something(input, i, ctxt, next) :
    return append([parse_thing.notify([name,words,input,i,ctxt,next],{})
                   for name,words in zip(CURRENT_OBJECTS, CURRENT_WORDS)])

main_parser = ActionTable(accumulator=append)

CURRENT_OBJECTS = []
CURRENT_WORDS = []

def run_parser(parser, input, world) :
    global CURRENT_OBJECTS, CURRENT_WORDS
    CURRENT_OBJECTS = world.actions.referenceable_objects()
    CURRENT_WORDS = [separate_object_words(world.actions.get_words(o)) for o in CURRENT_OBJECTS]
    def _end(input, i) :
        if len(input) == i :
            return [[]]
        else :
            return []
    return parser.notify([input, 0, None, _end], {})
