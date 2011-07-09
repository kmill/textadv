### Not to be imported
## Should be execfile'd

# basicactions.py

# These are handlers for actions a player may type (such as for "take
# [something]").

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
                effcont = ctxt.world[EffectiveContainer(ctxt.world[Location(x)])]
                if ctxt.world[Openable(effcont)] and not ctxt.world[IsOpen(effcont)] :
                    return IllogicalOperation(as_actor(str_with_objs("That's inside [the $y], which is closed.", y=effcont),
                                                       actor=actor))
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
    already held, an attempt is made to take it.  The transitive flag
    refers to allowing the actor be the owner of the object, and not
    necessarily holding onto it directly."""
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
        elif not ctxt.world[VisibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))
        elif not ctxt.world[AccessibleTo(x, actor)] :
            effcont = ctxt.world[EffectiveContainer(ctxt.world[Location(x)])]
            if ctxt.world[Openable(effcont)] and not ctxt.world[IsOpen(effcont)] :
                return IllogicalOperation(as_actor(str_with_objs("That's inside [the $y], which is closed.", y=effcont),
                                                   actor=actor))
            else :
                return IllogicalOperation(as_actor("{Bob|cap} {can't} get to that.", actor=actor))
    if only_hint :
        @actionsystem.before(action)
        @docstring("A check that the actor is holding the x in "+repr(action)+".  The holding may be transitive.")
        def _before_xobj_held(actor, x, ctxt, **kwargs) :
            if ctxt.world.query_relation(Wears(actor, x)) :
                raise AbortAction(str_with_objs("{Bob|cap} {is} wearing [the $x].", x=x), actor=actor)
            if not __is_held(actor, x, ctxt) :
                raise AbortAction(str_with_objs("{Bob|cap} {isn't} holding [the $x].", x=x), actor=actor)
    else :
        @actionsystem.trybefore(action)
        @docstring("An attempt is made to take the object x from "+repr(action)+" if the actor is not already holding it")
        def _trybefore_xobj_held(actor, x, ctxt, **kwargs) :
            if ctxt.world.query_relation(Wears(actor, x)) :
                raise AbortAction(str_with_objs("{Bob|cap} {is} wearing [the $x].", x=x), actor=actor)
            if not __is_held(actor, x, ctxt) :
                ctxt.actionsystem.do_first(Taking(actor, x), ctxt=ctxt, silently=True)
            # just in case it succeeds, but we don't yet have the object
            if transitive :
                can_do = (actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)])
            else :
                can_do = ctxt.world.query_relation(Has(actor, x))
            if not __is_held(actor, x, ctxt) :
                raise AbortAction(str_with_objs("{Bob|cap} {isn't} holding [the $x].", x=x), actor=actor)

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
# Help
##

class GettingHelp(BasicAction) :
    """GettingHelp(actor)"""
    verb = "get help"
    gerund = "getting help"
    numargs = 1
parser.understand("help", GettingHelp(actor))

@when(GettingHelp(actor))
def when_getting_help(actor, ctxt) :
    ctxt.write("""So you want help?

    [newline]You are controlling a character in a virtual world.  To
    play the game, you must give the character commands to interact
    with its surroundings.

    [newline]Some examples of commands one may try are the following:

    [newline]
    look ('l' for short)[break]
    inventory ('i' for short)[break]
    examine <i>something</i> ('x <i>something</i>' for short)[break]
    take <i>something</i>[break]
    drop <i>something</i>[break]
    put <i>something</i> in <i>something</i>[break]
    put <i>something</i> on <i>something</i>[break]
    go <i>direction</i> (or the first letter of the direction for short)[break]
    enter <i>something</i>[break]
    leave[break]
    open <i>something</i>[break]
    close <i>something</i>[break]
    unlock <i>something</i> with <i>something</i>[break]
    turn on <i>something</i>[break]
    ask <i>someone</i> about <i>something</i>[break]
    ask <i>someone</i> for <i>something</i>[break]
    give <i>something</i> to <i>someone</i>[break]

    [newline]This list is not exhaustive.  Part of the fun is figuring
    out what you can do.

    [newline]You may also click the underlined words to go in a
    direction or examine a particular object.

    [newline]If you get stuck, don't forget to examine things, as
    often times vital cluse are left in descriptions (this being a
    text-based game).

    [newline]For more help, take a look at <a
    href=\"http://eblong.com/zarf/if.html\"
    target=\"_blank\">http://eblong.com/zarf/if.html</a> for a
    reference card of perhaps-possible things to try.""")

##
# Look
##

class Looking(BasicAction) :
    """Looking(actor)"""
    verb = "look"
    gerund = "looking"
    numargs = 1
parser.understand("look/l/ls", Looking(actor))
parser.understand("look around", Looking(actor))

@when(Looking(actor))
def when_looking_default(actor, ctxt) :
    ctxt.activity.describe_current_location(actor)

##
# Inventory
##

class TakingInventory(BasicAction) :
    """TakingInventory(actor)"""
    verb = "take inventory"
    gerund = "taking out inventory"
    numargs = 1
parser.understand("inventory/i", TakingInventory(actor))

@when(TakingInventory(actor))
def when_takinginventory(actor, ctxt) :
    possessions = ctxt.world[Contents(actor)]
    if possessions :
        ctxt.write("{Bob|cap} {is} carrying:", actor=actor)
        for p in possessions :
            ctxt.activity.describe_possession(actor, p, 1)
    else :
        ctxt.write("{Bob|cap} {is} carrying nothing.", actor=actor)

##
# Examine
##

class Examining(BasicAction) :
    """Examining(actor, x)"""
    verb = "examine"
    gerund = "examining"
    numargs = 2
parser.understand("examine/x/read [something x]", Examining(actor, X))

require_xobj_visible(actionsystem, Examining(actor, X))

@when(Examining(actor, X))
def when_examining_default(actor, x, ctxt) :
    ctxt.activity.describe_object(actor, x)

##
# Taking
##

class Taking(BasicAction) :
    """Taking(actor, obj_to_take)"""
    verb = "take"
    gerund = "taking"
    numargs = 2
parser.understand("take/get [something x]", Taking(actor, X))
parser.understand("pick up [something x]", Taking(actor, X))

require_xobj_accessible(actionsystem, Taking(actor, X))
hint_xobj_notheld(actionsystem, Taking(actor, X))

@before(Taking(actor, X))
def before_take_when_already_have(actor, x, ctxt) :
    """You can't take what you already have.  Uses the contents of the
    player to figure this out."""
    if x in ctxt.world[Contents(actor)] :
        raise AbortAction("{Bob|cap} already {has} that.", actor=actor)

@before(Taking(actor, X))
def before_taking_check_ownership(actor, x, ctxt) :
    """You can't take what is owned by anyone else."""
    owner = ctxt.world[Owner(x)]
    if owner and owner != actor :
        raise AbortAction("That is not {bob's} to take.", actor=actor)

@before(Taking(actor, X))
def before_taking_check_fixedinplace(actor, x, ctxt) :
    """One cannot take what is fixed in place."""
    if ctxt.world[FixedInPlace(x)] :
        raise AbortAction(ctxt.world[NoTakeMessage(x)], actor=actor)

