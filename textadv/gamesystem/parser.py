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
from textadv.core.world import obj_to_id

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
### Basic data objects
###

class Word(object) :
    def __init__(self, word, pos, nosuchword_candidate=False) :
        """Takes the word itself along with its possible parts of
        speech as a list.  The nosuchword_candidate argument is to
        signal that the lexer generated this word object with no pos
        just in case TextNonTerminal can match it."""
        self.word = word
        self.pos = pos
        self.nosuchword_candidate = nosuchword_candidate
    def is_word(self, string) :
        return self.word.lower() == string.lower()
    def is_pos(self, pos) :
        return pos in self.pos
    def __repr__(self) :
        return "<Word "+repr(self.word)+" "+repr(self.pos)+">"

class ObjWords(object) :
    def __init__(self, obj, adjs, nouns) :
        self.obj = obj
        self.adjs = adjs
        self.nouns = nouns
    def matches(self, adjs, nouns) :
        for a in adjs :
            if a.lower() not in self.adjs :
                return False
        for n in nouns :
            if n.lower() not in self.nouns :
                return False
        return True
    def __repr__(self) :
        return "<ObjWords %r %r %r>" % (self.obj, self.adjs, self.nouns)

class Possibilities(object) :
    """Helps keep track of all possibilities.  A simple implementation
    at the moment."""
    def __init__(self, *seqs) :
        self.possibilities = list(seqs)
    def product(self, poss2) :
        """Multiply two sets of possibilities together by cartesian product."""
        poss = [p1 + p2 for p1 in self.possibilities for p2 in poss2.possibilities]
        return Possibilities(*poss)
    def sum(self, poss2) :
        """Unions two sets of possibilities."""
        poss = self.possibilities + poss2.possibilities
        return Possibilities(*poss)
    def __iter__(self) :
        return iter(self.possibilities)
    def __repr__(self) :
        return "<Possibilities %r>" % (self.possibilities,)

class DirectionWords(object) :
    def __init__(self, direction, names) :
        self.direction = direction
        self.names = names
    def matches(self, names) :
        for n in names :
            if n.lower() not in self.names :
                return False
        return True
    def __repr__(self) :
        return "<DirectionWords %r %r>" % (self.direction, self.names)

###
### Parser objects (do parsing)
###

class NonTerminal(object) :
    def __init__(self, var=None) :
        if var == None :
            var = None
        elif isinstance(var, VarPattern) :
            self.var = var.varName
        else :
            self.var = var
    def parse(self, input, i, parser, next) :
        """See Terminal for documentation of parse."""
        raise NotImplementedError("parse not implemented on abstract NonTerminal")
    def __eq__(self, other) :
        return type(self) == type(other) and self.var == other.var
    def __repr__(self) :
        return "<NonTerminal %s %s>" % (self.__class__.__name__, self.var)

class Matched(object) :
    """The score is 1 if it is normal, and 2 if it has a noun."""
    def __init__(self, binding, words, score, obj, is_noun=True) :
        self.words = words
        self.binding = binding
        self.obj = obj
        self.score = score
        self.is_noun = is_noun
    def __repr__(self) :
        return "<Matched %r %s=%r %r %r>" % (self.score, self.binding, self.obj, self.words, self.is_noun)

class PronounMatched(Matched) :
    """The score is 1 if it is normal, and 2 if it has a noun."""
    def __init__(self, binding, pronoun, score, obj) :
        self.pronoun = pronoun
        self.binding = binding
        self.obj = obj
        self.score = score
        self.is_noun = True
    def __repr__(self) :
        return "<PronounMatched %r %s=%r %r>" % (self.score, self.binding, self.obj, self.pronoun)

## Nonterminals:
## (grammar matcher things)

class Something(NonTerminal) :
    """Match a noun in the vicinity."""
    def parse(self, input, i, parser, next) :
        return match_noun_form(input, i, parser, self.var, parser.local_objects, next)
            
class Anything(NonTerminal) :
    """Match a noun in the game."""
    def parse(self, input, i, parser, next) :
        return match_noun_form(input, i, parser, self.var, parser.global_objects, next)

