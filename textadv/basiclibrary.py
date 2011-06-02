# basiclibrary.py
#
# imports everything you want, and sets up the actor object, a world
# object, and an ActorContext

from textadv.core.world import World, obj_to_id
from textadv.core.events import AbortAction, ActionHandled
from textadv.core.patterns import PVar, PPred, TagPattern, BasicPattern
from textadv.gamesystem.basicparser import understand, global_parser, parse_something
from textadv.gamesystem.utilities import *
from textadv.gamesystem.relations import *
from textadv.gamesystem.basicpatterns import x, y, z, get_x, get_y, get_z
from textadv.gamesystem.gamecontexts import ActorContext, execute_context
#from textadv.gamesystem.eventsystem import *
from textadv.gameworld.basicobjects import *
from textadv.gameworld.basicevents import *
import textwrap
import re
import string

class TerminalGameIO(object) :
    """This class may be replaced in the GameContext by anything which
    implements the following two methods."""
    def get_input(self) :
        return raw_input("> ")
    def write_line(self, *data) :
        paragraphs = re.split("\n\\s*\n", " ".join(data))
        to_print = []
        for p in paragraphs :
            fixed = " ".join([l.strip() for l in p.strip().split("\n")])
            one_p = []
            for f in fixed.split("<br>") :
                one_p.append("\n".join(textwrap.wrap(f)))
            to_print.append("\n".join(one_p))
        print string.replace("\n\n".join(to_print)+"\n", "&nbsp;", " ")

world = World()

player = world.new_obj("player", Actor, "AFGNCAAP", """{Bob|cap} {is} an ageless, faceless, gender-neutral, culturally-ambiguous adventure-person.  {Bob|cap} {does} stuff sometimes.""")
player["words"] = ["self", "AFGNCAAP"]
player["reported"] = False

hands = world.new_obj("hands", BObject, "hands", "These are your very trusty hands.")
hands["definite_name"] = "your hands"
hands.give_to(player)
hands["reported"] = False

game_context = ActorContext(None, TerminalGameIO(), global_parser, world, "player")

def basic_begin_game(see_world_size=False) :
    """Just start up the game using the context defined in
    basiclibrary."""
    if see_world_size :
        print "World serialization is",len(world.serialize()),"bytes"
        import zlib
        print "World serialization is",len(zlib.compress(world.serialize())),"bytes compressed"
    execute_context(game_context)
