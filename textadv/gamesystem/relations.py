# relations.py
#
# Defining relations between objects.  Relations must be created at
# the top level of a module!!!
#
# provides: make_many_to_one_relation, make_one_to_many_relation

from textadv.core.patterns import BasicPattern, VarPattern, NoMatchException
from textadv.gamesystem.basicpatterns import *

class Relation(BasicPattern) :
    @staticmethod
    def setup_table() :
        """Returns data which supports this relation, which is to be
        stored somewhere."""
        raise NotImplementedError("Relation is abstract")
    def add_relation(self, data) :
        """Adds self to data."""
        raise NotImplementedError("Relation is abstract")
    def remove_relation(self, data) :
        """Removes self from data."""
        raise NotImplementedError("Relation is abstract")
    def query_relation(self, data) :
        """Returns matches of self in data."""
        raise NotImplementedError("Relation is abstract")
    @classmethod
    def path_to(r, data, a, b) :
        """Finds a path from a to b using data as the database."""
        raise NotImplementedError("Relation is abstract")
    @classmethod
    def copy(r, data) :
        raise NotImplementedError("Relation is abstract")
    @classmethod
    def dump(r, data) :
        raise NotImplementedError("Relation is abstract")

class ManyToOneRelation(Relation) :
    def __init__(self, a, b) :
        """There can only be one instance of R(a, X) for any X."""
        self.args = [a, b]
    @staticmethod
    def setup_table() :
        return [dict(), []]
    def add_relation(self, data) :
        a, b = self.args
        rels,bounded = data
        if a in bounded :
            raise Exception("Already in a "+type(self).__name__+" many-to-one relation", a)
        bounded.append(a)
        rels[a] = b
    def remove_relation(self, data) :
        """b doesn't matter in a many-to-one relation"""
        a, b = self.args
        if type(b) is not VarPattern :
            raise Exception("Many-to-one relation requires b to be variable for removal", b)
        rels,bounded = data
        if a in bounded :
            bounded.remove(a)
            del rels[a]
    def query_relation(self, data) :
        rels,bounded = data
        out = []
        for a,b in rels.iteritems() :
            try :
                out.append(self.match(type(self)(a,b)))
            except NoMatchException :
                pass
        return out
    @classmethod
    def path_to(r, data, a, b) :
        rels, bounded = data
        out = [a]
        while a != b :
            if not rels.has_key(a) :
                return None
            a = rels[a]
            out.append(a)
        return out
    @classmethod
    def copy(r, data) :
        return [data[0].copy(), list(data[1])]
    @classmethod
    def dump(r, data) :
        for a,b in data[0].iteritems() :
            print "%s(%r, %r)" % (r.__name__, a, b)

class OneToManyRelation(Relation) :
    def __init__(self, a, b) :
        """There can only be one instance of R(X, b) for any X."""
        self.args = [a, b]
    @staticmethod
    def setup_table() :
        return [dict(), []]
    def add_relation(self, data) :
        a, b = self.args
        rels,bounded = data
        if b in bounded :
            raise Exception("Already in a "+type(self).__name__+" many-to-one relation", b)
        bounded.append(b)
        rels[b] = a
    def remove_relation(self, data) :
        """b doesn't matter in a many-to-one relation"""
        a, b = self.args
        if type(a) is not VarPattern :
            raise Exception("One-to-many relation requires a to be variable for removal", b)
        rels,bounded = data
        if b in bounded :
            bounded.remove(b)
            del rels[b]
    def query_relation(self, data) :
        rels,bounded = data
        out = []
        for b,a in rels.iteritems() :
            try :
                out.append(self.match(type(self)(a,b)))
            except NoMatchException :
                pass
        return out
    @classmethod
    def path_to(r, data, a, b) :
        rels, bounded = data
        out = [b]
        while a != b :
            if not rels.has_key(b) :
                return None
            b = rels[b]
            out.insert(0,b)
        return out
    @classmethod
    def copy(r, data) :
        return [data[0].copy(), list(data[1])]
    @classmethod
    def dump(r, data) :
        for b,a in data[0].iteritems() :
            print "%s(%r, %r)" % (r.__name__, a, b)