@before(Taking(actor, X))
def before_taking_check_if_part_of_something(actor, x, ctxt) :
    """One cannot take something which is part of something else."""
    assembly = ctxt.world.query_relation(PartOf(x, Y), var=Y)
    if assembly :
        raise AbortAction(str_with_objs("That's part of [the $y].", y=assembly[0]), actor=actor)

@before(Taking(actor, X))
def before_taking_check_not_self(actor, x, ctxt) :
    """One cannot take oneself."""
    if actor == x :
        raise AbortAction("{Bob|cap} cannot take {himself}.", actor=actor)

@before(Taking(actor, X) <= IsA(X, "person"))
def before_taking_check_not_other_person(actor, x, ctxt) :
    """One cannot take other people."""
    if actor != x :
         raise AbortAction(str_with_objs("[The $x] doesn't look like [he $x]'d appreciate that.", x=x))

@before(Taking(actor, X))
def before_taking_check_not_inside(actor, x, ctxt) :
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

@when(Taking(actor, X))
def when_taking_default(actor, x, ctxt) :
    """Carry out the taking by giving it to the actor."""
    ctxt.world.activity.give_to(x, actor)


@report(Taking(actor, X))
def report_taking_default(actor, x, ctxt) :
    """Prints out the default "Taken." message."""
    ctxt.write("Taken.")

##
# Dropping
##

class Dropping(BasicAction) :
    """Dropping(actor, obj_to_drop)"""
    verb = "drop"
    gerund = "dropping"
    numargs = 2
parser.understand("drop [something x]", Dropping(actor, X))

require_xobj_held(actionsystem, Dropping(actor, X), only_hint=True)

@before(Dropping(actor, X) <= PEquals(actor, X))
def before_dropping_self(actor, x, ctxt) :
    """One can't drop oneself."""
    raise AbortAction("{Bob|cap} can't be dropped.", actor=actor)

# @before(Dropping(actor, X))
# def before_dropping_worn_items(actor, x, ctxt) :
#     """One can't drop what's being worn."""
#     if ctxt.world.query_relation(Wears(actor, x)) :
#         raise AbortAction(str_with_objs("{Bob|cap} {is} wearing [the $x].", x=x), actor=actor)

@when(Dropping(actor, X))
def when_dropping_default(actor, x, ctxt) :
    """Carry out the dropping by moving the object to the location of
    the actor (if the location is a room or a container), but if the
    location is a supporter, the object is put on the supporter."""
    l = ctxt.world[Location(actor)]
    if ctxt.world[IsA(l, "supporter")] :
        ctxt.world.activity.put_on(x, ctxt.world[Location(actor)])
    else :
        ctxt.world.activity.put_in(x, ctxt.world[Location(actor)])

@report(Dropping(actor, X))
def report_drop_default(actor, x, ctxt) :
    """Prints the default "Dropped." message."""
    ctxt.write("Dropped.")

##
# Going
##

class Going(BasicAction) :
    """Going(actor, direction)"""
    verb = "go"
    gerund = "going"
    dereference_dobj = False
    numargs = 2
    def get_direction(self) :
        """An accessor method for the direction of the going
        action."""
        return self.args[1]
parser.understand("go [direction direction]", Going(actor, direction))
parser.understand("[direction direction]", Going(actor, direction))

@verify(Going(actor, direction))
def verify_going_make_real_direction_more_logical(actor, direction, ctxt) :
    """Makes a direction which is actually possible very logical.
    This is with respect to the visible container of the location of
    the actor."""
    loc = ctxt.world[VisibleContainer(ctxt.world[Location(actor)])]
    if direction in ctxt.world.activity.get_room_exit_directions(loc) :
        return VeryLogicalOperation()

@before(Going(actor, direction), wants_event=True)
def before_going_setup_variables(action, actor, direction, ctxt) :
    """Sets up some important variables such as where the destination
    is as well as through what one is getting there.  Also checks that
    there is an exit in that particular direction, and issues the
    appropriate NoGoMessage."""
    action.going_from = ctxt.world[VisibleContainer(ctxt.world[Location(actor)])]
    if direction not in ctxt.world.activity.get_room_exit_directions(action.going_from) :
        raise AbortAction(ctxt.world[NoGoMessage(action.going_from, direction)])
    action.going_via = ctxt.world.query_relation(Exit(action.going_from, direction, Y), var=Y)[0]
    action.going_to = action.going_via
    if ctxt.world[IsA(action.going_to, "door")] :
        action.going_to = ctxt.world.activity.door_other_side_from(action.going_to, action.going_from)

@before(Going(actor, direction), wants_event=True, insert_after=before_going_setup_variables)
def before_going_check_door(action, actor, direction, ctxt) :
    """Checks that the going_via is open if it is an openable door."""
    if ctxt.world[IsA(action.going_via, "door")] :
        if ctxt.world[Openable(action.going_via)] and not ctxt.world[IsOpen(action.going_via)] :
            ctxt.actionsystem.do_first(Opening(actor, action.going_via), ctxt, silently=True)
            if not ctxt.world[IsOpen(action.going_via)] :
                raise AbortAction(ctxt.world[NoGoMessage(action.going_from, direction)])

@before(Going(actor, direction), wants_event=True, insert_after=before_going_setup_variables)
def before_going_leave_enterables(action, actor, direction, ctxt) :
    """If currently in or on something which isn't action.going_from, try exiting first."""
    loc = ctxt.world[Location(actor)]
    while action.going_from != loc :
        if ctxt.world[IsA(loc, "supporter")] :
            do_action = GettingOff(actor)
            do_action.get_off_from = loc
        else :
            do_action = Exiting(actor)
            do_action.exit_from = loc
        ctxt.actionsystem.do_first(do_action, ctxt, silently=True)
        newloc = ctxt.world[ParentEnterable(actor)]
        if newloc == loc :
            raise AbortAction(str_with_objs("{Bob|cap} can't leave [the $z]", z=loc), actor=actor)
        loc = newloc


@when(Going(actor, direction), wants_event=True)
def when_going_default(action, actor, direction, ctxt) :
    """Puts the player in the new location."""
    ctxt.world.activity.put_in(actor, action.going_to)


@report(Going(actor, direction), wants_event=True)
def report_going_default(action, actor, direction, ctxt) :
    """There is nothing to report: the change in player location will
    make step_turn want to describe the location."""
    pass


##
# Entering
##

class Entering(BasicAction) :
    """Entering(actor, x)"""
    verb = "enter"
    gerund = "entering"
    numargs = 2
parser.understand("enter [something x]", Entering(actor, X))
parser.understand("get/go in/on [something x]", Entering(actor, X))

require_xobj_visible(actionsystem, Entering(actor, X))


@before(Entering(actor, X))
def before_entering_default(actor, x, ctxt) :
    """At this point, we assume x is not an enterable, so we abort the
    action with the NoEnterMessage."""
    raise AbortAction(ctxt.world[NoEnterMessage(x)], actor=actor)

