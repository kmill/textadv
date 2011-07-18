# rulesystem.py
#
# rule- and activity-based programming
#
# What's here:
# Exceptions: NotHandled, AbortAction, ActionHandled, MultipleResults, FinishWith, RestartWith
# Classes: ActionTable, PropertyTable, EventTable

from patterns import NoMatchException, AbstractPattern, BasicPattern, VarPattern

class AbortAction(Exception) :
    """Raised when a handler wants to stop the action from being
    handled anymore.  Used to signal that something bad happened.
    Stores arguments so they may be used by the caller."""
    def __init__(self, *args, **kwargs) :
        self.args = args
        self.kwargs = kwargs
class ActionHandled(Exception) :
    """Raised when a handler wants to stop the action from being
    handled anymore.  Used to signal that it's ok we're done."""
    pass

class MultipleResults(Exception) :
    """Raised when a handler has multiple values to return (for
    ActionTables with accumulators)."""
    pass

class FinishWith(Exception) :
    """Raised when a handler wants to return multiple values and also
    use the values accumulated so far (ActionHandled ignores the
    accumulated values)."""
    pass

class RestartWith(Exception) :
    """Raised when a handler wants to return multiple values and also
    overwrite the values accumulated so far (ActionHandled ignores the
    accumulated values)."""
    pass

class NotHandled(Exception) :
    """Raised when an event wants to prematurely exit.  Used to signal
    skipping without affecting anything."""
    pass

def handler_requires(b) :
    """A predicate which simply raises NotHandled if the argument is
    false."""
    if not b :
        raise NotHandled()

class PropertyTable(object) :
    """Represents a table of properties whose keys are patterns (for
    instance Description("myobj")).  Executes in reverse definition
    order, and the first successful result is returned."""
    def __init__(self) :
        self.properties = dict() # dict for some optimization
    def set_property(self, item, value, call=False) :
        if not isinstance(item, AbstractPattern) :
            raise Exception("The only properties may be AbstractPatterns.")
        if not self.properties.has_key(item.file_under()) :
            self.properties[item.file_under()] = [(item, value, call)]
        else :
            self.properties[item.file_under()].insert(0, (item, value, call))
    def __setitem__(self, item, value) :
        self.set_property(item, value)
    def get_property(self, item, data) :
        if not isinstance(item, BasicPattern) :
            raise Exception("The only properties may be BasicPatterns.")
        if not self.properties.has_key(item.file_under()) :
            raise KeyError(item)
        for key,value,call in self.properties[item.file_under()] :
            try :
                matches = key.match(item, data=data)
                if call :
                    for k,v in data.iteritems() :
                        matches[k] = v
                    return value(**matches)
                else :
                    return value
            except NoMatchException : # on these exceptions, just try next one
                pass
            except NotHandled :
                pass
        raise KeyError(item)
    def handler(self, item) :
        """This is a decorator to add a function which should be
        called when getting a property."""
        def __handler(f) :
            self.set_property(item, f, call=True)
            return f
        return __handler
    def dump(self) :
        for props in self.properties.itervalues() :
            for item, value, call in props :
                if call :
                    print repr(item)+" calls "+repr(value)
                else :
                    print repr(item)+" = "+repr(value)
    def copy(self) :
        """Returns a copy that behaves like the original by making a
        copy of the properties dictionary and puting the table items
        in new lists.  Values are not physically copied."""
        newtable = PropertyTable()
        newdict = dict()
        for t,table in self.properties.iteritems() :
            newdict[t] = list(table)
        newtable.properties = newdict
        return newtable
    def make_documentation(self, escape, heading_level=1) :
        import inspect
        hls = str(heading_level)
        props = self.properties.keys()
        props.sort(key=lambda x : x.__name__)
        for property in props :
            table = self.properties[property]
            print "<h"+hls+">"+escape(property.__name__)+"</h"+hls+">"
            print "<p>"+(escape(property.__doc__) or "<i>No documentation for property.</i>")+"</p>"
            if table :
                print "<ol>"
                for key,value,call in table :
                    print "<li><p>"+repr(key)
                    print ("<b>calls</b> <tt>"+escape(value.__name__)+"</tt>") if call else ("= "+escape(repr(value)))
                    print "</p>"
                    if call :
                        print "<p>"
                        print "<i>"+(escape(value.__doc__) or "(No documentation).")+"</i>"
                        try :
                            print "<small>(from <tt>"+inspect.getsourcefile(value)+"</tt>)</small>"
                        except TypeError :
                            pass
                        print "</p>"
                    print "</li>"
                print "</ol>"
            else :
                print "<p><i>No entries</i></p>"

