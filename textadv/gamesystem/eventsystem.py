# eventsystem.py
#
# Handles the main game event flow.  The actual events and actions are
# implemented in basicevents.py.  This system assumes the context is
# an ActorContext.  The two main sections are Actions and Events.
# Everything is attached to an ActionTable within this module.
#
# Provides:
# decorators: verify, trybefore, when, before, after
# verify objects
# functions: verify_function, run_action, do_first
# class: BasicAction
# event objects

from textadv.core.events import AbortAction, ActionHandled
from textadv.core.events import ActionTable, makeEventPatternDecorator
from textadv.core.patterns import BasicPattern

# basic definitions:

_event_table = ActionTable()
when = makeEventPatternDecorator(_event_table, withoutkey="data")

def event_notify(event, context) :
    """Low-level method to communicate with event_table.  Sets up
    proper data variables for actions and events."""
    return _event_table.notify(event, data={"world" : context.world}, context=context)

####
##
## Actions
##
####

###
### Action stage wrappers (not to be used directly, see decorators)
###
class Verify(BasicPattern) :
    def __init__(self, event) :
        self.args = [event]
class TryBefore(BasicPattern) :
    def __init__(self, event) :
        self.args = [event]
class Before(BasicPattern) :
    def __init__(self, event) :
        self.args = [event]
class After(BasicPattern) :
    def __init__(self, event) :
        self.args = [event]

###
### Decorators for actions
###

def verify(pattern) :
    return when(Verify(pattern))
def trybefore(pattern) :
    return when(TryBefore(pattern))
def before(pattern) :
    return when(Before(pattern))
def after(pattern) :
    return when(After(pattern))

###
### Verify
###

class BasicVerify(object) :
    """An object returned by an action verifier.  The score is a value
    from 0 (completely illogical) to 100 (perfectly logical).  Higher
    values may be used to make an object more likely to be used when
    disambiguating."""
    LOGICAL_CUTOFF = 90
    def __init__(self, score, reason) :
        self.score = score
        self.reason = reason
    def is_acceptible(self) :
        return self.score >= self.LOGICAL_CUTOFF
    def __repr__(self) :
        return "<BasicVerify %r %r>" % (self.score, self.reason)

def VeryLogicalOperation() :
    """For operations which are particularly apt."""
    return BasicVerify(150, "Very good.")
def LogicalOperation() :
    """For when the operation is logical."""
    return BasicVerify(100, "All good.")
def IllogicalAlreadyOperation(reason) :
    """For when the operation is illogical because it's been already
    done."""
    return BasicVerify(60, reason)
def IllogicalInaccessible(obj) :
    """For when the operation is illogical because the object is
    inaccessible."""
    return BasicVerify(20, reason)
def IllogicalOperation(reason) :
    return BasicVerify(0, reason)
def NonObviousOperation() :
    """To prevent automatically doing an operation."""
    return BasicVerify(99, "Non-obvious.")

###
### for Before
###

class DoInstead(Exception) :
    """A "before" event handler can raise this to abort the current
    action and instead do the action in the argument."""
    def __init__(self, instead, suppress_message=False) :
        self.instead = instead
        self.suppress_message = suppress_message


###
### Running actions
###

def verify_action(action, context, suppress_do_instead=True) :
    """Check that an action is logical (which says nothing about
    possible).  Returns either the most logical reason for doing the
    action, or the least logical reason (using the hokey "logical
    score"), where if any illogical reasons exist, we say the action
    is illogical.  If a DoInstead is thrown, then we instead verify
    that action, but this does not change the action itself (so put it
    in a Before, too)."""
    try :
        reasons = _event_table.collect(Verify(action),
                                       data={"world" : context.world}, context=context)
        reasons = [r for r in reasons if r is not None]
        reasons.sort(key=lambda x : x.score)
        if len(reasons) == 0 :
            return LogicalOperation()
        else :
            if not reasons[0].is_acceptible() :
                return reasons[0]
            else :
                return reasons[-1]
    except DoInstead as do :
        if suppress_do_instead :
            return verify_action(do.instead, context)
        else :
            raise do


