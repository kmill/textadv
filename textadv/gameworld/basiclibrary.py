# basiclibrary.py
#
# This is the basic library for how the world works.

from textadv.core.patterns import VarPattern, BasicPattern
from textadv.core.rulesystem import handler_requires, ActionHandled, MultipleResults, NotHandled, AbortAction
from textadv.gamesystem.relations import *
from textadv.gamesystem.world import *
from textadv.gamesystem.gamecontexts import actoractivities, actorrules
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.utilities import *
import textadv.gamesystem.parser as parser
from textadv.gamesystem.parser import understand
from textadv.gamesystem.eventsystem import BasicAction, verify, trybefore, before, when, report, do_first
from textadv.gamesystem.eventsystem import VeryLogicalOperation, LogicalOperation, IllogicalOperation, IllogicalInaccessible, NonObviousOperation

###
### The main game world!
###
world = World()

# A convenience function
def def_obj(name, type) :
    world.add_relation(IsA(name, type))


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
