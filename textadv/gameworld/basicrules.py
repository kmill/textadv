# The basic definition of how the world works

from textadv.core.patterns import VarPattern, BasicPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults, NotHandled, AbortAction
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *
from textadv.gamesystem.gamecontexts import actoractions
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.utilities import *
import textadv.gamesystem.parser as parser
from textadv.gamesystem.parser import understand
from textadv.gamesystem.eventsystem import BasicAction, verify, trybefore, before, when, report
from textadv.gamesystem.eventsystem import VeryLogicalOperation, LogicalOperation, IllogicalOperation, IllogicalInaccessible, NonObviousOperation

# The main game world!
world = World()

# A convenience function
def def_obj(name, type) :
    world.add_relation(IsA(name, type))

###
### Global properties
###

Global = world.make_property(1, "Global")

###
### Basic relations
###

# The following three are mutually exclusive relations which have to
# do with position.

@world.define_relation
class Contains(OneToManyRelation) :
    """Contains(x,y) for "x Contains y"."""

@world.define_relation
class Has(OneToManyRelation) :
    """Has(x,y) for "x Has y"."""

@world.define_relation
class PartOf(ManyToOneRelation) :
    """PartOf(x,y) for "x PartOf y"."""

#
# some helper actions to make it easy to use these three
#

