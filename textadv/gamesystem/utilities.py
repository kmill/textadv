# utilities.py
#
# some utilities like text processing

import string
import itertools
import re

def list_append(xs) :
    #return itertools.chain.from_iterable(xs)
    return [a for x in xs for a in x]

def join_with_spaces(xs) :
    return " ".join(xs)
def join(xs) :
    return "".join(xs)

def serial_comma(nouns, conj="and", comma=",", force_comma=False) :
    conj = " " + conj + " "
    if len(nouns) == 0 :
        return "nothing"
    elif len(nouns) == 1 :
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

DIRECTION_INVERSES = {"north" : "south",
                      "south" : "north",
                      "east" : "west",
                      "west" : "east",
                      "northwest" : "southeast",
                      "northeast" : "southwest",
                      "southwest" : "northeast",
                      "southeast" : "northwest",
                      "up" : "down",
                      "down" : "up",
                      "in" : "out",
                      "out" : "in"}

def inverse_direction(direction) :
    return DIRECTION_INVERSES[direction]

def add_direction_pair(dir, opp) :
    DIRECTION_INVERSES[dir] = opp
    DIRECTION_INVERSES[opp] = dir

def docstring(s) :
    def _docstring(f) :
        f.__doc__ = s
        return f
    return _docstring


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    if text :
        return "".join(html_escape_table.get(c,c) for c in text)
    else :
        return None


###
### Web interface stuff
###

def make_action_link(text, action, tag=None) :
    action = action.replace("'", "\\'")
    if tag :
        return '<a class="action" href="" onclick="return run_action(\'%s\');">%s&nbsp;%s</a>' % (action, tag, text)
    else :
        return '<a class="action" href="" onclick="return run_action(\'%s\');">%s</a>' % (action, text)

def wrap_examine(eval, act, obj, text, ctxt) :
    return make_action_link(eval.eval_str(text, ctxt, actor=act), "examine "+eval.eval_str(ctxt.world.get_property("Name", obj), ctxt, actor=act))

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
    """Takes keyword arguments and safely substitutes the keys into
    the input.  So, str_with_objs("[the $o]", o="waldo person") =>
    "[the <waldo person>]"."""
    newkwarg = dict()
    for key, value in kwarg.iteritems() :
        if " " in value :
            newkwarg[key] = "<%s>"%value
        else :
            newkwarg[key] = value
    return string.Template(input).safe_substitute(newkwarg)

def as_actor(input, actor) :
    """Takes input and actor, and returns [as
    <$actor>]$input[endas]."""
    if " " in actor :
        repla = "<%s>"%actor
    else :
        repla = actor
    return "[as %s]%s[endas]" % (repla, input)


###
### Implementation of fancy string parser.  Used in a Context
###

def _escape_str(match) :
    return "[char %r]" % ord(match.group())

def escape_str(input) :
    """Just makes it so the string won't be evaluated oddly in eval_str."""
    return re.sub(r"\[|\]|\$|{|}", _escape_str, input)


class MalformedException(Exception) :
    """For when the input to the StringEvaluator is malformed (as in,
    couldn't be parsed)."""
    pass


