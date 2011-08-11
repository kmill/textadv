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
def act_start_game_move_backdrops(ctxt) :
    """Moves the backdrops to where they ought to be."""
    current_location = ctxt.world[VisibleContainer(ctxt.world[Location(ctxt.actor)])]
    ctxt.world.activity.move_backdrops(current_location)

@actoractivities.to("start_game")
def act_start_game_describe_game(ctxt) :
    """Prints out the description of the game using global variables
    defined in basicsequence.py."""
    gd = ctxt.world[Global("game_description")]
    if gd :
        ctxt.write(gd+"[newline]")
    ctxt.write("<span class=\"game_title\">"+ctxt.world[Global("game_title")]+"</span>"+"[break]")
    ctxt.write(ctxt.world[Global("game_headline")], "by", ctxt.world[Global("game_author")])
    ctxt.write("[break]Release number", str(ctxt.world[Global("release_number")]), "[newline]")
    ctxt.write("Type '[action help]' for help.[newline]")

@actoractivities.to("start_game")
def act_start_game_describe_location(ctxt) :
    """Describes the current location, and, using the actor of the
    context, also sets variables for knowing when to give a new room
    description."""
    ctxt.activity.describe_current_location(ctxt.actor)
    ctxt.world[Global("last_location")] = ctxt.world[Global("current_location")]
    ctxt.world[Global("last_light")] = ctxt.world[Global("currently_lit")]
    ctxt.world[Global("last_described_location")] = ctxt.world[Global("current_described_location")]

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
        ctxt.activity.player_has_moved()
    ctxt.world[Global("last_location")] = ctxt.world[Global("current_location")]
    ctxt.world[Global("last_light")] = ctxt.world[Global("currently_lit")]


actoractivities.define_activity("player_has_moved",
                                doc="""To be run during step_turn after the player has moved.""")

@actoractivities.to("player_has_moved")
def act_player_has_moved_update_backdrops(ctxt) :
    """Moves the backdrops to where they ought to be."""
    current_location = ctxt.world[VisibleContainer(ctxt.world[Location(ctxt.actor)])]
    ctxt.world.activity.move_backdrops(current_location)

world[Global("inhibit_location_description_when_moved")] = False

@actoractivities.to("player_has_moved")
def act_player_has_moved_describe_location(ctxt) :
    """Describes the current location after the player has moved, if
    the last described location isn't the current location."""
    if not ctxt.world[Global("inhibit_location_description_when_moved")] :
        current_location = ctxt.world[VisibleContainer(ctxt.world[Location(ctxt.actor)])]
        last_light = ctxt.world[Global("last_light")]
        currently_lit = ctxt.world[ContainsLight(current_location)]
        if ctxt.world[Global("current_described_location")] != current_location or last_light != currently_lit :
            ctxt.write("[newline]")
            ctxt.activity.describe_current_location(ctxt.actor)
    ctxt.world[Global("inhibit_location_description_when_moved")] = False


actoractivities.define_activity("end_game_saying",
                                doc="""Sets the end_game_message
                                global variable to the given message
                                to tell the current context to end the
                                game.""")

world[Global("end_game_message")] = None

@actoractivities.to("end_game_saying")
def act_end_game_saying_default(msg, ctxt) :
    """Sets the end_game_message global to its argument.  If the
    message is false, then it is by default "The end"."""
    ctxt.world[Global("end_game_message")] = msg if msg else "The end"


actoractivities.define_activity("end_game_actions",
                                doc="""Various actions to run when the
                                game is ending.  Includes writing the
                                end_game_message.  If one wants to
                                cancel ending a game, then one should
                                set the end_game_message to false.""")

@actoractivities.to("end_game_actions")
def act_end_game_actions_write_message(ctxt) :
    """Writes something like "*** You have won ***", depending on the
    end_game_message global variable."""
    if ctxt.world[Global("end_game_message")] :
        ctxt.write("[newline]<b>*** %s ***</b>[newline]" % ctxt.world[Global("end_game_message")])
