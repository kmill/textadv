# basiclibrary.py
#
# imports everything you want, and sets up the actor object, a world
# object, and an ActorContext

from textadv.core.rulesystem import NotHandled, AbortAction, ActionHandled, MultipleResults, FinishWith
#from textadv.core.patterns import PVar, PPred, TagPattern, BasicPattern
#from textadv.gamesystem.basicparser import understand, global_parser, parse_something
from textadv.gamesystem.utilities import *
from textadv.gamesystem.relations import *
#from textadv.gamesystem.basicpatterns import x, y, z, get_x, get_y, get_z
from textadv.gamesystem.gamecontexts import ActorContext, execute_context
#from textadv.gamesystem.eventsystem import *
from textadv.gameworld.basiclibrary import *
#from textadv.gameworld.basicevents import *
import textwrap
import re
import string
import sys

world = world.copy()
actionsystem = actionsystem.copy()
parser = parser.copy()
actoractivities = actoractivities.copy()

verify = make_rule_decorator(actionsystem.action_verify)
trybefore = make_rule_decorator(actionsystem.action_trybefore)
before = make_rule_decorator(actionsystem.action_before)
when = make_rule_decorator(actionsystem.action_when)
report = make_rule_decorator(actionsystem.action_report)

class TerminalGameIO(object) :
    """This class may be replaced in the GameContext by anything which
    implements the following two methods."""
    def get_input(self, prompt=">") :
        return raw_input("\n"+prompt + " ")
    def write(self, *data) :
        for d in data :
            print d.replace("[newline]", "\n\n").replace("[break]", "\n").replace("[indent]","  "),
        return
        paragraphs = re.split("\n\\s*\n", " ".join(data))
        to_print = []
        for p in paragraphs :
            fixed = " ".join([l.strip() for l in p.strip().split("\n")])
            one_p = []
            for f in fixed.split("<br>") :
                one_p.append("\n".join(textwrap.wrap(f)))
            to_print.append("\n".join(one_p))
        print string.replace("\n\n".join(to_print)+"\n", "&nbsp;", " ")

game_context = ActorContext(None, TerminalGameIO(), world, actionsystem, parser, actoractivities, "player")

def basic_begin_game(see_world_size=False) :
    """Just start up the game using the context defined in
    basiclibrary."""
    game_context.world.set_game_defined()
    execute_context(game_context)