class StringEvaluator(object) :
    """The StringEvaulator object represents a string transformer
    which parses a string using a simple programming language.  More
    of a description is in the eval_str method.

    It's basically a scheme interpreter."""

    def __init__(self) :
        self.eval_functions = dict()

    def copy(self) :
        newse = StringEvaluator()
        newse.eval_functions = self.eval_functions.copy()
        return newse

    def add_eval_func(self, name) :
        def _add_eval_func(f) :
            if name in self.eval_functions :
                print "Warning: adding another StringEvaluator function named",name
            self.eval_functions[name] = f
            return f
        return _add_eval_func

    def eval_str(self, input, context, actor=None) :
        """Takes a string and evaluates constructs to reflect the
        state of the game world.
    
        Examples:
        [get $objname $property] => context.world[objname][property]
        [if $pred]$cons[endif]
        [if $pred]$cons[else]$alt[endif]
        [true]
        [false]
        [not $logic]
        [char num] => chr(num)
        {$word} => rewrites $word to make sense in the current context

        More can be defined using the decorator add_eval_func.
        """
        if not actor :
            actor = context.actor
        # first we need to parse the string
        parsed, i = self.__eval_parse(input)
        code = ["append"]
        try :
            i = 0
            while i < len(parsed) :
                i, val = self.__collect_structures(parsed, i)
                code.append(val)
        except MalformedException as x :
            print "eval_str: Offending input is"
            print input
            raise x
        evaled = self.__eval(code, context, actor)
        return "".join([str(o) for o in evaled])

    def __eval_parse(self, input, i=0, in_code=False) :
        """Pulls out [] and {} expressions, labeling them as such.
        Also makes it so [] expressions split by whitespace.  The
        characters < and > delimit strings when in_code.  Note that
        all whitespace is collapsed into a single space for < and >."""
        parsed = []
        j = i
        while i < len(input) :
            if input[i] == "[" :
                if i > j :
                    parsed.append(input[j:i])
                parsed2, i2 = self.__eval_parse(input, i+1, in_code=True)
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
                parsed.append(["reword"] + [("lit", f) for f in input[start:i].split("|")])
                i += 1
                j = i
            elif input[i] == "}" :
                raise Exception("Unmatched '}' in "+input)
            elif input[i] == "<" and in_code :
                if i > j :
                    parsed.append(input[j:i])
                start = i+1
                while input[i] != ">" : i += 1
                parsed.append(" ".join(input[start:i].split()))
                i += 1
                j = i
            elif in_code and input[i] in string.whitespace :
                if i > j :
                    parsed.append(input[j:i])
                i += 1
                j = i
            else :
                i += 1
        if j < i :
            parsed.append(input[j:i])
        return (parsed, i)

    def __collect_structures(self, expr, i=0) :
        """Finds [if ...]...[else]...[endif] and [as ...]...[endas]
        structures."""
        def _is_else(expr) :
            return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "else"
        def _is_endif(expr) :
            return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "endif"
        def _is_endas(expr) :
            return type(expr) == tuple and expr[0] == "code" and expr[1][0] == "endas"
        if type(expr[i]) == str :
            return i+1, ("lit", expr[i])
        else :
            t, val = expr[i][0:2]
            if t == "reword" :
                return i+1, expr[i]
            elif t == "code" :
                if val[0] == "if" :
                    try :
                        _i, pred = self.__collect_structures(val,1)
                        conses = ("if", pred, ["append"], ["append"])
                        consind = 2
                        i += 1
                        while not _is_endif(expr[i]) :
                            if _is_else(expr[i]) :
                                # start making alternate action
                                consind += 1
                                i += 1
                            else :
                                i, v = self.__collect_structures(expr, i)
                                conses[consind].append(v)
                        return i+1, conses
                    except IndexError :
                        raise MalformedException("Malformed 'if' statement.")
                elif val[0] == "as" :
                    try :
                        actor = val[1]
                        content = ["append"]
                        i += 1
                        while not _is_endas(expr[i]) :
                            i, v = self.__collect_structures(expr, i)
                            content.append(v)
                        return i+1, ["as", actor, content]
                    except IndexError :
                        raise MalformedException("Malformed 'as' statement.")
                else :
                    out = [val[0]]
                    j = 1
                    while j < len(val) :
                        j, o = self.__collect_structures(val,j)
                        out.append(o)
                    return i+1, out
            else :
                raise Exception("What kind of structure is this?", expr)

    def __eval(self, expr, context, actor) :
        if expr[0] == "lit" :
            return [expr[1]]
        elif expr[0] == "if" :
            res = self.__eval(expr[1], context, actor)
            # res might be the empty list
            if res and res[0] :
                return self.__eval(expr[2], context, actor)
            else :
                return self.__eval(expr[3], context, actor)
        elif expr[0] == "as" :
            return self.__eval(expr[2], context, expr[1])
        elif expr[0] == "current_actor_is" :
            if len(expr) == 1 :
                return [actor]
            else :
                return [actor == self.__eval(expr[1], context, actor)]
        elif self.eval_functions.has_key(expr[0]) :
            try :
                args = [self.__eval(x, context, actor) for x in expr[1:]]
                return self.eval_functions[expr[0]](self, actor, context, *args)
            except TypeError :
                print "String evaluator tried",expr
                raise
        else :
            raise Exception("Unknown expr",expr)
    def make_documentation(self, escape, heading_level=1) :
        import inspect
        hls = str(heading_level)
        print "<h"+hls+">String Evaluator</h"+hls+">"
        print "<p>This is the documentation for the object which takes strings meant written in a special language and evaluates them.</p>"
        shls = str(heading_level+1)
        print "<h"+shls+">Evaluator functions</h"+shls+">"
        funcs = self.eval_functions.items()
        funcs.sort(key=lambda x : x[0])
        for name, func in funcs :
            print "<h"+shls+">"+escape(name)+"</h"+shls+">"
            print "<p>"+(escape(func.__doc__) or "(No documentation).")+"</p>"
            print "<p><b>calls</b> <tt>"+escape(func.__name__)+"</tt>"
            try :
                print "<small>(from <tt>"+inspect.getsourcefile(func)+"</tt>)</small>"
            except TypeError :
                pass
            print "</p>"


