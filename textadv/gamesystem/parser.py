# parser.py
#
# a parser engine for interactive fiction

# The main parser in this file is assumed to be for an ActorContext
# or something like that.

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
from textadv.core.patterns import VarPattern, AbstractPattern
from textadv.core.rulesystem import ActionTable, ActionHandled
from textadv.gamesystem.utilities import list_append
from textadv.gamesystem.basicpatterns import *

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

class Matched(object) :
    def __init__(self, words, value, score, var=None, subobjects=None) :
        self.words = words
        self.value = value
        self.score = score
        self.var = var
        self.subobjects = subobjects
    def __repr__(self) :
        return "Matched(%r,%r,%r,%r,%r)" % (self.words, self.value, self.score,
                                            self.var, self.subobjects)

###
### Basic thing parser
###

parse_thing = ActionTable(accumulator=list_append)
@parse_thing.add_handler
def default_parse_thing(var, name, words, input, i, ctxt, next) :
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
                poss.extend(product([[Matched(input[i:i2+1], name, 2, var)]],
                                    next(input, i2+1)))
        # or just try concluding
        if len(curr_adjs) > 0 :
            # already a match
            poss.extend(product([[Matched(input[i:i2], name, 1, var)]],
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


# subparser takes (var, input, i, ctxt, actor, next)
subparsers = dict()
subparsers_doc = dict()
def define_subparser(name, doc=None) :
    subparsers[name] = ActionTable(accumulator=list_append)
    subparsers_doc[name] = doc

def add_subparser(name) :
    def _add_subparser(f) :
        subparsers[name].add_handler(f)
        return f
    return _add_subparser

def run_subparser(name, var, input, i, ctxt, actor, next) :
    return subparsers[name].notify([var, input, i, ctxt, actor, next], {})

define_subparser("something", "A parser to match against things in the game.")

@add_subparser("something")
def default_something(var, input, i, ctxt, actor, next) :
    """Tries to parse as if the following input were a thing."""
    return list_append([parse_thing.notify([var, name,words,input,i,ctxt,next],{})
                        for name,words in zip(CURRENT_OBJECTS, CURRENT_WORDS)])

define_subparser("action", """A parser to match against entire
actions.  The resulting Match.value should be something which can be
run.  This is the main parser.""")

### Adding things to the tables


class CallSubParser(object) :
    def __init__(self, name, var=None) :
        self.name = name
        self.var = var

def understand(text, result=None, dest="action") :
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
    for match in re.finditer(r"\[([A-Za-z]+)\s+([A-Za-z0-9_]+)\]", text) :
        parts.extend(text[lastindex:match.start()].split())
        lastindex = match.end()
        if subparsers.has_key(match.group(1).lower()) :
            csp = CallSubParser(match.group(1), match.group(2))
            parts.append(csp)
        else :
            raise Exception("Bad subparser "+match.group(1))
    parts.extend(text[lastindex:].split())
    subparser_add_sequence(dest, parts, result)

def subparser_add_sequence(dest, parts, result) :
    @add_subparser(dest)
    def _handler_sequence(var, input, i, ctxt, actor, next) :
        def _handler_part(part_i, var, input, i2) :
            def _next2(input, i3) :
                return _handler_part(part_i+1, var, input, i3)
            if part_i == len(parts) :
                return [[(i2, next(input, i2))]]
            elif type(parts[part_i]) == CallSubParser :
                csp = parts[part_i]
                return run_subparser(csp.name, csp.var, input, i2, ctxt, actor, _next2)
            elif parts[part_i] == input[i2] :
                return _handler_part(part_i+1, var, input, i2+1)
            else :
                return []
        res = _handler_part(0, var, input, i)
        out = []
        for r in res :
            i2, rest = r[-1]
            subobjects = r[:-1]
            score = 0
            matches = dict()
            for part in subobjects :
                if type(part) is Matched :
                    score += part.score
                    if part.var :
                        matches[part.var] = part.value
            matches["actor"] = actor
            if result :
                if type(result) == str :
                    value = result
                elif isinstance(result, AbstractPattern) :
                    value = result.expand_pattern(matches)
                else :
                    value = result(**matches)
            else :
                value = subobjects
            m = Matched(input[i:i2], value, score, var, subobjects)
            out.extend(product([[m]], rest))
        return out

CURRENT_OBJECTS = []
CURRENT_WORDS = []

def init_current_objects(ctxt) :
    global CURRENT_OBJECTS, CURRENT_WORDS
    CURRENT_OBJECTS = ctxt.world.actions.referenceable_objects()
    CURRENT_WORDS = [separate_object_words(ctxt.world.actions.get_words(o)) for o in CURRENT_OBJECTS]

def run_parser(name, input, ctxt) :
    def _end(input, i) :
        if len(input) == i :
            return [[]]
        else :
            return []
    return subparsers[name].notify([None, input, 0, ctxt, ctxt.actorname, _end], {})

def transform_text_to_words(text) :
    text = text.lower()
    if "," in text :
        actor, action = text.split(",",1)
        text = "ask "+actor+" to "+action
    return text.split()

def handle_all(input, ctxt) :
    words = transform_text_to_words(input)
    init_current_objects(ctxt)
    results = run_parser("action", words, ctxt)
    return results
