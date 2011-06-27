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
### Known words
###
# Helps let the user know which word was not recognized when they make a typo

KNOWN_WORDS = []

def add_known_words(*words) :
    KNOWN_WORDS.extend(words)


###
### Basically constant constants
###

PARSER_ARTICLES = ["a", "an", "the"]

add_known_words(*PARSER_ARTICLES)

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
def default_parse_thing(var, name, words, input, i, ctxt, next, multiplier=1) :
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
                poss.extend(product([[Matched(input[i:i2+1], name, 2*multiplier, var)]],
                                    next(i2+1)))
        # or just try concluding
        if len(curr_adjs) > 0 :
            # already a match
            poss.extend(product([[Matched(input[i:i2], name, 1*multiplier, var)]],
                                next(i2)))
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


define_subparser("object", "A parser which uses its variable as an object id, instead.")

@add_subparser("object")
def default_object(var, input, i, ctxt, actor, next) :
    """Tries to parse the input so that the var is the name of the object."""
    words = separate_object_words(ctxt.world.get_property("Words", var))
    return parse_thing.notify([None,var,words,input,i,ctxt,next,2],{})

define_subparser("action", """A parser to match against entire
actions.  The resulting Match.value should be something which can be
run.  This is the main parser.""")


define_subparser("text", """Just matches against any sequence of words.""")

@add_subparser("text")
def default_parse_text(var, input, i, ctxt, actor, next) :
    """Parses any number of words, stopping at or before the end of
    the input."""
    out = []
    for i2 in xrange(i+1,len(input)+1) :
        out.extend(product([[Matched(input[i:i2], " ".join(input[i:i2]), 1, var)]],
                           next(i2)))
    return out

### Adding things to the tables


class CallSubParser(object) :
    def __init__(self, name, var=None) :
        self.name = name
        self.var = var
    def __repr__(self) :
        return "CallSubParser(%r, %r)" % (self.name, self.var)

def understand(text, result=None, dest="action") :
    """Takes a textual form of a command and adds it to the parser so
    that action is executed.  The following is an example of the
    textual form:

    give [something y] to [something z]

    The understood nonterminals are [something varname] and [anything
    varname] where "something" refers to something the actor can
    immediately access, where "anything" refers to anything in the
    game world.

    One can give multiple options for a word by using a slash.  For
    instance:

    take/get [something x]

    Other nonterminals:
    - [direction x] for a cardinal direction
    
    - [text x] for taking some number of arbitrary words, and then
      binding x to the resulting string.

    - [object oid] for matching against a particular object.
    """

    parts = []
    lastindex = 0
    for match in re.finditer(r"\[([A-Za-z]+)\s+([^\]]+)\]", text) :
        textparts = text[lastindex:match.start()].split()
        for tp in textparts :
            opts = tp.split("/")
            parts.append(opts)
        lastindex = match.end()
        if subparsers.has_key(match.group(1).lower()) :
            csp = CallSubParser(match.group(1), match.group(2))
            print csp
            parts.append(csp)
        else :
            raise Exception("No such subparser %r" % match.group(1))
    parts.extend(text[lastindex:].split())
    subparser_add_sequence(dest, parts, result)

def subparser_add_sequence(dest, parts, result) :
    """Takes a sequence (parts) and adds a parser to the dest
    subparser which then returns result.  To be used with understand."""
    # first let the parser know about the words
    for part in parts :
        if type(part) is list :
            add_known_words(*part)
    # then add the subparser
    @add_subparser(dest)
    def _handler_sequence(var, input, i, ctxt, actor, next) :
        def _handler_part(part_i, var, input, i2) :
            def _next2(i3) :
                return _handler_part(part_i+1, var, input, i3)
            if part_i == len(parts) :
                return [[(i2, next(i2))]]
            elif type(parts[part_i]) is CallSubParser :
                csp = parts[part_i]
                return run_subparser(csp.name, csp.var, input, i2, ctxt, actor, _next2)
            elif type(parts[part_i]) is list and input[i2] in parts[part_i] :
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
    CURRENT_OBJECTS = ctxt.world.actions.referenceable_things()
    print CURRENT_OBJECTS
    CURRENT_WORDS = [separate_object_words(ctxt.world.actions.get_words(o)) for o in CURRENT_OBJECTS]

def run_parser(name, input, ctxt) :
    def _end(i) :
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

def disambiguate(results, ctxt, action_verifier) :
    return results[0].value

def handle_all(input, ctxt, action_verifier) :
    words = transform_text_to_words(input)
    if not words :
        raise NoInput()
    init_current_objects(ctxt)
    results = [r[0] for r in run_parser("action", words, ctxt)]
    if not results :
        raise NoSuchWord("uhoh")
    action = disambiguate(results, ctxt, action_verifier)
    return (action, len(results) > 0)
