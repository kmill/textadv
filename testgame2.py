# just a scrap idea of what should be the syntax

#from textadv.gameworld.basicrules import *
#from textadv.gamesystem.parser import *
#from textadv.gamesystem.utilities import *

from textadv.basiclibrary import *

def_obj("room0", "room")
world[Name("room0")] = "The Greater Room"

def_obj("room1", "room")
world[Name("room1")] = "The Great Test Room"
world[Description("room1")] = "You know, it's like a room and stuff."
world[ProvidesLight("room1")] = True
world.actions.move_to("room1", "room0")
world.actions.connect_rooms("room0", "out", "room1")

world.actions.move_to("player", "big box")

def_obj("red ball", "thing")
world[Description("red ball")] = "It's just a run-of-the-mill red ball."
world[Words("red ball")] = ["run-of-the-mill", "red", "@ball"]
world.actions.move_to("red ball", "room1")

def_obj("blue ball", "thing")
world[ProvidesLight("blue ball")] = False
world.actions.move_to("blue ball", "room1")

def_obj("big box", "container")
world[Name("big box")] = "big glass box"
world[IsOpaque("big box")] = False
world[Openable("big box")] = True
world[IsOpen("big box")] = False
world.actions.move_to("big box", "room1")

def_obj("whatchamacallit", "container")
world.actions.put_in("whatchamacallit", "big box")

#world.actions.describe_room("room1")

if False :
    print world[Openable("big box")]
    print world[IsOpen("big box")]
    print world[IsOpaque("big box")]
    print world[ProvidesLight("big box")]
    print world[IsLit("big box")]
    print world[EffectiveContainer("big box")]

from textadv.gamesystem.parser import *

@add_subparser("something")
def my_something(var, input, i, ctxt, actor, next) :
    if i < len(input) and input[i] == "woo" :
        return product([[Matched(input[i:i+1], "whatchamacallit", 2, var)]],
                       next(i+1))
    return []

print
print

game_context.actions.describe_current_location()


#print run_parser(parse_something, ["the", "run-of-the-mill", "ball"], world)
#print run_parser(parse_something, ["woo"], world)
