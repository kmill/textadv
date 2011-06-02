# relations.py
#
# some basic relations between objects
#
# for the "relations" table in the world database.  Relations are
# BasicPatterns so that they can be searched for by pattern matching
# in the relation table.

from textadv.core.patterns import BasicPattern

class Has(BasicPattern) :
    """As in "owner Has obj"."""
    def __init__(self, owner, obj) :
        self.args = [owner, obj]
class In(BasicPattern) :
    """As in "obj is In container"."""
    def __init__(self, obj, container) :
        self.args = [obj, container]

class Exit(BasicPattern) :
    """For connecting rooms."""
    def __init__(self, room_start, direction, room_end) :
        self.args = [room_start, direction, room_end]