@before(Entering(actor, X) <= IsEnterable(X))
def before_entering_default_enterable(actor, x, ctxt) :
    """By default, since we've passed all the checks, the actor can
    enter the enterable thing."""
    raise ActionHandled()

@before(Entering(actor, X) <= Openable(X) & IsEnterable(X))
def before_entering_check_open(actor, x, ctxt) :
    if not ctxt.world[IsOpen(x)] :
        # first check that we're not just inside.
        loc = ctxt.world[Location(actor)]
        if loc == x :
            raise NotHandled()
        while not ctxt.world[IsA(loc, "room")] :
            if loc == x :
                raise NotHandled()
            loc = ctxt.world[Location(loc)]
        # we're not just inside:
        ctxt.actionsystem.do_first(Opening(actor, x), ctxt, silently=True)
        if not ctxt.world[IsOpen(x)] :
            raise AbortAction("That needs to be open to be able to enter it.")

@before(Entering(actor, X) <= IsEnterable(X))
def before_entering_implicitly_exit(actor, x, ctxt) :
    """Implicitly exits and enters until actor is one level away from
    x."""
    # first figure out what the enterable which contains both x and
    # the actor is.  We go up the ParentEnterable location chains, and
    # then remove the shared root.
    actor_parent_enterables = [ctxt.world[ParentEnterable(actor)]]
    while not ctxt.world[IsA(actor_parent_enterables[-1], "room")] :
        actor_parent_enterables.append(ctxt.world[ParentEnterable(actor_parent_enterables[-1])])
    x_enterables = [ctxt.world[ParentEnterable(x)]]
    while not ctxt.world[IsA(x_enterables[-1], "room")] :
        x_enterables.append(ctxt.world[ParentEnterable(x_enterables[-1])])
    while actor_parent_enterables and x_enterables and actor_parent_enterables[-1] == x_enterables[-1] :
        actor_parent_enterables.pop()
        x_enterables.pop()
    # we might accidentally have x at the end of actor_parent_enterables
    if actor_parent_enterables and actor_parent_enterables[-1] == x :
        actor_parent_enterables.pop()
    # actor_parent_enterables ends up being the things we must exit
    # first.  We don't actually need to know what we're exiting, just
    # how many times.
    for y in actor_parent_enterables :
        if ctxt.world[IsA(y, "supporter")] :
            action = GettingOff(actor)
            action.get_off_from = y
        else :
            action = Exiting(actor)
            action.exit_from = y
        ctxt.actionsystem.do_first(action, ctxt, silently=True)
    # x_enterables ends up being the things we must enter first
    for y in x_enterables :
        ctxt.actionsystem.do_first(Entering(actor, y), ctxt, silently=True)

@before(Entering(actor, X) <= IsEnterable(X))
def before_entering_check_not_already_entered(actor, x, ctxt) :
    """Ensures that the actor is not already in or on x."""
    if x == ctxt.world[Location(actor)] :
        raise AbortAction(str_with_objs("{Bob|cap} {is} already on [the $x].", x=x),
                          actor=actor)

@before(Entering(actor, X) <= IsEnterable(X))
def before_entering_check_not_possession(actor, x, ctxt) :
    """Checks that the actor is not entering something that they are
    holding."""
    loc = ctxt.world[Location(x)]
    while not ctxt.world[IsA(loc, "room")] :
        if loc == actor :
            raise AbortAction("{Bob|cap} can't enter what {bob} {is} holding.", actor=actor)
        loc = ctxt.world[Location(loc)]

@before(Entering(actor, X) <= IsA(X, "door"))
def before_entering_door(actor, x, ctxt) :
    """For doors, we translate entering into going in the appropriate
    direction."""
    vis_loc = ctxt.world[VisibleContainer(ctxt.world[Location(actor)])]
    dir = ctxt.world.query_relation(Exit(vis_loc, Y, x), var=Y)[0]
    raise DoInstead(Going(actor, dir), suppress_message=True)

@when(Entering(actor, X) <= IsA(X, "container"))
def when_entering_container(actor, x, ctxt) :
    """For a container, put the actor in it."""
    ctxt.world.activity.put_in(actor, x)

@when(Entering(actor, X) <= IsA(X, "supporter"))
def when_entering_container(actor, x, ctxt) :
    """For a supporter, put the actor on it."""
    ctxt.world.activity.put_on(actor, x)

@report(Entering(actor, X))
def report_entering_describe_contents(actor, x, ctxt) :
    """Describes the contents of the new location if the actor is the
    actor of the context, disabling the location heading and the
    location description."""
    if ctxt.actor == actor :
        ctxt.activity.describe_location(actor, x, x, disable=[describe_location_Heading, describe_location_Description])

@report(Entering(actor, X) <= IsA(X, "container"))
def report_entering_container(actor, x, ctxt) :
    """Explains entering a container."""
    ctxt.write(str_with_objs("{Bob|cap} {gets} into [the $x].", x=x), actor=actor)

@report(Entering(actor, X) <= IsA(X, "supporter"))
def report_entering_supporter(actor, x, ctxt) :
    """Explains entering a supporter."""
    ctxt.write(str_with_objs("{Bob|cap} {gets} on top of [the $x].", x=x), actor=actor)


##
# Exiting
##

class Exiting(BasicAction) :
    "Exiting(actor)"
    verb = "exit"
    gerund = "exiting"
    numargs = 1
    exit_from = None
    def gerund_form(self, ctxt) :
        if self.exit_from :
            dobj = str_with_objs("[the $x]", x=self.exit_from)
            return "exiting "+dobj
        else :
            return "exiting"
    def infinitive_form(self, ctxt) :
        if self.exit_from :
            dobj = str_with_objs("[the $x]", x=self.exit_from)
            return "exit "+dobj
        else :
            return "exit"
parser.understand("exit", Exiting(actor))
parser.understand("leave", Exiting(actor))

@before(Exiting(actor), wants_event=True)
def before_Exiting_set_exit_from(event, actor, ctxt) :
    """Sets the event.exit_from attribute if it's not already set.  If
    we're exiting from a supporter, then instead do GettingOff."""
    if not event.exit_from :
        event.exit_from = ctxt.world[Location(actor)]
    if ctxt.world[IsA(event.exit_from, "supporter")] :
        newaction = GettingOff(actor)
        newaction.get_off_from = event.exit_from
        raise DoInstead(newaction, suppress_message=True)

@before(Exiting(actor), wants_event=True, insert_after=before_Exiting_set_exit_from)
def before_Exiting_needs_not_be_room(event, actor, ctxt) :
    """If the actor is just in a room, then it gets converted to going
    out."""
    if ctxt.world[IsA(event.exit_from, "room")] :
        raise DoInstead(Going(actor, "out"))

@before(Exiting(actor), wants_event=True, insert_after=before_Exiting_set_exit_from)
def before_Exiting_open_container(event, actor, ctxt) :
    """If we are exiting a closed container, try to open it first."""
    if ctxt.world[IsA(event.exit_from, "container")] :
        if ctxt.world[Openable(event.exit_from)] and not ctxt.world[IsOpen(event.exit_from)] :
            ctxt.actionsystem.do_first(Opening(actor, event.exit_from), ctxt, silently=True)
            if not ctxt.world[IsOpen(event.exit_from)] :
                raise AbortAction(str_with_objs("{Bob|cap} can't exit [the $z] because it is closed.", z=event.exit_from),
                                  actor=actor)

