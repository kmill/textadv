# basiclibrary.py
#
# This is the basic library for how the world works.

from textadv.core.patterns import VarPattern, BasicPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults, NotHandled, AbortAction, make_rule_decorator
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *
from textadv.gamesystem.gamecontexts import ActorActivities
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.utilities import *
#import textadv.gamesystem.parser as parser
from textadv.gamesystem.parser import default_parser
from textadv.gamesystem.actionsystem import BasicAction, DoInstead, verify_instead, ActionSystem
from textadv.gamesystem.actionsystem import VeryLogicalOperation, LogicalOperation, IllogicalOperation, IllogicalInaccessible, NonObviousOperation

###
### The main game world!
###
world = World()

actionsystem = ActionSystem()

verify = make_rule_decorator(actionsystem.action_verify)
trybefore = make_rule_decorator(actionsystem.action_trybefore)
before = make_rule_decorator(actionsystem.action_before)
when = make_rule_decorator(actionsystem.action_when)
report = make_rule_decorator(actionsystem.action_report)

parser = default_parser.copy()

actoractivities = ActorActivities()


###
### Global properties
###

@world.define_property
class Global(Property) :
    """Use Global("x") to get global variable "x"."""
    numargs = 1

###
### Directions
###

# Defines a subparser named "direction" which is loaded with basic
# directions and their one- or two-letter synonyms.

parser.define_subparser("direction", "Represents one of the directions one may go.")

def define_direction(direction, synonyms) :
    for synonym in synonyms :
        parser.understand(synonym, direction, dest="direction")

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


###
### Load in the rest of the library
###

# Why are these execfile'd rather than imported?  These files are very
# interdependent and need to be in the same namespace.  And, we can't
# have import statements in them between each other because that would
# cause double importing.  Eit.  Probably should do something with the
# "compile" function.

execfile("textadv/gameworld/basicrelations.py")
execfile("textadv/gameworld/basickinds.py")
execfile("textadv/gameworld/basicrules.py")
execfile("textadv/gameworld/basicactivities.py")
execfile("textadv/gameworld/basicactions.py")

##
# The default player
##

world.activity.def_obj("player", "person")
world[PrintedName("player")] = "[if [current_actor_is player]]yourself[else]the player[endif]"
world[ProperNamed("player")] = True
world[Words("player")] = ["yourself", "self", "AFGNCAAP"]
world[Description("player")] = """{Bob|cap} {is} an ageless, faceless,
gender-neutral, culturally-ambiguous adventure-person.  {Bob|cap}
{does} stuff sometimes."""
world[Reported("player")] = False
