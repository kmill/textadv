# cloak.py
#
# Cloak of Darkness (http://www.firthworks.com/roger/cloak)

execfile("textadv/basicsetup.py")
#from textadv.basicsetup import *

world[Global("game_title")] = "Cloak of Darkness"
world[Global("game_author")] = "Kyle Miller (adapted from http://www.firthworks.com/roger/cloak)"
world[Global("game_description")] = """Hurrying through the rainswept
November night, you're glad to see the bright lights of the Opera
House.  It's surprising that there aren't more people about but, hey,
what do you expect in a cheap demo game..."""

world.activity.put_in("player", "Foyer")

## The Cloak

quickdef(world, "cloak", "thing", {
        Name : "black velvet cloak",
        Words : ["handsome", "dark", "black", "satin", "velvet", "@cloak"],
        Description : """A handsome cloak, of velvet trimmed with
        satin, and slightly splattered with raindrops.  Its blackness
        is so deep that it almost seems to suck light from the room.""",
        IsWearable : True,
        })
world.activity.make_wear("player", "cloak")

@before(Dropping(actor, "cloak") <= PNot(PEquals(Location(actor), "Cloakroom")))
@before(PlacingOn(actor, "cloak", X) <= PNot(PEquals(Location(actor), "Cloakroom")))
def can_drop_cloak_only_in_cloakroom(actor, ctxt, x=None) :
    raise AbortAction("This isn't the best place to leave a smart cloak lying around.")

### The Foyer

quickdef(world, "Foyer", "room", {
        Name : "Foyer of the Opera House",
        Description : """You are standing in a spacious hall,
        splendidly decorated in red and gold, with glittering
        chandeliers overhead. The entrance from the street is to the
        [dir north], and there are doorways [dir south] and [dir west].""",
        })

world.activity.connect_rooms("Foyer", "south", "Bar")
world.activity.connect_rooms("Foyer", "west", "Cloakroom")
world[NoGoMessage("Foyer", "north")] = """You've only just arrived,
and besides, the weather outside seems to be getting worse."""

### The Bar

quickdef(world, "Bar", "room", {
        Name : "Foyer bar",
        Description : """The bar, much rougher than you'd have guessed
        after the opulence of the foyer to the [dir north], is
        completely empty. There seems to be some sort of [ob message]
        scrawled in the sawdust on the floor.""",
        })

@world.handler(ContainsLight("Bar"))
def light_in_bar(world) :
    """If the cloak is not in the cloakroom or on the hook, then the
    bar contains no light."""
    return world[ContainingRoom("cloak")] == "Cloakroom"

## The message

quickdef(world, "message", "thing", {
        Words : ["sawdust", "saw", "@dust", "@message", "@floor"],
        Scenery : True
        })
world.activity.put_in("message", "Bar")

# message_disturbance represents how disturbed the message has gotten.
world[Global("message_disturbance")] = 0

@when(Examining(actor, "message"))
def read_message_to_end_game(actor, ctxt) :
    if ctxt.world[Global("message_disturbance")] > 1 :
        ctxt.write("""The message has been carelessly trampled, making
        it difficult to read.  You can just distinguish the
        words...""")
        ctxt.activity.end_game_saying("You have lost")
        raise ActionHandled()
    else :
        ctxt.write("""The message, neatly marked in sawdust,
        reads...""")
        ctxt.activity.end_game_saying("You have won")
        raise ActionHandled()
        

@before(X <= PEquals(Location("player"), "Bar") & PNot(ContainsLight("Bar")))
def before_anything_in_bar(x, ctxt) :
    """We match on any action while the player is in the bar.  We only
    let the Going action keep going north."""
    if type(x) == Going :
        if x.get_direction() != "north" :
            ctxt.world[Global("message_disturbance")] += 2
            raise AbortAction("Blundering around in the dark isn't a good idea!")
    elif type(x) in [Looking, TakingInventory] :
        raise NotHandled()
    else :
        ctxt.world[Global("message_disturbance")] += 1
        raise AbortAction("In the dark? You could easily disturb something!")

### The Cloakroom

quickdef(world, "Cloakroom", "room", {
        Description : """The walls of this small room were clearly
        once lined with [ob hooks], though now only one remains. The
        exit is a door to the [dir east].""",
        })

quickdef(world, "hook", "supporter", {
        Words : ["small", "brass", "@hook", "@peg", "@hooks"],
        Scenery : True,
        Description : """It's just a small brass hook, [if [when hook
        Supports cloak]]with a [ob cloak] hanging on it.[else]screwed
        to the wall.[endif]""",
        })
world.activity.put_in("hook", "Cloakroom")

parser.understand("hang [something x] on/off [object hook]", PlacingOn(actor, X, "hook"))

# By default, there is a description of the items on a supporter, but
# we describe these items in the hook description.  We only have one
# supporter in the game, so let's disable the activity.
actoractivities.activity_table("describe_object").disable(f=describe_object_supporter)