@when(Exiting(actor), wants_event=True)
def when_Exiting_default(event, actor, ctxt) :
    """Puts the player into the ParentEnterable of the location."""
    ctxt.world.activity.put_in(actor, ctxt.world[ParentEnterable(event.exit_from)])

@report(Exiting(actor), wants_event=True)
def report_Exiting_default(event, actor, ctxt) :
    """Describes what happened, and describes the new location."""
    ctxt.write(str_with_objs("{Bob|cap} {gets} out of [the $z].", z=event.exit_from), actor=actor)
    #ctxt.activity.describe_current_location()

##
# Getting off
##

class GettingOff(BasicAction) :
    "GettingOff(actor)"
    verb = "get off"
    gerund = "getting off"
    numargs = 1
    get_off_from = None
    def gerund_form(self, ctxt) :
        if self.get_off_from :
            dobj = str_with_objs("[the $x]", x=self.get_off_from)
            return "getting off "+dobj
        else :
            return "getting off"
    def infinitive_form(self, ctxt) :
        if self.get_off_from :
            dobj = str_with_objs("[the $x]", x=self.get_off_from)
            return "get off "+dobj
        else :
            return "getting off"
parser.understand("get off", GettingOff(actor))

@before(GettingOff(actor), wants_event=True)
def before_GettingOff_set_get_off_from(event, actor, ctxt) :
    """Sets the event.get_off_from attribute if it's not already set.
    If we're getting off a container, then instead do Exiting."""
    if not event.get_off_from :
        event.get_off_from = ctxt.world[Location(actor)]
    if ctxt.world[IsA(event.get_off_from, "container")] :
        newaction = Exiting(actor)
        newaction.exit_from = event.get_off_from
        raise DoInstead(newaction, suppress_message=True)

@before(GettingOff(actor), wants_event=True, insert_after=before_GettingOff_set_get_off_from)
def before_GettingOff_non_supporter(event, actor, ctxt) :
    """Fails trying to get off a non supporter or a room."""
    if ctxt.world[IsA(event.get_off_from, "room")] :
        raise AbortAction("There's nothing to get off.", actor=actor)
    if not ctxt.world[IsA(event.get_off_from, "supporter")] :
        raise AbortAction(str_with_objs("{Bob|cap} can't get off of [the $z].", z=event.get_off_from),
                          actor=actor)

@when(GettingOff(actor), wants_event=True)
def when_GettingOff_default(event, actor, ctxt) :
    """Puts the player into the ParentEnterable of the location."""
    ctxt.world.activity.put_in(actor, ctxt.world[ParentEnterable(event.get_off_from)])

@report(GettingOff(actor), wants_event=True)
def report_GettingOff_default(event, actor, ctxt) :
    """Describes what happened, and describes the new location (if the actor is the actor of the context)."""
    ctxt.write(str_with_objs("{Bob|cap} {gets} off of [the $z].", z=event.get_off_from), actor=actor)
    if actor == ctxt.actor :
        ctxt.activity.describe_current_location(actor)


##
# Exiting something in particular
##

class ExitingParticular(BasicAction) :
    """ExitingParticular(actor, x)"""
    verb = "exit"
    gerund = "exiting"
    numargs = 2
parser.understand("exit [something x]", ExitingParticular(actor, X))
parser.understand("leave [something x]", ExitingParticular(actor, X))
parser.understand("get out of [something x]", ExitingParticular(actor, X))

require_xobj_visible(actionsystem, ExitingParticular(actor, X))

@before(ExitingParticular(actor, X))
def before_ExitingParticular_needs_to_be_in_x(actor, x, ctxt) :
    """Just checks that the actor is in the x, and then redirects to
    GettingOff."""
    if x != ctxt.world[Location(actor)] :
        raise AbortAction(str_with_objs("{Bob|cap} {is} not in [the $x].", x=x), actor=actor)
    raise DoInstead(Exiting(actor), suppress_message=True)


##
# Getting off something in particular
##

class GettingOffParticular(BasicAction) :
    """GettingOffParticular(actor, x)"""
    verb = "get off"
    gerund = "getting off"
    numargs = 2
parser.understand("get off [something x]", GettingOffParticular(actor, X))

require_xobj_visible(actionsystem, GettingOffParticular(actor, X))

@before(GettingOffParticular(actor, X))
def before_GettingOffParticular_needs_to_be_on_x(actor, x, ctxt) :
    """Just checks that the actor is on the x, and then redirects to
    GettingOff."""
    if x != ctxt.world[Location(actor)] :
        raise AbortAction(str_with_objs("{Bob|cap} {is} not on [the $x].", x=x), actor=actor)
    raise DoInstead(GettingOff(actor), suppress_message=True)


##
# Inserting something into something
##

class InsertingInto(BasicAction) :
    """InsertingInto(actor, x, y)"""
    verb = ("insert", "into")
    gerund = ("inserting", "into")
    numargs = 3
parser.understand("put/insert/drop [something x] in/into [something y]", InsertingInto(actor, X, Y))

require_xobj_held(actionsystem, InsertingInto(actor, X, Y))
require_xobj_accessible(actionsystem, InsertingInto(actor, Z, X))

@before(InsertingInto(actor, X, Y) <= PEquals(X, Y))
def before_InsertingInto_not_on_itself(actor, x, y, ctxt) :
    """One can't place something in itself."""
    raise AbortAction(str_with_objs("{Bob|cap} can't put [the $x] into itself.", x=x), actor=actor)

@before(InsertingInto(actor, X, Y))
def before_InsertingInto_object_into_own_contents(actor, x, y, ctxt) :
    """One can't place something into something which is in it."""
    loc = ctxt.world[Location(y)]
    while not ctxt.world[IsA(loc, "room")] :
        if loc == x :
            raise AbortAction(str_with_objs("{Bob|cap} will have to remove [the $y] from [the $x] first.",
                                            x=x, y=y), actor=actor)
        loc = ctxt.world[Location(loc)]

@before(InsertingInto(actor, X, Y) <= Openable(X) & PNot(IsOpen(X)))
def before_InsertingInto_closed_container(actor, x, y, ctxt) :
    """One can't place something into a closed container."""
    ctxt.actionsystem.do_first(Opening(actor, Y))
    if not ctxt.world[IsOpen(Y)] :
        raise AbortAction(str_with_objs("[The $y] is closed.", y=y))

@before(InsertingInto(actor, X, Y) <= PNot(IsA(Y, "container")))
def before_InsertingInto_needs_container(actor, x, y, ctxt) :
    """One can only insert things into a container."""
    raise AbortAction(str_with_objs("{Bob|cap} can't put [the $x] into [the $y].", x=x, y=y), actor=actor)

