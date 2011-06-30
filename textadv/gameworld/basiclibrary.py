# basiclibrary.py
#
# This is the basic library for how the world works.

from textadv.core.patterns import VarPattern, BasicPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults, NotHandled, AbortAction, make_rule_decorator
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *
from textadv.gamesystem.gamecontexts import actoractivities, actorrules
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

world.define_activity("def_obj", doc="""Defines an object of a
particular kind in the game world.""")
@world.to("def_obj")
def default_def_obj(name, kind, world) :
    """Adds the relation IsA(name, kind)."""
    world.add_relation(IsA(name, kind))


###
### Global properties
###

@world.define_property
class Global(Property) :
    """Use Global("x") to get global variable "x"."""
    numargs = 1

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
