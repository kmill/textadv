# basicobjects.py
#
# all objects in the basic library for a game

from textadv.core.patterns import PVar, PPred
from textadv.core.world import WObject, addproperty, obj_to_id
from textadv.gamesystem.relations import *
from textadv.gamesystem.basicpatterns import x, y, z, get_x, get_y, get_z
from textadv.gamesystem.utilities import *

class BObject(WObject) :
    def setup(self, name, description) :
        self["name"] = name
        self["description"] = description
        self["inhibit_article"] = False # inhibits putting "the" or "a" in front
        self["reported"] = True
        self["examined"] = False
        self["subject_pronoun"] = "it"
        self["object_pronoun"] = "it"
        self["possessive"] = "its"
        # Property "reference_objects" refers to whether get_objects
        # will report subobjects.
        self["reference_self"] = True
        self["reference_objects"] = True
        self["takeable"] = True
        self["no_take_msg"] = "That can't be taken."
    @addproperty()
    def words(self) :
        """This property should return a list of words which a player
        may use to describe the object.  Distinguished words for this
        object (such as the noun) should be prefixed by an at-sign
        (@).  Each element of the list must be a word (no spaces).  By
        default, the last word of the name property is assumed to be
        the noun."""
        words = self["name"].split()
        words[-1] = "@"+words[-1]
        return words
    @addproperty()
    def printed_name(self) :
        return self["name"]
    @addproperty()
    def indefinite_name(self) :
        """Implements the default behavior for indefinite_name by
        choosing 'a' or 'an' by seeing if the name starts with a
        vowel."""
        printed_name = self["printed_name"]
        if self["inhibit_article"] :
            return printed_name
        elif printed_name[0] in "aeiou" :
            return "an " + printed_name
        else :
            return "a " + printed_name
    @addproperty()
    def definite_name(self) :
        """Implements the default behavior for definite_name by adding
        the definite article."""
        if self["inhibit_article"] :
            return self["printed_name"]
        else :
            return "the " + self["printed_name"]
    def get_location(self) :
        return self.s_R_x(In)[0]
    def set_examined(self) :
        """Sets the examined flag to True."""
        self["examined"] = True
    def move_to(self, new_loc, revoke=True) :
        """Revokes all Has and In relations, and then adds In(self.id,
        new_loc)."""
        new_loc = obj_to_id(new_loc)
        if revoke :
            self.world.delete("relations", Has(x, self))
            self.world.delete("relations", In(self, x))
        self.world.db["relations"].insert(In(self.id, new_loc))
    def give_to(self, new_owner) :
        """Revokes all Has and In relations, and then adds
        Has(new_owner, self.id)."""
        new_owner = obj_to_id(new_owner)
        self.world.delete("relations", Has(x, self))
        self.world.delete("relations", In(self, x))
        self.world.db["relations"].insert(Has(new_owner, self.id))
    def get_objects(self) :
        """Returns a list of all objects which an actor could
        conceivably be referencing (including the object itself)."""
        out = [self] if self["reference_self"] else []
        if self["reference_objects"] :
            objs = self.world.lookup("relations", In(BObject(x), self), res=get_x)
            for o in objs :
                out.extend(o.get_objects())
        return out
    def get_contents(self) :
        """Returns all objects which are immediately in the object."""
        return self.x_R_s(In)
    @addproperty()
    def contents(self) :
        """Do not override this property!  It runs get_contents so
        that the string language works with [get obj contents]."""
        return self.get_contents()
    def s_R_x(self, relation, obx=None) :
        """Returns all objects x such that relation(self.id, x.id).
        If obx is set, then instead returns whether such a relation
        exists, with obx in place of x."""
        if obx == None :
            return self.world.lookup("relations", relation(self, BObject(x)), res=get_x)
        else :
            return len(self.world.lookup("relations", relation(self, obx))) > 0
    def x_R_s(self, relation, obx=None) :
        """Returns all objects x such that relation(x.id, self.id).
        If obx is set, then instead returns whether such a relation
        exists, with obx in place of x."""
        if obx == None :
            return self.world.lookup("relations", relation(BObject(x), self), res=get_x)
        else :
            return len(self.world.lookup("relations", relation(obx, self))) > 0
    def transitive_in(self, container) :
        """Sees if self is contained in container, even if self is
        contained in something which is contained in the container,
        etc.  Assumes each thing is contained in exactly one thing at
        most.  If there are loops, then this will not terminate."""
        containers = self.s_R_x(In)
        if containers :
            if containers[0] == container :
                return True
            else :
                return containers[0].transitive_in(container)
        else :
            return False
    def wants_to(self, action, context) :
        """Returns true or false whether this particular object wants
        to do the action. Returns false actually, because objects
        don't want to do actions."""
        msg = str_with_objs("[cap [get $self subject_pronoun]] doesn't seem interested.",
                            self=self)
        context.write_line(msg)
        return False

