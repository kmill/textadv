# patterns.py
#
# pattern matching decorators
#
# What's here:
# Exceptions: DuplicateVariableException, NoMatchException
# Patterns: AbstractPattern, PVar=VarPattern, PPred=PredicatePattern, BasicPattern, TagPattern
# Decorators: wantsPattern

###
### Exceptions
###

class DuplicateVariableException(Exception) :
    pass

class NoMatchException(Exception) :
    pass

###
### Patterns
###

class AbstractPattern(object) :
    def __init__(self) :
        raise NotImplementedError("AbstractPattern is abstract (no __init__)")
    def match(self, input, matches=None, data=None) :
        """Try to match against the input, and return a dictionary
        with the variables bound.  Assume that the "matches" argument
        will be modified."""
        raise NotImplementedError("AbstractPattern is abstract (no match)")
    def expand_pattern(self, replacements) :
        """Try to use the replacements dictionary to modify the
        pattern.  By default returns self."""
        return self

class VarPattern(AbstractPattern) :
    """Creates a pattern which matches anything, but binds the result
    as a variable. The second argument can restrict the variable to
    having to match that given pattern."""
    def __init__(self, varName, pattern=None) :
        self.varName = varName
        self.pattern = pattern
    def match(self, input, matches=None, data=None) :
        if matches == None : matches = dict()
        if matches.has_key(self.varName) :
            raise DuplicateVariableException(self.varName)
        if self.pattern is not None :
            matches = self.pattern.match(input, matches=matches, data=data)
        matches[self.varName] = input
        return matches
    def expand_pattern(self, replacements) :
        if self.varName in replacements :
            return replacements[self.varName]
        else :
            raise KeyError(self.varName)
    def __repr__(self) :
        if self.pattern is not None :
            return "<VarPattern %r %r>" % (self.varName, self.pattern)
        else :
            return "<VarPattern %r>" % self.varName

# for convenience
PVar = VarPattern

class PredicatePattern(AbstractPattern) :
    """A pattern which matches first on the given pattern, then checks
    that each of the predicates are true, when evaluated on the
    variables in the pattern."""
    def __init__(self, pattern, *predicates) :
        self.pattern = pattern
        self.predicates = predicates
    def match(self, input, matches=None, data=None) :
        if matches == None : matches = dict()
        matches = self.pattern.match(input, matches=matches, data=data)
        for p in self.predicates :
            if not p(**matches) :
                raise NoMatchException(self, "Predicate failed")
        return matches
    def __repr__(self) :
        return "<PredicatePattern %r %r>" % (self.pattern, self.predicates)

# for convenience
PPred = PredicatePattern

class BasicPattern(AbstractPattern) :
    """A basic pattern which takes some number of
    subpatterns. Subpatterns may be other objects, but these are only
    tested for equality. This is essentially a tagged list
    pattern. Subclasses need only make sure self.args is a list of
    patterns."""
    def __init__(self, *args) :
        self.args = args
    def match(self, input, matches=None, data=None) :
        if matches == None : matches = dict()
        if self.__class__ is not input.__class__ :
            raise NoMatchException(self, input)
        if len(self.args) != len(input.args) :
            raise NoMatchException(self, input)
        for myarg, inputarg in zip(self.args, input.args) :
            if isinstance(myarg, AbstractPattern) :
                matches = myarg.match(inputarg, matches=matches, data=data)
            else :
                if not (myarg == inputarg) :
                    raise NoMatchException(myarg, inputarg)
        return matches
    def expand_pattern(self, replacements) :
        """Expands a basic pattern by reinstantiating itself with
        expanded arguments."""
        newargs = []
        for arg in self.args :
            if isinstance(arg, AbstractPattern) :
                newargs.append(arg.expand_pattern(replacements))
            else :
                newargs.append(arg)
        return type(self)(*newargs)
    def __repr__(self) :
        return "<%s%s>" % (self.__class__.__name__, "".join([" "+repr(a) for a in self.args]))