# @before(InsertingInto(actor, X, Y))
# def before_InsertingInto_worn_item(actor, x, y, ctxt) :
#     """One cannot insert what one is wearing."""
#     if ctxt.world.query_relation(Wears(actor, x)) :
#         raise AbortAction(str_with_objs("{Bob|cap} {is} wearing [the $x].", x=x), actor=actor)

@when(InsertingInto(actor, X, Y))
def when_InsertingInto_default(actor, x, y, ctxt) :
    """Makes y contain x."""
    ctxt.world.activity.put_in(x, y)

@report(InsertingInto(actor, X, Y))
def report_InsertingInto_default(actor, x, y, ctxt) :
    """Provides a default message for InsertingInto."""
    ctxt.write(str_with_objs("{Bob|cap} {puts} [the $x] into [the $y].", x=x, y=y), actor=actor)


##
# Placing something on something
##

class PlacingOn(BasicAction) :
    """PlacingOn(actor, x, y)"""
    verb = ("place", "on")
    gerund = ("placing", "on")
    numargs = 3
parser.understand("put/place/drop [something x] on/onto [something y]", PlacingOn(actor, X, Y))

require_xobj_held(actionsystem, PlacingOn(actor, X, Y))
require_xobj_accessible(actionsystem, PlacingOn(actor, Z, X))

@before(PlacingOn(actor, X, Y) <= PEquals(X, Y))
def before_PlacingOn_not_on_itself(actor, x, y, ctxt) :
    """One can't place something on itself."""
    raise AbortAction(str_with_objs("{Bob|cap} can't place [the $x] on itself.", x=x), actor=actor)

@before(PlacingOn(actor, X, Y))
def before_PlacingOn_object_onto_own_contents(actor, x, y, ctxt) :
    """One can't place something onto something which is on it."""
    loc = ctxt.world[Location(y)]
    while not ctxt.world[IsA(loc, "room")] :
        if loc == x :
            raise AbortAction(str_with_objs("{Bob|cap} will have to take [the $y] off [the $x] first.",
                                            x=x, y=y), actor=actor)
        loc = ctxt.world[Location(loc)]

@before(PlacingOn(actor, X, Y) <= PNot(IsA(Y, "supporter")))
def before_PlacingOn_needs_supporter(actor, x, y, ctxt) :
    """One can only place things on a supporter."""
    raise AbortAction(str_with_objs("{Bob|cap} can't place [the $x] on [the $y].", x=x, y=y), actor=actor)

# @before(PlacingOn(actor, X, Y))
# def before_PlacingOn_worn_item(actor, x, y, ctxt) :
#     """One cannot place what one is wearing on anything."""
#     if ctxt.world.query_relation(Wears(actor, x)) :
#         raise AbortAction(str_with_objs("{Bob|cap} {is} wearing [the $x].", x=x), actor=actor)


@when(PlacingOn(actor, X, Y))
def when_PlacingOn_default(actor, x, y, ctxt) :
    """Makes y support x."""
    ctxt.world.activity.put_on(x, y)

@report(PlacingOn(actor, X, Y))
def report_PlacingOn_default(actor, x, y, ctxt) :
    """Provides a default message for PlacingOn."""
    ctxt.write(str_with_objs("{Bob|cap} {places} [the $x] on [the $y].", x=x, y=y), actor=actor)

##
# Opening
##

class Opening(BasicAction) :
    """Opening(actor, x)"""
    verb = "open"
    gerund = "opening"
    numargs = 2
parser.understand("open [something x]", Opening(actor, X))

require_xobj_accessible(actionsystem, Opening(actor, X))

@verify(Opening(actor, X) <= Openable(X))
def verify_opening_openable(actor, x, ctxt) :
    """That which is openable is more logical to open."""
    return VeryLogicalOperation()

@verify(Opening(actor, X) <= PEquals(X, Location(actor)))
def verify_opening_actor_location(actor, x, ctxt) :
    """We can get into the case that we are inside a box that we
    trapped ourselves in without light.  We want to still be able to
    open it."""
    raise ActionHandled(VeryLogicalOperation())

@before(Opening(actor, X) <= PNot(Openable(X)))
def before_opening_unopenable(actor, x, ctxt) :
    """That which isn't openable can't be opened."""
    raise AbortAction(ctxt.world[NoOpenMessages(x, "no_open")], actor=actor)

@before(Opening(actor, X) <= Lockable(X) & IsLocked(X))
def before_opening_locked(actor, x, ctxt) :
    """That which is locked can't be immediately opened."""
    raise AbortAction(ctxt.world[NoLockMessages(x, "no_open")], actor=actor)

@before(Opening(actor, X) <= Openable(X) & IsOpen(X))
def before_opening_already_open(actor, x, ctxt) :
    """That which is open can't be opened again."""
    raise AbortAction(ctxt.world[NoOpenMessages(x, "already_open")], actor=actor)

@when(Opening(actor, X))
def when_opening(actor, x, ctxt) :
    """Sets the IsOpen property to True."""
    ctxt.world[IsOpen(x)] = True

@report(Opening(actor, X))
def report_opening(actor, x, ctxt) :
    """Writes 'Opened.'"""
    ctxt.write("Opened.")


##
# Closing
##

class Closing(BasicAction) :
    """Closing(actor, x)"""
    verb = "close"
    gerund = "closing"
    numargs = 2
parser.understand("close [something x]", Closing(actor, X))

require_xobj_accessible(actionsystem, Closing(actor, X))

@verify(Closing(actor, X) <= Openable(X))
def verify_closing_openable(actor, x, ctxt) :
    """That which is openable is more logical to close."""
    return VeryLogicalOperation()

@before(Closing(actor, X) <= PNot(Openable(X)))
def before_closing_unopenable(actor, x, ctxt) :
    """That which isn't openable can't be closed."""
    raise AbortAction(ctxt.world[NoOpenMessages(x, "no_close")], actor=actor)

@before(Closing(actor, X) <= Openable(X) & PNot(IsOpen(X)))
def before_closing_already_open(actor, x, ctxt) :
    """That which is closed can't be closed again."""
    raise AbortAction(ctxt.world[NoOpenMessages(x, "already_closed")], actor=actor)

@when(Closing(actor, X))
def when_closing(actor, x, ctxt) :
    """Sets the IsOpen property to False."""
    ctxt.world[IsOpen(x)] = False

@report(Closing(actor, X))
def report_closing(actor, x, ctxt) :
    """Writes 'Closed.'"""
    ctxt.write("Closed.")


##
# Unlocking
##

class UnlockingWith(BasicAction) :
    """UnlockingWith(actor, x, key)"""
    verb = ("unlock", "with")
    gerund = ("unlocking", "with")
    numargs = 3
parser.understand("unlock [something x] with [something y]", UnlockingWith(actor, X, Y))
parser.understand("open [something x] with [something y]", UnlockingWith(actor, X, Y))

require_xobj_accessible(actionsystem, UnlockingWith(actor, X, Y))
require_xobj_held(actionsystem, UnlockingWith(actor, Z, X))

