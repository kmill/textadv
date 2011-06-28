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
from textadv.gamesystem.eventsystem import BasicAction, verify, trybefore, before, when, report, do_first
from textadv.gamesystem.eventsystem import VeryLogicalOperation, LogicalOperation, IllogicalOperation, IllogicalInaccessible, NonObviousOperation

# The main game world!
world = World()

# A convenience function
def def_obj(name, type) :
    world.add_relation(IsA(name, type))

###
### Global properties
###

@world.define_property
class Global(Property) :
    """Use Global("x") to get global variable "x"."""
    numargs = 1

###
### Basic position relations
###

# The following four are mutually exclusive relations which have to
# do with position.

@world.define_relation
class Contains(OneToManyRelation) :
    """Contains(x,y) for "x Contains y"."""

@world.define_relation
class Supports(OneToManyRelation) :
    """Supports(x,y) for "x Supports y"."""

@world.define_relation
class Has(OneToManyRelation) :
    """Has(x,y) for "x Has y"."""

@world.define_relation
class PartOf(ManyToOneRelation) :
    """PartOf(x,y) for "x PartOf y"."""

#
# some helper actions to make it easy to use these three relations
#

# move X to Y (so then Y Contains X)
@world.to("move_to")
def default_move_to(x, y, world) :
    """Called with move_to(x, y).  Moves x to be contained by y, first
    removing all Contains, Supports, Has, and PartOf relations."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Supports(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(Contains(y, x))

# give X to Y (so then Y Has X)
@world.to("give_to")
def default_give_to(x, y, world) :
    """Called with give_to(x, y).  Gives x to y, first
    removing all Contains, Supports, Has, and PartOf relations."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Supports(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(Has(y, x))

# make X part of Y (so then X PartOf Y)
@world.to("make_part_of")
def default_make_part_of(x, y, world) :
    """Called with make_part_of(x, y).  Makes x a part of y, first
    removing all Contains, Supports, Has, and PartOf relations."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Supports(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(PartOf(x, y))

@world.to("remove_obj")
def default_remove_obj(obj, world) :
    """Effectively removes an object from play by making it have no
    positional location."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Supports(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(X, x))

@world.define_property
class Location(Property) :
    """Location(X) is the current immediate location in which X
    resides (by containment).  Usually used to get the location of
    the actor."""
    numargs = 1

@world.handler(Location(X))
def object_location(x, world) :
    """Gets the location of an object by what currently contains it."""
    locs = world.query_relation(Contains(Y, x), var=Y)
    return locs[0] if locs else None

@world.define_property
class Owner(Property) :
    """Gets the owner of the object."""
    numargs = 1

@world.handler(Owner(X))
def rule_Owner_default(x, world) :
    """We assume that the owner of an object is the first object which
    Has some object which in some chain of containment (containment
    optional).  Returns None if no owner was found."""
    poss_owner = world.query_relation(Has(Y, x), var=Y)
    if poss_owner :
        return poss_owner[0]
    poss_container = world.query_relation(Contains(Y, x), var=Y)
    if poss_container :
        return world[Owner(poss_container[0])]
    return None

###
### Kinds and instances
###

@world.define_relation
class KindOf(ManyToOneRelation) :
    """Represents a class-like hierarchy."""

world.add_relation(KindOf("room", "kind"))
world.add_relation(KindOf("thing", "kind"))
world.add_relation(KindOf("door", "thing"))
world.add_relation(KindOf("container", "thing"))
world.add_relation(KindOf("supporter", "thing"))
world.add_relation(KindOf("person", "thing"))

@world.define_property
@world.define_relation
class IsA(ManyToOneRelation, Property) :
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
    """Gets all things in the world (that is, all objects which
    inherit from "thing")."""
    objects = world.query_relation(IsA(X, Y), var=X)
    things = [o for o in objects if world[IsA(o, "thing")]]
    return things

###
### Directions
###


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

###*
###* Property definitions
###*

###
### Defining: kind
###

##
# Property: Name
##

@world.define_property
class Name(Property) :
    """Represents the name of a kind.  Then, the id of a thing may be
    differentiated from what the user will call it (for shorthand)."""
    numargs = 1

@world.handler(Name(X) <= IsA(X, "kind"))
def default_Name(x, world) :
    """The default name of a thing is its id, X."""
    return str(x)

##
# Property: Description
##

@world.define_property
class Description(Property) :
    """Represents a textual description of a kind.  There is no
    default value of this for kinds."""
    numargs = 1

