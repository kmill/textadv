# actionsystem.py
#
# A bunch of rule tables for handling what to do with actions in the
# game.  These are assumed to be used in a player context.

from textadv.core.patterns import BasicPattern
from textadv.core.rulesystem import ActivityTable, RuleTable, AbortAction, make_rule_decorator
from textadv.gamesystem.utilities import str_with_objs

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
            raise Exception("Pattern requires exactly "+str(self.numargs)+" arguments.")
    def update_actor(self, newactor) :
        """Sometimes the actor is not set properly (for instance, with
        AskingTo).  We need to be able to reset it."""
        self.args = list(self.args)
        self.args[0] = newactor
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
                dobj = str_with_objs("[the $x]", x=self.args[1])
            else :
                dobj = self.args[1]
            return self.gerund + " " + dobj
        elif len(self.args) == 3 :
            if self.dereference_dobj :
                dobj = str_with_objs("[the $x]", x=self.args[1])
            else :
                dobj = self.args[1]
            if self.dereference_iobj :
                iobj = str_with_objs("[the $x]", x=self.args[2])
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
                dobj = str_with_objs("[the $x]", x=self.args[1])
            else :
                dobj = self.args[1]
            return self.verb + " " + dobj
        elif len(self.args) == 3 :
            if self.dereference_dobj :
                dobj = str_with_objs("[the $x]", x=self.args[1])
            else :
                dobj = self.args[1]
            if self.dereference_iobj :
                iobj = str_with_objs("[the $x]", x=self.args[2])
            else :
                iobj = self.args[1]
            return (self.verb[0] + " " + dobj + " " + self.verb[1] + " " + iobj)
        else :
            raise Exception("Default gerund form only works with 1-3 args")
###
### Handling actions
###

class ActionSystem(object) :
    def __init__(self) :
        self.action_verify = RuleTable(doc="""Handles verifying actions for being
        at least somewhat logical. Should not change world state.""")
        self.action_trybefore = RuleTable(doc="""Handles a last attempt to make
        the action work (one shouldn't work with this table directly).""")
        self.action_before = RuleTable(doc="""Checks an action to see if it is
        even possible (opening a door is logical, but it's not immediately
        possible to open a locked door)""")
        self.action_when = RuleTable(doc="""Carries out the action.  Must not fail.""")
        self.action_report = RuleTable(doc="""Explains what happened with this
        action.  Should not change world state.""")
        self.verify = make_rule_decorator(self.action_verify)
        self.trybefore = make_rule_decorator(self.action_trybefore)
        self.before = make_rule_decorator(self.action_before)
        self.when = make_rule_decorator(self.action_when)
        self.report = make_rule_decorator(self.action_report)
    def verify_action(self, action, ctxt) :
        """Returns either the best reason for doing the action, or, if
        there is a reason not to do it, the worst."""
        reasons = self.action_verify.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
        reasons = [r for r in reasons if r is not None]
        reasons.sort(key=lambda x : x.score)
        if len(reasons) == 0 :
            return LogicalOperation()
        else :
            if not reasons[0].is_acceptible() :
                return reasons[0]
            else :
                return reasons[-1]
    def run_action(self, action, ctxt, is_implied=False, write_action=False, silently=False) :
        """Runs an action by the following steps:
        * Verify - if the action is not reasonable, then the action fails
        * Trybefore - just tries to make the world in the right state for Before to succeed.
        * Before - checks if the action is possible.  May throw DoInstead to redirect execution.
        * When - carries out the action.
        * Report - reports the action.  Executes if the silently flag is False.

        is_implied, if true forces a description of the action to be
        printed.  Also (should) prevent possibly dangerous actions
        from being carried out.

        write_action is a boolean or a string such as "(first %s)".
        If considered to be true, then describes action.

        silently, if true, prevents reporting the action."""
        if (write_action or is_implied) :
            if write_action is True : write_action = "(%s)"
            ctxt.write(write_action % action.gerund_form(ctxt))
            ctxt.write("[newline]")
        reasonable = self.verify_action(action, ctxt)
        if not reasonable.is_acceptible() :
            ctxt.write(reasonable.reason)
            raise AbortAction()
        self.action_trybefore.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
        try :
            self.action_before.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
        except DoInstead as ix :
            msg = False if ix.suppress_message or silently else "(%s instead)"
            self.run_action(ix.instead, ctxt, write_action=msg)
            return
        did_something = self.action_when.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
        #if not did_something :
        #    raise AbortAction("There was nothing to do.") # this doesn't seem to be the right thing to do.
        if not silently :
            self.action_report.notify(action, {"ctxt" : ctxt}, {"world" : ctxt.world})
    def do_first(self, action, ctxt, silently=False) :
        """Runs an action with a "(first /doing something/)" message.
        If silently is True, then this message is not printed."""
        self.run_action(action, ctxt=ctxt, is_implied=True, write_action="(first %s)", silently=silently)
    def copy(self) :
        """Returns a copy which behaves like the original, but for
        which modifications do not change the original."""
        newat = ActionSystem()
        newat.action_verify = self.action_verify.copy()
        newat.action_trybefore = self.action_trybefore.copy()
        newat.action_before = self.action_before.copy()
        newat.action_when = self.action_when.copy()
        newat.action_report = self.action_report.copy()
        return newat
    def make_documentation(self, escape, heading_level=1) :
        hls = str(heading_level)
        print "<h"+hls+">Event system</h"+hls+">"
        print "<p>This is the documentation for the event system.</p>"
        def _make_action_docs(heading_level, table, heading) :
            shls = str(heading_level+1)
            print "<h"+shls+">"+heading+"</h"+shls+">"
            table.make_documentation(escape, heading_level=heading_level+2)
        _make_action_docs(heading_level, self.action_verify, "action_verify")
        _make_action_docs(heading_level, self.action_trybefore, "action_trybefore")
        _make_action_docs(heading_level, self.action_before, "action_before")
        _make_action_docs(heading_level, self.action_when, "action_when")
        _make_action_docs(heading_level, self.action_report, "action_report")


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

class IllogicalNotVisible(BasicVerify) :
    """For when the thing is illogical because it can't be seen.
    Meant to prevent unseemly disambiguations because of objects not
    presently viewable.  These kinds of verify objects are special
    cased in the parser."""
    def __init__(self, reason) :
        self.score = 0
        self.reason = reason

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
    return BasicVerify(10, reason)
def NonObviousOperation() :
    """To prevent automatically doing an operation."""
    return BasicVerify(99, "Non-obvious.")

##
## Redirecting action execution
##

class DoInstead(Exception) :
    """A "before" event handler can raise this to abort the current
    action and instead do the action in the argument."""
    def __init__(self, instead, suppress_message=False) :
        self.instead = instead
        self.suppress_message = suppress_message

def verify_instead(action, ctxt) :
    """Used when it's necessary to verify another action because it's
    known that a before handler is going to throw a DoInstead."""
    raise ActionHandled(verify_action(action, ctxt))
