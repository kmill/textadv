# basiclibrary.py
#
# imports everything you want to make a game

from textadv.core.rulesystem import NotHandled, AbortAction, ActionHandled, MultipleResults, FinishWith
from textadv.gamesystem.utilities import *
from textadv.gamesystem.relations import *
from textadv.gamesystem.gamecontexts import ActorContext, execute_context
from textadv.gameworld.basiclibrary import *
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

def quickdef(world, obname, kind, props={}) :
    """Defines an object with less typing.  The props argument is a
    dictionary of things like "Scenery: True", which is taken to mean
    "world[Scenery(obname)] = True"""
    world.activity.def_obj(obname, kind)
    for prop, val in props.iteritems() :
        world[prop(obname)] = val

def make_actorcontext_with_io(io_obj) :
    """Copies the game, and creates an ActorContext with the given io."""
    return ActorContext(None, io_obj, world.copy(), actionsystem.copy(), parser.copy(), actoractivities.copy(), "player")

def basic_begin_game(game_context) :
    """Just start up the game using the supplied context."""
    game_context.world.set_game_defined()
    execute_context(game_context)