@before(UnlockingWith(actor, X, Y) <= PNot(Lockable(X)))
def before_unlocking_unlockable(actor, x, y, ctxt) :
    """One can't unlock that which has no lock."""
    raise AbortAction(ctxt.world[NoLockMessages(x, "no_unlock")], actor=actor)

@before(UnlockingWith(actor, X, Y) <= Lockable(X) & PNot(IsLocked(X)))
def before_unlocking_unlocked(actor, x, y, ctxt) :
    """One can't unlock that which is already unlocked."""
    raise AbortAction(ctxt.world[NoLockMessages(x, "already_unlocked")], actor=actor)

@before(UnlockingWith(actor, X, Y) <= Lockable(X) & PNot(PEquals(Y, KeyOfLock(X))))
def before_unlocking_unlocked(actor, x, y, ctxt) :
    """One can't unlock with the wrong key."""
    raise AbortAction(ctxt.world[WrongKeyMessages(x, y)], actor=actor)

@when(UnlockingWith(actor, X, Y))
def when_unlocking_locked(actor, x, y, ctxt) :
    """We just set the IsLocked property to false."""
    ctxt.world[IsLocked(x)] = False

@report(UnlockingWith(actor, X, Y))
def report_unlocking_locked(actor, x, y, ctxt) :
    """Just outputs 'Unlocked.'"""
    ctxt.write("Unlocked.")

#
# Help the user know they need a key
#
class Unlocking(BasicAction) :
    """Unlock(actor, x)"""
    verb = "unlock"
    gerund = "unlocking"
    numargs = 2
parser.understand("unlock [something x]", Unlocking(actor, X))
require_xobj_accessible(actionsystem, Unlocking(actor, X))
@before(Unlocking(actor, X))
def before_unlocking_fail(actor, x, ctxt) :
    """Unlocking requires a key."""
    raise AbortAction(str_with_objs("Unlocking requires a key.", x=x), actor=actor)


##
# Locking
##

class LockingWith(BasicAction) :
    """LockingWith(actor, x, key)"""
    verb = ("lock", "with")
    gerund = ("locking", "with")
    numargs = 3
parser.understand("lock [something x] with [something y]", LockingWith(actor, X, Y))
parser.understand("close [something x] with [something y]", LockingWith(actor, X, Y))

require_xobj_accessible(actionsystem, LockingWith(actor, X, Y))
require_xobj_held(actionsystem, LockingWith(actor, Z, X))

@before(LockingWith(actor, X, Y) <= PNot(Lockable(X)))
def before_locking_lockable(actor, x, y, ctxt) :
    """One can't lock that which has no lock."""
    raise AbortAction(ctxt.world[NoLockMessages(x, "no_lock")], actor=actor)

@before(LockingWith(actor, X, Y) <= Lockable(X) & IsLocked(X))
def before_locking_locked(actor, x, y, ctxt) :
    """One can't lock that which is already locked."""
    raise AbortAction(ctxt.world[NoLockMessages(x, "already_locked")], actor=actor)

@before(LockingWith(actor, X, Y) <= Lockable(X) & PNot(PEquals(Y, KeyOfLock(X))))
def before_locking_locked(actor, x, y, ctxt) :
    """One can't lock with the wrong key."""
    raise AbortAction(ctxt.world[WrongKeyMessages(x, y)], actor=actor)

@when(LockingWith(actor, X, Y))
def when_locking_locked(actor, x, y, ctxt) :
    """We just set the IsLocked property to true."""
    ctxt.world[IsLocked(x)] = True

@report(LockingWith(actor, X, Y))
def report_locking_locked(actor, x, y, ctxt) :
    """Just outputs 'Locked.'"""
    ctxt.write("Locked.")

#
# Help the user know they need a key
#
class Locking(BasicAction) :
    """Locking(actor, x)"""
    verb = "lock"
    gerund = "locking"
    numargs = 2
parser.understand("lock [something x]", Locking(actor, X))
require_xobj_accessible(actionsystem, Locking(actor, X))
@before(Locking(actor, X))
def before_locking_fail(actor, x, ctxt) :
    """Locking requires a key."""
    raise AbortAction(str_with_objs("Locking requires a key.", x=x), actor=actor)


##
# Wearing
##
class Wearing(BasicAction) :
    """Wearing(actor, x)"""
    verb = "wear"
    gerund = "wearing"
    numargs = 2
parser.understand("wear [something x]", Wearing(actor, X))
parser.understand("put on [something x]", Wearing(actor, X))
parser.understand("put [something x] on", Wearing(actor, X))

require_xobj_held(actionsystem, Wearing(actor, X))

@before(Wearing(actor, X) <= PNot(IsWearable(X)))
def before_wearing_unwearable(actor, x, ctxt) :
    """Wearing requires something wearable."""
    raise AbortAction(str_with_objs("[The $x] can't be worn.", x=x), actor=actor)

@before(Wearing(actor, X))
def before_wearing_worn(actor, x, ctxt) :
    """You can't put on something already worn."""
    if ctxt.world.query_relation(Wears(actor, x)) :
        raise AbortAction("{Bob|cap} {is} already wearing that.", actor=actor)

@when(Wearing(actor, X))
def when_wearing_default(actor, x, ctxt) :
    """Makes the actor wear the wearable."""
    ctxt.world.activity.make_wear(actor, x)

@report(Wearing(actor, X))
def report_wearing_default(actor, x, ctxt) :
    """Just reports the wearing."""
    ctxt.write(str_with_objs("{Bob|cap} now {wears} [the $x].", x=x), actor=actor)


##
# Taking off
##
class TakingOff(BasicAction) :
    """TakingOff(actor, x)"""
    verb = "take off"
    gerund = "taking off"
    numargs = 2
parser.understand("take off [something x]", TakingOff(actor, X))
parser.understand("take [something x] off", TakingOff(actor, X))
parser.understand("remove [something x]", TakingOff(actor, X))

@before(TakingOff(actor, X))
def before_takingoff_not_worn(actor, x, ctxt) :
    """Clothes must be presently worn to be taken off."""
    if not ctxt.world.query_relation(Wears(actor, x)) :
        raise AbortAction("{Bob|cap} {is} not wearing that.", actor=actor)

@when(TakingOff(actor, X))
def when_takingoff_default(actor, x, ctxt) :
    """Moves the worn thing into the possessions of the actor (which
    removes the Wears relation)."""
    ctxt.world.activity.give_to(x, actor)

@report(TakingOff(actor, X))
def report_takingoff_default(actor, x, ctxt) :
    """Reports that the actor took it off."""
    ctxt.write(str_with_objs("{Bob|cap} {takes} off [the $x].", x=x), actor=actor)


##
# Switching on
##

class SwitchingOn(BasicAction) :
    """SwitchingOn(actor, x)"""
    verb = "switch on"
    gerund = "switching on"
    numargs = 2
parser.understand("switch/turn on [something x]", SwitchingOn(actor, X))
parser.understand("switch/turn [something x] on", SwitchingOn(actor, X))

require_xobj_accessible(actionsystem, SwitchingOn(actor, X))

@verify(SwitchingOn(actor, X) <= Switchable(X))
def verify_switching_on_switchable(actor, x, ctxt) :
    """That which is switchable is more logical to switch on."""
    return VeryLogicalOperation()