class Scenery(BObject) :
    """An object which is there, but neither takeable nor reported.
    Adds flavor to the game."""
    def setup(self, name, desc) :
        BObject.setup(self, name, desc)
        self["takeable"] = False
        self["reported"] = False

class Enterable(BObject) :
    """Needs to have the "enterable" property, as well as the
    "no_enter_msg" property."""
    def setup(self, name=None, desc=None) :
        if name is not None :
            BOBject.setup(self, name, desc)
        self["enterable"] = True
        self["no_enter_msg"] = "{Bob|cap} can't enter that."

class Openable(BObject) :
    """Represents things which can be opened and closed."""
    def setup(self, name=None, desc=None) :
        if name is not None :
            BObject.setup(self, name, desc)
        self["open"] = False
        self["openable"] = True
        self["no_open_msg"] = "That cannot be opened."
        self["no_close_msg"] = "That cannot be closed."
        self["already_open_msg"] = "That is already open."
        self["already_closed_msg"] = "That is already closed."
    @addproperty()
    def is_open_msg(self) :
        if self["open"] :
            return "open"
        else :
            return "closed"

class Lockable(BObject) :
    """Needs to have the "locked" property.  This class handles
    unlocking with a key."""
    def setup(self) :
        self["lockable"] = True
        self["no_lock_msg"] = "That cannot be locked."
        self["no_unlock_msg"] = "That cannot be unlocked."
        self["already_locked_msg"] = "That is already locked."
        self["already_unlocked_msg"] = "That is already unlocked."
        self["lock_needs_key_msg"] = "That needs a key to lock."
        self["unlock_needs_key_msg"] = "That needs a key to unlock."
        self["wrong_key_msg"] = "The key doesn't fit."
    def unlockable_with(self, obj) :
        obj = obj_to_id(obj)
        objs = []
        try : objs = self["keys"]
        except KeyError : pass
        objs = objs+[obj]
        self["keys"] = objs
    @addproperty()
    def is_locked_msg(self) :
        if self["locked"] :
            return "locked"
        else :
            return "unlocked"

class Door(Enterable, Openable, Lockable) :
    def setup(self, name, description) :
        BObject.setup(self, name, description)
        Openable.setup(self)
        Lockable.setup(self)
        self["reported"] = False
        self["takeable"] = False
        self["no_enter_msg"] = "The door is closed."
        self["open"] = False
        self["locked"] = False
        self["lockable"] = False
        self["no_open_msg"] = "The door is locked."
        self["no_close_msg"] = "The door is locked."
        self["already_open_msg"] = "The door is already open."
        self["already_closed_msg"] = "The door is already closed."
    def add_exit_for(self, side, direction) :
        side = obj_to_id(side)
        self.move_to(side, revoke=False)
        self.world.db["relations"].insert(Exit(side, direction, self.id))
    def other_side(self, actor) :
        actor = self.world.get_obj(actor)
        pattern = PPred(In(self, Room(x)), lambda x: actor.get_location() != x)
        return self.world.lookup("relations", pattern, res=get_x)[0]
    @addproperty()
    def enterable(self) :
        return self["open"]
    @addproperty()
    def openable(self) :
        return not self["locked"]

