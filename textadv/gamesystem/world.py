# world.py
# The definition of the main world database.  Properties are what can be used to query the properties database

from textadv.core.patterns import BasicPattern
from textadv.core.rulesystem import ActionTable, PropertyTable

class ActionHelperObject(object) :
    def __init__(self, world) :
        self.__world__ = world
    def __getattr__(self, name) :
        def _caller(*args) :
            return self.__world__.call(name, *args)
        return _caller

class World(object) :
    def __init__(self) :
        self.properties = PropertyTable()
        self.relations = dict()
        self.relation_handlers = []
        self._actions = dict()
        self.actions = ActionHelperObject(self)
    def __setitem__(self, item, value) :
        self.properties[item] = value
    def __getitem__(self, item) :
        return self.properties.get_property(item, {"world" : self})
    def handler(self, item) :
        return self.properties.handler(item)

    def add_relation(self, relation) :
        relation.add_relation(self.relations[type(relation)])
    def remove_relation(self, relation) :
        relation.remove_relation(self.relations[type(relation)])
    def define_relation(self, r) :
        self.relation_handlers.append(r)
        self.relations[r] = r.setup_table()
    def query_relation(self, relation, var=None) :
        res = relation.query_relation(self.relations[type(relation)])
        if var is None :
            return res
        else :
            return [r[var.varName] for r in res]
    def r_path_to(self, r, a, b) :
        return r.path_to(self.relations[r], a, b)

    def define_action(self, name, **kwargs) :
        self._actions[name] = ActionTable(**kwargs)
    def to(self, name) :
        def _to(f) :
            if not self._actions.has_key(name) :
                self._actions[name] = ActionTable()
            self._actions[name].add_handler(f)
            return f
        return _to
    def call(self, name, *args) :
        return self._actions[name].notify(args, {"world" : self})

    def dump(self) :
        print "**Property table:**"
        self.properties.dump()
        print "**Relation tables:**"
        for r in self.relation_handlers :
            print " * For %s *" % r.__name__
            r.dump(self.relations[r])


PROPERTY_COUNTER = 0

def make_property(numargs, name=None) :
    if name == None :
        global PROPERTY_COUNTER
        PROPERTY_COUNTER += 1
        name = "_NewProperty<%r>" % PROPERTY_COUNTER
    class _NewProperty(BasicPattern) :
        def __init__(self, *args) :
            if len(args) != numargs :
                raise Exception("Property requires exactly "+str(numargs)+" arguments.")
            self.args = args
    _NewProperty.__name__ = name
    return _NewProperty