@before(SwitchingOn(actor, X) <= PNot(Switchable(X)))
def before_switching_on_unswitchable(actor, x, ctxt) :
    """That which isn't switchable can't be switched on."""
    raise AbortAction(ctxt.world[NoSwitchMessages(x, "no_switch_on")], actor=actor)

@before(SwitchingOn(actor, X) <= Switchable(X) & IsSwitchedOn(X))
def before_switching_on_already_switched_on(actor, x, ctxt) :
    """That which is switched on can't be switched on again."""
    raise AbortAction(ctxt.world[NoSwitchMessages(x, "already_on")], actor=actor)

@when(SwitchingOn(actor, X))
def when_switching_on(actor, x, ctxt) :
    """Sets the IsSwitchedOn property to True."""
    ctxt.world[IsSwitchedOn(x)] = True

@report(SwitchingOn(actor, X))
def report_switching_on(actor, x, ctxt) :
    """Writes 'Switched on.'"""
    ctxt.write("Switched on.")

##
# Switching Off
##

class SwitchingOff(BasicAction) :
    """SwitchingOff(actor, x)"""
    verb = "switch off"
    gerund = "switching off"
    numargs = 2
parser.understand("switch/turn off [something x]", SwitchingOff(actor, X))
parser.understand("switch/turn [something x] off", SwitchingOff(actor, X))

require_xobj_accessible(actionsystem, SwitchingOff(actor, X))

@verify(SwitchingOff(actor, X) <= Switchable(X))
def verify_switching_off_switchable(actor, x, ctxt) :
    """That which is switchable is more logical to switch off."""
    return VeryLogicalOperation()

@before(SwitchingOff(actor, X) <= PNot(Switchable(X)))
def before_switching_off_unswitchable(actor, x, ctxt) :
    """That which isn't switchable can't be switched off."""
    raise AbortAction(ctxt.world[NoSwitchMessages(x, "no_switch_off")], actor=actor)

@before(SwitchingOff(actor, X) <= Switchable(X) & PNot(IsSwitchedOn(X)))
def before_switching_off_already_switched_off(actor, x, ctxt) :
    """That which is switched off can't be switched off again."""
    raise AbortAction(ctxt.world[NoSwitchMessages(x, "already_off")], actor=actor)

@when(SwitchingOff(actor, X))
def when_switching_off(actor, x, ctxt) :
    """Sets the IsSwitchedOn property to False."""
    ctxt.world[IsSwitchedOn(x)] = False

@report(SwitchingOff(actor, X))
def report_switching_off(actor, x, ctxt) :
    """Writes 'Switched off.'"""
    ctxt.write("Switched off.")

##
# Switching
##

class Switching(BasicAction) :
    """Switching(actor, x)"""
    verb = "switch"
    gerund = "switching"
    numargs = 2
parser.understand("switch/turn [something x]", Switching(actor, X))

require_xobj_accessible(actionsystem, Switching(actor, X))

@before(Switching(actor, X) <= Switchable(X))
def verify_switching_switchable(actor, x, ctxt) :
    """That which is switchable is more logical to switch."""
    return VeryLogicalOperation()

@before(Switching(actor, X) <= PNot(Switchable(X)))
def before_switching_unswitchable(actor, x, ctxt) :
    """That which isn't switchable can't be switched."""
    raise AbortAction(ctxt.world[NoSwitchMessages(x, "no_switch")], actor=actor)

@before(Switching(actor, X) <= Switchable(X))
def before_switching_switchable(actor, x, ctxt) :
    """Does the proper switching on/off."""
    if ctxt.world[IsSwitchedOn(x)] :
        raise DoInstead(SwitchingOff(actor, x), suppress_message=True)
    else :
        raise DoInstead(SwitchingOn(actor, x), suppress_message=True)

###
### Actions that don't do anything
###

##
# Attacking
##
class Attacking(BasicAction) :
    """Attacking(actor, x)"""
    verb = "attack"
    gerund = "attacking"
    numargs = 2
parser.understand("attack/kill [something x]", Attacking(actor, X))

require_xobj_accessible(actionsystem, Attacking(actor, X))

@before(Attacking(actor, X))
def before_attacking_default(actor, x, ctxt) :
    """By default, you can't attack."""
    raise AbortAction("Violence isn't the answer to this one.", actor=actor)

##
# Eating
##
class Eating(BasicAction) :
    """Eating(actor, x)"""
    verb = "eat"
    gerund = "eating"
    numargs = 2
parser.understand("eat [something x]", Eating(actor, X))

require_xobj_accessible(actionsystem, Eating(actor, X))

@before(Eating(actor, X))
def before_eating_default(actor, x, ctxt) :
    """By default, you can't eat."""
    raise AbortAction("{Bob|cap} {doesn't} feel like eating that.", actor=actor)

##
# Swimming and SwimmingIn
##

class Swimming(BasicAction) :
    """Swimming(actor)"""
    verb = "swim"
    gerund = "swimming"
    numargs = 1
class SwimmingIn(BasicAction) :
    """SwimmingIn(actor, X)"""
    verb = "swim"
    gerund = "swimming in"
    numargs = 2
parser.understand("swim", Swimming(actor))
parser.understand("swim in [something x]", SwimmingIn(actor, X))

require_xobj_accessible(actionsystem, SwimmingIn(actor, X))

@before(Swimming(actor))
def before_swimming_default(actor, ctxt) :
    """By default, you can't swim."""
    raise AbortAction("There's no place to swim.", actor=actor)

@before(SwimmingIn(actor, X))
def before_swimming_in_default(actor, x, ctxt) :
    """By default, you can't swim in anything."""
    raise AbortAction("{Bob|cap} can't swim in that.", actor=actor)

##
# Cutting and CuttingWith
##

class Cutting(BasicAction) :
    """Cutting(actor, X)"""
    verb = "cut"
    gerund = "cutting"
    numargs = 2
parser.understand("cut [something x]", Cutting(actor, X))

require_xobj_accessible(actionsystem, Cutting(actor, X))

@before(Cutting(actor, X))
def before_cutting_default(actor, x, ctxt) :
    """By default, you can't cut."""
    raise AbortAction("{Bob|cap} can't cut that.", actor=actor)

class CuttingWith(BasicAction) :
    """CuttingWith(actor, X, Y)"""
    verb = ("cut", "with")
    gerund = ("cutting", "with")
    numargs = 3
parser.understand("cut [something x] with [something y]", CuttingWith(actor, X, Y))

require_xobj_accessible(actionsystem, CuttingWith(actor, X, Y))
require_xobj_held(actionsystem, CuttingWith(actor, Z, X))

@before(CuttingWith(actor, X, Y))
def before_cutting_with_default(actor, x, y, ctxt) :
    """By default, you can't cut with anything."""
    raise AbortAction(str_with_objs("{Bob|cap} can't cut [the $x] with [the $y].", x=x, y=y), actor=actor)