class Room(Enterable) :
    def setup(self, name, description) :
        BObject.setup(self, name, description)
        self["inhibit_article"] = True
        self["visited"] = False
        self["takeable"] = False
        self["default_no_go_msg"] = "You can't go that way."
        self["no_go_msgs"] = dict()
        self["enterable"] = True
        self["reference_self"] = False
    def make_description(self) :
        out = self["printed_name"] + "\n\n"
        out += self["description"].strip()
        pattern = In(BObject(x), self)
        objs = self.world.lookup("relations", pattern, res=get_x)
        objs = [o for o in objs if o["reported"]]
        if len(objs) > 0 :
            out += "\n\nYou see "
            out += serial_comma([self.world.get_obj(o)["indefinite_name"] for o in objs])
            out += "."
        return out
    def connect(self, room2, direction, connect_inverse=True) :
        room2 = obj_to_id(room2)
        self.world.db["relations"].delete(Exit(self.id, direction, x))
        self.world.db["relations"].insert(Exit(self.id, direction, room2))
        if connect_inverse :
            invdirection = inverse_direction(direction)
            self.world.db["relations"].delete(Exit(room2, invdirection, x))
            self.world.db["relations"].insert(Exit(room2, invdirection, self.id))
    def get_exit(self, direction) :
        """Returns None if no exit in that direction."""
        exit = self.world.lookup("relations", Exit(self.id, direction, x), res=get_x)
        if exit :
            return self.world.get_obj(exit[0])
        else : return None
    def no_go_message(self, direction) :
        """Called to get the reason why there is no exit in a
        particular direction."""
        if self["no_go_msgs"].has_key(direction) :
            return self["no_go_msgs"][direction]
        else :
            return self["default_no_go_msg"]
    def visit(self) :
        self["visited"] = True
    
    # handling regions:
    def get_objects(self) :
        """Returns a list of all objects which an actor could
        conceivably be referencing (including the room)."""
        out = [self] if self["reference_self"] else []
        if self["reference_objects"] :
            objs = self.world.lookup("relations", In(BObject(x), self), res=get_x)
            for o in objs :
                out.extend(o.get_objects())
        regions = self.world.lookup("relations", In(self, Region(x)), res=get_x)
        for r in regions :
            out.extend(r.get_objects())
        return out
    def get_contents(self) :
        """Returns all objects which are immediately in the room (and
        objects which are accessible)."""
        out = self.x_R_s(In)
        regions = self.world.lookup("relations", In(self, Region(x)), res=get_x)
        for r in regions :
            out.extend(r.get_objects())
        return out

class Region(BObject) :
    """Rooms can be placed into a region which gives extra visible
    objects (like the sky)."""
    def setup(self, name) :
        BObject.setup(self, name, "NO DESCRIPTION")
        self["takeable"] = False # you shouldn't be able to see this, anyway
    def add_rooms(self, rooms) :
        for room in rooms :
            self.world.db["relations"].insert(In(obj_to_id(room), self.id))
    def get_objects(self) :
        """Returns a list of all objects which an actor could
        conceivably be referencing within this region.  Regions can
        also be in regions."""
        out = []
        objs = self.world.lookup("relations", In(BObject(x), self), res=get_x)
        for o in objs :
            if not isinstance(o, Room) and not isinstance(o, Region) :
                out.extend(o.get_objects())
        regions = self.world.lookup("relations", In(self, Region(x)), res=get_x)
        for r in regions :
            out.extend(r.get_objects())
        return out

