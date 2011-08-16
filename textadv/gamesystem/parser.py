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
from textadv.core.patterns import VarPattern, AbstractPattern, ExpansionException
from textadv.core.rulesystem import ActivityTable, ActionHandled
from textadv.gamesystem.utilities import list_append, docstring
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.actionsystem import BasicAction, IllogicalNotVisible

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
    def __init__(self, pattern, options, subparsers) :
        self.pattern = pattern
        self.options = options
        self.subparsers = subparsers
    def __repr__(self) :
        return "Ambiguous(%r, %r, %r)" % (self.pattern, self.options, self.subparsers)

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
            nouns.append(w[1:].lower())
        else :
            adjs.append(w.lower())
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

PARSER_ARTICLES = ["a", "an", "the", "some"]

###
### Matched objects
###

class Matched(object) :
    def __init__(self, words, value, score, subparser, var=None, subobjects=None) :
        self.words = words
        self.value = value
        self.score = score
        self.var = var
        self.subparser = subparser
        self.subobjects = subobjects
    def __repr__(self) :
        return "Matched(%r,%r,%r,%r,%r,%r)" % (self.words, self.value, self.score,
                                               self.subparser, self.var, self.subobjects)


###
### For the "understand" method.
###

class CallSubParser(object) :
    def __init__(self, name, var=None) :
        self.name = name
        self.var = var
    def __repr__(self) :
        return "CallSubParser(%r, %r)" % (self.name, self.var)


###
### Construct documentation
###