###
### The default string evaluator
###

stringeval = StringEvaluator()

@stringeval.add_eval_func("append")
def _str_eval_append(eval, act, ctxt, *xs) :
    """Treats the args as lists and appends them."""
    return itertools.chain.from_iterable(xs)

@stringeval.add_eval_func("true")
def _str_eval_true(eval, act, ctxt) :
    """Returns true."""
    return [True]

@stringeval.add_eval_func("false")
def _str_eval_true(eval, act, ctxt) :
    """Returns false."""
    return [False]

@stringeval.add_eval_func("not")
def _str_eval_true(eval, act, ctxt, x) :
    """Returns the Python 'not' of the argument."""
    return [not x]

@stringeval.add_eval_func("==")
def _str_eval_eq(eval, act, ctxt, x, y) :
    """Returns the Python == of the arguments."""
    return [x == y]

@stringeval.add_eval_func("first")
def _str_eval_first(eval, act, ctxt, x) :
    """Returns the first element of the argument."""
    return [x[0]]

@stringeval.add_eval_func("get")
def _str_eval_get(eval, act, ctxt, prop, *args) :
    """Calls ctxt.world.get_property on the arguments."""
    args = [a[0] for a in args]
    return [ctxt.world.get_property(prop[0], *args)]

@stringeval.add_eval_func("the")
def _str_eval_the(eval, act, ctxt, ob) :
    """Gets DefiniteName of the supplied object."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, eval.eval_str(ctxt.world.get_property("DefiniteName", ob), ctxt, actor=act), ctxt)]

@stringeval.add_eval_func("the_")
def _str_eval_the_(eval, act, ctxt, ob) :
    """Gets DefiniteName of the supplied object, but doesn't wrap it in an examination tag."""
    ob = ob[0]
    return [eval.eval_str(ctxt.world.get_property("DefiniteName", ob), ctxt, actor=act)]


@stringeval.add_eval_func("a")
def _str_eval_a(eval, act, ctxt, ob) :
    """Gets IndefiniteName of the supplied object."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, eval.eval_str(ctxt.world.get_property("IndefiniteName", ob), ctxt, actor=act), ctxt)]

@stringeval.add_eval_func("The")
def _str_eval_The(eval, act, ctxt, ob) :
    """Gets DefiniteName of the supplied object, capitalized."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, _cap(eval.eval_str(ctxt.world.get_property("DefiniteName", ob), ctxt, actor=act)), ctxt)]

@stringeval.add_eval_func("A")
def _str_eval_A(eval, act, ctxt, ob) :
    """Gets IndefiniteName of the supplied object, capitalized."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, _cap(eval.eval_str(ctxt.world.get_property("IndefiniteName", ob), ctxt, actor=act)), ctxt)]

@stringeval.add_eval_func("cap")
def _str_eval_cap(eval, act, ctxt, s) :
    """Capitalizes the string using utilities._cap."""
    s = s[0]
    return [_cap(s)]

@stringeval.add_eval_func("char")
def _str_eval_char(eval, act, ctxt, n) :
    """Runs python chr on the argument as an integer."""
    n = n[0]
    return [chr(int(n))]

@stringeval.add_eval_func("eval_str")
def _str_eval_eval_str(eval, act, ctxt, x) :
    """Call eval_str on the argument."""
    x = x[0]
    return [eval.eval_str(x, ctxt, actor=act)]

@stringeval.add_eval_func("he")
def _str_eval_he(eval, act, ctxt, ob) :
    """Gets SubjectPronoun of the supplied object."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, eval.eval_str(ctxt.world.get_property("SubjectPronoun", ob), ctxt, actor=act), ctxt)]
