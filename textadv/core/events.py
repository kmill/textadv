# events.py
#
# event-based programming
#
# What's here:
# Exceptions: IrrelevantEventException, AbortAction, ActionHandled
# Classes: ActionTable
# Decorators: add_action, makeEventDecorator, makeEventPatternDecorator

from patterns import NoMatchException, PVar, BasicPattern, wantsPattern

class IrrelevantEventException(Exception) :
    """Raised when an event wants to prematurely exit.  Used to signal
    skipping without affecting anything."""
    pass
class AbortAction(Exception) :
    """Raised when an event wants to stop the action from being
    handled anymore.  Used to signal that something bad happened.
    Stores arguments so they may be used by the caller."""
    def __init__(self, *args, **kwargs) :
        self.args = args
        self.kwargs = kwargs
class ActionHandled(Exception) :
    """Raised when an event wants to stop the action from being
    handled anymore.  Used to signal that it's ok we're done."""
    pass

class ActionTable(object) :
    """The action table is a bunch of "actions" which are all
    functions which take an event and supplementary data.  The
    variables are applied to each function.  If the action doesn't
    care about the event, then it may raise IrrelevantEventException.
    If an event wants to stop all notification, then it should raise
    AbortAction.

    Actions are executed in reverse order.  That way, actions which
    are given later (and which are assumed to be more specific) get
    executed first."""
    def __init__(self) :
        self.actions = []
    def add_action(self, action) :
        self.actions.insert(0, action)
    def notify(self, event, **data) :
        """Notify the actions of the event until they are all handled,
        or an exception is thrown.  ActionHandled is caught by this
        method and will skip the rest of the action handling.  Returns
        True if there was some action which could handle the event."""
        ret = False
        try :
            for action in self.actions :
                try :
                    action(event, **data)
                    ret = True
                except IrrelevantEventException :
                    # I guess the action didn't care...
                    pass
            return ret
        except ActionHandled :
            return True
    def collect(self, event, **data) :
        """Notify the actions of the event, and return their outputs
        together as a list.  ActionHandled aborts the rest of the
        events, and then returns what was collected."""
        out = []
        try :
            for action in self.actions :
                try :
                    out.append(action(event, **data))
                except IrrelevantEventException :
                    pass
        except ActionHandled :
            pass
        return out
    def __repr__(self) :
        return "<ActionTable %r>" % self.actions

###
### Decorators
###
def add_action(table) :
    if not isinstance(table, ActionTable) :
        raise Exception("Action table must be ActionTable when adding action.")
    def _add_action(f) :
        table.add_action(f)
        return f
    return _add_action

def makeEventDecorator(table) :
    """Result is a decorator which is equivalent to
    add_action(table)."""
    if not isinstance(table, ActionTable) :
        raise Exception("Action table must be ActionTable for decorator.")
    return add_action(table)

def makeEventPatternDecorator(table, withoutkey=None) :
    """Result is a decorator which is equivalent to composing
     add_action(table) and wantsPattern(pattern) but returns the
     original function so the decorator can be chained."""
    if not isinstance(table, ActionTable) :
        raise Exception("Action table must be ActionTable for decorator.")
    def _make(pattern) :
        def __make(f) :
            patt_f = wantsPattern(pattern, withoutkey=withoutkey)(f)
            def __do_it(*input,**kinput) :
                """Rewrites NoMatchException as
                IrrelevantEventException."""
                try :
                    return patt_f(*input,**kinput)
                except NoMatchException as x :
                    raise IrrelevantEventException()
            table.add_action(__do_it)
            return f
        return __make
    return _make

###
### Tests
###

import unittest

class TestEvents(unittest.TestCase) :
    class PEnters(BasicPattern) :
        def __init__(self, actor, place) :
            self.args = [actor, place]
    class PBefore(BasicPattern) :
        def __init__(self, event) :
            self.args = [event]
    class PAfter(BasicPattern) :
        def __init__(self, event) :
            self.args = [event]

    def test_table(self) :
        table = ActionTable()
        when = makeEventPatternDecorator(table)
        test = []
        x = PVar("x")
        data = dict()
        data[1] = 1
        
        @when(self.PEnters("kyle", x))
        def action1(x, data) :
            data[1] += 1
            test.append("action1:"+x)

        @when(self.PAfter(self.PEnters("kyle", x)))
        @when(self.PBefore(self.PEnters("kyle", x)))
        def action2(x, data) :
            data[1] += 1
            test.append("action2:"+x)

        table.notify(self.PBefore(self.PEnters("kyle", "vestibule")), data=data)
        table.notify(self.PEnters("kyle", "vestibule"), data=data)
        table.notify(self.PAfter(self.PEnters("kyle", "vestibule")), data=data)
        self.assertEqual(test,
                         ["action2:vestibule","action1:vestibule", "action2:vestibule"])

    def test_stopping_test(self) :
        table = ActionTable()
        when = makeEventPatternDecorator(table)
        test = []
        x = PVar("x")
        
        @when(self.PEnters("kyle", x))
        def action1(x) :
            raise AbortAction()
            test.append("action1:"+x)

        @when(self.PAfter(self.PEnters("kyle", x)))
        @when(self.PBefore(self.PEnters("kyle", x)))
        def action2(x) :
            test.append("action2:"+x)

        try :
            table.notify(self.PBefore(self.PEnters("kyle", "vestibule")))
            table.notify(self.PEnters("kyle", "vestibule"))
            table.notify(self.PAfter(self.PEnters("kyle", "vestibule")))
        except AbortAction :
            self.assertEqual(test, ["action2:vestibule"])

if __name__=="__main__" :
    unittest.main(verbosity=2)
