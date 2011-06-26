# relations.py
#
# Defining relations between objects
#
# provides: make_many_to_one_relation, make_one_to_many_relation

from textadv.core.patterns import BasicPattern, VarPattern, NoMatchException

class Relation(BasicPattern) :
    def add_relation(self, table) :
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
    def dump(r, data) :
        for a,b in data[0].iteritems() :
            print "%s(%r, %r)" % (r.__name__, a, b)

RELATION_COUNTER = 0

def make_many_to_one_relation(name=None) :
    if name == None :
        global RELATION_COUNTER
        RELATION_COUNTER += 1
        name = "_NewManyToOneRelation<%r>" % RELATION_COUNTER
    class _NewManyToOneRelation(ManyToOneRelation) :
        pass
    _NewManyToOneRelation.__name__ = name
    return _NewManyToOneRelation

def make_one_to_many_relation(name=None) :
    if name == None :
        global RELATION_COUNTER
        RELATION_COUNTER += 1
        name = "_NewOneToManyRelation<%r>" % RELATION_COUNTER
    class _NewOneToManyRelation(OneToManyRelation) :
        pass
    _NewOneToManyRelation.__name__ = name
    return _NewOneToManyRelation
