###*
###* Actions by a person
###*

###
### Oft-used requirements on actions
###

def require_xobj_accessible(actionsystem, action) :
    """Adds a rule which ensures that x is accessible to the actor in
    the action."""
    @actionsystem.verify(action)
    @docstring("Ensures the object x in "+repr(action)+" is accessible to the actor.  Added by require_xobj_accessible.")
    def _verify_xobj_accessible(actor, x, ctxt, **kwargs) :
        if not ctxt.world[AccessibleTo(x, actor)] :
            if not ctxt.world[VisibleTo(x, actor)] :
                return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))
            else :
                return IllogicalOperation(as_actor("{Bob|cap} {can't} get to that.", actor=actor))

def require_xobj_visible(actionsystem, action) :
    """Adds a rule which ensures that x is visible to the actor in
    the action."""
    @actionsystem.verify(action)
    @docstring("Ensures the object x in "+repr(action)+" is visible to the actor.  Added by require_xobj_visible.")
    def _verify_xobj_visible(actor, x, ctxt, **kwargs) :
        if not ctxt.world[VisibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))

def require_xobj_held(actionsystem, action, only_hint=False, transitive=True) :
    """Adds rules which check if the object x is held by the actor in
    the action, and if only_hint is not true, then if the thing is not
    already held, an attempt is made to take it."""
    def __is_held(actor, x, ctxt) :
        if transitive :
            return actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)]
        else :
            return ctxt.world.query_relation(Has(actor, x))
    @actionsystem.verify(action)
    @docstring("Makes "+repr(action)+" more logical if object x is held by the actor.  Also ensures that x is accessible to the actor. Added by require_xobj_held.")
    def _verify_xobj_held(actor, x, ctxt, **kwargs) :
        if ctxt.world.query_relation(Has(actor, x)) :
            return VeryLogicalOperation()
        elif not ctxt.world[AccessibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))
    if only_hint :
        @actionsystem.before(action)
        @docstring("A check that the actor is holding the x in "+repr(action)+".  The holding may be transitive.")
        def _before_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {isn't} holding that.", actor=actor)
    else :
        @actionsystem.trybefore(action)
        @docstring("An attempt is made to take the object x from "+repr(action)+" if the actor is not already holding it")
        def _trybefore_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                ctxt.actionsystem.do_first(Take(actor, x), ctxt=ctxt)
            # just in case it succeeds, but we don't yet have the object
            if transitive :
                can_do = (actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)])
            else :
                can_do = ctxt.world.query_relation(Has(actor, x))
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {doesn't} have that.", actor=actor)

def hint_xobj_notheld(actionsystem, action) :
    """Adds a rule which makes the action more logical if x is not
    held by the actor of the action."""
    @actionsystem.verify(action)
    @docstring("Makes "+repr(action)+" more logical if object x is not held by the actor.  Added by hint_xobj_notheld.")
    def _verify_xobj_notheld(actor, x, ctxt, **kwargs) :
        if not ctxt.world.query_relation(Has(actor, x)) :
            return VeryLogicalOperation()

###
### Action definitions
###

##
# Look
##

class Look(BasicAction) :
    """Look(actor)"""
    verb = "look"
    gerund = "looking"
    numargs = 1
parser.understand("look/l", Look(actor))

@when(Look(actor))
def when_look_default(actor, ctxt) :
    ctxt.activity.describe_current_location()

##
# Inventory
##

class Inventory(BasicAction) :
    """Inventory(actor)"""
    verb = "take inventory"
    gerund = "taking out inventory"
    numargs = 1
parser.understand("inventory/i", Inventory(actor))

@when(Inventory(actor))
def when_inventory(actor, ctxt) :
    possessions = ctxt.world[Contents(actor)]
    if possessions :
        ctxt.write("{Bob|cap} {is} carrying:")
        for p in possessions :
            ctxt.activity.describe_possession(actor, p, 1)
    else :
        ctxt.write("{Bob|cap} {is} carrying nothing.")

##
# Examine
##

class Examine(BasicAction) :
    """Examine(actor, x)"""
    verb = "examine"
    gerund = "examining"
    numargs = 2
parser.understand("examine/x [something x]", Examine(actor, X))

require_xobj_visible(actionsystem, Examine(actor, X))

@when(Examine(actor, X))
def when_examine_default(actor, x, ctxt) :
    ctxt.activity.describe_object(actor, x)

##
# Taking
##

class Take(BasicAction) :
    """Take(actor, obj_to_take)"""
    verb = "take"
    gerund = "taking"
    numargs = 2
parser.understand("take/get [something x]", Take(actor, X))
parser.understand("pick up [something x]", Take(actor, X))

require_xobj_accessible(actionsystem, Take(actor, X))
hint_xobj_notheld(actionsystem, Take(actor, X))

@before(Take(actor, X))
def before_take_when_already_have(actor, x, ctxt) :
    """You can't take what you already have."""
    if ctxt.world.query_relation(Has(actor, x)) :
        raise AbortAction("{Bob|cap} already {has} that.", actor=actor)

@before(Take(actor, X))
def before_take_check_ownership(actor, x, ctxt) :
    """You can't take what is owned by anyone else."""
    owner = ctxt.world[Owner(x)]
    if owner and owner != actor :
        raise AbortAction("That is not {bob's} to take.", actor=actor)

@before(Take(actor, X))
def before_take_check_fixedinplace(actor, x, ctxt) :
    """One cannot take what is fixed in place."""
    if ctxt.world[FixedInPlace(x)] :
        raise AbortAction("That's fixed in place.")

@before(Take(actor, X))
def before_take_check_not_self(actor, x, ctxt) :
    """One cannot take oneself."""
    if actor == x :
        raise AbortAction("{Bob|cap} cannot take {himself}.", actor=actor)

@before(Take(actor, X) <= IsA(X, "person"))
def before_take_check_not_other_person(actor, x, ctxt) :
    """One cannot take other people."""
    if actor != x :
         raise AbortAction(str_with_objs("[The $x] doesn't look like [he $x]'d appreciate that.", x=x))

@before(Take(actor, X))
def before_take_check_not_inside(actor, x, ctxt) :
    """One cannot take what one is inside or on.  Assumes there is a
    room at the top of the heirarchy of containment and support."""
    loc = ctxt.world[Location(actor)]
    while not ctxt.world[IsA(loc, "room")] :
        if loc == x :
            if ctxt.world[IsA(x, "container")] :
                raise AbortAction(str_with_objs("{Bob|cap}'d have to get out of [the $x] first.", x=x), actor=actor)
            elif ctxt.world[IsA(x, "supporter")] :
                raise AbortAction(str_with_objs("{Bob|cap}'d have to get off [the $x] first.", x=x), actor=actor)
            else :
                raise Exception("Unknown object location type.")
        loc = ctxt.world[Location(loc)]

@when(Take(actor, X))
def when_take_default(actor, x, ctxt) :
    """Carry out the taking by giving it to the actor."""
    ctxt.world.activity.give_to(x, actor)


@report(Take(actor, X))
def report_take_default(actor, x, ctxt) :
    """Prints out the default "Taken." message."""
    ctxt.write("Taken.")

##
# Dropping
##

class Drop(BasicAction) :
    """Drop(actor, obj_to_drop)"""
    verb = "drop"
    gerund = "dropping"
    numargs = 2
parser.understand("drop [something x]", Drop(actor, X))

require_xobj_held(actionsystem, Drop(actor, X), only_hint=True)

@when(Drop(actor, X))
def when_drop_default(actor, x, ctxt) :
    """Carry out the dropping by moving the object to the location of
    the actor (if the location is a room or a container), but if the
    location is a supporter, the object is put on the supporter."""
    l = ctxt.world[Location(actor)]
    if ctxt.world[IsA(l, "supporter")] :
        ctxt.world.activity.put_on(x, ctxt.world[Location(actor)])
    else :
        ctxt.world.activity.put_in(x, ctxt.world[Location(actor)])

@report(Drop(actor, X))
def report_drop_default(actor, x, ctxt) :
    """Prints the default "Dropped." message."""
    ctxt.write("Dropped.")

##
# Going
##

class Go(BasicAction) :
    verb = "go"
    gerund = "going"
    dereference_dobj = False
    numargs = 2 # Go(actor, direction)
parser.understand("go [direction x]", Go(actor, X))
parser.understand("[direction x]", Go(actor, X))

class AskTo(BasicAction) :
    verb = ("ask", "to")
    gerund = ("asking", "to")
    numargs = 3
    def gerund_form(self, ctxt) :
        dobj = ctxt.world.get_property("DefiniteName", self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.gerund[0] + " " + dobj + " to " + comm
    def infinitive_form(self, ctxt) :
        dobj = ctxt.world.get_property("DefiniteName", self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.verb[0] + " " + dobj + " to " + comm
parser.understand("ask [something x] to [action y]", AskTo(actor, X, Y))

class GiveTo(BasicAction) :
    verb = ("give", "to")
    gerund = ("giving", "to")
    numargs = 3
parser.understand("give [something x] to [something y]", GiveTo(actor, X, Y))

class Destroy(BasicAction) :
    verb = "destroy"
    gerund = "destroying"
    numargs = 2
parser.understand("destroy [something x]", Destroy(actor, X))

@when(Destroy(actor, X))
def when_destroy(actor, x, ctxt) :
    ctxt.world.activity.remove_obj(x)

@report(Destroy(actor, X))
def report_destroy(actor, x, ctxt) :
    ctxt.write("*Poof*")

class Open(BasicAction) :
    verb = "open"
    gerund = "opening"
    numargs = 2
parser.understand("open [something x]", Open(actor, X))

require_xobj_accessible(actionsystem, Open(actor, X))

@when(Open(actor, X))
def when_open(actor, x, ctxt) :
    ctxt.world[IsOpen(x)] = True

@report(Open(actor, X))
def report_open(actor, x, ctxt) :
    ctxt.write("Opened.")
