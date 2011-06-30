# utilities.py
#
# some utilities like text processing

import string
import itertools
import re

def list_append(xs) :
    #return itertools.chain.from_iterable(xs)
    return [a for x in xs for a in x]

def serial_comma(nouns, conj="and", comma=",", force_comma=False) :
    conj = " " + conj + " "
    if len(nouns) == 1 :
        return nouns[0]
    elif len(nouns) == 2 :
        if force_comma :
            return nouns[0] + comma + conj + nouns[1]
        else :
            return nouns[0] + conj + nouns[1]
    else :
        comma_sp = comma + " "
        return comma_sp.join(nouns[:-1]) + comma + conj + nouns[-1]

def is_are_list(nouns) :
    if len(nouns) == 0 :
        return "is nothing"
    elif len(nouns) == 1 :
        return "is "+nouns[0]
    else :
        return "are "+serial_comma(nouns)

def obj_is_are_list(context, objs, propname=None) :
    if prop is None :
        prop = "IndefiniteName"
    objs = [context.world.get_property(prop, o) for o in objs]
    return is_are_list(objs)

DIRECTION_INVERSES = {"north" : "south",
                      "south" : "north",
                      "east" : "west",
                      "west" : "east",
                      "up" : "down",
                      "down" : "up",
                      "in" : "out",
                      "out" : "in"}

def inverse_direction(direction) :
    return DIRECTION_INVERSES[direction]

def docstring(s) :
    def _docstring(f) :
        f.__doc__ = s
        return f
    return _docstring

###
### Object interface for fancy strings
###

# "You aren't able to pick up the ball."
# "He isn't able to pick up the ball."
# str_with_objs("[as $actor]{You} {aren't} able to pick up [get $object definite_name][endas].",
#               actor=actor, object=the_ball)

# "The door is currently [if [get door open]]open[else]closed[endif]."

# see eval_str for more information.

def str_with_objs(input, **kwarg) :
    newkwarg = dict()
    for key, value in kwarg.iteritems() :
        if " " in value :
            newkwarg[key] = "<%s>"%value
        else :
            newkwarg[key] = value
    return string.Template(input).safe_substitute(newkwarg)

def as_actor(input, actor) :
    return "[as %s]%s[endas]" % (actor, input)


###
### Implementation of fancy string parser.  Used in a Context
###

def _escape_str(match) :
    return "[char %r]" % ord(match.group())

def escape_str(input) :
    """Just makes it so the string won't be evaluated oddly in eval_str."""
    return re.sub(r"\[|\]|\$|{|}", _escape_str, input)

def eval_str(input, context) :
    """Takes a string and evaluates constructs to reflect the state of
    the game world.
    
    [get $objname $property] => context.world[objname][property]
    [if $pred]$cons[endif]
    [if $pred]$cons[else]$alt[endif]
    [true]
    [false]
    [not $logic]
    [char num] => chr(num)
    {$word} => rewrites $word to make sense in the current context
    """
    # first we need to parse the string
    parsed, i = _eval_parse(input)
    code = ["append"]
    i = 0
    try :
        while i < len(parsed) :
            i, val = _collect_structures(parsed, i)
            code.append(val)
    except MalformedException as x :
        print "eval_str: Offending input is"
        print input
        raise x
    evaled = _eval(code, context, context.actor)
    return "".join([str(o) for o in evaled])

def _eval_parse(input, i=0, in_code=False) :
    """Pulls out [] and {} expressions, labeling them as such.  Also
    makes it so [] expressions split by whitespace.  The characters <
    and > delimit strings when in_code."""
    parsed = []
    j = i
    while i < len(input) :
        if input[i] == "[" :
            if i > j :
                parsed.append(input[j:i])
            parsed2, i2 = _eval_parse(input, i+1, in_code=True)
            parsed.append(("code", parsed2))
            i = i2
            j = i
        elif input[i] == "]" :
            if i > j :
                parsed.append(input[j:i])
            return (parsed, i+1)
        elif input[i] == "{" :
            if i > j :
                parsed.append(input[j:i])
            start = i + 1
            i += 1
            while input[i] != "}" : i += 1
            parsed.append(("reword", input[start:i].split("|")))
            i += 1
            j = i
        elif input[i] == "}" :
            raise Exception("Unmatched '}' in "+input)
        elif input[i] == "<" and in_code :
            start = i+1
            while input[i] != ">" : i += 1
            parsed.append(input[start:i])
            i += 1
            j = i
        elif in_code and input[i] in string.whitespace :
            if i-1 > j :
                parsed.append(input[j:i])
            i += 1
            j = i
        else :
            i += 1
    if j < i :
        parsed.append(input[j:i])
    return (parsed, i)