@stringeval.add_eval_func("him")
def _str_eval_him(eval, act, ctxt, ob) :
    """Gets ObjectPronoun of the supplied object."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, eval.eval_str(ctxt.world.get_property("ObjectPronoun", ob), ctxt, actor=act), ctxt)]
@stringeval.add_eval_func("He")
def _str_eval_He(eval, act, ctxt, ob) :
    """Gets SubjectPronoun of the supplied object, capitalized."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, _cap(eval.eval_str(ctxt.world.get_property("SubjectPronoun", ob), ctxt, actor=act)), ctxt)]
@stringeval.add_eval_func("Him")
def _str_eval_Him(eval, act, ctxt, ob) :
    """Gets ObjectPronoun of the supplied object, capitalized."""
    ob = ob[0]
    return [wrap_examine(eval, act, ob, _cap(eval.eval_str(ctxt.world.get_property("ObjectPronoun", ob), ctxt, actor=act)), ctxt)]

@stringeval.add_eval_func("newline")
def _str_eval_newline(eval, act, ctxt) :
    """Passes through [newline] so that the writer can handle the formatting code."""
    return ["[newline]"]
@stringeval.add_eval_func("break")
def _str_eval_break(eval, act, ctxt) :
    """Passes through [break] so that the writer can handle the formatting code."""
    return ["[break]"]
@stringeval.add_eval_func("indent")
def _str_eval_indent(eval, act, ctxt) :
    """Passes through [indent] so that the writer can handle the formatting code."""
    return ["[indent]"]

def _cap(string) :
    return string[0].upper()+string[1:]

@stringeval.add_eval_func("when")
def _str_eval_when(eval, act, ctxt, *obs) :
    """Returns the results of a query by ctxt.world.query_relation.
    Meant to be used in the context of an 'if'-statement predicate.
    If no second object, then defaults to the current actor (so one
    can write [when box Contains] instead of [when box Contains
    actor])"""
    if len(obs) == 2 :
        ob1, relation, ob2 = obs[0], obs[1], [act]
    else :
        ob1, relation, ob2 = obs
    return [ctxt.world.query_relation(ctxt.world.get_relation(relation[0])(ob1[0], ob2[0]))]

@stringeval.add_eval_func("serial_comma")
def _str_eval_serial_comma(eval, act, ctxt, *obs) :
    """Concatenates a list of objects, getting indefinite names, using
    a serial comma (using serial_comma)."""
    objs = [str_with_objs("[a $o]", o=o) for o in list_append(*obs)]
    return eval.eval_str(serial_comma(objs), ctxt, actor=act)

@stringeval.add_eval_func("is_are_list")
def _str_eval_is_are_list(eval, act, ctxt, *obs) :
    """Concatenates a list of objects, getting indefinite names, and
    puts proper is/are in front (using is_are_list)."""
    objs = [str_with_objs("[a $o]", o=o) for o in list_append(*obs)]
    return eval.eval_str(is_are_list(objs), ctxt, actor=act)

@stringeval.add_eval_func("dir")
def _str_eval_dir(eval, act, ctxt, *obs) :
    """Takes a direction and possibly some text, and provides a link
    to go in that direction."""
    if len(obs) == 1 :
        dir = obs[0][0]
        text = obs[0][0]
    else :
        dir = obs[0][0]
        text = obs[1][0]
    return [make_action_link(text, "go "+dir)]

@stringeval.add_eval_func("look")
def _str_eval_dir(eval, act, ctxt, *obs) :
    """Takes a direction and possibly some text, and provides a link
    to go in that direction."""
    if len(obs) == 1 :
        dir = obs[0][0]
        text = obs[0][0]
    else :
        dir = obs[0][0]
        text = obs[1][0]
    return [make_action_link(text, "look "+dir, tag="&#9862;")]

