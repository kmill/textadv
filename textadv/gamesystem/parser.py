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
from textadv.core.rulesystem import ActivityTable, ActionHandled
from textadv.gamesystem.utilities import list_append, docstring
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.actionsystem import BasicAction

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
    def __init__(self, pattern, options) :
        self.pattern = pattern
        self.options = options
    def __repr__(self) :
        return "Ambiguous(%r, %r)" % (self.pattern, self.options)

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
        self.parse_thing = ActivityTable(accumulator=list_append, doc="""A
        parse_thing parser takes the arguments (parser, var, name,
        words, input, i, ctxt, next, multiplier=1), and then tries to
        parse the input from the point of view of the name and the
        words=(adjs,nouns) arguments.  Note: this may be backwards
        from what is expected--we try to find the thing we're looking
        for rather than try to find any thing.  Should return
        [Matched(..), ...] or something.""")
    def init_current_objects(self, ctxt) :
        """For parsing efficiency of things (needed in the something
        parser).  Gets the referenceable objects and their words."""
        self.CURRENT_OBJECTS = ctxt.world.activity.referenceable_things()
        self.CURRENT_WORDS = [separate_object_words(ctxt.world.get_property("Words", o))
                              for o in self.CURRENT_OBJECTS]
    def add_known_words(self,*words) :
        """Helps let the user know which word was not recognized when
        they make a typo."""
        self.KNOWN_WORDS.extend(words)
    def __is_word_for_thing(self, word) :
        for adjs,nouns in self.CURRENT_WORDS :
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
        
        - [object oid] for matching against a particular object."""
        
        parts = []
        lastindex = 0
        for match in re.finditer(r"\[([A-Za-z]+)\s+([^\]]+)\]", text) :
            textparts = text[lastindex:match.start()].split()
            for tp in textparts :
                parts.append(tp.split("/"))
            lastindex = match.end()
            if self.subparsers.has_key(match.group(1).lower()) :
                csp = CallSubParser(match.group(1), match.group(2))
                parts.append(csp)
            else :
                raise Exception("No such subparser %r" % match.group(1))
        textparts = text[lastindex:].split()
        for tp in textparts :
            parts.append(tp.split("/"))
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
                elif i2 < len(input) and type(parts[part_i]) is list and input[i2] in parts[part_i] :
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

    def transform_command_to_words(self, text) :
        text = text.lower()
        if "," in text :
            actor, action = text.split(",",1)
            text = "ask "+actor+" to "+action
        return text.split()
    def transform_text_to_words(self, text) :
        text = text.lower()
        return text.split()

    def handle_all(self, input, ctxt, action_verifier) :
        words = self.transform_command_to_words(input)
        if not words :
            raise NoInput()
        self.init_current_objects(ctxt)
        results = [r[0] for r in self.run_parser("action", words, ctxt)]
        if not results :
            # then maybe we didn't know one of the words
            for word in words :
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
            scores = [(r, action_verifier(r.value, ctxt)) for r in results]
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
                        raise __construct_amb_exception([r.value for r in new_best_results])
            else :
                # well, none of them are acceptible.  Let's go for the
                # worst one.
                return scores[0][0].value, True
    def __construct_amb_exception(self, results) :
        # It's ambiguous. Construct the possibilities for each argument
        def __construct_pattern(results, to_replace, next_var) :
            poss_args = [[a] for a in results[0].args]
            # the following represents that the result is a matched object
            # which needs to be followed for disambiguation
            more_disambig_flag = [isinstance(a, BasicAction) for a in results[0].args]
            for r in results[1:] :
                for a,curr_poss in zip(r.args, poss_args) :
                    if a not in curr_poss :
                        curr_poss.append(a)
            constructed_args = []
            for poss, disamb_more in zip(poss_args, more_disambig_flag) :
                var = next_var[0]
                next_var[0] = chr(ord(var) + 1)
                if len(poss) == 1 : # no need to disambiguate this slot
                    constructed_args.extend(poss)
                else :
                    if disamb_more :
                        constructed_args.append(__construct_pattern(poss, to_replace, next_var))
                    else :
                        to_replace[var] = poss
                        constructed_args.append(VarPattern(var))
            return type(results[0])(*constructed_args)
        to_replace = dict()
        return Ambiguous(__construct_pattern(results, to_replace, ['a']), to_replace)

    def copy(self) :
        newparser = Parser()
        newparser.KNOWN_WORDS = list(self.KNOWN_WORDS)
        for name, table in self.subparsers.iteritems() :
            newparser.subparsers[name] = table.copy()
        newparser.parse_thing = self.parse_thing.copy()
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
def default_parse_thing(parser, var, name, words, input, i, ctxt, next, multiplier=1) :
    """Given a set of words and a name, tries to find a subsequence by
    using the grammar [art]? [adjs]* [noun]?, where there is at least
    one adjective or noun."""
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


default_parser.define_subparser("action", """A parser to match against entire
actions.  The resulting Match.value should be a BasicAction.  This is
the main parser.""")

default_parser.define_subparser("something", "A parser to match against things in the game.")

@default_parser.add_subparser("something")
def default_something(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse as if the following input were a thing."""
    return list_append([parser.parse_thing.notify([parser, var, name, words,input,i,ctxt,next],{})
                        for name,words in zip(parser.CURRENT_OBJECTS, parser.CURRENT_WORDS)])


default_parser.define_subparser("object", "A parser which uses its variable as an object id, instead.")

@default_parser.add_subparser("object")
def default_object(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse the input so that the var is the name of the object."""
    words = separate_object_words(ctxt.world.get_property("Words", var))
    return parser.parse_thing.notify([parser, None,var,words,input,i,ctxt,next,2],{})


default_parser.define_subparser("text", """Just matches against any sequence of words.""")

@default_parser.add_subparser("text")
def default_parse_text(parser, var, input, i, ctxt, actor, next) :
    """Parses any number of words, stopping at or before the end of
    the input."""
    out = []
    for i2 in xrange(i+1,len(input)+1) :
        out.extend(product([[Matched(input[i:i2], " ".join(input[i:i2]), 1, var)]],
                           next(i2)))
    return out
