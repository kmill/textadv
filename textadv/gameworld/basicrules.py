# The basic definition of how the world works

from textadv.core.patterns import VarPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *

X = VarPattern("x")
Y = VarPattern("y")
Z = VarPattern("z")

# The main game world!
world = World()

# A convenience function
def def_obj(name, type) :
    world.add_relation(IsA(name, type))

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
    kind = world.query_relation(IsA(x, Z))
    if not kind :
        return False
    else :
        return world.r_path_to(KindOf, kind[0]["z"], y)

###
### Defining basic objects
###

# All objects have a name
Name = make_property(1, "Name")
@world.handler(Name(X))
def default_Name(x, world) :
    handler_requires(world[IsA(x, "thing")])
    return str(x)

# All objects have a description
Description = make_property(1, "Description")
world[Description(X)] = "It does't seem that interesting."

# All objects have a list of words which can describe them
Words = make_property(1, "Words")
@world.handler(Words(X))
def default_Words(x, world) :
    words = world[Name(x)].split()
    words[-1] = "@"+words[-1]
    return words

@world.to("get_words")
def get_words_Default(x, world) :
    raise ActionHandled(*world[Words(x)])

# There's also the printed name of the object
PrintedName = make_property(1, "PrintedName")
@world.handler(PrintedName(X))
def default_PrintedName(x, world) :
    return world[Name(x)]

Contents = make_property(1, "Contents")
@world.handler(Contents(X))
def container_contents(x, world) :
    handler_requires(IsA(x, "container"))
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

# Rooms

Enterable = make_property(1, "Enterable")
@world.handler(Enterable(X))
def default_enterable(x, world) :
    return False

@world.handler(Enterable(X))
def room_enterable(x, world) :
    handler_requires(IsA(x, "room"))
    return True

@world.handler(Contents(X))
def room_contents(x, world) :
    handler_requires(IsA(x, "room"))
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

# action.describe_room
@world.to("describe_room")
def describe_room_Heading(x, world) :
    world.actions.describe_room_heading(x)

@world.to("describe_room")
def describe_room_Description(x, world) :
    print "\n\n"+world[Description(x)]

@world.to("describe_room")
def describe_room_Objects(x, world) :
    obs = world[Contents(x)]
    if obs :
        print "\n"+repr(obs)

# action.describe_room_heading
@world.to("describe_room_heading")
def describe_room_heading_Name(x, world) :
    print world[Name(x)],

@world.to("describe_room_heading")
def describe_room_location(x, world) :
    r = world.query_relation(Contains(Y, x), Y)
    if r and world[Enterable(r[0])]:
        print "(in",world[Name(r[0])]+")",