class Direction(NonTerminal) :
    """Match a direction word."""
    def parse(self, input, i, parser, next) :
        if i < len(input) and input[i].is_pos("direction") :
            dirs = enums_with_words(parser.global_enums["directions"], [input[i].word])
            if dirs :
                poss = Possibilities([Matched(self.var, [input[i]], 1, o.direction, is_noun=False)
                                      for o in dirs])
                return poss.product(next(input, i+1))
        return Possibilities()

class TextNonTerminal(NonTerminal) :
    """Match some arbitrary string of words, as in [word]+."""
    def parse(self, input, i, parser, next) :
        poss = Possibilities()
        for j in xrange(i,len(input)) :
            myword = " ".join(w.word for w in input[i:j+1])
            poss2 = Possibilities([Matched(self.var, input[i:j+1], 1, myword)])
            poss2 = poss2.product(next(input, j+1))
            poss = poss.sum(poss2)
        return poss

class ObjectNonTerminal(NonTerminal) :
    """Match some object which has the given id.  We assume var is the
    object name."""
    def parse(self, input, i, parser, next) :
        objs = [o for o in parser.global_objects if o.obj.id == self.var]
        if len(objs) == 0 :
            raise Exception("No such object id "+repr(self.var))
        return match_noun_form(input, i, parser, self.var, objs, next, multiplier=2)

# end of these

def objs_with_words(word_set, adjs, nouns) :
    """Find all objects such that adjs and nouns describes them,
    unless both sets are empty."""
    if not adjs and not nouns :
        return []
    else :
        return [o for o in word_set if o.matches(adjs, nouns)]

def enums_with_words(word_set, words) :
    """Like objs_with_words, but for use with some kind of enum like
    direction."""
    if not words :
        return []
    else :
        return [o for o in word_set if o.matches(words)]

# noun_form is:
# [art]? [adjs]* [noun]? (a cheat, either at least one adj or have a noun)
def match_noun_form(input, i, parser, binding, word_set, next, multiplier=1) :
    # try to find [adjs]* [noun]? forms, aborting when the chain is no longer a real object:
    def match_adjs_nouns(curr_adjs, i2) :
        poss = Possibilities()
        if i2 < len(input) :
            # try adding another adjective
            if input[i2].is_pos("adj") :
                new_adjs = curr_adjs + [input[i2].word]
                if objs_with_words(word_set, new_adjs, []) :
                    poss = poss.sum(match_adjs_nouns(new_adjs, i2+1))
            # or try concluding with a noun
            if input[i2].is_pos("noun") :
                nouns = [input[i2].word]
                objs = objs_with_words(word_set, curr_adjs, nouns)
                if objs :
                    matches = Possibilities(*[[Matched(binding, input[i:i2+1], 2*multiplier, o.obj)]
                                              for o in objs])
                    poss = poss.sum(matches.product(next(input, i2+1)))
        # or just conclude the noun
        objs = objs_with_words(word_set, curr_adjs, [])
        if objs :
            matches = Possibilities(*[[Matched(binding, input[i:i2], 1*multiplier, o.obj)]
                                      for o in objs])
            poss = poss.sum(matches.product(next(input, i2)))
        return poss
    possib = Possibilities()
    if i < len(input) :
        if input[i].is_pos("pronoun") :
            if parser.has_pronoun(input[i].word) :
                possib2 = Possibilities([PronounMatched(binding, input[i], 1*multiplier, parser.resolve_pronoun(input[i].word))])
                possib = possib.sum(possib2.product(next(input, i+1)))
        # skip the article
        if input[i].is_pos("art") :
            i += 1
        possib = possib.sum(match_adjs_nouns([], i))
    return possib

class Terminal(object) :
    """Abstract terminal object.  Should only be extended."""
    def __init__(self, string) :
        self.string = string
    def parse(self, input, i, parser, next) :
        """Parse against input starting from i.  The argument next is
        a continuation which takes the input and a starting i.  The
        result must be a Possibilities object."""
        if i<len(input) and self == input[i] :
            return Possibilities([self]).product(next(input, i+1))
        else :
            return Possibilities()
    def __eq__(self, other) :
        return type(self) == type(other) and self.string == other.string
    def __repr__(self) :
        return "<Terminal %s>" % self.string