def identity(x) : return x

class ActivityTable(object) :
    """Runs the functions one at a time until an AbortAction is raised
    or there are no more functions.  Functions are run in the order
    they were added to the ActivityTable, unless reverse is set to True.
    Accumulator is a function which takes the list of results to make
    a return value.  By default it's just the identity function.
    Unlike the other tables in the rulesystem, the functions are not
    selected by a pattern."""
    def __init__(self, accumulator=None, reverse=False, doc=None) :
        self.actions = []
        self.wants_table = []
        self.accumulator = accumulator or identity
        self.reverse = reverse
        self.doc = doc
        self.disabled = []
        self.current_disabled = None
        self.last_current_disabled = []
    def notify(self, args, data, disable=None) :
        self.__push_current_disabled(disable or [])
        acc = []
        for f, wt in zip(self.actions, self.wants_table) :
            if f in self.current_disabled :
                continue
            try :
                if wt :
                    acc.append(f(self, *args, **data))
                else :
                    acc.append(f(*args, **data))
            except NotHandled :
                pass
            except ActionHandled as ix :
                self.__pop_current_disabled()
                return self.accumulator(ix.args)
            except MultipleResults as ix :
                acc.extend(ix.args)
            except RestartWith as ix :
                acc = list(ix.args)
            except FinishWith as ix :
                self.__pop_current_disabled()
                return self.accumulator(acc + ix.args)
            except :
                self.__pop_current_disabled()
                raise
        self.__pop_current_disabled()
        return self.accumulator(acc)
    def add_handler(self, f, insert_first=None, insert_last=None, insert_before=None, insert_after=None,
                    wants_table=None) :
        """A function (which can be used as a decorator) which adds
        the function to the table.  At most one of the following may be set:
        * insert_first: puts the handler in a position so it executes first
        * insert_last: puts the handler in a position so it executes last
        * insert_before: puts the handler in a position so it executes immediately before the function in insert_before
        * insert_after: puts the handler in a position so it executes immediately after the function in insert_after

        Other settings:
        * wants_table_as: marks to give the table to the function as its first argument

        If none are set, then insert_first is default if reverse is true, otherwise it's insert_last."""
        if insert_first is None and insert_last is None and insert_before is None and insert_after is None :
            if self.reverse : insert_first=True
            else : insert_last=True
        if insert_first :
            self.actions.insert(0, f)
            self.wants_table.insert(0, wants_table)
        elif insert_last :
            self.actions.append(f)
            self.wants_table.append(wants_table)
        elif insert_before :
            i = self.actions.index(insert_before)
            self.actions.insert(i,f)
            self.wants_table.insert(i, wants_table)
        elif insert_after :
            i = self.actions.index(insert_before)
            self.actions.insert(i+1, f)
            self.wants_table.insert(i+1, wants_table)
        return f
    def disable(self, f=None) :
        """This disables a function in the activity table
        semi-permanently.  Should not be used once a game has
        started."""
        if self.current_disabled is not None :
            raise Exception("Should be using temp_disable.")
        if f :
            if f in self.actions :
                self.disabled.append(f)
            else :
                raise Exception("The given f=%r is not in the table." % f)
        else :
            raise Exception("No f given to disable.")
    def temp_disable(self, f=None) :
        """This disables a function temporarily during the execution
        of the table."""
        if f :
            if f in self.actions :
                self.current_disabled.append(f)
            else :
                raise Exception("The given f=%r is not in the table." % f)
        else :
            raise Exception("No f given to temporarily disable.")
    def temp_enable(self, f=None) :
        """This enables a function temporarily during the execution of
        the table.  Does not require the function to have been
        previously disabled."""
        if f :
            if f in self.current_disabled :
                self.current_disabled.remove(f)
        else :
            raise Exception("No f given to temporarily disable.")
    def __push_current_disabled(self, to_disable) :
        self.last_current_disabled.append(self.current_disabled)
        self.current_disabled = to_disable+self.disabled
    def __pop_current_disabled(self) :
        self.current_disabled = self.last_current_disabled.pop()
    def copy(self) :
        """Returns a copy which behaves like before, except the
        activity table has been suitably remade.  Values are stored in
        the new table by reference."""
        newtable = ActivityTable(accumulator=self.accumulator,
                                 reverse=self.reverse,
                                 doc=self.doc)
        newtable.actions = list(self.actions)
        newtable.wants_table = list(self.wants_table)
        newtable.disabled = list(self.disabled)
        return newtable
    def make_documentation(self, escape, heading_level=1) :
        import inspect
        print "<p>"
        if self.doc : print escape(self.doc)
        else : print "<i>(No documentation)</i>"
        print "</p><p>"
        if self.reverse : print "Runs in reverse-definition order."
        else : print "Runs in definition order."
        print "Accumulator: "
        print "<tt>"+escape(self.accumulator.__name__)+"</tt></p>"
        if self.actions :
            print "<ol>"
            for handler, wt in zip(self.actions, self.wants_table) :
                print "<li><p>"
                if handler in self.disabled :
                    print "<b><i>DISABLED</i></b>"
                print "<b>call</b> <tt>"+escape(handler.__name__)+"</tt>"
                if wt :
                    print "<b>with table</b>"
                try :
                    print "<small><i>(from <tt>"+inspect.getsourcefile(handler)+"</tt>)</i></small>"
                except TypeError :
                    pass
                print "</p>"
                print "<p><i>"+(escape(handler.__doc__) or "(No documentation).")+"</i>"
                print "</p>"
                print "</li>"
            print "</ol>"
        else :
            print "<p><i>No entries</i></p>"

