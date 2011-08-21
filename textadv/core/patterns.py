# patterns.py
#
# Support for pattern matching
#
# What's here:
# Exceptions: DuplicateVariableException, NoMatchException
# Patterns: AbstractPattern, VarPattern, BasicPattern

###
### Exceptions
###

class DuplicateVariableException(Exception) :
    """A variable can only be matched against once."""
    pass

class NoMatchException(Exception) :
    """Raised if a matched cannot be made."""
    pass

class ExpansionException(Exception) :
    """Raised if an expansion cannot be made, not due to a KeyError,
    but due to failed support."""
    pass

###
### Metaclass
###

class ClassHashByName(type) :
    def __hash__(self) :
        return hash("ClassHashByName "+self.__name__)
    def __eq__(self, b) :
        if type(b) == str :
            return False
        else :
            return self.__name__ == b.__name__
    def __ne__(self, b) :
        if type(b) == str :
            return True
        else :
            return self.__name__ != b.__name__


###
### Patterns
###

class AbstractPattern(object) :
    __metaclass__ = ClassHashByName
    def __init__(self) :
        raise NotImplementedError("AbstractPattern is abstract (no __init__)")
    def match(self, input, matches=None, data=None) :
        """Try to match against the input, and return a dictionary
        with the variables bound.  Assume that the "matches" argument
        will be modified."""
        raise NotImplementedError("AbstractPattern is abstract (no match)", self)
    def expand_pattern(self, replacements, data=None) :
        """Try to use the replacements dictionary to modify the
        pattern.  By default returns self."""
        return self
    def file_under(self) :
        return type(self)
    def __le__(self, b) :
        return PatternRequires(self, b)
    def __and__(self, b) :
        if not isinstance(b, AbstractPattern) :
            raise Exception("Not anding with a pattern", self, b)
        return PatternConjunction(self, b)
    def __hash__(self) :
        return hash(repr(self))

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
        # first make the binding, so that continued matching will cause DuplicateVariableException
        matches[self.varName] = input
        if self.pattern is not None :
            matches = self.pattern.match(input, matches=matches, data=data)
        return matches
    def expand_pattern(self, replacements, data=None) :
        if self.varName in replacements :
            return replacements[self.varName]
        else :
            raise KeyError(self.varName)
    def __repr__(self) :
        if self.pattern is not None :
            return "VarPattern(%r,%r)" % (self.varName, self.pattern)
        else :
            return "VarPattern(%r)" % self.varName

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
        if type(self) != type(input) :
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
    def expand_pattern(self, replacements, data=None) :
        """Expands a basic pattern by reinstantiating itself with
        expanded arguments."""
        newargs = []
        for arg in self.args :
            if isinstance(arg, AbstractPattern) :
                newargs.append(arg.expand_pattern(replacements, data=data))
            else :
                newargs.append(arg)
        return type(self)(*newargs)
    def test(self, world) :
        targs = [a.test(world) if isinstance(a, AbstractPattern) else a for a in self.args]
        return world[type(self)(*targs)]
    def __repr__(self) :
        return "%s(%s)" % (self.__class__.__name__, ",".join(repr(a) for a in self.args))
    def __eq__(self, other) :
        return type(other) == type(self) and self.args == other.args
    def __hash__(self) :
        return hash("BasicPattern "+self.__repr__())

class PatternRequires(AbstractPattern) :
    def __init__(self, pattern, support) :
        self.pattern = pattern
        self.support = support
    def match(self, input, matches=None, data=None) :
        matches = self.pattern.match(input, matches, data)
        try :
            if not self.support.expand_pattern(matches, data=data).test(data["world"]) :
                raise NoMatchException(self, self.support)
            return matches
        except KeyError :
            raise NoMatchException(self, self.support)
    def expand_pattern(self, replacements, data=None) :
        """Like match, except returns the expanded pattern after
        trying to expand the support."""
        if data is not None :
            if not self.support.expand_pattern(replacements, data=data).test(data["world"]) :
                raise ExpansionException(self)
        return self.pattern.expand_pattern(replacements, data=data)
    def file_under(self) :
        return self.pattern.file_under()
    def __repr__(self) :
        return "%r <= %r" % (self.pattern, self.support)