class WordTerminal(Terminal) :
    """Matches a particular word with a particular part of speech."""
    def __init__(self, string, pos) :
        self.string = string
        self.pos = pos
    def parse(self, input, i, parser, next) :
        if i<len(input) and input[i].is_word(self.string) and input[i].is_pos(self.pos) :
            return Possibilities([self]).product(next(input, i+1))
        else :
            return Possibilities()
    def __repr__(self) :
        return "<WordTerminal %s %s>" % (self.string, self.pos)

class Terminator(Terminal) :
    """Matches the end of a stream."""
    def __init__(self, val=None) :
        """The optional value represents the final meaning of the
        parsed expression."""
        self.val = val
    def parse(self, input, i, parser, next) :
        if len(input) == i :
            return Possibilities([self])
        else :
            return Possibilities()
    def __eq__(self, other) :
        return type(self) == type(other)
    def __repr__(self) :
        return "<Terminator>"

class UnionGrammar(object) :
    """A parser object which is the union of some number of
    patterns. Holds the grammar in a tree structure."""
    def __init__(self) :
        self.choices = []
        self.rest = []
    def add_sequence(self, seq, result=None) :
        if seq == [] :
            next = Terminator(result)
            rest = None
        else :
            next = seq[0]
            rest = seq[1:]
            if type(next) == str :
                next = Terminal(next)
        try :
            i = self.choices.index(next)
        except ValueError :
            g = UnionGrammar()
            self.choices.append(next)
            self.rest.append(g)
            i = -1
        if rest is not None :
            self.rest[i].add_sequence(rest, result)
    def parse(self, input, i, parser, next) :
        poss = Possibilities()
        for j in xrange(len(self.choices)) :
            def _next(input2, i2) :
                return self.rest[j].parse(input2, i2, parser, next)
            poss = poss.sum(self.choices[j].parse(input, i, parser, _next))
        return poss
    def __repr__(self) :
        out = "<UnionGrammar {"
        for choice, rest in zip(self.choices, self.rest) :
            out += repr(choice) + "=" + repr(rest)
        return out
    def to_string(self, prefix="") :
        if self.choices == [] :
            return "\n"
        out = "UnionGrammar\n"
        out = ""
        for i, (choice, rest) in enumerate(zip(self.choices, self.rest)) :
            rc = repr(choice)
            if i == 0 :
                newprefix = prefix + " "*(len(rc)+3)
                out += " |-" + rc + rest.to_string(prefix=newprefix)
            else :
                if i + 1 == len(self.choices) :
                    newprefix = prefix + " "*(len(rc)+3)
                else :
                    newprefix = prefix + " |"+ " "*(len(rc)+1)
                out += prefix + " |-" + rc + rest.to_string(prefix=newprefix)
        return out