##
# Property: Words
##

@world.define_property
class Words(Property) :
    """This is a list of words which can describe the kind.  Words may
    be prefixed with @ to denote that they are nouns (and matching a
    noun gives higher priority to the disambiguator)."""
    numargs = 1

@world.handler(Words(X))
def default_Words(x, world) :
    """The default handler assumes that the words in Name(x) are
    suitable for the object, and furthermore that the last word is a
    noun (so "big red ball" returns ["big", "red", "@ball"])."""
    words = world[Name(x)].split()
    words[-1] = "@"+words[-1]
    return words

###
### Defining: room
###

world[Description(X) <= IsA(X, "room")] = "It's a place to be."

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
    """Called with connect_rooms(room1, dir, room2).  Gives room1 an
    exit to room2 in direction dir.  By default, also adds in reverse
    direction, unless the optional argument "reverse" is false."""
    world.add_relation(Adjacent(room1, room2))
    world.add_relation(Exit(room1, dir, room2))
    if reverse :
        world.add_relation(Adjacent(room2, room1))
        world.add_relation(Exit(room2, inverse_direction(dir), room1))

##
# Property: Contents
##

@world.define_property
class Contents(Property) :
    """Gets a list of things which are the contents of the object.
    Only goes one level deep."""
    numargs = 1