class PatternConjunction(AbstractPattern) :
    def __init__(self, *support) :
        self.support = support
    def test(self, world) :
        return all(s.test(world) for s in self.support)
    def expand_pattern(self, matches, data=None) :
        return PatternConjunction(*[s.expand_pattern(matches, data=data) for s in self.support])
    def __and__(self, b) :
        if not isinstance(b, AbstractPattern) :
            raise Exception("Not anding with a BasicPattern")
        return PatternConjunction(*(list(self.support)+[b]))
    def __repr__(self) :
        return " & ".join(repr(s) for s in self.support)

class PNot(AbstractPattern) :
    def __init__(self, to_not) :
        self.to_not = to_not
    def test(self, world) :
        return not self.to_not.test(world)
    def expand_pattern(self, matches, data=None) :
        return PNot(self.to_not.expand_pattern(matches, data=data))
    def __repr__(self) :
        return "PNot(%r)" % self.to_not

class PEquals(AbstractPattern) :
    def __init__(self, a, b) :
        self.a, self.b = a, b
    def test(self, world) :
        a = self.a.test(world) if isinstance(self.a, AbstractPattern) else self.a
        b = self.b.test(world) if isinstance(self.b, AbstractPattern) else self.b
        return (a==b)
    def expand_pattern(self, matches, data=None) :
        a = self.a.expand_pattern(matches, data=data) if isinstance(self.a, AbstractPattern) else self.a
        b = self.b.expand_pattern(matches, data=data) if isinstance(self.b, AbstractPattern) else self.b
        return PEquals(a, b)
    def __repr__(self) :
        return "PEquals(%r, %r)" % (self.a, self.b)

class PIn(AbstractPattern) :
    def __init__(self, a, bs) :
        self.a, self.bs = a, bs
    def test(self, world) :
        a = self.a.test(world) if isinstance(self.a, AbstractPattern) else self.a
        bs = [b.test(world) if isinstance(b, AbstractPattern) else b for b in self.bs]
        return (a in bs)
    def expand_pattern(self, matches, data=None) :
        a = self.a.expand_pattern(matches, data=data) if isinstance(self.a, AbstractPattern) else self.a
        bs = [b.expand_pattern(matches, data=data) if isinstance(b, AbstractPattern) else b for b in self.bs]
        return PIn(a, bs)
    def __repr__(self) :
        return "PIn(%r, %r)" % (self.a, self.bs)

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
        pattern = VarPattern("x")
        self.assertEqual(pattern.match("hi"), {"x":"hi"})

    def test_duplicate_var(self) :
        pattern = BasicPattern(VarPattern("x"), VarPattern("x"))
        self.assertRaises(DuplicateVariableException, pattern.match, BasicPattern(1, 2))
        pattern = BasicPattern(VarPattern("x", VarPattern("x")))
        self.assertRaises(DuplicateVariableException, pattern.match, BasicPattern(1))

    def test_pattern_subclasses(self) :
        pattern = self.PEnters(self.PActor(VarPattern("actor")), self.PRoom(VarPattern("room")))
        self.assertEqual(pattern.match(self.PEnters(self.PActor("Kyle"), self.PRoom("Vestibule"))),
                         {"actor":"Kyle", "room":"Vestibule"})

    def test_pattern_failure(self) :
        pattern = self.PActor("kyle")
        # because of class mismatch:
        self.assertRaises(NoMatchException, pattern.match, self.PRoom("kyle"))
        # because of string mismatch:
        self.assertRaises(NoMatchException, pattern.match, self.PActor("bob"))

    def test_bind_pattern(self) :
        pattern = VarPattern("y", self.PActor(VarPattern("x"))) 
        matches = pattern.match(self.PActor("kyle"))
        self.assertEqual(matches["x"], "kyle")
        self.assertEqual(repr(matches["y"]), "PActor('kyle')")

    def test_expand(self) :
        p = self.PActor(VarPattern("x"))
        self.assertRaises(KeyError, p.expand_pattern, {"y":3})
        self.assertEqual(p.expand_pattern({"x":3}), self.PActor(3))

if __name__=="__main__" :
    unittest.main(verbosity=2)
