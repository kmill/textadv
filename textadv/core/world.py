# world.py
#
# a representation of the game world with support for querying its
# state.

from database import DictionaryTable, RelationTable, Database
from patterns import AbstractPattern, NoMatchException

import inspect

###
### Decorator for WObject
###
def addproperty(name=None) :
    """Adds a property function to a WObject class.  If the argument
    is omitted, the name of the property is assumed to be f.__name__.
    The property name must be a string if it is supplied."""
    class_locals = inspect.currentframe().f_back.f_locals
    if "prop_handlers" not in class_locals :
        class_locals["prop_handlers"] = dict()
    prop_handlers = inspect.currentframe().f_back.f_locals["prop_handlers"]
    def _addproperty(f) :
        thename = name
        if type(name) is not str :
            thename = f.__name__
        prop_handlers[thename] = f
        return f
    return _addproperty

###
### Helpful utility functions
###

def obj_to_id(obj) :
    """Gives the id of an object if it isn't already an id."""
    if type(obj) == str :
        return obj
    else :
        return obj.id

###
### Main class for world objects
###
class WObject(AbstractPattern) :
    """Base class for world objects.  Ties into a world object so that
    all references to same object will have the same data.  This
    method should not be overridden."""
    def __init__(self, id) :
        """This object can be instantiated as a pattern, also.  But,
        without a world, most methods will not work."""
        self.id = id
        # the world should be set separately by World in new_obj
        #self.world = world
    def set_world(self, world) :
        self.world = world
        return self
    def setup(self) :
        """This method sets up an object for the first time.  The
        __init__ method should not do setup because it is more of an
        object accessor.  Also, setup /should not/ modify local variables"""
        pass
    def _get_data(self) :
        return self.world.db["objects"].lookup(self.id)[0][1] # [1] for get v
    def get_prop(self, prop) :
        """Basically, get_prop gets a property from the object.  If
        it's set in the data of the object, then that wins.
        Otherwise, it tries to find a prop_handler which is then
        called on self.  This happens by looking through the
        superclasses for a prop_handler."""
        data = self._get_data()
        if prop in data :
            return data[prop]
        else :
            try :
                return self._get_prop(type(self), prop)
            except KeyError as err :
                #print "get_prop error because of object "+repr(self)
                raise err
    def _get_prop(self, cls, prop) :
        if cls.__dict__.has_key("prop_handlers") and prop in cls.prop_handlers :
            return cls.prop_handlers[prop](self)
        else :
            for sup in cls.mro()[1:] : # skip self!
                if sup is not AbstractPattern :
                    try : return self._get_prop(sup, prop)
                    except KeyError as ke :
                        if ke.args[0] == prop :
                            pass
                        else :
                            raise
            raise KeyError(prop)
    def __getitem__(self, prop) :
        return self.get_prop(prop)
    def set_prop(self, prop, value) :
        self._get_data()[prop] = value
    def __setitem__(self, prop, value) :
        self.set_prop(prop, value)
    def del_prop(self, prop) :
        del self._get_data()[prop]
    def match(self, input, matches=None, data=None) :
        """The WObject class implements match so that they can enter
        patterns.  The matcher is almost equivalent to just putting in
        the id in place of the object (it also checks types).  Note
        that this matches for subclasses of the type, too, unless the
        id is actually a string."""
        if matches == None : matches = dict()
        if type(input) == str :
            objs = data["world"].lookup_objs(input, data=data)
            if len(objs) > 0 :
                input = objs[0]
            else :
                raise NoMatchException(self, input)
            #print self, input
        if isinstance(input, type(self)) :
            if type(self.id) == str :
                if self.id == input.id :
                    return matches
                else :
                    raise NoMatchException(self, input.id)
            else :
                matches = self.id.match(input, matches=matches, data=data)
                return matches
        elif type(self) == type(input) and self.id == input.id :
            return matches
        else :
            raise NoMatchException(self, input)
    def expand_pattern(self, replacements) :
        """Expanding a WObject just turns it into a string
        (hopefully).  It actually just returns the id, expanded if
        needed."""
        if isinstance(self.id, AbstractPattern) :
            res = self.id.expand_pattern(replacements)
            if isinstance(res, WObject) :
                if type(res) == type(self) :
                    return res.id
                else :
                    raise Exception("Can't expand WObject pattern against wrong type.")
            else :
                return res
        else :
            return self.id
    def __eq__(self, other) :
        if isinstance(other, WObject) :
            return self.id == other.id
        else :
            return self.id == other
    def __ne__(self, other) :
        return not self.__eq__(other)
    def __str__(self) :
        """This is so we can write "objid" == obj as well."""
        return self.id
    def __repr__(self) :
        return "<%s %r>" % (self.__class__.__name__, self.id)