class ManyToManyRelation(Relation) :
    def __init__(self, a, b) :
        """There can be any number of R(a, X) and R(X, b).  This
        relation is commutative unless the is_commutative staticmethod
        is overridden.  Commutativity is handled by adding both R(a,b)
        and R(b,a) to the database."""
        self.args = [a, b]
    @staticmethod
    def setup_table() :
        return []
    def add_relation(self, data) :
        data.append(self.args)
        if self.is_commutative() :
            data.append((self.args[1], self.args[0]))
    def remove_relation(self, data) :
        commutative = self.is_commutative()
        i = 0
        while i < len(data) :
            try :
                self.match(type(self)(*data[i]))
                del data[i] # implicit i++
            except NoMatchException :
                i += 1
    def query_relation(self, data) :
        out = []
        for r in data :
            try :
                out.append(self.match(type(self)(*r)))
            except NoMatchException :
                pass
        return out
    @staticmethod
    def is_commutative() :
        return True
    @classmethod
    def path_to(r, data, a, b) :
        """Breadth-first search."""
        paths = {a : [a]}
        seen = []
        to_visit = [a]
        while to_visit :
            visiting = to_visit.pop(0)
            seen.append(visiting)
            neighbors = [res["x"] for res in r(visiting, X).query_relation(data)]
            for n in neighbors :
                if n not in seen :
                    to_visit.append(n)
                    if not paths.has_key(n) :
                        paths[n] = paths[visiting] + [n]
                if b == n :
                    return paths[n]
        return None
    @classmethod
    def copy(r, data) :
        return list(data)
    @classmethod
    def dump(r, data) :
        for rel in data :
            print repr(r(*rel))

class DirectedManyToManyRelation(ManyToManyRelation) :
    @staticmethod
    def is_commutative() :
        return False

class FreeformRelation(Relation) :
    def __init__(self, *args) :
        """There can be any number of arguments.  There are no
        assumptions about this relation."""
        self.args = args
    @staticmethod
    def setup_table() :
        return []
    def add_relation(self, data) :
        data.append(self.args)
    def remove_relation(self, data) :
        i = 0
        while i < len(data) :
            try :
                self.match(type(self)(*data[i]))
                del data[i] # implicit i++
            except NoMatchException :
                i += 1
    def query_relation(self, data) :
        out = []
        for r in data :
            try :
                out.append(self.match(type(self)(*r)))
            except NoMatchException :
                pass
        return out
    @classmethod
    def copy(r, data) :
        return list(data)
    @classmethod
    def dump(r, data) :
        for rel in data :
            print repr(r(*rel))


def __fix_module_name(cls) :
    import inspect
    locals = inspect.currentframe().f_back.f_back.f_locals
    cls.__module__ = locals["__name__"]

def make_many_to_one_relation(name) :
    class _NewManyToOneRelation(ManyToOneRelation) :
        pass
    _NewManyToOneRelation.__name__ = name
    __fix_module_name(_NewManyToOneRelation)
    return _NewManyToOneRelation

def make_one_to_many_relation(name) :
    class _NewOneToManyRelation(OneToManyRelation) :
        pass
    _NewOneToManyRelation.__name__ = name
    __fix_module_name(_NewOneToManyRelation)
    return _NewOneToManyRelation

def make_many_to_many_relation(name) :
    class _NewManyToManyRelation(ManyToManyRelation) :
        pass
    _NewManyToManyRelation.__name__ = name
    __fix_module_name(_NewManyToManyRelation)
    return _NewManyToManyRelation

def make_directed_many_to_many_relation(name) :
    class _NewDirectedManyToManyRelation(ManyToManyRelation) :
        @staticmethod
        def is_commutative() :
            return False
    _NewDirectedManyToManyRelation.__name__ = name
    __fix_module_name(_NewDirectedManyToManyRelation)
    return _NewDirectedManyToManyRelation

def make_freeform_relation(numargs, name) :
    class _NewFreeformRelation(FreeformRelation) :
        def __init__(self, *args) :
            if len(args) != numargs :
                raise Exception("Relation "+name+" requires "+str(numargs)+" arguments.")
            self.args = args
    _NewFreeformRelation.__name__ = name
    __fix_module_name(_NewFreeformRelation)
    return _NewFreeformRelation