@world.handler(Contents(X) <= IsA(X, "room"))
def contents_room(x, world) :
    """Gets the immediate contents of a room."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

##
# Property: Enterable
##
@world.define_property
class Enterable(Property) :
    """Is true if the object is something someone could enter."""
    numargs = 1

# By default it's false
world[Enterable(X)] = False
# But for rooms it's true.
world[Enterable(X) <= IsA(X, "room")] = True


##
# Property: IsLit
##
@world.define_property
class IsLit(Property) :
    """A property which represents if a player could see anything in
    something which is enterable."""
    numargs = 1

# Enterable things are lit by default
world[IsLit(X) <= Enterable(X)] = True


###
### Defining: thing
###

world[Description(X) <= IsA(X, "thing")] = "It does't seem that interesting."

##
# Property: Report
##

@world.define_property
class Reported(Property) :
    """Represents whether the object should be automatically reported
    in room descriptions."""
    numargs = 1

world[Reported(X) <= IsA(X, "thing")] = True

##
# Properties: InhibitArticle, PrintedName, DefiniteName, IndefiniteName
##

@world.define_property
class InhibitArticle(Property) :
    """Tells the default DefiniteName and Indefinite name properties
    whether to put the article in front.  For instance, we don't want
    to be talking about the Bob."""
    numargs = 1

world[InhibitArticle(X) <= IsA(X, "thing")] = False

@world.define_property
class PrintedName(Property) :
    """Gives a textual representation of an object which can then be
    prefaced by an article (that is, unless InhibitArticle is true).
    This is separate from Name because it might be dynamic in some
    way.  (Note: it might be that this property isn't necessary)."""
    numargs = 1

@world.handler(PrintedName(X) <= IsA(X, "thing"))
def default_PrintedName(x, world) :
    """By default, PrintedName(X) is Name(X)."""
    return world[Name(x)]

@world.define_property
class DefiniteName(Property) :
    """Gives the definite name of an object.  For instance, "the ball"
    or "Bob"."""
    numargs = 1

@world.handler(DefiniteName(X) <= IsA(X, "thing"))
def default_DefiniteName(x, world) :
    """By default, DefiniteName is just the PrintedName with "the"
    stuck in front, unless InhibitArticle is true."""
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    else :
        return "the "+printed_name

@world.define_property
class IndefiniteName(Property) :
    """Gives the indefinite name of an object.  For instance, "a ball"
    or "Bob"."""
    numargs = 1

@world.handler(IndefiniteName(X) <= IsA(X, "thing"))
def default_IndefiniteName(x, world) :
    """By default, IndefiniteName is the PrintedName with "a" or "an"
    (depending on whether the PrintedName starts with a vowel) stuck
    to the front, unless InhibitArticle is true."""
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    elif printed_name[0] in "aeoiu" :
        return "an "+printed_name
    else :
        return "a "+printed_name

##
# Properties: SubjectPronoun, ObjectPronoun, PossessivePronoun
##

@world.define_property
class SubjectPronoun(Property) :
    """Represents the pronoun for when the object is the subject of a
    sentence."""
    numargs = 1

@world.define_property
class ObjectPronoun(Property) :
    """Represents the pronoun for when the object is the object of a
    sentence."""
    numargs = 1

@world.define_property
class PossessivePronoun(Property) :
    """Represents the possesive pronoun of the object."""
    numargs = 1

world[SubjectPronoun(X) <= IsA(X, "thing")] = "it"
world[ObjectPronoun(X) <= IsA(X, "thing")] = "it"
world[PossessivePronoun(X) <= IsA(X, "thing")] = "its"


##
# FixedInPlace
##

@world.define_property
class FixedInPlace(Property) :
    """Represents something which can't be taken because it's fixed in
    place.  For instance, scenery."""
    numargs = 1

# by default, things are not fixed in place
world[FixedInPlace(X) <= IsA(X, "thing")] = False


##
# AccessibleTo
##

@world.define_property
class AccessibleTo(Property) :
    """AccessibleTo(X, actor) checks whether X is accessible to the
    actor."""
    numargs = 2

# by default, things aren't accessible
world[AccessibleTo(X, actor)] = False
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_held(x, actor, world) :
    """Anything the actor has is accessible."""
    if world.query_relation(Has(actor, x)) :
        return True
    else :
        raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_in_same_room(x, actor, world) :
    """Anything in the same room as the actor is accessible if the
    room is lit."""
    actor_room = world.query_relation(Contains(Y, actor), var=Y)
    x_room = world.query_relation(Contains(Y, x), var=Y)
    if actor_room and x_room and actor_room[0] == x_room[0] and world[IsLit(actor_room[0])] :
        return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_in_open_container(x, actor, world) :
    """If an object is in a container which is open (assumed true if
    not openable), then the object is accessible if the container is
    accessible."""
    x_location = world.query_relation(Contains(Y, x), var=Y)
    if x_location and world[IsA(x_location[0], "container")] :
        open_not_matters = world[Openable(x_location[0])] and world[IsOpen(x_location[0])]
        if open_not_matters and world[AccessibleTo(x_location[0], actor)] :
            return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_part_of(x, actor, world) :
    """If an object is part of something, and that something is
    accessible, then the object is accessible."""
    x_assembly = world.query_relation(PartOf(x, Y), var=Y)
    if x_assembly and world[AccessibleTo(x_assembly[0], actor)] :
        return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_on_supporter(x, actor, world) :
    """If an object is on something, and that something is
    accessible, then the object is accessible."""
    x_supporter = world.query_relation(Supports(Y, x), var=Y)
    if x_supporter and world[AccessibleTo(x_supporter[0], actor)] :
        return True
    raise NotHandled()

###
### Defining: container
###

@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    """Gets the immediate contents of the container."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]



###
### Defining: person
###

@world.define_property
class Gender(Property) :
    """Represents the gender of a person.  Examples of options are
    "male", "female", and "unknown"."""
    numargs = 1

world[Gender(X) <= IsA(X, "person")] = "unknown" # other options are male and female


@world.handler(SubjectPronoun(X) <= IsA(X, "person"))
def person_SubjectPronoun(x, world) :
    """Gives a default subject pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "he"
    elif gender == "female" :
        return "she"
    else :
        return "they"
@world.handler(ObjectPronoun(X) <= IsA(X, "person"))
def person_ObjectPronoun(x, world) :
    """Gives a default object pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "them"
@world.handler(PossessivePronoun(X) <= IsA(X, "person"))
def person_PossessivePronoun(x, world) :
    """Gives a default possessive pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "their"

##
# Properties: SubjectPronounIfMe, ObjectPronounIfMe, PossessivePronounIfMe
##

@world.define_property
class SubjectPronounIfMe(Property) :
    """Represents the subject pronoun, but when referring to the
    current actor."""
    numargs = 1
@world.define_property
class ObjectPronounIfMe(Property) :
    """Represents the object pronoun, but when referring to the
    current actor."""
    numargs = 1
@world.define_property
class PossessivePronounIfMe(Property) :
    """Represents the possessive pronoun, but when referring to the
    current actor."""
    numargs = 1

world[SubjectPronounIfMe(X) <= IsA(X, "person")] = "you"
world[ObjectPronounIfMe(X) <= IsA(X, "person")] = "you"
world[PossessivePronounIfMe(X) <= IsA(X, "person")] = "your"

##
# The default player
##

def_obj("player", "person")
world[PrintedName("player")] = "[if [current_actor_is player]]yourself[else]the player[endif]"
world[InhibitArticle("player")] = True
world[Words("player")] = ["yourself", "self", "AFGNCAAP"]
world[Description("player")] = """{Bob|cap} {is} an ageless, faceless,
gender-neutral, culturally-ambiguous adventure-person.  {Bob|cap}
{does} stuff sometimes."""


###
### Other properties
###

##
# Properties: Openable, IsOpen

@world.define_property
class Openable(Property) :
    """Represents whether an object is able to be opened and closed."""
    numargs = 1

world[Openable(X) <= IsA(X, "thing")] = False # by default, things aren't openable

@world.define_property
class IsOpen(Property) :
    """Represents whether an openable object is open."""
    numargs = 1

world[IsOpen(X) <= Openable(X)] = False # by default, openable things are closed


###
### Other kinds
###

##
## Scenery
##

world.add_relation(KindOf("scenery", "thing"))
# scenery is fixed in place
world[FixedInPlace(X) <= IsA(X, "scenery")] = True
# scenery is not reported
world[Reported(X) <= IsA(X, "scenery")] = False


###*
###* Actions
###*

###
### Action: room descriptions
###

# action.describe_room
@actoractions.to("describe_room")
def describe_room_Heading(x, ctxt) :
    """Runs describe_room_heading."""
    ctxt.actions.describe_room_heading(x)
    ctxt.write("[newline]")

@actoractions.to("describe_room")
def describe_room_Description(x, ctxt) :
    """Prints the description property of the room."""
    ctxt.write(ctxt.world[Description(x)])

@actoractions.to("describe_room")
def describe_room_Objects(x, ctxt) :
    """Prints the contents of the room."""
    obs = ctxt.world[Contents(x)]
    if obs :
        ctxt.write("[newline]You see "+serial_comma([ctxt.world[IndefiniteName(o)] for o in obs])+".")

# action.describe_room_heading
@actoractions.to("describe_room_heading")
def describe_room_heading_Name(x, ctxt) :
    """Prints the name of the room."""
    ctxt.write(ctxt.world[Name(x)])

@actoractions.to("describe_room_heading")
def describe_room_location(x, ctxt) :
    """Prints the room's location, if it is contained in another room."""
    r = ctxt.world.query_relation(Contains(Y, x), Y)
    if r and ctxt.world[Enterable(r[0])]:
        ctxt.write("(in",world[Name(r[0])]+")")

# actions.describe_current_room
@actoractions.to("describe_current_room")
def describe_current_room_default(ctxt) :
    """Calls describe_room using the location of the current actor."""
    ctxt.actions.describe_room(ctxt.world[Location(ctxt.actorname)])


###*
###* Actions by the actor
###*

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
                do_first(Take(actor, x), ctxt=ctxt)
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

class Look(BasicAction) :
    """Look(actor)"""
    verb = "look"
    gerund = "looking"
    numargs = 1
understand("look/l", Look(actor))

@when(Look(actor))
def when_look_default(actor, ctxt) :
    ctxt.actions.describe_current_room()

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
    """You can't take what you already have."""
    if ctxt.world.query_relation(Has(actor, x)) :
        raise AbortAction("{Bob|cap} already {has} that.", actor=actor)

@before(Take(actor, X))
def before_take_check_ownership(actor, x, ctxt) :
    """You can't take what is owned by anyone else."""
    owner = ctxt.world[Owner(x)]
    if owner and owner != actor :
        raise AbortAction("That is not {bob's} to take.", actor=actor)

@before(Take(actor, X))
def before_take_check_fixedinplace(actor, x, ctxt) :
    """One cannot take what is fixed in place."""
    if ctxt.world[FixedInPlace(x)] :
        raise AbortAction("That's fixed in place.")

@before(Take(actor, X))
def before_take_check_not_self(actor, x, ctxt) :
    """One cannot take oneself."""
    if actor == x :
        raise AbortAction("{Bob|cap} cannot take {himself}.", actor=actor)

@before(Take(actor, X) <= IsA(X, "person"))
def before_take_check_not_other_person(actor, x, ctxt) :
    """One cannot take other people."""
    if actor != x :
        raise AbortAction(str_with_objs("[The $x] doesn't look like [he $x]'d appreciate that.", x=x))

@before(Take(actor, X))
def before_take_check_not_inside(actor, x, ctxt) :
    """One cannot take what one is inside."""
    if ctxt.world.r_path_to(Contains, x, actor) :
        raise AbortAction(str_with_objs("{Bob|cap} {is} inside of that.", actor=actor))

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