def _is_else(expr) :
    return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "else"
def _is_endif(expr) :
    return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "endif"
def _is_endas(expr) :
    return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "endas"

class MalformedException(Exception) :
    pass

def _collect_structures(expr, i=0) :
    """Finds [if ...]...[else]...[endif] and [as ...]...[endas]
    structures."""
    if type(expr[i]) == str :
        return i+1, ("lit", expr[i])
    else :
        t, val = expr[i]
        if t == "reword" :
            return i+1, expr[i]
        elif t == "code" :
            if val[0] == "if" :
                try :
                    _i, pred = _collect_structures(val,1)
                    conses = ("if", pred, ["append"], ["append"])
                    consind = 2
                    i += 1
                    while not _is_endif(expr[i]) :
                        if _is_else(expr[i]) :
                            # start making alternate action
                            consind += 1
                            i += 1
                        else :
                            i, v = _collect_structures(expr, i)
                            conses[consind].append(v)
                    return i+1, conses
                except IndexError :
                    raise MalformedException("Malformed if statement.")
            if val[0] == "as" :
                try :
                    actor = val[1]
                    content = ["append"]
                    i += 1
                    while not _is_endas(expr[i]) :
                        i, v = _collect_structures(expr, i)
                        content.append(v)
                    return i+1, ["as", actor, content]
                except IndexError :
                    raise MalformedException("Malformed as statement.")
            else :
                out = [val[0]]
                j = 1
                while j < len(val) :
                    j, o = _collect_structures(val,j)
                    out.append(o)
                return i+1, out
        else :
            raise Exception("What kind of structure is this?", expr)

def _eval(expr, context, actor) :
    if expr[0] == "lit" :
        return expr[1]
    elif expr[0] == "reword" :
        return reword(expr[1], context, actor)
    elif expr[0] == "if" :
        res = _eval(expr[1], context, actor)
        # res might be the empty list
        if res and res[0] :
            return _eval(expr[2], context, actor)
        else :
            return _eval(expr[3], context, actor)
    elif expr[0] == "as" :
        return _eval(expr[2], context, expr[1])
    elif expr[0] == "current_actor_is" :
        if len(expr) == 1 :
            return [actor]
        else :
            return [actor == _eval(expr[1], context, actor)]
    elif _str_eval_functions.has_key(expr[0]) :
        try :
            args = [_eval(x, context, actor) for x in expr[1:]]
            return _str_eval_functions[expr[0]](context, *args)
        except TypeError :
            print "String evaluator tried",expr
            raise
    else :
        raise Exception("Unknown expr",expr)

_str_eval_functions = {}
def add_str_eval_func(name) :
    def _add_str_eval_func(f) :
        _str_eval_functions[name] = f
        return f
    return _add_str_eval_func

# treat args as lists, append args
_str_eval_functions["append"] = lambda context, *x : itertools.chain.from_iterable(x)
# evals to true
_str_eval_functions["true"] = lambda context : [True]
# evals to false
_str_eval_functions["false"] = lambda context : [False]
# negates arg
_str_eval_functions["not"] = lambda context, x : [not x[0]]
# gets prop(*args) property from world
_str_eval_functions["get"] = lambda context, prop, *args : [context.world.get_property(prop,*args)]
# gets definite_name property
_str_eval_functions["the"] = lambda context, ob : [context.world.get_property("DefiniteName", ob)]
# gets indefinite_name property
_str_eval_functions["a"] = lambda context, ob : [context.world.get_property("IndefiniteName", ob)]
# gets definite_name property, capitalized
_str_eval_functions["The"] = lambda context, ob : [_cap(context.world.get_property("DefiniteName", ob))]
# gets indefinite_name property, capitalized
_str_eval_functions["A"] = lambda context, ob : [_cap(context.world.get_property("IndefiniteName", ob))]
# capitalizes a word
_str_eval_functions["cap"] = lambda context, s : [_cap(s[0])+s[1:]]
# number to char
_str_eval_functions["char"] = lambda context, s : [chr(int(s))]