class RuleTable(object) :
    """The rule table is a bunch of patterns and function pairs.
    OUT-OF-DATE DOCUMENTATION. The variables are applied to each
    function.  If the action doesn't care about the event, then it may
    raise NotHandled.  If an event wants to stop all notification,
    then it should raise AbortAction.

    Actions are executed in reverse order.  That way, actions which
    are given later (and which are assumed to be more specific) get
    executed first.

    This is basically an ActivityTable which also first pattern
    matches."""
    def __init__(self, accumulator=None, reverse=True, doc=None) :
        self.actions = {"default" : []} # default is for the tables not defined yet.
        self.accumulator = accumulator or identity
        self.reverse = reverse
        self.doc = doc
        self.disabled = []
        self.current_disabled = None
        self.last_current_disabled = []
    def add_handler(self, pattern, f, insert_first=None, insert_last=None, insert_before=None, insert_after=None, wants_event=False, wants_table=False) :
        """Adds (pattern, f) to the table.  At most one of the following may be set:
        * insert_first: puts the handler in a position so it executes first
        * insert_last: puts the handler in a position so it executes last
        * insert_before: puts the handler in a position so it executes immediately before the function in insert_before (ignoring pattern)
        * insert_after: puts the handler in a position so it executes immediately after the function in insert_after (ignoring pattern)

        If none are set, then insert_first is default if reverse is true, otherwise it's insert_last.

        If wants_event is true, then the event is also supplied to the function as its first argument.

        If wants_table is true, then the table itself is supplied as the next argument."""
        if insert_first is None and insert_last is None and insert_before is None and insert_after is None :
            if self.reverse : insert_first=True
            else : insert_last=True
        file_under = pattern.file_under()
        if issubclass(file_under, BasicPattern) :
            if file_under not in self.actions :
                self.actions[file_under] = list(self.actions["default"])
            destinations = [self.actions[file_under]]
        else :
            destinations = self.actions.values()
            
        for actions in destinations :
            if insert_first :
                actions.insert(0, (pattern, f, wants_event, wants_table))
            elif insert_last :
                actions.append((pattern, f, wants_event, wants_table))
            elif insert_before :
                for i in xrange(0, len(actions)) :
                    if actions[i][1] is insert_before : break
                else : raise Exception("insert_before failed, since %r not in table." % insert_before)
                actions.insert(i, (pattern, f, wants_event, wants_table))
            elif insert_after :
                for i in xrange(0, len(actions)) :
                    if actions[i][1] is insert_after : break
                else : raise Exception("insert_after failed, since %r not in table." % insert_after)
                actions.insert(i+1, (pattern, f, wants_event, wants_table))
    def notify(self, event, data, pattern_data=None, disable=None) :
        self.__push_current_disabled(disable or [])
        accum = []
        if not pattern_data :
            pattern_data = data
        for (pattern, f, wants_event, wants_table) in self.actions.get(event.file_under(), []) :
            if f in self.current_disabled :
                continue
            try :
                matches = pattern.match(event, data=pattern_data)
                for k,v in data.iteritems() :
                    matches[k] = v
                if wants_event :
                    if wants_table :
                        accum.append(f(event, self, **matches))
                    else :
                        accum.append(f(event, **matches))
                else :
                    if wants_table :
                        accum.append(f(self, **matches))
                    else :
                        accum.append(f(**matches))
            except NoMatchException :
                pass
            except NotHandled :
                pass
            except ActionHandled as ix :
                self.__pop_current_disabled()
                return self.accumulator(ix.args)
            except MultipleResults as ix :
                acc.extend(ix.args)
            except RestartWith as ix :
                acc = list(ix.args)
            except FinishWith as ix :
                self.__pop_current_disabled()
                return self.accumulator(acc + ix.args)
            except :
                self.__pop_current_disabled()
                raise
        return self.accumulator(accum)
    def __push_current_disabled(self, to_disable) :
        self.last_current_disabled.append(self.current_disabled)
        self.current_disabled = to_disable+self.disabled
    def __pop_current_disabled(self) :
        self.current_disabled = self.last_current_disabled.pop()
    def disable(self, f=None) :
        """This disables a function in the activity table
        semi-permanently.  Should not be used once a game has
        started."""
        if self.current_disabled is not None :
            raise Exception("Should be using temp_disable.")
        if f :
            if any(f==f0 for (p,f0,we,wt) in list_append(self.actions.values())) :
                self.disabled.append(f)
            else :
                raise Exception("The given f=%r is not in the table." % f)
        else :
            raise Exception("No f given to disable.")
    def temp_disable(self, f=None) :
        """This disables a function temporarily during the execution
        of the table."""
        if f :
            if any(f==f0 for (p,f0,we,wt) in list_append(self.actions.values())) :
                self.current_disabled.append(f)
            else :
                raise Exception("The given f=%r is not in the table." % f)
        else :
            raise Exception("No f given to temporarily disable.")
    def temp_enable(self, f=None) :
        """This enables a function temporarily during the execution of
        the table.  Does not require the function to have been
        previously disabled."""
        if f :
            if f in self.current_disabled :
                self.current_disabled.remove(f)
        else :
            raise Exception("No f given to temporarily disable.")
    def copy(self) :
        """Returns a copy which behaves like before, except the
        activity table has been suitably remade.  Values are stored in
        the new table by reference."""
        newtable = RuleTable(accumulator=self.accumulator,
                             reverse=self.reverse,
                             doc=self.doc)
        newtable.actions = dict()
        for key, actions in self.actions.iteritems() :
            newtable.actions[key] = list(actions)
        newtable.disabled = list(self.disabled)
        return newtable
    def make_documentation(self, escape, heading_level=1) :
        import inspect
        hls = str(heading_level)
        print "<p>"
        if self.doc : print escape(self.doc)
        else : print "<i>(No documentation)</i>"
        print "</p><p>"
        if self.reverse : print "Runs in reverse-definition order."
        else : print "Runs in definition order."
        print "Accumulator: "
        print "<tt>"+escape(self.accumulator.__name__)+"</tt></p>"
        if self.actions :
            for file_under,actions in self.actions.iteritems() :
                if file_under == "default" :
                    continue # we don't need to see anything about 'default'
                print "<h"+hls+">"+escape(file_under.__name__)+"</h"+hls+">"
                print "<p>"+(escape(file_under.__doc__) or "<i>No documentation for pattern.</i>")+"</p>"
                print "<ol>"
                for key,handler,we,wt in actions :
                    print "<li><p>"
                    if handler in self.disabled :
                        print "<b><i>DISABLED</i></b>"
                    print escape(repr(key))#+"<br>"
                    print "<b>calls</b> <tt>"+escape(handler.__name__)+"</tt>"
                    withs = []
                    if we :
                        withs.append("event")
                    if wt :
                        withs.append("table")
                    print "<b>with "+"and".join(withs)+"</b>"
                    try :
                        print "<small><i>(from <tt>"+inspect.getsourcefile(handler)+"</tt>)</i></small>"
                    except TypeError :
                        pass
                    print "</p>"
                    print "<p><i>"+(escape(handler.__doc__) or "(No documentation)")+"</i>"
                    print "</p>"
                    print "</li>"
                print "</ol>"
        else :
            print "<p><i>No entries</i></p>"

##
## A class for helping have many ActionTables and EventTables (see World)
##

class ActivityHelperObject(object) :
    def __init__(self, handler) :
        self.__handler__ = handler
    def __getattr__(self, name) :
        def _caller(*args, **kwargs) :
            return self.__handler__.call_activity(name, *args, **kwargs)
        return _caller

class RuleHelperObject(object) :
    def __init__(self, handler) :
        self.__handler__ = handler
    def __getattr__(self, name) :
        def _caller(*args, **kwargs) :
            return self.__handler__.call_rule(name, *args, **kwargs)
        return _caller

##
## A decorator
##

def make_rule_decorator(table) :
    def _deco(pattern, **kwargs) :
        def __deco(f) :
            table.add_handler(pattern, f, **kwargs)
            return f
        return __deco
    return _deco

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
