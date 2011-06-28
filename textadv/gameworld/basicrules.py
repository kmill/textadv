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

@world.to("put_in")
def default_put_in(x, y, world) :
    """A synonym for "move_to"."""
    world.actions.move_to(x, y)

# put X on Y (so then Y Supports X)
@world.to("put_on")
def default_put_on(x, y, world) :
    """Called with put_on(x, y).  Puts x onto y, first removing all
    Contains, Supports, Has, and PartOf relations."""
    world.remove_relation(Contains(X, x))
    world.remove_relation(Supports(X, x))
    world.remove_relation(Has(X, x))
    world.remove_relation(PartOf(x, X))
    world.add_relation(Supports(y, x))

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
    world.remove_relation(Contains(X, obj))
    world.remove_relation(Supports(X, obj))
    world.remove_relation(Has(X, obj))
    world.remove_relation(PartOf(obj, X))

@world.define_property
class Location(Property) :
    """Location(X) is the current immediate location in which X
    resides.  Usually used to get the location of the actor."""
    numargs = 1

world[Location(X)] = None
@world.handler(Location(X))
def object_location_Contains(x, world) :
    """Gets the location of an object by what currently contains it."""
    locs = world.query_relation(Contains(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_Has(x, world) :
    """Gets the location of an object by what currently has it."""
    locs = world.query_relation(Has(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_Supports(x, world) :
    """Gets the location of an object by what currently supports it."""
    locs = world.query_relation(Supports(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_PartOf(x, world) :
    """Gets the location of an object by what it is currently part of."""
    locs = world.query_relation(PartOf(x, Y), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()


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
# Property: Visited
##

@world.define_property
class Visited(Property) :
    """Represents whether a room has been visited."""
    numargs = 1

world[Visited(X) <= IsA(X, "room")] = False

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
# Property: EffectiveContainer
##

@world.define_property
class EffectiveContainer(Property) :
    """Gets the object which effectively contain an object which is
    "inside" this one (change to "on top of" for supporters).
    Specifically, if the object is a closed box, then the box is the
    effective container.  Otherwise, it's the effective container of
    the location of the open box."""
    numargs = 1

@world.handler(EffectiveContainer(X) <= IsA(X, "room"))
def rule_EffectiveContainer_if_x_in_room(x, world) :
    """The effective container for a room is the room itself."""
    return x

##
# Property: ProvidesLight
##
@world.define_property
class ProvidesLight(Property) :
    """Represents whether the object is a source of light, and not
    because of its contents."""
    numargs = 1

# rooms provide light by default
world[ProvidesLight(X) <= IsA(X, "room")] = True

##
# Property: IsLit
##
@world.define_property
class IsLit(Property) :
    """Represents whether the object is lit from the inside, and not
    whether some outside source is lighting it (for this, we must
    instead look at the EffectiveContainer of the object)."""
    numargs = 1

@world.handler(IsLit(X) <= IsA(X, "room"))
def rul_IsLit_room_default_is_ProvidesLight(x, world) :
    """A room, by default, is lit if it provides light itself."""
    return world[ProvidesLight(x)]

@world.handler(IsLit(X) <= IsA(X, "room"))
def rule_IsLit_contents_can_light_room(x, world) :
    """A room is lit if any of its contents are lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

###
### Defining: thing
###

world[Description(X) <= IsA(X, "thing")] = "It does't seem that interesting."

# Most things don't provide light
world[ProvidesLight(X) <= IsA(X, "thing")] = False

@world.handler(IsLit(X) <= IsA(X, "thing"))
def rul_IsLit_thing_default_is_ProvidesLight(x, world) :
    """By default, a thing is lit if it provides light."""
    return world[ProvidesLight(x)]

@world.handler(IsLit(X) <= IsA(X, "thing"))
def rule_IsLit_if_parts_lit(x, world) :
    """A thing provides light if any of its constituent parts are lit up."""
    parts = world.query_relation(PartOf(Y, x), var=Y)
    if any(world[IsLit(o)] for o in parts) :
        return True
    else : raise NotHandled()


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
def rule_AccessibleTo_if_in_same_effective_container(x, actor, world) :
    """Anything in the same effective container to the actor is
    accessible if the effective container is lit."""
    actor_eff_cont = world[EffectiveContainer(world[Location(actor)])]
    if actor_eff_cont == x :
        # otherwise we'd be looking too many levels high
        x_eff_cont = x
    else :
        x_eff_cont = world[EffectiveContainer(world[Location(x)])]
    if actor_eff_cont == x_eff_cont and world[IsLit(actor_eff_cont)] :
        return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_immediately_in_container(x, actor, world) :
    """If the actor is immediately in the container x, then x is
    accessible.  Prevents such things as closing a box around oneself
    and then not being able to refer to the box anymore."""
    if world[IsA(x, "container")] and world.query_relation(Contains(x, actor)) :
        return True
    else : raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_part_of(x, actor, world) :
    """If an object is part of something, and that something is
    accessible, then the object is accessible."""
    x_assembly = world.query_relation(PartOf(x, Y), var=Y)
    if x_assembly and world[AccessibleTo(x_assembly[0], actor)] :
        return True
    raise NotHandled()

##
# Property: IsOpaque
##

@world.define_property
class IsOpaque(Property) :
    """Represents whether the object cannot transmit light."""
    numargs = 1

# And, let's just say that things are usually opaque.
world[IsOpaque(X) <= IsA(X, "thing")] = True


##
# Property: Enterable
##
@world.define_property
class Enterable(Property) :
    """Is true if the object is something someone could enter."""
    numargs = 1

# By default it's false
world[Enterable(X) <= IsA(X, "thing")] = False

###
### Defining: container
###

@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    """Gets the immediate contents of the container."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

##
# Properties: Openable, IsOpen
##

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

#
# Lighting for container
#

world[IsOpaque(X) <= IsA(X, "container")] = False


@world.handler(IsOpaque(X) <= IsA(X, "container"))
def rule_IsOpaque_if_openable_container_is_closed(x, world) :
    """A container is by default not opaque, but if it is openable,
    then it is not opaque if it is open."""
    if world[Openable(x)] and not world[IsOpen(x)]:
        return True
    else :
        raise NotHandled()

@world.handler(IsLit(X) <= IsA(X, "container"))
def rule_IsLit_for_container(x, world) :
    """A container is lit if it is not opaque and one of its contents
    is lit."""
    if not world[IsOpaque(x)] and any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(EffectiveContainer(X) <= IsA(X, "container"))
def rule_EffectiveContainer_if_x_in_container(x, world) :
    """The effective container for a container is the container itself
    if it is opaque, otherwise it is the effective container of the
    location of the container."""
    if world[IsOpaque(x)] :
        return x
    else :
        return world[EffectiveContainer(world[Location(x)])]

###
### Defining: supporter
###

@world.handler(Contents(X) <= IsA(X, "supporter"))
def supporter_contents(x, world) :
    """Gets the things the supporter immediately supports."""
    return [o["y"] for o in world.query_relation(Supports(x, Y))]


#
# Lighting for supporter
#

# A supporter doesn't block light.
world[IsOpaque(X) <= IsA(X, "supporter")] = False

@world.handler(IsLit(X) <= IsA(X, "supporter"))
def rule_IsLit_for_supporter(x, world) :
    """A supporter is lit if it is not opaque and one of its objects
    is lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(EffectiveContainer(X) <= IsA(X, "supporter"))
def rule_EffectiveContainer_if_x_on_supporter(x, world) :
    """The effective container of a supporter is the effective
    container of the location of the supporter."""
    return world[EffectiveContainer(world[Location(x)])]

###
### Defining: person
###

@world.handler(Contents(X) <= IsA(X, "person"))
def supporter_contents(x, world) :
    """Gets the things the person immediately has."""
    return [o["y"] for o in world.query_relation(Has(x, Y))]

##
# Property: Gender
##

@world.define_property
class Gender(Property) :
    """Represents the gender of a person.  Examples of options are
    "male", "female", and "unknown"."""
    numargs = 1

world[Gender(X) <= IsA(X, "person")] = "unknown" # other options are male and female

##
# Property: Pronouns
##

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

#
# Light for a person
#

@world.handler(IsLit(X) <= IsA(X, "person"))
def rule_IsLit_possessions_can_light_person(x, world) : # maybe should handle concealment at some point?
    """A person is lit if any of its posessions are lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

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
world[Reported("player")] = False


###
### Other properties
###



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
### Action: location descriptions
###

__DESCRIBE_LOCATION_obj_mentioned = []

@actoractions.to("describe_location")
def describe_location_init_global_vars(loc, eff_cont, ctxt) :
    """We have a global variable __DESCRIBE_LOCATION_obj_mentioned
    which is a list of all objects that have already been mentioned.
    This is cleared by this init function."""
    global __DESCRIBE_LOCATION_obj_mentioned
    __DESCRIBE_LOCATION_obj_mentioned = []

@actoractions.to("describe_location")
def describe_location_Heading(loc, eff_cont, ctxt) :
    """Constructs the heading using describe_location_heading.  If the
    room is in darkness, then, writes "Darkness"."""
    if ctxt.world[IsLit(eff_cont)] :
        ctxt.actions.describe_location_heading(loc, eff_cont)
    else :
        ctxt.write("Darkness")
    ctxt.write("[newline]")

@actoractions.to("describe_location")
def describe_location_Description(loc, eff_cont, ctxt) :
    """Prints the description property of the effective container if
    it is a room, unless the room is in darkness.  Darkness stops
    further description of the location."""
    if ctxt.world[IsLit(eff_cont)] :
        if ctxt.world[IsA(eff_cont, "room")] :
            ctxt.write(ctxt.world[Description(eff_cont)])
    else :
        ctxt.write("You can't see a thing; it's incredibly dark.")
        raise ActionHandled()

@actoractions.to("describe_location")
def describe_location_Objects(loc, eff_cont, ctxt) :
    """Prints the of the location by asking the effective
    container to do so."""
    obs = ctxt.world[Contents(eff_cont)]
    obs = [o for o in obs if ctxt.world[Reported(o)]]
    if obs :
        ctxt.write("[newline]You see "+serial_comma([" ".join(ctxt.actions.object_description(o)) for o in obs])+".")

@actoractions.to("describe_location")
def describe_location_set_visited(loc, eff_cont, ctxt) :
    """If the effective container is a room, then we set it to being
    visited."""
    if ctxt.world[IsA(eff_cont, "room")] :
        ctxt.world[Visited(eff_cont)] = True


@actoractions.to("describe_location_heading")
def describe_location_heading_Name(loc, eff_cont, ctxt) :
    """Prints the name of the effective container."""
    ctxt.write(ctxt.world[Name(eff_cont)])

@actoractions.to("describe_location_heading")
def describe_location_property_heading_location(loc, eff_cont, ctxt) :
    """Creates a description of where the location is with respect to
    the effective container."""
    while loc != eff_cont :
        if ctxt.world[IsA(loc, "container")] :
            ctxt.write("(in",world[DefiniteName(loc)]+")")
        elif ctxt.world[IsA(loc, "supporter")] :
            ctxt.write("(on",world[DefiniteName(loc)]+")")
        else :
            return
        loc = ctxt.world[Location(loc)]

@actoractions.to("object_description")
def object_description_DefiniteName(o, ctxt) :
    """Describes the object based on its indefinite name."""
    return ctxt.world[IndefiniteName(o)]

@actoractions.to("object_description")
def object_description_container(o, ctxt) :
    if ctxt.world[IsA(o, "container")] :
        contents = ctxt.world[Contents(o)]
        contents = [o for o in contents if ctxt.world[Reported(o)]]
        if contents :
            return "(in which "+is_are_list([" ".join(ctxt.actions.object_description(x)) for x in contents])+")"
        else : raise NotHandled()
    else : raise NotHandled()


@actoractions.to("describe_current_location")
def describe_current_location_default(ctxt) :
    """Calls describe_location using the Location and the
    EffectiveContainer of the current actor."""
    loc = ctxt.world[Location(ctxt.actorname)]
    eff_cont = ctxt.world[EffectiveContainer(loc)]
    ctxt.actions.describe_location(loc, eff_cont)


###*
###* Actions by a person
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
    ctxt.actions.describe_current_location()

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
    """Carry out the dropping by moving the object to the location of
    the actor (if the location is a room or a container), but if the
    location is a supporter, the object is put on the supporter."""
    l = ctxt.world[Location(actor)]
    if ctxt.world[IsA(l, "supporter")] :
        ctxt.world.actions.put_on(x, ctxt.world[Location(actor)])
    else :
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

class Destroy(BasicAction) :
    verb = "destroy"
    gerund = "destroying"
    numargs = 2
understand("destroy [something x]", Destroy(actor, X))

@when(Destroy(actor, X))
def when_destroy(actor, x, ctxt) :
    ctxt.world.actions.remove_obj(x)

@report(Destroy(actor, X))
def report_destroy(actor, x, ctxt) :
    ctxt.write("*Poof*")

class Open(BasicAction) :
    verb = "open"
    gerund = "opening"
    numargs = 2
understand("open [something x]", Open(actor, X))

require_xobj_accessible(Open(actor, X))

@when(Open(actor, X))
def when_open(actor, x, ctxt) :
    ctxt.world[IsOpen(x)] = True

@report(Open(actor, X))
def report_open(actor, x, ctxt) :
    ctxt.write("Opened.")