class TagPattern(AbstractPattern) :
    """The first argument matches on the type of the basic pattern."""
    def __init__(self, t, *args) :
        self.t = t
        self.args = args
    def match(self, input, matches=None, data=None) :
        if matches == None :matches = dict()
        if not isinstance(input, BasicPattern) :
            raise NoMatchException(self, input)
        if len(self.args) != len(input.args) :
            raise NoMatchException(self, input)
        t = self.t.match(input.__class__, matches=matches, data=data)
        for myarg, inputarg in zip(self.args, input.args) :
            if isinstance(myarg, AbstractPattern) :
                matches = myarg.match(inputarg, matches=matches, data=data)
            else :
                if not (myarg == inputarg) :
                    raise NoMatchException(myarg, inputarg)
        return matches
    def expand_pattern(self, replacements) :
        """Expands a tag pattern by expanding everything, and then
        using the t field as a constructor."""
        newt = self.t.expand_pattern(replacements)
        newargs = []
        for arg in self.args :
            if isinstance(arg, AbstractPattern) :
                newargs.append(arg.expand_pattern(replacements))
            else :
                newargs.append(arg)
        return netw(*newargs)
    def __repr__(self) :
        return "<TagPattern %r %s>" % (self.t, "".join([" "+repr(a) for a in self.args]))
###
### Decorator
###

def wantsPattern(pattern, withoutkey=None) :
    """Returns a decorator which wraps "match" around a function.  If
    the decorated function is given more than one argument after the
    pattern, these are placed in the first slots of the original.  The
    "withoutkey" argument is not passed on."""
    def _wantsPattern(f) :
        def __wantsPattern(input, *args, **kwargs) :
            matches = pattern.match(input,data=kwargs.get("data",None))
            newkwargs = kwargs.copy()
            if withoutkey is not None :
                if newkwargs.has_key(withoutkey) :
                    del newkwargs[withoutkey]
            matches.update(newkwargs) # overwrite matched values!
            return f(*args,**matches)
        return __wantsPattern
    return _wantsPattern

###
### Tests
###
import unittest

class TestPatterns(unittest.TestCase) :
    class PActor(BasicPattern) :
        def __init__(self, actor) :
            self.args = [actor]
        def __eq__(self, other) :
            return type(self) == type(other) and self.args == other.args
    class PRoom(BasicPattern) :
        def __init__(self, room) :
            self.args = [room]
    class PEnters(BasicPattern) :
        def __init__(self, actor, place) :
            self.args = [actor, place]

    def test_var(self) :
        pattern = PVar("x")
        self.assertEqual(pattern.match("hi"), {"x":"hi"})

    def test_duplicate_var(self) :
        pattern = BasicPattern(PVar("x"), PVar("x"))
        self.assertRaises(DuplicateVariableException, pattern.match, BasicPattern(1, 2))

    def test_pattern_subclasses(self) :
        pattern = self.PEnters(self.PActor(PVar("actor")), self.PRoom(PVar("room")))
        self.assertEqual(pattern.match(self.PEnters(self.PActor("Kyle"), self.PRoom("Vestibule"))),
                         {"actor":"Kyle", "room":"Vestibule"})

    def test_pattern_failure(self) :
        pattern = self.PActor("kyle")
        # because of class mismatch:
        self.assertRaises(NoMatchException, pattern.match, self.PRoom("kyle"))
        # because of string mismatch:
        self.assertRaises(NoMatchException, pattern.match, self.PActor("bob"))

    def test_bind_pattern(self) :
        pattern = PVar("y", self.PActor(PVar("x"))) 
        matches = pattern.match(self.PActor("kyle"))
        self.assertEqual(matches["x"], "kyle")
        self.assertEqual(repr(matches["y"]), "<PActor 'kyle'>")

    def test_predicate_pattern(self) :
        def p(x) :
            return x>=21
        pattern = PPred(BasicPattern("age", PVar("x")),
                        p)
        matches = pattern.match(BasicPattern("age", 50))
        self.assertEqual(matches["x"], 50)
        self.assertRaises(NoMatchException, pattern.match, BasicPattern("age", 12))

    def test_decorator(self) :
        @wantsPattern(self.PActor(PVar("x")))
        def f(x) :
            return x.upper()
        self.assertRaises(NoMatchException, f, self.PRoom("whoops"))
        self.assertEqual(f(self.PActor("kyle")), "KYLE")

    def test_decorator_args(self) :
        @wantsPattern(PVar("x"))
        def f(data, x) :
            return data[x]
        self.assertEqual(f(1, {1:2}), 2)
        self.assertEqual(f(1, data={1:2}), 2)

    def test_expand(self) :
        p = self.PActor(PVar("x"))
        self.assertRaises(KeyError, p.expand_pattern, {"y":3})
        self.assertEqual(p.expand_pattern({"x":3}), self.PActor(3))

if __name__=="__main__" :
    unittest.main(verbosity=2)