class Parser(object) :
    """The main parser object. By default, it's grammar is a
    UnionGrammar, which can be extended easily by using
    add_sentence."""
    def __init__(self) :
        self.grammar = UnionGrammar()
        self.lexicon = dict()
        self.local_lexicon = dict()
        self.local_objects = []
        self.global_objects = []
        self.pronouns = dict()
        self.global_enums = {"directions" : []}
    def add_default_words(self) :
        self.add_word("a", "art")
        self.add_word("an", "art")
        self.add_word("the", "art")
        self.add_word("it", "pronoun")
        self.add_word("north", "direction")
        # a little cheat, but posessives don't do anything special at the moment
        self.add_word("my", "art")
        self.add_word("your", "art")
        self.add_word("his", "art")
        self.add_word("her", "art")
        self.add_word("their", "art")
        self.add_word("our", "art")
    def add_word(self, w, pos) :
        """Adds a word to the main parser dictionary. Make sure that w is
        lower case."""
        if self.lexicon.has_key(w) :
            if w not in self.lexicon[w] :
                self.lexicon[w].append(pos)
        else :
            self.lexicon[w] = [pos]
    def add_local_word(self, w, pos) :
        """Adds a word to the local parser dictionary. Make sure that w is
        lower case."""
        if pos not in self._get_word_pos(w) :
            if w in self.local_lexicon :
                self.local_lexicon[w].append(pos)
            else :
                self.local_lexicon[w] = [pos]
    def reset_local_words(self) :
        """Reset words which are added from turn to turn (as opposed
        to global words like verbs and articles."""
        self.local_lexicon = dict()
    def _has_word(self, w) :
        return w.lower() in self.local_lexicon or w in self.lexicon
    def _get_word_pos(self, w) :
        w = w.lower()
        return self.local_lexicon.get(w, []) + self.lexicon.get(w, [])
    def has_pronoun(self, pronoun) :
        return self.pronouns.has_key(pronoun)
    def resolve_pronoun(self, pronoun) :
        return self.pronouns[pronoun]
    def set_pronoun(self, pronoun, object) :
        self.pronouns[pronoun] = object
    def add_sentence(self, seq, result) :
        """Adds a sentence by inserting it into the contained
        UnionGrammar.  Also adds any non-tagged words to the lexicon
        as verbs.  Result is a pattern which gets expanded by the
        terminal variables to represent the final meaning."""
        seq2 = []
        for p in seq :
            if type(p) == str :
                seq2.append(WordTerminal(p, "verb"))
                self.add_word(p, "verb")
            else :
                seq2.append(p)
        self.grammar.add_sequence(seq2, result)
    def set_local_objects(self, objs) :
        """Takes a list of (obj, words) where words is a list of words
        as strings.  If a word is prefixd with an @, then it is added
        to the lexicon as a noun.  This sets the collection of objects
        referenced by Something."""
        self.local_objects = []
        self._set_objects(self.local_objects, objs)
    def set_global_objects(self, objs) :
        """Takes a list of (obj, words) where words is a list of words
        as strings.  If a word is prefixd with an @, then it is added
        to the lexicon as a noun.  This sets the collection of objects
        referenced by Anything."""
        self.global_objects = []
        self._set_objects(self.global_objects, objs)
    def _set_objects(self, dest, objs) :
        for (obj, words) in objs :
            words = [w.lower() for w in words]
            adjs = []
            nouns = []
            for w in words :
                if w[0] == "@" :
                    self.add_local_word(w[1:], "noun")
                    nouns.append(w[1:])
                else :
                    self.add_local_word(w, "adj")
                    adjs.append(w)
            dest.append(ObjWords(obj, adjs, nouns))
    def add_global_direction(self, direction, names) :
        names = [name.lower() for name in names]
        for name in names :
            self.add_word(name, "direction")
        if not self.global_enums.has_key("directions") :
            self.global_enums["directions"] = []
        self.global_enums["directions"].append(DirectionWords(direction, names))
    def lex(self, input) :
        """Takes raw text input and converts it to a list of lexed
        sentences."""
        sentences = input.split(".")
        return [self.lex_sentence(s) for s in sentences]
    def lex_sentence(self, sentence) :
        """Takes raw text (after it's split into sentences) and creates a
        list of Word objects which represent the possibilities of each
        word."""
        lexed = []
        for word in re.findall("'.+?'|,|[0-9A-Za-z_]+", sentence) :
            if self._has_word(word) :
                lexed.append(Word(word, self._get_word_pos(word)))
            else :
                lexed.append(Word(word, [], nosuchword_candidate=True))
        return lexed
    def parse(self, lexed, grammar=None) :
        if grammar == None :
            grammar = self.grammar
        def _next(input, i) :
            raise Exception("Shouldn't be called.")
        return grammar.parse(lexed, 0, self, _next)
    def parse_all(self, input, grammar=None) :
        """Take raw input, and then parses it after lexing."""
        return [self.parse(l, grammar=grammar) for l in self.lex(input)]
    def _gen_replacements(self, p) :
        repla = dict()
        for w in p :
            if isinstance(w, Matched) :
                repla[w.binding] = w.obj
        return repla
    def _get_terminator_action(self, p) :
        return p[-1].val
    def _get_noun_score(self, p) :
        """Just sums up the noun scores so that we can select things
        that are nouned over those that are not."""
        score = 0
        for w in p :
            if isinstance(w, Matched) :
                score += w.score
        return score
    def handle(self, lexed, possibilities, actor, verifyfn, handlefn) :
        poss = []
        actions = []
        for p in possibilities :
            repla = self._gen_replacements(p)
            if "actor" not in repla :
                repla["actor"] = actor
            poss.append(p)
            actions.append(self._get_terminator_action(p).expand_pattern(repla))
        if len(actions) == 0 :
            # Perhaps it was because we didn't know a word?
            for w in lexed :
                if w.nosuchword_candidate :
                    raise NoSuchWord(w.word)
            # Nope.
            raise NoUnderstand()
        elif len(actions) == 1 :
            handlefn(poss[0], actions[0])
        else :
            # otherwise, it's ambiguous
            scores = [(p, a, verifyfn(a)) for p,a in zip(poss,actions)]
            scores.sort(key=lambda z : z[2].score)
            if scores[-1][2].is_acceptible() :
                best_score = scores[-1][2].score
                best = [s for s in scores if s[2].score == best_score]
                if len(best) == 1 :
                    handlefn(best[0][0], best[0][1], write_action=True)
                else :
                    best.sort(key=lambda z : self._get_noun_score(z[0]))
                    best_n_score = self._get_noun_score(scores[-1][0])
                    best2 = [b for b in best if self._get_noun_score(b[0]) == best_n_score]
                    if len(best2) == 1 :
                        handlefn(best2[0][0], best2[0][1], write_action=True)
                    else :
                        actions = [z[1] for z in best2]
                        types = set(type(a) for a in actions)
                        if len(types) > 1 :
                            # Don't know how to handle if there are two different actions!
                            raise Ambiguous()
                        numargs = len(actions[0].args)
                        amb_objs = [set(obj_to_id(a.args[i]) for a in actions)
                                    for i in xrange(numargs)]
                        amb_objs = [list(ao) for ao in amb_objs if len(ao) > 1]
                        amb_objs = list(itertools.chain(amb_objs))
                        raise Ambiguous(amb_objs)
            else :
                # I don't know how to best disambiguate things which don't work.
                handlefn(scores[0][0], scores[0][1])
    def handle_all(self, input, actor, verifyfn, handlefn) :
        def _new_handlefn(sentence, action, write_action=False) :
            """Makes a new handle function with a new signature which saves the
            last noun referred to as "it".  If a pronoun was used in
            the sentence, then we write out the action."""
            had_pronoun = False
            for w in sentence :
                if isinstance(w, Matched) and w.is_noun :
                    had_pronoun = had_pronoun or isinstance(w, PronounMatched)
                    self.set_pronoun("it", w.obj)
            if had_pronoun or write_action :
                handlefn(action, write_action=True)
            else :
                handlefn(action)
        all_lexed = self.lex(input)
        if all_lexed == [] :
            raise NoInput()
        for lexed in all_lexed :
            self.handle(lexed, self.parse(lexed), actor, verifyfn, _new_handlefn)
    def __repr__(self) :
        return "<Parser %s\nlexicon=%r\nlocal_lexicon=%r>" % (self.grammar.to_string(prefix=" "*len("<Parser ")), self.lexicon, self.local_lexicon)

if __name__=="__main__" :
    p = Parser()
    p.add_sentence(["inventory"], None)
    p.add_sentence(["examine", Something("x")], None)
    p.add_sentence(["unlock", Something("x"), "with", Something("y")], None)
    p.add_sentence(["debug_dump", Anything("x")], None)
    p.add_sentence(["give", Something("x"), "to", Something("y")], None)
    p.add_sentence(["give", Something("x"), Something("y")], None)
    p.add_sentence(["take", Something("x")], None)

    p.add_default_words()

    p.set_local_objects([("ball1", ["big", "red", "@ball"]),
                         ("ball2", ["small", "blue", "@ball"])])

    print p
    
    print p.parse_all("give red red")
    print p.parse_all("take the red ball")
    print p.parse_all("take the ball")