class Actor(BObject) :
    def setup(self, name, description) :
        BObject.setup(self, name, description)
        self["takeable"] = False
        self["subject_pronoun"] = "they" # default is gender-neutral
        self["object_pronoun"] = "them" # default is gender-neutral
        self["possessive"] = "theirs"
        self["subject_pronoun_if_me"] = "you" # default is 2nd person
        self["object_pronoun_if_me"] = "you"
        self["possessive_if_me"] = "yours"
    @addproperty()
    def definite_name(self) :
        return self["printed_name"]
    @addproperty()
    def indefinite_name(self) :
        return self["printed_name"]
    def make_inventory(self) :
        out = "{Bob|cap} {has}"
        objs = self.s_R_x(Has)
        objs = [o for o in objs if o["reported"]]
        if len(objs) == 0 :
            return out+" nothing."
        else :
            out += ":"
            for o in objs :
                out += "<br>&nbsp;&nbsp;&nbsp;"+o["indefinite_name"]
            return out
    def set_gender(self, gender) :
        if gender == "male" :
            self["subject_pronoun"] = "he"
            self["object_pronoun"] = "him"
            self["possessive"] = "his"
        elif gender == "female" :
            self["subject_pronoun"] = "she"
            self["object_pronoun"] = "her"
            self["possessive"] = "her"
        else :
            raise Exception("Unimplemented gender "+repr(gender))
    def get_objects(self) :
        objs = self.world.lookup("relations", Has(self, BObject(x)), res=get_x)
        out = [self]
        for o in objs :
            out.extend(o.get_objects())
        return out
    def obj_accessible(self, obj) :
        obj = self.world.get_obj(obj)
        return obj in self.get_location().get_objects()
    def wants_to(self, action, context) :
        """Returns true or false whether this particular actor wants
        to do the action. Extend by modifying wants_to_if_me and
        wants_to_if_command."""
        if context.actor == action.get_actor() :
            return self.wants_to_if_me(action, context)
        else :
            return self.wants_to_if_command(action, context)
    def wants_to_if_me(self, action, context) :
        """Returns true or false depending on whether the actor wants
        to do the action, assuming the action was done within the
        actor's context (for instance, the player character).  This
        method should write messages."""
        return True
    def wants_to_if_command(self, action, context) :
        """Returns true or false depending on whether the actor wants
        to do the action, assuming the actor is not the actor of the
        current context (for instance, an NPC). This method should
        write messages."""
        msg = str_with_objs("[cap [get $self subject_pronoun]] doesn't seem interested.",
                            self=self)
        context.write_line(msg)
        return False
    def ask_about(self, text, context) :
        """This is called when an actor is asked about something.  The
        something is text."""
        msg = str_with_objs("[cap [get $self subject_pronoun]] doesn't seem interested.",
                            self=self)
        context.write_line(msg)

class Readable(BObject) :
    """Needs to have the "read_msg" property. If "read_msg" is not
    set, it defaults to the description."""
    @addproperty()
    def read_msg(self) :
        return self["description"]

class Device(BObject) :
    """Represents a device which can be switched on and off."""
    def setup(self, name, desc) :
        BObject.setup(self, name, desc)
        self["switched_on"] = False
        self["switch_on_msg"] = "{Bob|cap} {switches} it on."
        self["no_switch_on_msg"] = "That is already switched on."
        self["switch_off_msg"] = "{Bob|cap} {switches} it off."
        self["no_switch_off_msg"] = "That is already switched off."
    @addproperty()
    def is_switched_msg(self) :
        return "on" if self["switched_on"] else "off"

class Container(BObject) :
    """Represents an object into which objects can be put."""
    def setup(self, name, desc) :
        BObject.setup(self, name, desc)

class NonGameObject(BObject) :
    """Lets there be global functions which are accessible from the
    string language as properties. These objects are not referenceable
    by the parser."""
    def setup(self) :
        pass
    @addproperty()
    def words(self) :
        """Prevents being used by the parser for anything."""
        return []
