# just a scrap idea of what should be the syntax

#from textadv.gameworld.basicrules import *
#from textadv.gamesystem.parser import *
#from textadv.gamesystem.utilities import *

from textadv.basicsetup import *

world.activity.def_obj("room0", "room")
world[Name("room0")] = "The Greater Room"

world.activity.def_obj("room1", "room")
world[Name("room1")] = "The Great Test Room"
world[Description("room1")] = "You know, it's like a room and stuff."
world[ProvidesLight("room1")] = True
world.activity.connect_rooms("room0", "out", "room1")

world.activity.put_in("player", "big box")

world.activity.def_obj("red ball", "thing")
world[Description("red ball")] = "It's just a run-of-the-mill red ball."
world[Words("red ball")] = ["run-of-the-mill", "red", "@ball"]
world.activity.put_in("red ball", "room1")

world.activity.def_obj("blue ball", "thing")
world[ProvidesLight("blue ball")] = False
world.activity.put_in("blue ball", "big box")
#world[NotableDescription("blue ball")] = """There's this blue ball
#sitting there which is really catching your eye."""

world.activity.def_obj("big box", "container")
world[Name("big box")] = "big glass box"
world[Description("big box")] = "You wonder why anyone would make such a thing, but it's a gigantic glass box."
world[IsEnterable("big box")] = True
world[IsOpaque("big box")] = False
world[Openable("big box")] = True
world[IsOpen("big box")] = False
world.activity.put_in("big box", "room1")
world[NotableDescription("big box")] = """A big glass box is sitting here."""

world.activity.def_obj("whatchamacallit", "container")
world.activity.put_in("whatchamacallit", "big box")

world.activity.def_obj("oak table", "supporter")
world[Description("oak table")] = "It's a very old looking oak table which is in need of a refinishing."
world[Scenery("oak table")] = True
world.activity.put_in("oak table", "room1")

world.activity.def_obj("candlestick", "thing")
world.activity.put_on("candlestick", "oak table")

@actoractivities.to("terse_obj_description", insert_first=True)
def terse_obj_desc_disable_for_woo(actor, o, notables, mentioned, ctxt) :
    """Disables the container description for the whatchamacallit."""
    if o == "whatchamacallit" :
        ctxt.activity_table("terse_obj_description").temp_disable(f=terse_obj_description_container)
    raise NotHandled()

@before(Take(actor, "oak table"))
def cant_take_table(actor, ctxt) :
    raise AbortAction("It's much too heavy.")

#world.actions.describe_room("room1")

if False :
    print world[Openable("big box")]
    print world[IsOpen("big box")]
    print world[IsOpaque("big box")]
    print world[ProvidesLight("big box")]
    print world[IsLit("big box")]
    print world[EffectiveContainer("big box")]

from textadv.gamesystem.parser import *

@parser.add_subparser("something")
def my_something(parser, var, input, i, ctxt, actor, next) :
    if i < len(input) and input[i] == "woo" :
        return product([[Matched(input[i:i+1], "whatchamacallit", 2, var)]],
                       next(i+1))
    return []

print
print

game_context.activity.describe_current_location()


#print run_parser(parse_something, ["the", "run-of-the-mill", "ball"], world)
#print run_parser(parse_something, ["woo"], world)
