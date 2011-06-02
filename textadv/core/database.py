# database.py
#
# a database system with pattern-based querying
#
# What's here:
# Classes: DictionaryTable, RelationTable, Database

import patterns

class Table(object) :
    def lookup(self, pattern, data=None, res=None) :
        """Returns a list of results by matching against pattern.  If
        res is set, then the match data is first put through res, and
        the results of res are accumulated instead.  The data argument
        is passed on to match."""
        raise NotImplementedError("Abstract base class.")
    def update(self, pattern, newval) :
        raise NotImplementedError("Abstract base class.")
    def insert(self, pattern, val=None) :
        raise NotImplementedError("Abstract base class.")
    def delete(self, pattern, data=None) :
        raise NotImplementedError("Abstract base class.")
    def has_pattern(self, pattern, data=None) :
        """Like has_key for dictionaries."""
        return len(self.lookup(pattern, data=None)) > 0

class DictionaryTable(Table) :
    def __init__(self, myDict=None) :
        if myDict == None :
            self.myDict = dict()
        else :
            self.myDict = myDict
    def lookup(self, pattern, data=None, res=None) :
        """Returns (k,v) tuples for results."""
        if type(pattern) == str :
            if self.myDict.has_key(pattern) :
                if res == None :
                    return [(pattern, self.myDict[pattern])]
                else :
                    return [res(key=pattern, value=self.myDict[pattern])]
            else :
                return []
        else :
            out = []
            for key,value in self.myDict.iteritems() :
                try :
                    matches = pattern.match(key, data=data)
                    if res==None :
                        out.append((key,value))
                    else :
                        out.append(res(key=key, value=value))
                except patterns.NoMatchException :
                    pass
            return out
    def has_pattern(self, pattern, data=None) :
        if type(pattern) == str :
            return self.myDict.has_key(pattern)
        else :
            for key,value in self.MyDict.iteritems() :
                try :
                    pattern.match(key, data=data)
                    return True
                except patterns.NoMatchException :
                    pass
            return False
    def update(self, pattern, newval) :
        if type(pattern) == str :
            self.myDict[pattern] = newval
        else :
            for key,value in self.myDict.iteritems() :
                try :
                    pattern.match(key)
                    self.myDict[key] = newval
                except patterns.NoMatchException :
                    pass
    def insert(self, pattern, val) :
        self.myDict[pattern] = val
    def delete(self, pattern) :
        if type(pattern) == str :
            del self.myDict[pattern]
        else :
            for key in self.myDict.iterkeys() :
                try :
                    pattern.match(key)
                    del self.myDict[key]
                except patterns.NoMatchException :
                    pass
    def __repr__(self) :
        return "<DictionaryTable %r>" % self.myDict

class RelationTable(Table) :
    def __init__(self) :
        self.items = []
    def lookup(self, pattern, data=None, res=None) :
        out = []
        for item in self.items :
            try :
                matches = pattern.match(item, data=data)
                if res == None :
                    out.append(item)
                else :
                    out.append(res(**matches))
            except patterns.NoMatchException :
                pass
        return out
    def update(self, pattern, newval) :
        raise NotImplementedError("RelationTable has no values.")
    def insert(self, pattern, val=None) :
        self.items.append(pattern)
    def delete(self, pattern, data=None) :
        newitems = []
        for item in self.items :
            try :
                pattern.match(item, data=data)
            except patterns.NoMatchException :
                newitems.append(item)
        self.items = newitems
    def __repr__(self) :
        return "<RelationTable %r>" % self.items

class Database(object) :
    def __init__(self) :
        self.tables = dict()
    def add_table(self, tablename, table) :
        self.tables[tablename] = table
    def __getitem__(self, tablename) :
        return self.tables[tablename]
    def __repr__(self) :
        return "<Database %r>" % self.tables

###
### Tests
###

import unittest

class TestDatabase(unittest.TestCase) :
    from patterns import PVar, BasicPattern, PPred
    
    class Actor(BasicPattern) :
        def __init__(self, actor) :
            self.args = [actor]
    class Room(BasicPattern) :
        def __init__(self, room) :
            self.args = [room]
    class In(BasicPattern) :
        def __init__(self, actor, place) :
            self.args = [actor, place]

    def test_dictionary_table(self) :
        table = DictionaryTable()
        table.insert("hi", 2)
        table.insert("there",3)
        self.assertEqual(table.lookup("hi"), [("hi", 2)])
        table.update("hi", 3)
        self.assertEqual(table.lookup("hi"), [("hi", 3)])
        table.delete("hi")
        self.assertEqual(table.lookup("hi"), [])

    def test_relation_table(self) :
        table = RelationTable()
        table.insert(self.In(self.Actor("kyle"), self.Room("41")))
        res = table.lookup(self.In(self.PVar("x"), self.Room("41")))
        self.assertEqual(repr(res), "[<In <Actor 'kyle'> <Room '41'>>]")
        
        table.delete(self.In(self.PVar("x"), self.PVar("y")))
        res = table.lookup(self.PVar("x"))
        self.assertEqual(res, [])

    def test_database(self) :
        db = Database()
        db.add_table("objects", DictionaryTable())
        db.add_table("relations", RelationTable())
        
        def object_prop(obj, prop) :
            return db["objects"].lookup(obj)[0][1].get(prop, None)
        
        db["objects"].insert("kyle", {"type":"Actor", "name":"Kyle"})
        db["objects"].insert("ball", {"type":"Object", "name":"red ball"})
        db["objects"].insert("41", {"type":"Room", "name":"41"})
        db["relations"].insert(self.In("kyle", "41"))
        db["relations"].insert(self.In("ball", "41"))
        
        x = self.PVar("x")

        def whats_in_room(room, type=None) :
            def get_x(x) :
                return x
            inroom = self.In(x, room)
            if type is not None :
                def needType(x) :
                    return object_prop(x, "type") == type
                return db["relations"].lookup(self.PPred(inroom, needType), res=get_x)
            else :
                return db["relations"].lookup(inroom, res=get_x)

        objs = whats_in_room("41")
        self.assertItemsEqual(objs, ["kyle", "ball"])

        actors = whats_in_room("41", "Actor")
        self.assertEqual(actors, ["kyle"])

if __name__=="__main__" :
    unittest.main(verbosity=2)