# move X to Y (so then Y Contains X)
@world.to("move_to")
def default_move_to(x, y, world) :
    world.remove_relation(Contains(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(Contains(y, x))

# give X to Y (so then Y Has X)
@world.to("give_to")
def default_give_to(x, y, world) :
    world.remove_relation(Contains(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(Has(y, x))

# make X part of Y (so then X PartOf Y)
@world.to("make_part_of")
def default_make_part_of(x, y, world) :
    world.remove_relation(Contains(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(PartOf(x, y))

@world.to("remove_obj")
def default_remove_obj(obj, world) :
    """Effectively removes an object from play by making it have no
    positional location."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(X, x))

Location = world.make_property(1, "Location")
@world.handler(Location(X))
def object_location(x, world) :
    """Gets the location of an object by what currently contains it."""
    locs = world.query_relation(Contains(Y, x), var=Y)
    return locs[0] if locs else None

#
# Kinds and instances
#

@world.define_relation
class KindOf(ManyToOneRelation) :
    """Represents a class-like hierarchy."""

world.add_relation(KindOf("room", "kind"))
world.add_relation(KindOf("thing", "kind"))
world.add_relation(KindOf("door", "thing"))
world.add_relation(KindOf("container", "thing"))
world.add_relation(KindOf("person", "thing"))

@world.register_property
@world.define_relation
class IsA(ManyToOneRelation) :
    """Represents inheriting from a kind.  As a relation, represents a
    direct inheritence.  As a property, represents the transitive IsA
    relation."""

@world.handler(IsA(X,Y))
def property_handler_IsA(x, y, world) :
    """Lets one ask whether a particular object has a kind, searching
    up the KindOf tree."""
    kind = world.query_relation(IsA(x, Z), var=Z)
    if not kind :
        return False
    else :
        return world.r_path_to(KindOf, kind[0], y)

world.define_action("referenceable_things", accumulator=list_append)
@world.to("referenceable_things")
def referenceable_things_Default(world) :
    """Gets all things in the world."""
    objects = world.query_relation(IsA(X, Y), var=X)
    things = [o for o in objects if world[IsA(o, "thing")]]
    return things

#
# connecting rooms together
#

@world.define_relation
class Adjacent(DirectedManyToManyRelation) :
    """Used for searching for paths between rooms."""

@world.define_relation
class Exit(FreeformRelation) :
    """Used to denote an exit from one room to the next.  Exit(room1,
    dir, room2)."""

@world.to("connect_rooms")
def default_connect_rooms(room1, dir, room2, world, reverse=True) :
    world.add_relation(Adjacent(room1, room2))
    world.add_relation(Exit(room1, dir, room2))
    if reverse :
        world.add_relation(Adjacent(room2, room1))
        world.add_relation(Exit(room2, inverse_direction(dir), room1))

#
# Directions
#


parser.define_subparser("direction", "Represents one of the directions one may go.")

def define_direction(direction, synonyms) :
    for synonym in synonyms :
        understand(synonym, direction, dest="direction")

define_direction("north", ["north", "n"])
define_direction("south", ["south", "s"])
define_direction("east", ["east", "e"])
define_direction("west", ["west", "w"])
define_direction("northwest", ["northwest", "nw"])
define_direction("southwest", ["southwest", "sw"])
define_direction("northeast", ["northeast", "ne"])
define_direction("southeast", ["southeast", "se"])
define_direction("up", ["up", "u"])
define_direction("down", ["down", "d"])

###
### Defining basic objects
###

# All objects have a name
Name = world.make_property(1, "Name")
@world.handler(Name(X) <= IsA(X, "thing"))
def default_Name(x, world) :
    return str(x)

# All objects have a description
Description = world.make_property(1, "Description")
world[Description(X)] = "It does't seem that interesting."

# All objects have a list of words which can describe them
Words = world.make_property(1, "Words")
@world.handler(Words(X))
def default_Words(x, world) :
    words = world[Name(x)].split()
    words[-1] = "@"+words[-1]
    return words

@world.to("get_words")
def get_words_Default(x, world) :
    raise ActionHandled(*world[Words(x)])

InhibitArticle = world.make_property(1, "InhibitArticle")
world[InhibitArticle(X) <= IsA(X, "thing")] = False

# There's also the printed name of the object
PrintedName = world.make_property(1, "PrintedName")
@world.handler(PrintedName(X))
def default_PrintedName(x, world) :
    return world[Name(x)]

DefiniteName = world.make_property(1, "DefiniteName")
@world.handler(DefiniteName(X))
def default_DefiniteName(x, world) :
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    else :
        return "the "+printed_name

IndefiniteName = world.make_property(1, "IndefiniteName")
@world.handler(IndefiniteName(X))
def default_IndefiniteName(x, world) :
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    elif printed_name[0] in "aeoiu" :
        return "an "+printed_name
    else :
        return "a "+printed_name

SubjectPronoun = world.make_property(1, "SubjectPronoun")
world[SubjectPronoun(X)] = "it"
ObjectPronoun = world.make_property(1, "ObjectPronoun")
world[ObjectPronoun(X)] = "it"
Possessive = world.make_property(1, "Possessive")
world[Possessive(X)] = "its"

Takeable = world.make_property(1, "Takeable")
world[Takeable(X)] = True # by default, things are takeable
NoTakeMsg = world.make_property(1, "NoTakeMsg")
world[NoTakeMsg(X)] = "{Bob|cap} can't take that."

AccessibleTo = world.make_property(2, "AccessibleTo")
world[AccessibleTo(X, actor)] = False # by default, things aren't accessible
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_held(x, actor, world) :
    if world.query_relation(Has(actor, x)) :
        return True
    else :
        raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_in_same_room(x, actor, world) :
    actor_room = world.query_relation(Contains(Y, actor), var=Y)
    x_room = world.query_relation(Contains(Y, x), var=Y)
    if actor_room and x_room and actor_room[0] == x_room[0] :
        return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_in_open_container(x, actor, world) :
    x_location = world.query_relation(Contains(Y, x), var=Y)
    if x_location and world[IsA(x_location[0], "container")] :
        if world[IsOpen(x_location[0])] and world[AccessibleTo(x_location[0], actor)] :
            return True
    raise NotHandled()

Owner = world.make_property(1, "Owner")
@world.handler(Owner(X))
def rule_Owner_default(x, world) :
    poss_owner = world.query_relation(Has(Y, x), var=Y)
    if poss_owner :
        return poss_owner[0]
    poss_container = world.query_relation(Contains(Y, x), var=Y)
    if poss_container :
        return world[Owner(poss_container[0])]
    return None

# Containers

Contents = world.make_property(1, "Contents")
@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

IsOpen = world.make_property(1, "IsOpen")
world[IsOpen(X)] = False # by default, containers are closed.

# Rooms

Enterable = world.make_property(1, "Enterable")
world[Enterable(X)] = False

world[Enterable(X) <= IsA(X, "room")] = True

@world.handler(Contents(X) <= IsA(X, "room"))
def room_contents(x, world) :
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

# action.describe_room
@actoractions.to("describe_room")
def describe_room_Heading(x, ctxt) :
    ctxt.actions.describe_room_heading(x)
    ctxt.write("[newline]")

@actoractions.to("describe_room")
def describe_room_Description(x, ctxt) :
    ctxt.write(ctxt.world[Description(x)])

@actoractions.to("describe_room")
def describe_room_Objects(x, ctxt) :
    obs = ctxt.world[Contents(x)]
    if obs :
        ctxt.write("[newline]You see "+serial_comma([ctxt.world[IndefiniteName(o)] for o in obs])+".")

# action.describe_room_heading
@actoractions.to("describe_room_heading")
def describe_room_heading_Name(x, ctxt) :
    ctxt.write(ctxt.world[Name(x)])

@actoractions.to("describe_room_heading")
def describe_room_location(x, ctxt) :
    r = ctxt.world.query_relation(Contains(Y, x), Y)
    if r and ctxt.world[Enterable(r[0])]:
        ctxt.write("(in",world[Name(r[0])]+")")

# actions.describe_current_room
@actoractions.to("describe_current_room")
def describe_current_room_default(ctxt) :
    ctxt.actions.describe_room(ctxt.world[Location(ctxt.actorname)])

# Persons

Gender = world.make_property(1, "Gender")
world[Gender(X) <= IsA(X, "person")] = "unknown" # other options are male and female

@world.handler(SubjectPronoun(X) <= IsA(X, "person"))
def person_SubjectPronoun(x, world) :
    gender = world[Gender(x)]
    if gender == "male" :
        return "he"
    elif gender == "female" :
        return "she"
    else :
        return "they"
@world.handler(ObjectPronoun(X) <= IsA(X, "person"))
def person_ObjectPronoun(x, world) :
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "them"
@world.handler(Possessive(X) <= IsA(X, "person"))
def person_Possessive(x, world) :
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "their"

# The default is 2nd person for pronouns
SubjectPronounIfMe = world.make_property(1, "SubjectPronounIfMe")
world[SubjectPronounIfMe(X) <= IsA(X, "person")] = "you"

ObjectPronounIfMe = world.make_property(1, "ObjectPronounIfMe")
world[ObjectPronounIfMe(X) <= IsA(X, "person")] = "you"

PossessiveIfMe = world.make_property(1, "PossessiveIfMe")
world[PossessiveIfMe(X) <= IsA(X, "person")] = "your"

# The player
def_obj("player", "person")
world[Name("player")] = "[if [current_actor_is <player>]]yourself[else]the player[endif]"
world[InhibitArticle("player")] = True
world[Words("player")] = ["yourself", "self", "AFGNCAAP"]
world[Description("player")] = """{Bob|cap} {is} an ageless, faceless,
gender-neutral, culturally-ambiguous adventure-person.  {Bob|cap}
{does} stuff sometimes."""

###
### Scenery
###

# scenery is not takeable
world[Takeable(X) <= IsA(X, "scenery")] = False


###
### Oft-used requirements on actions
###

def require_xobj_accessible(action) :
    """Adds a rule which ensures that x is accessible to the actor in
    the action."""
    @verify(action)
    @docstring("Ensures the object x in "+repr(action)+" is accessible to the actor.  Added by require_xobj_accessible.")
    def _verify_xobj_accessible(actor, x, ctxt, **kwargs) :
        if not ctxt.world[AccessibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))

def require_xobj_held(action, only_hint=False, transitive=True) :
    """Adds rules which check if the object x is held by the actor in
    the action, and if only_hint is not true, then if the thing is not
    already held, an attempt is made to take it."""
    def __is_held(actor, x, ctxt) :
        if transitive :
            return actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)]
        else :
            return ctxt.world.query_relation(Has(actor, x))
    @verify(action)
    @docstring("Makes "+repr(action)+" more logical if object x is held by the actor.  Also ensures that x is accessible to the actor. Added by require_xobj_held.")
    def _verify_xobj_held(actor, x, ctxt, **kwargs) :
        if ctxt.world.query_relation(Has(actor, x)) :
            return VeryLogicalOperation()
        elif not ctxt.world[AccessibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))
    if only_hint :
        @before(action)
        @docstring("A check that the actor is holding the x in "+repr(action)+".  The holding may be transitive.")
        def _before_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {isn't} holding that.", actor=actor)
    else :
        @trybefore(action)
        @docstring("An attempt is made to take the object x from "+repr(action)+" if the actor is not already holding it")
        def _trybefore_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                do_first(Take(actor, x), context=context)
            # just in case it succeeds, but we don't yet have the object
            if transitive :
                can_do = (actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)])
            else :
                can_do = ctxt.world.query_relation(Has(actor, x))
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {doesn't} have that.", actor=actor)

def hint_xobj_notheld(action) :
    """Adds a rule which makes the action more logical if x is not
    held by the actor of the action."""
    @verify(action)
    @docstring("Makes "+repr(action)+" more logical if object x is not held by the actor.  Added by hint_xobj_notheld.")
    def _verify_xobj_notheld(actor, x, ctxt, **kwargs) :
        if not ctxt.world.query_relation(Has(actor, x)) :
            return VeryLogicalOperation()

###
### Action definitions
###

##
# Taking
##

class Take(BasicAction) :
    """Take(actor, obj_to_take)"""
    verb = "take"
    gerund = "taking"
    numargs = 2
understand("take/get [something x]", Take(actor, X))

require_xobj_accessible(Take(actor, X))
hint_xobj_notheld(Take(actor, X))

@before(Take(actor, X))
def before_take_when_already_have(actor, x, ctxt) :
    """You can only take what you don't have."""
    if ctxt.world.query_relation(Has(actor, x)) :
        raise AbortAction("{Bob|cap} already {has} that.", actor=actor)

@before(Take(actor, X))
def before_take_check_ownership(actor, x, ctxt) :
    """You can only take what is not owned by anyone else."""
    owner = ctxt.world[Owner(x)]
    if owner and owner != actor :
        raise AbortAction("That is not {bob's} to take.", actor=actor)

@before(Take(actor, X))
def before_take_check_takeable(actor, x, ctxt) :
    """One cannot take what is not takeable."""
    if not ctxt.world[Takeable(x)] :
        raise AbortAction(ctxt.world[NoTakeMsg(x)], actor=actor)

@when(Take(actor, X))
def when_take_default(actor, x, ctxt) :
    """Carry out the taking by giving it to the actor."""
    ctxt.world.actions.give_to(x, actor)

@report(Take(actor, X))
def report_take_default(actor, x, ctxt) :
    """Prints out the default "Taken." message."""
    ctxt.write("Taken.")

##
# Dropping
##

class Drop(BasicAction) :
    """Drop(actor, obj_to_drop)"""
    verb = "drop"
    gerund = "dropping"
    numargs = 2
understand("drop [something x]", Drop(actor, X))

require_xobj_held(Drop(actor, X), only_hint=True)

@when(Drop(actor, X))
def when_drop_default(actor, x, ctxt) :
    """Carry out the dropping by moving the object to the location of the actor."""
    ctxt.world.actions.move_to(x, ctxt.world[Location(actor)])

@report(Drop(actor, X))
def report_drop_default(actor, x, ctxt) :
    """Prints the default "Dropped." message."""
    ctxt.write("Dropped.")

##
# Going
##

class Go(BasicAction) :
    verb = "go"
    gerund = "going"
    dereference_dobj = False
    numargs = 2 # Go(actor, direction)
understand("go [direction x]", Go(actor, X))
understand("[direction x]", Go(actor, X))

class AskTo(BasicAction) :
    verb = ("ask", "to")
    gerund = ("asking", "to")
    numargs = 3
    def gerund_form(self, ctxt) :
        dobj = ctxt.world.get_property("DefiniteName", self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.gerund[0] + " " + dobj + " to " + comm
    def infinitive_form(self, ctxt) :
        dobj = ctxt.world.get_property("DefiniteName", self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.verb[0] + " " + dobj + " to " + comm
understand("ask [something x] to [action y]", AskTo(actor, X, Y))

class GiveTo(BasicAction) :
    verb = ("give", "to")
    gerund = ("giving", "to")
    numargs = 3
understand("give [something x] to [something y]", GiveTo(actor, X, Y))