class Parser(object) :
    def __init__(self) :
        self.KNOWN_WORDS = []
        self.add_known_words(*PARSER_ARTICLES)
        # subparser takes (parser, var, input, i, ctxt, actor, next)
        self.subparsers = dict()
        self.object_classes = {"something" : "thing", "somewhere" : "room"}
        self.parse_thing = ActivityTable(accumulator=list_append, doc="""A
        parse_thing parser takes the arguments (parser, subparser,
        var, name, words, input, i, ctxt, next, multiplier=1), and
        then tries to parse the input from the point of view of the
        name and the words=(adjs,nouns) arguments.  The subparser is
        the name of the subparser which called parse_thing so that we
        can disambiguate properly.  Note: this may be backwards from
        what is expected--we try to find the thing we're looking for
        rather than try to find any thing.  Should return
        [Matched(..), ...] or something.""")
    def init_current_objects(self, ctxt, with_objs=None) :
        """For parsing efficiency of things (needed in the something
        parser).  Gets the referenceable objects and their words."""
        self.current_objects = dict()
        self.current_words = dict()
        self.current_names = dict()
        for parser, kind in self.object_classes.iteritems() :
            if with_objs and parser in with_objs :
                self.current_objects[parser] = with_objs[parser]
            else :
                self.current_objects[parser] = ctxt.world.activity.objects_of_kind(kind)
            self.current_words[parser] = [separate_object_words(ctxt.world.get_property("Words", o))
                                          for o in self.current_objects[parser]]
            self.current_names[parser] = dict()
            for o in self.current_objects[parser] :
                self.current_names[parser][o] = " ".join(ctxt.stringeval.eval_str(ctxt.world.get_property("Name", o), ctxt).split())
    def add_object_class(self, parsername, kind) :
        """Sets up the object_classes dictionary for a subparser
        called parsername so that current_objects[parsername] will be
        loaded with objects of kind kind when init_current_objects is
        run.  The current_words[parsername] entry will be updated."""
        self.object_classes[parsername] = kind
    def add_known_words(self,*words) :
        """Helps let the user know which word was not recognized when
        they make a typo."""
        self.KNOWN_WORDS.extend(words)
    def __is_word_for_thing(self, word) :
        for word_list in self.current_words.itervalues() :
            for adjs,nouns in word_list :
                if word in adjs or word in nouns :
                    return True
        return False

    def define_subparser(self, name, doc=None) :
        self.subparsers[name] = ActivityTable(accumulator=list_append, doc=doc)
    def add_subparser(self, name, **kwargs) :
        def _add_subparser(f) :
            self.subparsers[name].add_handler(f, **kwargs)
            return f
        return _add_subparser
    def run_subparser(self, name, var, input, i, ctxt, actor, next) :
        return self.subparsers[name].notify([self, var, input, i, ctxt, actor, next], {})
    def run_parser(self, name, input, ctxt) :
        """Like run_subparser, but matches the end of input, too."""
        def _end(i) :
            if len(input) == i :
                return [[]]
            else :
                return []
        return self.subparsers[name].notify([self, None, input, 0, ctxt, ctxt.actor, _end], {})

    def understand(self, text, result=None, dest="action") :
        """Takes a textual form of a command and adds it to the parser
        so that action is executed.  The following is an example of
        the textual form:
        
        give [something y] to [something z]
        
        The understood nonterminals are [something varname] and
        [anything varname] where "something" refers to something the
        actor can immediately access, where "anything" refers to
        anything in the game world.

        One can give multiple options for a word by using a slash.
        For instance:

        take/get [something x]

        Other nonterminals:
        - [direction x] for a cardinal direction
        
        - [text x] for taking some number of arbitrary words, and then
        binding x to the resulting string.
        
        - [object oid] for matching against a particular object.

        The whitespace in the variable is turned into a single space.
        For instance, [object  my    ball] is the same as [object my ball]."""
        
        parts = []
        lastindex = 0
        for match in re.finditer(r"\[([A-Za-z]+)\s+([^\]]+)\]", text) :
            textparts = text[lastindex:match.start()].split()
            for tp in textparts :
                parts.append(tp.lower().split("/"))
            lastindex = match.end()
            if self.subparsers.has_key(match.group(1).lower()) :
                csp = CallSubParser(match.group(1), " ".join(match.group(2).split()))
                parts.append(csp)
            else :
                raise Exception("No such subparser %r" % match.group(1))
        textparts = text[lastindex:].split()
        for tp in textparts :
            parts.append(tp.lower().split("/"))
        self.__subparser_add_sequence(dest, parts, result, text)
    def __subparser_add_sequence(self, dest, parts, result, text) :
        """Takes a sequence (parts) and adds a parser to the dest
        subparser which then returns result.  To be used with
        understand."""
        # first let the parser know about the words
        for part in parts :
            if type(part) is list :
                self.add_known_words(*part)
        # then add the subparser
        @self.add_subparser(dest)
        @docstring("Parses "+repr(text)+" as "+repr(result)+".")
        def _handler_sequence(parser, var, input, i, ctxt, actor, next) :
            def _handler_part(part_i, var, input, i2) :
                def _next2(i3) :
                    return _handler_part(part_i+1, var, input, i3)
                if part_i == len(parts) :
                    # we've matched all of our parts, so return (with
                    # extra data at the end so we can construct the
                    # proper Matched object)
                    return [[(i2, next(i2))]]
                elif type(parts[part_i]) is CallSubParser :
                    # or, we have a subparser to execute
                    csp = parts[part_i]
                    return parser.run_subparser(csp.name, csp.var, input, i2, ctxt, actor, _next2)
                elif i2 < len(input) and type(parts[part_i]) is list and input[i2].lower() in parts[part_i] :
                    # as in "if we haven't reached the end of input,
                    # and we have a list of options in parts, check to
                    # see if the input is currently one of these
                    # options." Then we go on.
                    return _handler_part(part_i+1, var, input, i2+1)
                else :
                    return []
            res = _handler_part(0, var, input, i)
            out = []
            # We need to massage the data to handle the last tuple.
            for r in res :
                i2, rest = r[-1]
                subobjects = r[:-1]
                score = 0
                matches = dict()
                subparsers = dict()
                for part in subobjects :
                    if type(part) is Matched :
                        score += part.score # score is accumulation of all subscores
                        if part.var :
                            matches[part.var] = part.value
                            if part.subparser == "action" :
                                subparsers[part.var] = part.supdata
                            else :
                                subparsers[part.var] = ("subparser", part.subparser)
                matches["actor"] = actor
                subparsers["actor"] = ("subparser", "something")
                supdata = None
                if result :
                    if type(result) == str :
                        value = result
                    elif isinstance(result, AbstractPattern) :
                        try :
                            value = result.expand_pattern(matches, data={"world":ctxt.world})
                            supdata = result.expand_pattern(subparsers)
                        except ExpansionException :
                            continue # just skip it!
                    else :
                        value = result(**matches)
                else :
                    value = subobjects
                m = Matched(input[i:i2], value, score, dest, var=var, subobjects=subobjects)
                m.supdata = supdata # hack!!! We need this to disambiguate properly
                out.extend(product([[m]], rest))
            return out

    def transform_text_to_words(self, text) :
        text = text.replace(",", " , ").replace("?", " ? ")
        return text.strip().split()

    def handle_all(self, input, ctxt, action_verifier) :
        words = self.transform_text_to_words(input)
        if not words :
            raise NoInput()
        self.init_current_objects(ctxt)
        results = [r[0] for r in self.run_parser("action", words, ctxt)]
        if not results :
            # then maybe we didn't know one of the words
            for word in words :
                word = word.lower()
                if word not in self.KNOWN_WORDS and not self.__is_word_for_thing(word) :
                    raise NoSuchWord(word)
            raise NoUnderstand()
        action, did_disambiguate = self.disambiguate(results, ctxt, action_verifier)
        return (action, did_disambiguate)

    def disambiguate(self, results, ctxt, action_verifier) :
        """Try to disambiguate the results if needed using the
        action_verifier to get whether things work.  Returns (action,
        did_disambiguate) pair, where did_disambiguate represents
        whether there were multiple logical options."""
        if len(results) == 1 : # no need to disambiguate
            return results[0].value, False
        else : # it's ambiguous!
            # first, see if verification helps at all
            scores_pre = [(r, action_verifier(r.value, ctxt)) for r in results]
            # we separate out the ones which are illogical because
            # something wasn't visible because we don't want to even
            # mention the objects involved (because they weren't
            # visible).
            scores = [(r, v) for r,v in scores_pre if type(v) is not IllogicalNotVisible]
            if len(scores) == 0 :
                # In this case, we are stuck with an invalid action
                # because some item is not visible
                scores_not_visible = [r for r,v in scores_pre if type(v) is IllogicalNotVisible]
                # we say is_disambiguating=False so there is no
                # disambiguation message
                return scores_not_visible[0].value, False
            scores.sort(key=lambda z : z[1].score)
            is_disambiguating = 1 < len([True for r,v in scores if v.is_acceptible()])
            if scores[-1][1].is_acceptible() :
                # good, there is some acceptible action.
                best_score = scores[-1][1].score
                best_results = [r for r,v in scores if v.score >= best_score]
                if len(best_results) == 1 : # good, the verification score saved us
                    return best_results[0].value, is_disambiguating
                else :
                    # we assume that the order of the results
                    # disambiguates potential multi-action result sets
                    # (that is, we assume the order reflects the order
                    # of parser definition).  We take the action
                    # parsed by the last-defined parser
                    ordered_best_results = [r for r in results if r in best_results]
                    ordered_best_results.reverse()
                    new_results = []
                    for r in ordered_best_results :
                        if type(r.value) is type(ordered_best_results[0].value) :
                            new_results.append(r)
                        else :
                            break
                    new_results.sort(key=lambda r : r.score)
                    best_score = new_results[-1].score
                    new_best_results = [r for r in new_results if r.score >= best_score]
                    if len(new_best_results) == 1 : # good, the specificity score saved us
                        return new_best_results[0].value, True
                    else :
                        # We need the user to disambiguate.  The
                        # following returns the Ambiguous exception.
                        raise self.__construct_amb_exception([r.value for r in new_best_results],
                                                             [r.supdata for r in new_best_results])
            else :
                # well, none of them are acceptible.  Let's go for the
                # worst one.
                return scores[0][0].value, True
    def __construct_amb_exception(self, results, supdata) :
        # It's ambiguous. Construct the possibilities for each argument
        def __construct_pattern(results, supdata, subparsers, to_replace, next_var) :
            poss_args = [[a] for a in results[0].args]
            poss_subparsers = [(isinstance(r, BasicAction) and s) or
                               (type(s) == tuple and len(s) == 2 and s[0] == "subparser" and s[1])
                               for r,s in zip(results[0].args, supdata[0].args)]
            # the following represents that the result is a matched object
            # which needs to be followed for disambiguation
            more_disambig_flag = [isinstance(a, BasicAction) for a in results[0].args]
            for r,sup in zip(results[1:], supdata[1:]) :
                for a,curr_poss in zip(r.args, poss_args) :
                    if a not in curr_poss :
                        curr_poss.append(a)
                for i in xrange(0, len(poss_subparsers)) : # part of a hack to get the 'subparser'
                    s = sup.args
                    if more_disambig_flag[i] :
                        if not poss_subparsers[i] :
                            poss_subparsers[i] = r[i]
                        elif type(r.args[i]) != type(s[i]) :
                            raise Exception("Conflicting subactions", r.args[i], s)
                    elif type(s[i]) == tuple and len(s[i]) == 2 and s[i][0] == "subparser" :
                        if not poss_subparsers[i] :
                            poss_subparsers[i] = s[i][1]
                        elif s[i][1] != poss_subparsers[i] :
                            raise Exception("Conflicting subparsers", s[i][1], poss_subparsers[i])
            constructed_args = []
            for poss, disamb_more, sp, i in zip(poss_args, more_disambig_flag, poss_subparsers, xrange(0, len(poss_args))) :
                var = next_var[0]
                next_var[0] = chr(ord(var) + 1)
                if len(poss) == 1 : # no need to disambiguate this slot
                    constructed_args.extend(poss)
                elif i == 0 : # this is the actor of the action.  don't need to disambiguate
                    constructed_args.append(poss[0])
                else :
                    if disamb_more :
                        constructed_args.append(__construct_pattern(poss, [sp]*len(poss), # len maybe hack?
                                                                    subparsers, to_replace, next_var))
                    else :
                        to_replace[var] = poss
                        subparsers[var] = sp
                        constructed_args.append(VarPattern(var))
            return type(results[0])(*constructed_args)
        to_replace = dict()
        subparsers = dict()
        return Ambiguous(__construct_pattern(results, supdata, subparsers, to_replace, ['a']),
                         to_replace, subparsers)

    def copy(self) :
        newparser = Parser()
        newparser.KNOWN_WORDS = list(self.KNOWN_WORDS)
        for name, table in self.subparsers.iteritems() :
            newparser.subparsers[name] = table.copy()
        newparser.parse_thing = self.parse_thing.copy()
        newparser.object_classes = self.object_classes.copy()
        return newparser
    def make_documentation(self, escape, heading_level=1) :
        hls = str(heading_level)
        shls = str(heading_level+1)
        print "<h"+hls+">Parser</h"+hls+">"
        print "<p>This is the documentation for the parser.</p>"
        for spn in self.subparsers.iterkeys() :
            print "<h"+shls+">"+escape(spn)+"</h"+shls+">"
            self.subparsers[spn].make_documentation(escape, heading_level=heading_level+2)


