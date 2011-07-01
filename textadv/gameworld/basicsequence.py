### Not to be imported
## Should be execfile'd

# basicsequence.py

# This represents the basic sequence of events occuring over the
# entire game, and over a single turn.

actoractivities.define_activity("start_game",
                                doc="""Runs when the game begins.""")

world[Global("game_title")] = "(set title with Global(\"game_title\"))"
world[Global("game_headline")] = "An Interactive Fiction"
world[Global("game_author")] = "(set author with Global(\"game_author\"))"
world[Global("release_number")] = 1
world[Global("game_description")] = None

@actoractivities.to("start_game")
def act_start_game_describe_game(ctxt) :
    """Prints out the description of the game using global variables
    defined in basicsequence.py."""
    gd = ctxt.world[Global("game_description")]
    if gd :
        ctxt.write(gd+"[newline]")
    ctxt.write(ctxt.world[Global("game_title")]+"[break]")
    ctxt.write(ctxt.world[Global("game_headline")], "by", ctxt.world[Global("game_author")])
    ctxt.write("[break]Release number", str(ctxt.world[Global("release_number")]), "[newline]")

@actoractivities.to("start_game")
def act_start_game_describe_location(ctxt) :
    """Describes the current location, and, using the actor of the
    context, also sets variables for knowing when to give a new room
    description."""
    ctxt.activity.describe_current_location()
    ctxt.world[Global("last_location")] = ctxt.world[Global("current_location")]
    ctxt.world[Global("last_light")] = ctxt.world[Global("currently_lit")]

world[Global("game_started")] = False

@actoractivities.to("start_game")
def act_start_game_done(ctxt) :
    """Sets a global variable signifying the game has started (so we don't run start_game again)."""
    ctxt.world[Global("game_started")] = True


actoractivities.define_activity("step_turn",
                                doc="""To be run after the player context has run an action.""")

@actoractivities.to("step_turn")
def act_step_turn_check_current_location(ctxt) :
    """Gives a description of the current location if either the room
    or the light conditions have changed from last turn."""
    last_location = ctxt.world[Global("last_location")]
    current_location = ctxt.world[VisibleContainer(ctxt.world[Location(ctxt.actor)])]
    last_light = ctxt.world[Global("last_light")]
    currently_lit = ctxt.world[ContainsLight(current_location)]
    if current_location != last_location or last_light != currently_lit :
        ctxt.write("[newline]")
        ctxt.activity.describe_current_location()
    ctxt.world[Global("last_location")] = ctxt.world[Global("current_location")]
    ctxt.world[Global("last_light")] = ctxt.world[Global("currently_lit")]