@before(CuttingWith(actor, X, Y) <= IsA(X, "person"))
def before_cutting_a_person_with(actor, x, y, ctxt) :
    """Make the default CuttingWith more entertaining when it's a person."""
    raise AbortAction("Violence isn't the answer to this one.")


##
# Climbing
##

class Climbing(BasicAction) :
    """Climbing(actor, X)"""
    verb = "climb"
    gerund = "climbing"
    numargs = 2
parser.understand("climb [something x]", Climbing(actor, X))

require_xobj_accessible(actionsystem, Climbing(actor, X))

@before(Climbing(actor, X))
def before_climbing_default(actor, x, ctxt) :
    """By default, you can't climb."""
    raise AbortAction(str_with_objs("{Bob|cap} can't climb [the $x].", x=x), actor=actor)

##
# Pushing
##

class Pushing(BasicAction) :
    """Pushing(actor, X)"""
    verb = "push"
    gerund = "pushing"
    numargs = 2
parser.understand("push/press [something x]", Pushing(actor, X))

require_xobj_accessible(actionsystem, Pushing(actor, X))

@before(Pushing(actor, X))
def before_pushing_default(actor, x, ctxt) :
    """By default, you can't push things."""
    raise AbortAction(str_with_objs("{Bob|cap} can't push [the $x].", x=x), actor=actor)

##
# GivingTo
##

class GivingTo(BasicAction) :
    """GivingTo(actor, X, Y)"""
    verb = ("give", "to")
    gerund = ("giving", "to")
    numargs = 3
parser.understand("give [something x] to [something y]", GivingTo(actor, X, Y))
parser.understand("give [something y] [something x]", GivingTo(actor, X, Y))

require_xobj_held(actionsystem, GivingTo(actor, X, Y))
require_xobj_accessible(actionsystem, GivingTo(actor, Z, X))

@before(GivingTo(actor, X, Y) <= PNot(IsA(Y, "person")))
def before_giving_to_inanimate(actor, x, y, ctxt) :
    """You can't give things to inanimate things."""
    raise AbortAction(str_with_objs("[The $y] can't take [the $x].",x=x, y=y), actor=actor)

@before(GivingTo(actor, X, Y) <= IsA(Y, "person"))
def before_giving_to_person_default(actor, x, y, ctxt) :
    """People don't want things by default, unless y is the actor of
    the context."""
    if y != ctxt.actor :
        raise AbortAction(str_with_objs("[The $y] doesn't seem interested in [the $x]", x=x, y=y), actor=actor)

@before(GivingTo(actor, X, Y) <= PEquals(actor, Y))
def before_giving_to_self(actor, x, y, ctxt) :
    """You can't give things to yourself."""
    raise AbortAction("{Bob|cap} already {has} that.", actor=actor)


@when(GivingTo(actor, X, Y))
def when_giving_to_default(actor, x, y, ctxt) :
    """Changes the ownership of the object."""
    ctxt.world.activity.give_to(x, y)


@report(GivingTo(actor, X, Y))
def report_giving_to_default(actor, x, y, ctxt) :
    """Writes a message of the transaction."""
    ctxt.write(str_with_objs("{Bob|cap} gives [the $x] to [the $y].", x=x, y=y), actor=actor)


##
# AskingAbout
##

class AskingAbout(BasicAction) :
    verb = ("ask", "about")
    gerund = ("asking", "about")
    dereference_iobj = False
    numargs = 3
parser.understand("ask [something x] about [text y]", AskingAbout(actor, X, Y))

require_xobj_accessible(actionsystem, AskingAbout(actor, X, Y))

@report(AskingAbout(actor, X, Y))
def report_asking_about_default(actor, x, y, ctxt) :
    """Gracefully ignores asking."""
    ctxt.write(str_with_objs("[The $x] has nothing to say about that.", x=x), actor=actor)


##
# AskingFor
##

class AskingFor(BasicAction) :
    verb = ("ask", "for")
    gerund = ("asking", "for")
    numargs = 3
parser.understand("ask [something x] for [something y]", AskingFor(actor, X, Y))

require_xobj_accessible(actionsystem, AskingFor(actor, X, Y))
require_xobj_visible(actionsystem, AskingFor(actor, Z, X))

@before(AskingFor(actor, X, Y))
def before_askingfor_turn_to_givingto(actor, x, y, ctxt) :
    """Turns the AskingFor into a AskingTo(...,GivingTo(...))."""
    raise DoInstead(AskingTo(actor, x, GivingTo(x, y, actor)), suppress_message=True)


##
# AskingTo
##

class AskingTo(BasicAction) :
    verb = ("ask", "to")
    gerund = ("asking", "to")
    numargs = 3
    def gerund_form(self, ctxt) :
        dobj = str_with_objs("[the $x]", x=self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.gerund[0] + " " + dobj + " to " + comm
    def infinitive_form(self, ctxt) :
        dobj = str_with_objs("[the $x]", x=self.args[1])
        comm = self.args[2].infinitive_form(ctxt)
        return self.verb[0] + " " + dobj + " to " + comm
parser.understand("ask [something x] to [action y]", AskingTo(actor, X, Y))

require_xobj_accessible(actionsystem, AskingTo(actor, X, Y))

@verify(AskingTo(actor, X, Y))
def verify_askingto_by_verify_y(actor, x, y, ctxt) :
    """Updates the actor for y to x and then verifies that action."""
    y.update_actor(x)
    return ctxt.actionsystem.verify_action(y, ctxt)

@before(AskingTo(actor, X, Y))
def before_askingto_check_willing(actor, x, y, ctxt) :
    """Checks if the askee is willing to do the action by calling the
    actor activity 'npc_is_willing'."""
    y.update_actor(x)
    ctxt.activity.npc_is_willing(actor, y)

@when(AskingTo(actor, X, Y))
def when_askingto_make_it_happen(actor, x, y, ctxt) :
    """Makes the actor x do the action."""
    y.update_actor(x)
    ctxt.actionsystem.run_action(y, ctxt)

###
### Debugging actions
###


class MagicallyDestroying(BasicAction) :
    verb = "destroy"
    gerund = "destroying"
    numargs = 2
parser.understand("magically destroy [something x]", MagicallyDestroying(actor, X))

@when(MagicallyDestroying(actor, X))
def when_magicallydestroying(actor, x, ctxt) :
    ctxt.world.activity.remove_obj(x)

@report(MagicallyDestroying(actor, X))
def report_magicallydestroying(actor, x, ctxt) :
    ctxt.write("*Poof*")


class MagicallyTaking(BasicAction) :
    verb = "magically take"
    gerund = "magically taking"
    numargs = 2
parser.understand("magically take [something x]", MagicallyTaking(actor, X))

@verify(MagicallyTaking(actor, X) <= PEquals(actor, X))
def verify_magically_taking_no_actor(actor, x, ctxt) :
    raise AbortAction("That would crash the program.")

@when(MagicallyTaking(actor, X))
def when_magically_taking(actor, x, ctxt) :
    ctxt.world.activity.give_to(x, actor)
@report(MagicallyTaking(actor, X))
def report_magically_taking(actor, x, ctxt) :
    ctxt.write("*poof*[newline]Taken.")
