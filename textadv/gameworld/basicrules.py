# The basic definition of how the world works

from textadv.core.patterns import VarPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *
from textadv.gamesystem.gamecontexts import actoractions
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.utilities import *

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

# Contains(x,y) for "x Contains y"
Contains = make_one_to_many_relation(name="Contains")
world.define_relation(Contains)

# Has(x,y) for "x Has y"
Has = make_one_to_many_relation(name="Has")
world.define_relation(Has)

# PartOf(x,y) for "x PartOf y"
PartOf = make_many_to_one_relation(name="PartOf")
world.define_relation(PartOf)

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

# basically classes
KindOf = make_many_to_one_relation(name="KindOf")
world.define_relation(KindOf)
world.add_relation(KindOf("room", "kind"))
world.add_relation(KindOf("thing", "kind"))
world.add_relation(KindOf("door", "thing"))
world.add_relation(KindOf("container", "thing"))
world.add_relation(KindOf("person", "thing"))
# basically instances
IsA = make_many_to_one_relation(name="IsA")
world.define_relation(IsA)

@world.handler(IsA(X,Y))
def property_handler_IsA(x, y, world) :
    """Lets one ask whether a particular object has a kind, searching
    up the KindOf tree."""
    kind = world.query_relation(IsA(x, Z), var=Z)
    if not kind :
        return False
    else :
        return world.r_path_to(KindOf, kind[0], y)

# connecting rooms together
Adjacent = make_directed_many_to_many_relation(name="Adjacent")
world.define_relation(Adjacent)

Exit = make_freeform_relation(3, "Exit")
world.define_relation(Exit)

@world.to("connect_rooms")
def default_connect_rooms(room1, dir, room2, world, reverse=True) :
    world.add_relation(Adjacent(room1, room2))
    world.add_relation(Exit(room1, dir, room2))
    if reverse :
        world.add_relation(Adjacent(room2, room1))
        world.add_relation(Exit(room2, inverse_direction(dir), room1))

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
def defaulte_DefiniteName(x, world) :
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    else :
        return "the "+printed_name

IndefiniteName = world.make_property(1, "IndefiniteName")
@world.handler(IndefiniteName(X))
def defaulte_IndefiniteName(x, world) :
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

# Containers

Contents = world.make_property(1, "Contents")
@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

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
