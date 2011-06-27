# eventsystem.py
#
# A bunch of rule tables for handling what to do in the game.  Many of
# these are assumed to be used in a player context.

from textadv.core.patterns import BasicPattern
from textadv.core.rulesystem import ActionTable, EventTable

###
### Actions
###

class BasicAction(BasicPattern) :
    """All patterns which represent actions should subclass this
    object.  It importantly implements gerund_form, which should print
    something informative like "doing suchandsuch with whatever"."""
    verb = "NEED VERB"
    gerund = "NEEDING GERUND"
    dereference_dobj = True
    dereference_iobj = True
    def __init__(self, *args) :
        if len(args) == self.numargs :
            self.args = args
        else :
            raise Exception("Pattern requires exactly "+self.numargs+" arguments.")
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
    def gerund_form(self, ctxt) :
        if len(self.args) == 1 :
            return self.gerund
        elif len(self.args) == 2 :
            if self.dereference_dobj :
                dobj = ctxt.world.get_property("DefiniteName", self.args[1])
            else :
                dobj = self.args[1]
            return self.gerund + " " + dobj
        elif len(self.args) == 3 :
            if self.dereference_dobj :
                dobj = ctxt.world.get_property("DefiniteName", self.args[1])
            else :
                dobj = self.args[1]
            if self.dereference_iobj :
                iobj = ctxt.world.get_property("DefiniteName", self.args[2])
            else :
                iobj = self.args[1]
            return (self.gerund[0] + " " + dobj + " " + self.gerund[1] + " " + iobj)
        else :
            raise Exception("Default gerund form only works with 1-3 args")

###
### Handling actions
###

action_verify = EventTable()
action_trybefore = EventTable()
action_before = EventTable()
action_when = EventTable()
action_report = EventTable()

def _make_action_decorator(table) :
    def _deco(pattern, **kwargs) :
        def __deco(f) :
            table.add_handler(pattern, f, **kwargs)
            return f
        return __deco
    return _deco

verify = _make_action_decorator(action_verify)
trybefore = _make_action_decorator(action_trybefore)
before = _make_action_decorator(action_before)
when = _make_action_decorator(action_when)
report = _make_action_decorator(action_report)


##
## for Verify
##

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
def IllogicalInaccessible(reason) :
    """For when the operation is illogical because the object is
    inaccessible."""
    return BasicVerify(20, reason)
def IllogicalOperation(reason) :
    return BasicVerify(0, reason)
def NonObviousOperation() :
    """To prevent automatically doing an operation."""
    return BasicVerify(99, "Non-obvious.")

##
## for Before
##

class DoInstead(Exception) :
    """A "before" event handler can raise this to abort the current
    action and instead do the action in the argument."""
    def __init__(self, instead, suppress_message=False) :
        self.instead = instead
        self.suppress_message = suppress_message

##
## Verifying the action
##

def verify_action(action, ctxt) :
    reasons = action_verify.notify(action, {"ctxt" : ctxt})
    reasons = [r for r in reasons if r is not None]
    reasons.sort(key=lambda x : x.score)
    if len(reasons) == 0 :
        return LogicalOperation()
    else :
        if not reasons[0].is_acceptible() :
            return reasons[0]
        else :
            return reasons[-1]

##
## Running the action
##

def run_action(action, ctxt, is_implied=False, write_action=False, silently=False) :
    if write_action is True : write_action = "(%s)"
    if (write_action or is_implied) and not silently :
        ctxt.write(write_action % action.gerund_form(ctxt))
        ctxt.write("[newline]")
    reasonable = verify_action(action, ctxt)
    if not reasonable.is_acceptible() :
        ctxt.write(reasonable.reason)
        raise AbortAction()
    action_trybefore.notify(action, {"ctxt" : ctxt})
    try :
        action_before.notify(action, {"ctxt" : ctxt})
    except DoInstead as ix :
        msg = False if ix.suppress_message or silently else "(%s instead)"
        run_action(ix.instead, ctxt, write_action=msg)
        return
    did_something = action_when.notify(action, {"ctxt" : ctxt})
    if not did_something :
        raise AbortAction("There was nothing to do.")
    action_report.notify(action, {"ctxt" : ctxt})

def do_first(action, ctxt, silently=False) :
    run_action(action, ctxt=ctxt, is_implied=True, write_action="(first %s)", silently=False)
