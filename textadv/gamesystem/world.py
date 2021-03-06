# world.py
# The definition of the main world database.  Properties are what can be used to query the properties database

from textadv.core.patterns import BasicPattern
from textadv.core.rulesystem import ActivityTable, PropertyTable, ActivityHelperObject


class Property(BasicPattern) :
    """This is the main property class.  The numargs attribute must be
    created."""
    def __init__(self, *args) :
        if len(args) != self.numargs :
            raise Exception("Property requires exactly "+str(self.numargs)+" arguments.")
        self.args = args

class World(object) :
    def __init__(self) :
        self.properties = PropertyTable()
        self.property_types = dict() # name -> Property
        self.inv_property_types = dict() # Property -> name
        self.modified_properties = dict()
        self.game_defined = False
        self.relations = dict()
        self.relation_handlers = []
        self.name_to_relation = dict()
        self._activities = dict()
        self.activity = ActivityHelperObject(self)
    def set_game_defined(self) :
        """Set when it's time to close off arbitrary property
        definitions."""
        self.game_defined = True
    def __setitem__(self, item, value) :
        if self.game_defined :
            self.modified_properties[item] = value
        else :
            self.properties[item] = value
    def __getitem__(self, item) :
        if self.modified_properties.has_key(item) :
            return self.modified_properties[item]
        return self.properties.get_property(item, {"world" : self})
    def handler(self, item) :
        return self.properties.handler(item)

    def _make_property(self, numargs, name) :
        class _NewProperty(BasicPattern) :
            def __init__(self, *args) :
                if len(args) != numargs :
                    raise Exception("Property requires exactly "+str(numargs)+" arguments.")
                self.args = args
        _NewProperty.__name__ = name
        return self.define_property(_NewProperty)
    def define_property(self, prop) :
        if self.property_types.has_key(prop.__name__) :
            raise Exception("Property with name %r already defined" % prop.__name__)
        self.property_types[prop.__name__] = prop
        self.inv_property_types[prop] = prop.__name__
        return prop
    def set_property(self, name, *args, **kwargs) :
        """This is __setitem__ but by the registered name of the property."""
        self[self.property_types[name](*args)] = kwargs["value"]
    def get_property(self, name, *args) :
        """This is __getitem__ but by name."""
        return self[self.property_types[name](*args)]

    def add_relation(self, relation) :
        relation.add_relation(self.relations[type(relation)])
    def remove_relation(self, relation) :
        relation.remove_relation(self.relations[type(relation)])
    def define_relation(self, r) :
        if self.game_defined :
            raise Exception("Can't define new relation when game is defined.")
        self.relation_handlers.append(r)
        self.relations[r] = r.setup_table()
        self.name_to_relation[r.__name__] = r
        return r
    def query_relation(self, relation, var=None) :
        res = relation.query_relation(self.relations[type(relation)])
        if var is None :
            return res
        else :
            return [r[var.varName] for r in res]
    def r_path_to(self, r, a, b, **kwargs) :
        return r.path_to(self.relations[r], a, b, **kwargs)
    def get_relation(self, name) :
        return self.name_to_relation[name]

    def define_activity(self, name, **kwargs) :
        self._activities[name] = ActivityTable(**kwargs)
    def to(self, name, **kwargs) :
        if self.game_defined :
            raise Exception("Can't add new actions when game is defined.")
        def _to(f) :
            if not self._activities.has_key(name) :
                self._activities[name] = ActivityTable()
            self._activities[name].add_handler(f, **kwargs)
            return f
        return _to
    def call_activity(self, name, *args, **kwargs) :
        data = {"world" : self}
        data.update(kwargs)
        return self._activities[name].notify(args, data)
    def activity_table(self, name) :
        """Gets the action table of the given name."""
        return self._activities[name]

    def copy(self) :
        """Makes a copy of the world which behaves the same as the
        present one, but is disconnected.  However, the values of
        modified_properties are not copied but referenced."""
        newworld = World()
        newworld.properties = self.properties.copy()
        newworld.property_types = self.property_types.copy()
        newworld.inv_property_types = self.inv_property_types.copy() # Property -> name
        for k,v in self.modified_properties.iteritems() :
            newworld.modified_properties[k] = v
        newworld.game_defined = self.game_defined
        for r,data in self.relations.iteritems() :
            newworld.relations[r] = r.copy(data)
        newworld.relation_handlers = list(self.relation_handlers)
        newworld.name_to_relation = self.name_to_relation.copy()
        for name, table in self._activities.iteritems() :
            newworld._activities[name] = table.copy()
        return newworld
    def serialize(self) :
        import pickle
        mp = []
        for k,v in self.modified_properties.iteritems() :
            mp.append((self.inv_property_types[type(k)], k.args, v))
        return pickle.dumps((mp, self.relations))
    def deserialize(self, data) :
        import pickle
        import copy
        mp, rel = pickle.loads(data)
        newworld = copy.copy(self)
        newworld.modified_properties = dict()
        for name, args, v in mp :
            newworld.modified_properties[self.property_types[name](*args)] = v
        newworld.relations = rel
        return newworld

    def dump(self) :
        print "**Property table:**"
        self.properties.dump()
        print "\n**Modified property table:**"
        for k,v in self.modified_properties.iteritems() :
            print "%r = %r" % (k,v)
        print "\n**Relation tables:**"
        for r in self.relation_handlers :
            print " * For %s *" % r.__name__
            r.dump(self.relations[r])
    def make_documentation(self, escape, heading_level=1) :
        hls = str(heading_level)
        print "<h"+hls+">World</h"+hls+">"
        print "<p>This is the documentation for the game world object.</p>"
        shls = str(heading_level+1)
        print "<h"+shls+">Property table</h"+shls+">"
        self.properties.make_documentation(escape, heading_level=heading_level+2)
        print "<h"+shls+">Relation tables</h"+shls+">"
        sshls = str(heading_level+2)
        for r in self.relation_handlers :
            print "<h"+sshls+">"+escape(r.__name__)+"</h"+sshls+">"
            print "<p><i>"+(escape(r.__doc__) or "(No documentation)")+"</i></p>"
            print "<pre>"
            r.dump(self.relations[r])
            print "</pre>"
        print "<h"+shls+">Activity tables</h"+shls+">"
        for name, table in self._activities.iteritems() :
            print "<h"+sshls+">to "+escape(name)+"</h"+sshls+">"
            table.make_documentation(escape, heading_level=heading_level+3)
