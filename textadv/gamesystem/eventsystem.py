# eventsystem.py
#
# A bunch of rule tables for handling what to do in the game.  Many of
# these are assumed to be used in a player context.

from textadv.core.patterns import BasicPattern
from textadv.core.rulesystem import ActionTable, EventTable, AbortAction

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
    def infinitive_form(self, ctxt) :
        """Doesn't prepend "to"."""
        if len(self.args) == 1 :
            return self.verb
        elif len(self.args) == 2 :
            if self.dereference_dobj :
                dobj = ctxt.world.get_property("DefiniteName", self.args[1])
            else :
                dobj = self.args[1]
            return self.verb + " " + dobj
        elif len(self.args) == 3 :
            if self.dereference_dobj :
                dobj = ctxt.world.get_property("DefiniteName", self.args[1])
            else :
                dobj = self.args[1]
            if self.dereference_iobj :
                iobj = ctxt.world.get_property("DefiniteName", self.args[2])
            else :
                iobj = self.args[1]
            return (self.verb[0] + " " + dobj + " " + self.verb[1] + " " + iobj)
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
    """Returns either the best reason for doing the action, or, if
    there is a reason not to do it, the worst."""
    reasons = action_verify.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
    reasons = [r for r in reasons if r is not None]
    reasons.sort(key=lambda x : x.score)
    if len(reasons) == 0 :
        return LogicalOperation()
    else :
        if not reasons[0].is_acceptible() :
            return reasons[0]
        else :
            return reasons[-1]

def verify_instead(action, ctxt) :
    """Used when it's necessary to verify another action because it's
    known that a before handler is going to throw a DoInstead."""
    raise ActionHandled(verify_action(action, ctxt))

##
## Running the action
##

def run_action(action, ctxt, is_implied=False, write_action=False, silently=False) :
    """Runs an action by the following steps:
    * Verify - if the action is not reasonable, then the action fails
    * Trybefore - just tries to make the world in the right state for Before to succeed.
    * Before - checks if the action is possible.  May throw DoInstead to redirect execution.
    * When - carries out the action.
    * Report - reports the action.  Executes if the silently flag is False.

    is_implied, if true forces a description of the action to be
    printed.  Also (should) prevent possibly dangerous actions from
    being carried out.

    write_action is a boolean or a string such as "(first %s)".  If
    considered to be true, then describes action.

    silently, if true, prevents reporting the action.
"""
    if (write_action or is_implied) and not silently :
        if type(write_action) is not str : write_action = "(%s)"
        ctxt.write(write_action % action.gerund_form(ctxt))
        ctxt.write("[newline]")
    reasonable = verify_action(action, ctxt)
    if not reasonable.is_acceptible() :
        ctxt.write(reasonable.reason)
        raise AbortAction()
    action_trybefore.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
    try :
        action_before.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
    except DoInstead as ix :
        msg = False if ix.suppress_message or silently else "(%s instead)"
        run_action(ix.instead, ctxt, write_action=msg)
        return
    did_something = action_when.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
    if not did_something :
        raise AbortAction("There was nothing to do.")
    if not silently :
        action_report.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})

def do_first(action, ctxt, silently=False) :
    run_action(action, ctxt=ctxt, is_implied=True, write_action="(first %s)", silently=False)

def make_documentation(escape, heading_level=1) :
    hls = str(heading_level)
    print "<h"+hls+">Event system</h"+hls+">"
    print "<p>This is the documentation for the event system.</p>"
    def _make_action_docs(heading_level, table, heading, desc) :
        shls = str(heading_level+1)
        print "<h"+shls+">"+heading+"</h"+shls+">"
        print "<p><i>"+desc+"</i></p>"
        table.make_documentation(escape, heading_level=heading_level+2)
    _make_action_docs(heading_level, action_verify, "action_verify",
                      "Handles verifying actions for being at least somewhat logical. Should not change world state.")
    _make_action_docs(heading_level, action_trybefore, "action_trybefore",
                      "Handles a last attempt to make the action work (one shouldn't work with this table directly).")
    _make_action_docs(heading_level, action_before, "action_before",
                      "Checks an action to see if it is even possible (opening a door is logical, but it's not immediately possible to open a locked door)")
    _make_action_docs(heading_level, action_when, "action_when",
                      "Carries out the action.  Must not fail.")
    _make_action_docs(heading_level, action_report, "action_report",
                      "Explains what happened with this action.  Should not change world state.")