# gets subject_pronoun property
_str_eval_functions["he"] = lambda context, ob : [context.world.get_property("SubjectPronoun", ob)]
# gets object_pronoun property
_str_eval_functions["him"] = lambda context, ob : [context.world.get_property("ObjectPronoun", ob)]
# gets subject_pronoun property, capitalized
_str_eval_functions["He"] = lambda context, ob : [_cap(context.world.get_property("SubjectPronoun", ob))]
# gets object_pronoun property, capitalized
_str_eval_functions["Him"] = lambda context, ob : [_cap(context.world.get_property("ObjectPronoun", ob))]

# text formatting
_str_eval_functions["newline"] = lambda context : ["[newline]"]
_str_eval_functions["break"] = lambda context : ["[break]"]
_str_eval_functions["indent"] = lambda context : ["[indent]"]

def _cap(string) :
    return string[0].upper()+string[1:]

# if no first object, then first defaults to actor (so one can write
# [when In box] box] instead of [when actor In box])
@add_str_eval_func("when")
def _str_eval_fn_when(context, *obs) :
    if len(obs) == 2 :
        ob1, relation, ob2 = context.actor, obs[0], obs[1]
    else :
        ob1, relation, ob2 = obs
    return [context.world.query_relation(context.world.get_relation(relation)(ob1, ob2))]

# concatenates list of objects, getting indefinite names, and puts proper is/are in front
@add_str_eval_func("is_are_list")
def _str_eval_fn_is_are_list(context, *obs) :
    return [obj_is_are_list(context, list_append(o[0] for o in obs))]

###
### Reworder.  Makes is/are work out depending on context
###

# Rule: when doing {word}, write everything as if there was some guy
# named Bob doing the actions.  Bracket every word that should change
# depending on context.  We assume that if the actor of the context
# did the action, it should be reported in the second person.
#
# flags are specified by {word|flag1|flag2|...}
# flags:
# cap - capitalizes word (useful for start of sentences)
# obj - makes "bob" be the object of a sentence

def reword(args, context, actor) :
    word = args[0]
    flags = args[1:]
    is_me = (context.actor == actor)
    capitalized = word[0] in string.uppercase
    rewritten = _reword(word.lower(), flags, context.world, actor, is_me)
    if capitalized or "cap" in flags:
        return _cap(rewritten)
    else :
        return rewritten

# These are for going from 3rd person to 2nd person.  They are
# exceptions to the rule that 2nd person to 3rd person adds an 's' to
# the end.
_reword_replacements = {"is" : "are",
                        "has" : "have",
                        "hasn't" : "haven't",
                        "does" : "do",
                        "doesn't" : "don't",
                        "can" : "can",
                        "can't" : "can't",
                        "switches" : "switch",
                        "isn't" : "aren't",
                        "himself" : "yourself"
                        }

def _reword(word, flags, world, actor, is_me) :
    if is_me :
        if word == "he" :
            return world.get_property("SubjectPronounIfMe", actor)
        elif word == "him" :
            return world.get_property("ObjectPronounIfMe", actor)
        elif word == "bob" :
            if "obj" in flags :
                return world.get_property("ObjectPronounIfMe", actor)
            else :
                return world.get_property("SubjectPronounIfMe", actor)
        elif word == "bob's" :
            return world.get_property("PossessivePronounIfMe", actor)
        elif _reword_replacements.has_key(word) :
            return _reword_replacements[word]
        else : # assume it's a verb, take off s
            return word[0:-1]
    else :
        if word == "he" :
            return world.get_property("SubjectPronoun", actor)
        elif word == "him" :
            return world.get_property("ObjectPronoun", actor)
        elif word == "bob" :
            return world.get_property("DefiniteName", actor)
        elif word == "bob's" :
            return world.get_property("PossessivePronoun", actor)
        else : # we assume the word should stay as-is
            return word
