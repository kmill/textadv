# cloak.py
#
# Cloak of Darkness (http://www.firthworks.com/roger/cloak)

from textadv.basicsetup import *

world[Global("game_title")] = "Cloak of Darkness"
world[Global("game_author")] = "Kyle Miller (adapted from http://www.firthworks.com/roger/cloak)"
world[Global("game_description")] = """Walking along, you come across
the abandoned Opera House.  You wonder what's inside."""

world.activity.put_in("player", "Foyer")

world.activity.def_obj("cloak", "thing")
world[Name("cloak")] = "black velvet cloak"
world[Description("cloak")] = "It seems to be light-absorbent."
world[IsWearable("cloak")] = True
world.activity.make_wear("player", "cloak")

### The Foyer

world.activity.def_obj("Foyer", "room")
world[Description("Foyer")] = """This is the foyer of the Opera House.
There's nothing and no one to see.  There are exits to the south,
west, and north, but northward looks questionable."""

world.activity.connect_rooms("Foyer", "south", "Bar")
world.activity.connect_rooms("Foyer", "west", "Cloakroom")
world[NoGoMessage("Foyer", "north")] = """That way is much too decrepit to pass through."""

### The Bar

world.activity.def_obj("Bar", "room")

@world.handler(ContainsLight("Bar"))
def light_in_bar(world) :
    loc = world[Location("cloak")]
    if loc in ["Cloakroom", "small brass hook"] :
        return True
    else : return False

### The Cloakroom

world.activity.def_obj("Cloakroom", "room")

world.activity.def_obj("small brass hook", "supporter")
world.activity.put_in("small brass hook", "Cloakroom")
parser.understand("hang [object cloak] on/off [object small brass hook]", PlacingOn(actor, "cloak", "small brass hook"))