class World(object) :
    """This is a representation of the entire game state along with
    accessors of the game state as objects.  The stored data must all
    be serializable, because this class is ideally serializable (that
    way the game state can be copied or saved)."""
    def __init__(self) :
        self.db = Database()
        self.db.add_table("objects", DictionaryTable()) # game objects
        self.db.add_table("relations", RelationTable()) # relations between objects
        self.db.add_table("global", DictionaryTable()) # global variables
    def get_obj(self, id) :
        """Returns the object corresponding to id.  If it's not a
        string, we just assume it's already the right object."""
        if type(id) == str :
            try :
                return self.db["objects"].lookup(id)[0][1]["type"](id).set_world(self)
            except IndexError :
                raise KeyError(id)
        else :
            return id
    def __getitem__(self, id) :
        """By default, we assume that we want to get an object when
        doing world['id']."""
        return self.get_obj(id)
    def new_obj(self, id, objtype, *args, **kargs) :
        if self.db["objects"].has_pattern(id) :
            raise Exception("Already defined", id)
        # Insert the object data into the object table, with type data
        # for reconstitution in get_obj
        self.db["objects"].insert(id, {"type" : objtype})
        # Then create an object representation
        o = objtype(id).set_world(self)
        # And set it up for the first time
        o.setup(*args, **kargs)
        return o
    def lookup(self, table, pattern, data=None, res=None) :
        """Returns (k,v) pairs."""
        if data == None :
            data = {"world" : self}
        else :
            data = data.copy()
            data["world"] = self
        return self.db[table].lookup(pattern, data=data, res=res)
    def lookup_objs(self, pattern, data=None) :
        """Returns actual objects which match pattern."""
        return self.lookup("objects", pattern, data, res=lambda key,value : self.get_obj(key))
    def delete(self, table, pattern, data=None) :
        if data == None :
            data = {"world" : self}
        else :
            data = data.copy()
            data["world"] = self
        return self.db[table].delete(pattern, data=data)
    def glob_var(self, id) :
        return self.db["global"].lookup(id)[0][1]
    def set_glob_var(self, id, val) :
        return self.db["global"].update(id, val)
    def serialize(self) :
        import pickle
        return pickle.dumps(self)
    @staticmethod
    def deserialize(serialized) :
        import pickle
        return pickle.loads(serialized)
    def copy(self) :
        return self.deserialize(self.serialize())

    def __repr__(self) :
        return "<World db=%r>" % self.db


###
### Tests
###

import unittest

class TestWorld(unittest.TestCase) :
    def test_world(self) :
        world = World()
        ball = world.new_obj("ball", WObject)
        self.assertEquals(ball["type"], WObject)
        ball["name"] = "red ball"
        self.assertEquals(ball["name"], "red ball")
        # try reconstitution
        ball2 = world["ball"]
        self.assertEquals(ball2["name"], "red ball")

    def test_pickleable(self) :
        world = World()
        ball = world.new_obj("ball", WObject)
        ball["name"] = "red ball"
        s = world.serialize()
        w2 = World.deserialize(s)
        ball2 = w2["ball"]
        self.assertEquals(ball2["name"], "red ball")
        w3 = world.copy()
        self.assertEquals(w3["ball"]["name"], "red ball")

    def test_world_pattern(self) :
        class Room(WObject) :
            pass
        
        world = World()
        room_41 = world.new_obj("room_41", Room)
        
        pattern = Room("room_41")
        matches = world.lookup("objects", pattern, res=lambda key,value : key)
        self.assertEquals(matches, ["room_41"])
        
        self.assertEquals(repr(world.lookup_objs(pattern)), "[<Room 'room_41'>]")

    def test_object_eq(self) :
        class Room(WObject) :
            pass
        
        world = World()
        room_41 = world.new_obj("room_41", Room)
        self.assertTrue(room_41 == room_41)
        self.assertTrue(room_41 == "room_41")
        self.assertTrue("room_41" == room_41)
        
if __name__=="__main__" :
    unittest.main(verbosity=2)