@stringeval.add_eval_func("ob")
def _str_eval_ob(eval, act, ctxt, *obs) :
    """Takes an object and possible text, and provides a link to
    examine that object."""
    if len(obs) == 1 :
        ob = obs[0][0]
        text = obs[0][0]
    else :
        ob = obs[0][0]
        text = obs[1][0]
    ob = eval.eval_str(ob, ctxt, actor=act)
    text = eval.eval_str(text, ctxt, actor=act)
    return [make_action_link(text, "examine "+ob)]

@stringeval.add_eval_func("goto")
def _str_eval_goto(eval, act, ctxt, *obs) :
    """Takes a room and possible text, and provides a link to
    go to that room."""
    if len(obs) == 1 :
        ob = obs[0][0]
        text = obs[0][0]
    else :
        ob = obs[0][0]
        text = obs[1][0]
    ob = eval.eval_str(ob, ctxt, actor=act)
    text = eval.eval_str(text, ctxt, actor=act)
    return [make_action_link(text, "go to "+ob)]

@stringeval.add_eval_func("action")
def _str_eval_action(eval, act, ctxt, *obs) :
    """Takes an action (as a string) and possible text, and provides a
    link to do that action.  Calls make_action_link."""
    if len(obs) == 1 :
        action = obs[0][0]
        text = obs[0][0]
    else :
        action = obs[0][0]
        text = obs[1][0]
    action = eval.eval_str(action, ctxt, actor=act)
    text = eval.eval_str(text, ctxt, actor=act)
    return [make_action_link(text, action)]


###
### Reworder.  Makes is/are work out depending on context
###

@stringeval.add_eval_func("reword")
def _str_eval_reword(eval, actor, ctxt, *args) :
    """This command has the syntactic sugar {word|flag1|flag2} for
    [reword word flag1 flag2].

    Rule: when doing {word}, write everything as if there was some
    guy named Bob doing the actions.  Bracket every word that should
    change depending on context.  We assume that if the actor of the
    context did the action, it should be reported in the second
    person.

    flags are specified by {word|flag1|flag2|...}
    flags:
    cap - capitalizes word (useful for start of sentences)
    obj - makes "bob" be the object of a sentence"""

    word = args[0][0]
    flags = args[1:]
    is_me = (ctxt.actor == actor)
    capitalized = word[0] in string.uppercase
    rewritten = _reword(word.lower(), flags, ctxt.world, actor, is_me)
    if capitalized or "cap" in flags:
        return _cap(rewritten)
    else :
        return rewritten

# These are for going from 3rd person to 2nd person.  They are
# exceptions to the rule that 2nd person to 3rd person adds an 's' to
# the end.  These are fine to be global because English language
# shouldn't change between games.
_reword_replacements = {"is" : "are",
                        "has" : "have",
                        "hasn't" : "haven't",
                        "does" : "do",
                        "doesn't" : "don't",
                        "can" : "can",
                        "can't" : "can't",
                        "switches" : "switch",
                        "isn't" : "aren't",
                        }

def _reword(word, flags, world, actor, is_me) :
    if is_me :
        if word == "he" :
            return world.get_property("SubjectPronounIfMe", actor)
        elif word == "him" :
            return world.get_property("ObjectPronounIfMe", actor)
        elif word == "himself" :
            return world.get_property("ReflexivePronounIfMe", actor)
        elif word == "bob" :
            if "obj" in flags :
                return world.get_property("ObjectPronounIfMe", actor)
            else :
                return world.get_property("SubjectPronounIfMe", actor)
        elif word == "his" :
            return world.get_property("PossessivePronounIfMe", actor)
        elif _reword_replacements.has_key(word) :
            return _reword_replacements[word]
        else : # assume it's a verb
            if len(word)>3 and word[-3:]=="ies" :
                return word[0:-3]+"y"
            else : # take off the s
                return word[0:-1]
    else :
        if word == "he" :
            return world.get_property("SubjectPronoun", actor)
        elif word == "him" :
            return world.get_property("ObjectPronoun", actor)
        elif word == "himself" :
            return world.get_property("ReflexivePronoun", actor)
        elif word == "bob" :
            return world.get_property("DefiniteName", actor)
        elif word == "his" :
            return world.get_property("PossessivePronoun", actor)
        else : # we assume the word should stay as-is
            return word