###
### Default parser
###

default_parser = Parser()

@default_parser.parse_thing.add_handler
def default_parse_thing(parser, subparser, var, name, words, input, i, ctxt, next, multiplier=1) :
    """Given a set of words and a name, tries to find a subsequence by
    using the grammar [art]? [adjs]* [noun]?, where there is at least
    one adjective or noun."""
    def match_adjs_nouns(curr_adjs, i2) :
        poss = []
        if i2 < len(input) :
            # try adding another adjective
            if input[i2].lower() in adjs :
                new_adjs = curr_adjs + [input[i2].lower()]
                if parser_valid_description(new_adjs, [], adjs, nouns) :
                    poss.extend(match_adjs_nouns(new_adjs, i2+1))
            # or try concluding with a noun
            if input[i2].lower() in nouns :
                # already a match because input[i2] is one of the nouns.
                m2 = 1
                if parser.current_names[subparser][name] == " ".join(input[i:i2+1]) :
                    m2 += 0.5
                poss.extend(product([[Matched(input[i:i2+1], name, 2*multiplier*m2, subparser, var=var)]],
                                    next(i2+1)))
        # or just try concluding
        if len(curr_adjs) > 0 :
            # already a match
            m2 = 1
            if parser.current_names[subparser][name] == " ".join(input[i:i2]) :
                m2 += 0.5
            poss.extend(product([[Matched(input[i:i2], name, 1*multiplier*m2, subparser, var)]],
                                next(i2)))
        return poss
    adjs,nouns = words
    poss = []
    if i < len(input) :
        i2 = i
        # skip over articles
        if input[i].lower() in PARSER_ARTICLES :
            i2 += 1
            i += 1 # for bumping up score for exact matches
        poss.extend(match_adjs_nouns([], i2))
    return poss