def run_action(action, context, is_implied=False, write_action=False) :
    """Tries to run an action.  If it is aborted by AbortAction, it
    raises AbortAction.  Stages:
    
    1) Verify action (run by parser to determine whether makes sense).
    Should not change game state.  Returns a BasicVerify object.
    Handlers are defined by @verify.  If a verify action raises
    DoInstead, then that action is checked in place of the current
    action.  If DoInstead is used, it is important to also fire
    DoInstead in the Before action.

    1.5) TryBefore action.  Do things before Before to try to get
    things into a good state. For instance, if an action needs a key
    in the hand, but the key can be picked up, then it should be
    picked up.  These are set by things like xobj_held (see
    basicevents.py)
    
    2) Before action.  May raise AbortAction if the action is bad, or
    DoInstead to instead try to do something else. Handlers are
    defined by @before.

    3) Do action.  Handlers are defined by @when.

    4) After action.  Handlers are defined by @after.
    """
    if write_action is True : write_action = "(%s)"
    if write_action or is_implied :
        context.write_line(write_action % action.gerund_form(context.world))
    try :
        reasonable = verify_action(action, context, suppress_do_instead=False)
    except DoInstead as ix :
        msg = False if ix.suppress_message else "(%s instead)"
        run_action(ix.instead, context=context, write_action=msg)
        return
    if not reasonable.is_acceptible() : # non-reasonable actions just don't work
        context.write_line(reasonable.reason)
        raise AbortAction()
    actor = context.world.get_obj(action.get_actor())
    if not actor.wants_to(action, context) :
        raise AbortAction()
    event_notify(TryBefore(action), context=context)
    try :
        event_notify(Before(action), context=context)
    except DoInstead as ix :
        msg = False if ix.suppress_message else "(%s instead)"
        run_action(ix.instead, context=context, write_action=msg)
        return
    did_something = event_notify(action, context=context)
    if not did_something :
        context.write_line("There was nothing to do.")
        raise AbortAction()
    event_notify(After(action), context=context)


def do_first(action, context) :
    """Does run_action, but makes it first print what it's doing as "(first doing whatever)"."""
    run_action(action, context=context, is_implied=True, write_action="(first %s)")

###
### The basic action.
###
class BasicAction(BasicPattern) :
    """All patterns which represent actions should subclass this
    object.  It importantly implements gerund_form, which should print
    something informative like "doing suchandsuch with whatever"."""
    verb = "NEED VERB"
    gerund = "NEEDING GERUND"
    def get_actor(self) :
        """An accessor method for the actor of the action. Assumed to
        be first element."""
        return self.args[0]
    def get_do(self) :
        """An accessor method for the direct object of the action.
        Assumed to be the second element."""
        return self.args[1]
    def get_io(self) :
        """An accessor method for the indirect object of the action.
        Assumed to be the third element."""
        return self.args[2]
    def gerund_form(self, world) :
        if len(self.args) == 1 :
            return self.gerund
        elif len(self.args) == 2 :
            dobj = world.get_obj(self.args[1])
            return self.gerund + " " + dobj["definite_name"]
        elif len(self.args) == 3 :
            dobj = world.get_obj(self.args[1])
            iobj = world.get_obj(self.args[2])
            return (self.gerund[0] + " " + dobj["definite_name"]
                    + " " + self.gerund[1] + " " + iobj["definite_name"])
        else :
            raise Exception("Default gerund form only works with 1-3 args")

####
##
## Events
##
####

###
### Event definitions
###

# Events should be used with the @when decorator.

class BasicEvent(BasicPattern) :
    """An event is something which occurs at a game level, such as
    starting the game, or starting/ending a turn."""
    pass

class StartGame(BasicEvent) :
    def __init__(self) :
        self.args = []

class StartTurn(BasicEvent) :
    def __init__(self) :
        self.args = []

# Unclear how this is different from StartTurn
# class EndTurn(BasicEvent) :
#     def __init__(self) :
#         self.args = []

class EndGameWin(BasicEvent) :
    def __init__(self) :
        self.args = []

class EndGameLoss(BasicEvent) :
    def __init__(self) :
        self.args = []

class ExitGame(BasicEvent) :
    def __init__(self) :
        self.args = []

# mechanism to finish the game:

class GameIsEnding(Exception) :
    def __init__(self, msg) :
        self.msg = msg

def finish_game(endgameobj) :
    raise GameIsEnding(endgameobj)