default_parser.define_subparser("action", """A parser to match against entire
actions.  The resulting Match.value should be a BasicAction.  This is
the main parser.""")

default_parser.define_subparser("something", "A parser to match against things in the game.")

@default_parser.add_subparser("something")
def default_something(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse as if the following input were a thing."""
    return list_append([parser.parse_thing.notify([parser, "something", var, name, words,input,i,ctxt,next],{})
                        for name,words in zip(parser.current_objects["something"], parser.current_words["something"])])


default_parser.define_subparser("somewhere", "A parser to match against rooms in the game.")

@default_parser.add_subparser("somewhere")
def default_somewhere(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse as if the following input were a room."""
    return list_append([parser.parse_thing.notify([parser, "somewhere", var, name, words,input,i,ctxt,next],{})
                        for name,words in zip(parser.current_objects["somewhere"], parser.current_words["somewhere"])])


default_parser.define_subparser("object", "A parser which uses its variable as an object id, instead.")

@default_parser.add_subparser("object")
def default_object(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse the input so that the var is the name of the object."""
    words = separate_object_words(ctxt.world.get_property("Words", var))
    return parser.parse_thing.notify([parser,"something",None,var,words,input,i,ctxt,next,2],{})


default_parser.define_subparser("text", """Just matches against any sequence of words.""")

@default_parser.add_subparser("text")
def default_parse_text(parser, var, input, i, ctxt, actor, next) :
    """Parses any number of words, stopping at or before the end of
    the input."""
    out = []
    for i2 in xrange(i+1,len(input)+1) :
        out.extend(product([[Matched(input[i:i2], " ".join(input[i:i2]), 1, "text", var=var)]],
                           next(i2)))
    return out
