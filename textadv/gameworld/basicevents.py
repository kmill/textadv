# basicevents.py
#
# The basic events library which implements events and action
# definitions for the objects in the basic objects library
# basicobjects.py

from textadv.gamesystem.eventsystem import *
from textadv.gamesystem.parser import Ambiguous
from textadv.gamesystem.basicpatterns import *
from textadv.gamesystem.basicparser import understand, add_direction
from textadv.gameworld.basicobjects import *

actor = Actor(PVar("actor"))

###
### Events
###

@when(StartGame())
def _basic_start_game(context) :
    context.write_line("starting game...\n\n")

@when(StartTurn())
def _player_startturn(context) :
    context.actor.get_location().visit()

###
### Useful macros for actions
###

# In these, action is a pattern with free variables actor and x.

def xobj_accessible(action) :
    """Ensures that x is accessible to the actor x in the action."""
    @verify(action)
    def _verify_xobj_accessible(actor, x, context, **kwargs) :
        if not actor.obj_accessible(x) :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))

def xobj_held(action, no_imply=False) :
    """Ensures that x is held by the actor, and if it isn't, an
    attempt is made to take the item first.  The no_imply argument
    says whether to attempt to take the object if the actor does not
    already have it."""
    @verify(action)
    def _verify_xobj_held(actor, x, context, **kwargs) :
        if actor.s_R_x(Has, x) :
            return VeryLogicalOperation()
        elif not actor.obj_accessible(x) :
            return IllogicalOperation("{Bob|cap} {doesn't} have "+x["definite_name"]+".", actor=actor)
    if no_imply :
        @before(action)
        def _before_xobj_held_noimply(actor, x, context, **kwargs) :
            if not actor.s_R_x(Has, x) :
                raise AbortAction("{Bob|cap} {doesn't} have "+x["definite_name"]+".", actor=actor)
    else :
        @trybefore(action)
        def _trybefore_xobj_held_implied(actor, x, context, **kwargs) :
            if not actor.s_R_x(Has, x) :
                do_first(Take(actor, x), context=context)
            # just in case do_first does something else and doesn't
            # get x to the actor:
            if not actor.s_R_x(Has, x) :
                raise AbortAction("{Bob|cap} {doesn't} have "+x["definite_name"]+".", actor=actor)

def xobj_not_held(action) :
    """Hints that x should not already be held by the actor.  No
    attempt is made to first drop x."""
    @verify(action)
    def _verify_xobj_not_held(actor, x, context, **kwargs) :
        if not actor.s_R_x(Has, x) :
            return VeryLogicalOperation()

###
### Action definitions
###

##
# Inventory
##
class Inventory(BasicAction) :
    verb = "check inventory"
    gerund = "checking inventory"
    def __init__(self, actor) :
        self.args = [actor]

understand("inventory", Inventory(actor))
understand("i", Inventory(actor))

@when(Inventory(actor))
def _when_inventory(actor, context) :
    context.write_line(actor.make_inventory(), actor=actor)
    raise ActionHandled()

##
# Look
##
class Look(BasicAction) :
    verb = "look"
    gerund = "looking"
    def __init__(self, actor) :
        self.args = [actor]

understand("look", Look(actor))
understand("l", Look(actor))

@when(Look(actor))
def _when_look(actor, context) :
    context.write_line(actor.get_location().make_description(), actor=actor)
    raise ActionHandled()

##
# Examine
##
class Examine(BasicAction) :
    verb = "examine"
    gerund = "examining"
    def __init__(self, actor, object) :
        self.args = [actor, object]

understand("examine [something x]", Examine(actor, x))
understand("x [something x]", Examine(actor, x))

xobj_accessible(Examine(actor, BObject(x)))

@verify(Examine(actor, BObject(x)))
def _verify_examine(actor, x, context) :
    if actor.s_R_x(Has, x) :
        return VeryLogicalOperation()

@when(Examine(actor, BObject(x)))
def _when_examine(actor, x, context) :
    context.write_line(x["description"].strip(), actor=actor)
    x.set_examined()
    raise ActionHandled()

##
# Take
##
class Take(BasicAction) :
    verb = "take"
    gerund = "taking"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("take [something x]", Take(actor, x))
understand("get [something x]", Take(actor, x))

xobj_accessible(Take(actor, BObject(x)))
xobj_not_held(Take(actor, BObject(x)))

@before(Take(actor, BObject(x)))
def _before_take2(actor, x, context) :
    if actor.s_R_x(Has, x) :
        raise AbortAction("{Bob|cap} already {has} that.", actor=actor)

@before(Take(actor, BObject(x)))
def _before_take3(actor, x, context) :
    # should be fixed a bit, since doesn't handle transitive containment
    res = context.world.lookup("relations", Has(y, x), res=get_y)
    if res and actor != res[0] :
        raise AbortAction("That is not {bob's} to take.", actor=actor)

@before(Take(actor, BObject(x)))
def _before_take_4(actor, x, context) :
    if not x["takeable"] :
        raise AbortAction(x["no_take_msg"], actor=actor)

@when(Take(actor, BObject(x)))
def _when_take1(actor, x, context) :
    x.give_to(actor)
    raise ActionHandled()

@after(Take(actor, BObject(x)))
def _after_take1(actor, x, context) :
    context.write_line("Taken.")

##
# Drop
##
class Drop(BasicAction) :
    verb = "drop"
    gerund = "dropping"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("drop [something x]", Drop(actor, x))

xobj_held(Drop(actor, x), no_imply=True)

@when(Drop(actor, BObject(x)))
def _when_drop1(actor, x, context) :
    x.move_to(actor.get_location())
    raise ActionHandled()

@after(Drop(actor, BObject(x)))
def _after_drop1(actor, x, context) :
    context.write_line("Dropped.")

##
# Going from room to room
##
class Go(BasicAction) :
    """This event is automatically rewritten as a GoFrom event.  That
    way, we can override going in particular directions."""
    verb = "go"
    gerund = "going"
    def __init__(self, actor, direction) :
        self.args = [actor, direction]
    def gerund_form(self, world) :
        return "going %s" % self.args[1]
# class GoFrom(BasicAction) :
#     verb = "go"
#     gerund = ("going","from")
#     def __init__(self, actor, direction, room) :
#         self.args = [actor, direction, room]
#     def gerund_form(self, world) :
#         destname = world.get_obj(self.args[2])["printed_name"]
#         return "going %s from %s" % (self.args[1], destname)
class Enter(BasicAction) :
    verb = "enter"
    gerund = "entering"
    def __init__(self, actor, room) :
        self.args = [actor, room]
    def gerund_form(self, world) :
        destname = world.get_obj(self.args[1])["printed_name"]
        return "entering %s" % destname

understand("go [direction x]", Go(actor, x))
understand("[direction x]", Go(actor, x))
understand("enter [something x]", Enter(actor, x))
understand("go into [something x]", Enter(actor, x))

add_direction("north", ["north", "n"])
add_direction("south", ["south", "s"])
add_direction("east", ["east", "e"])
add_direction("west", ["west", "w"])
add_direction("up", ["up", "u"])
add_direction("down", ["down", "d"])
add_direction("in", ["in"])
add_direction("out", ["out", "o"])

direction = PVar("direction")

@verify(Go(actor, direction))
def _verify_go(actor, direction, context) :
    """Just check if we can go that way, to boost the option."""
    if actor.get_location().get_exit(direction) :
        return VeryLogicalOperation()

#@before(Go(actor, direction))
#def _instead_go(actor, direction, context) :
#    raise DoInstead(GoFrom(actor, direction, actor.get_location()), suppress_message=True)

@before(Go(actor, direction))
def _before_gofrom1(actor, direction, context) :
    room = actor.get_location()
    exit = room.get_exit(direction)
    if not exit :
        # Perhaps we should try going into something in the room
        if direction=="in" :
            maybe_in = context.world.lookup("relations", In(Enterable(x), room), res=get_x)
            if len(maybe_in) == 1 :
                raise DoInstead(Enter(actor, maybe_in[0]))
            else :
                raise Ambiguous([maybe_in])
        raise AbortAction(room.no_go_message(direction), actor=actor)

@when(Go(actor, direction))
def _when_go1(actor, direction, context) :
    exit = actor.get_location().get_exit(direction)
    run_action(Enter(actor, exit), context=context, write_action=False)
    raise ActionHandled()

xobj_accessible(Enter(actor, Enterable(x)))

@before(Enter(actor, x))
def _before_enter_default(actor, x, context) :
    raise AbortAction("{Bob|cap} {can't} enter that.", actor=actor)

@before(Enter(actor, Enterable(x)))
def _before_enter1(actor, x, context) :
    if not x["enterable"] :
        raise AbortAction(x["no_enter_msg"], actor=x)
    raise ActionHandled()

@verify(Enter(actor, Room(x)))
def _verify_enter_room1(actor, x, context) :
    # This should only be called by the "go direction" rewrite because
    # rooms shouldn't be given by name in the parser.  We also don't
    # want to restrict ourselves to going to rooms we can immediately
    # see!  (This ruins doors, unless we are more tricky, which we
    # aren't right now.)
    raise ActionHandled()

@when(Enter(actor, Room(x)))
def _when_enter1(actor, x, context) :
    actor.move_to(x)

@after(Enter(actor, Room(x)))
def _after_enter1(actor, x, context) :
    """A description is only made when the actor is the current
    player."""
    if context.actor == actor :
        context.write_line("\n")
        context.write_line(x.make_description(), actor=actor)

@when(Enter(actor, Door(x)))
def _when_enter_door(actor, x, context) :
    run_action(Enter(actor, x.other_side(actor)), context=context)
    raise ActionHandled()

##
# Open
##
class Open(BasicAction) :
    verb = "open"
    gerund = "opening"
    def __init__(self, actor, object) :
        self.args = [actor, object]

understand("open [something x]", Open(actor, x))

xobj_accessible(Open(actor, BObject(x)))

@before(Open(actor, BObject(x)))
def _before_open1(actor, x, context) :
    raise AbortAction("{Bob|cap} {can't} open that.", actor=actor)

@before(Open(actor, Openable(x)))
def _before_open_openable(actor, x, context) :
    if not x["open"] and not x["openable"] :
        raise AbortAction(x["no_open_msg"], actor=actor)
    elif x["open"] :
        raise AbortAction(x["already_open_msg"], actor=actor)
    raise ActionHandled()

@when(Open(actor, Openable(x)))
def _when_open_openable(actor, x, context) :
    x["open"] = True

@after(Open(actor, Openable(x)))
def _after_open_openable(actor, x, context) :
    context.write_line("Opened.")


@before(Open(actor, Lockable(x)))
def _before_open_lockable(actor, x, context) :
    if not x["open"] and x["locked"] :
        raise AbortAction(x["no_open_msg"], actor=actor)

##
# Close
##
class Close(BasicAction) :
    verb = "close"
    gerund = "closing"
    def __init__(self, actor, object) :
        self.args = [actor, object]

understand("close [something x]", Close(actor, x))

xobj_accessible(Close(actor, BObject(x)))

@before(Close(actor, BObject(x)))
def _before_close1(actor, x, context) :
    raise AbortAction("{Bob|cap} {can't} close that.", actor=x)

@before(Close(actor, Openable(x)))
def _before_close_openable(actor, x, context) :
    if x["open"] and not x["openable"] :
        raise AbortAction(x["no_close_msg"], actor=actor)
    elif not x["open"] :
        raise AbortAction(x["already_closed_msg"], actor=actor)
    raise ActionHandled()

@when(Close(actor, Openable(x)))
def _when_close_openable(actor, x, context) :
    x["open"] = False

@after(Close(actor, Openable(x)))
def _after_close_opneable(actor, x, context) :
    context.write_line("Closed.")

@before(Close(actor, Lockable(x)))
def _before_close_lockable(actor, x, context) :
    if x["open"] and x["locked"] :
        raise AbortAction(x["no_close_msg"], actor=actor)

##
# Unlock and UnlockWith  (I don't want to do Lock and LockWith right now).
##
class Unlock(BasicAction) :
    verb = "unlock"
    gerund = "unlocking"
    def __init__(self, actor, object) :
        self.args = [actor, object]

understand("unlock [something x]", Unlock(actor, x))

xobj_accessible(Unlock(actor, BObject(x)))

@before(Unlock(actor, BObject(x)))
def _before_unlock1(actor, x, context) :
    raise AbortAction("{Bob|cap} {can't} unlock that.", actor=actor)

@verify(Unlock(actor, Lockable(x)))
def _verify_unlock_lockable(actor, x, context) :
    return VeryLogicalOperation()

@before(Unlock(actor, Lockable(x)))
def _before_unlock_lockable(actor, x, context) :
    if x["locked"] and not x["lockable"] :
        raise AbortAction(x["no_unlock_msg"], actor=actor)
    elif not x["locked"] :
        raise AbortAction(x["already_unlocked_msg"], actor=actor)
    elif len(x["keys"]) > 0 :
        raise AbortAction(x["unlock_needs_key_msg"], actor=actor)
    raise ActionHandled()

@when(Unlock(actor, Lockable(x)))
def _when_unlock_lockable(actor, x, context) :
    x["locked"] = False

@after(Unlock(actor, Lockable(x)))
def _after_unlock_lockable(actor, x, context) :
    context.write_line("Unlocked.")

class UnlockWith(BasicAction) :
    verb = "unlock"
    gerund = ("unlocking","with")
    def __init__(self, actor, object, key) :
        self.args = [actor, object, key]

understand("unlock [something x] with [something y]", UnlockWith(actor, x, y))

xobj_accessible(UnlockWith(actor, BObject(x), y))
xobj_held(UnlockWith(actor, z, BObject(x)))

@verify(UnlockWith(actor, Lockable(x), BObject(y)))
def _before_unlockwith1(actor, x, y, context) :
    return VeryLogicalOperation()

@before(UnlockWith(actor, BObject(x), BObject(y)))
def _before_unlockwith1(actor, x, y, context) :
    """Whether we can unlock is related to whether x can be
    unlocked."""
    event_notify(Before(Unlock(actor, x)), context=context)

@before(UnlockWith(actor, Lockable(x), BObject(y)))
def _before_unlockwith_lockable(actor, x, y, context) :
    if y.id not in x["keys"] :
        raise AbortAction(x["wrong_key_msg"], actor=actor)
    else :
        raise ActionHandled()

@when(UnlockWith(actor, Lockable(x), y))
def _when_unlockwith_lockable(actor, x, y, context) :
    x["locked"] = False

@after(UnlockWith(actor, Lockable(x), y))
def _after_unlock_lockable(actor, x, y, context) :
    context.write_line("Unlocked.")

##
# OpenWith.  First unlock, then open
##

class OpenWith(BasicAction) :
    verb = "open"
    gerund = ("open", "with")
    def __init__(self, actor, object, key) :
        self.args = [actor, object, key]

understand("open [something x] with [something y]", OpenWith(actor, x, y))

@verify(OpenWith(actor, x, y))
def _verify_openwith1(actor, x, y, context) :
    return verify_action(UnlockWith(actor, x, y), context=context)
@verify(OpenWith(actor, x, y))
def _verify_openwith2(actor, x, y, context) :
    return verify_action(Open(actor, x), context=context)

@before(OpenWith(actor, x, y))
def _before_openwith(actor, x, y, context) :
    do_first(UnlockWith(actor, x, y), context=context)
    raise DoInstead(Open(actor, x), suppress_message=True)


##
# Attacking
##

class Attack(BasicAction) :
    verb = "attack"
    gerund = "attacking"
    def __init__(self, actor, attackee) :
        self.args = [actor, attackee]

understand("attack [something x]", Attack(actor, x))
understand("kill [something x]", Attack(actor, x))

xobj_accessible(Attack(actor, x))

@before(Attack(actor, x))
def _before_attack_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't attack that.", actor=actor)

##
# Reading
##

class Read(BasicAction) :
    verb = "read"
    gerund = "reading"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("read [something x]", Read(actor, x))

xobj_accessible(Read(actor, x))

@before(Read(actor, x))
def _before_read_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't read that.", actor=actor)

@verify(Read(actor, Readable(x)))
def _verify_read_readable(actor, x, context) :
    return VeryLogicalOperation()

@before(Read(actor, Readable(x)))
def _before_read_readable(actor, x, context) :
    raise ActionHandled()

@when(Read(actor, Readable(x)))
def _when_read_readable(actor, x, context) :
    context.write_line(x["read_msg"], actor=actor)

##
# Cutting
##

class Cut(BasicAction) :
    verb = "cut"
    gerund = "cutting"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("cut [something x]", Cut(actor, x))
xobj_accessible(Cut(actor, x))
@before(Cut(actor, x))
def _before_cut_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't cut that.", actor=actor)

class CutWith(BasicAction) :
    verb = "cut"
    gerund = ("cutting", "with")
    def __init__(self, actor, obj, cutter) :
        self.args = [actor, obj, cutter]

understand("cut [something x] with [something y]", CutWith(actor, x, y))

xobj_accessible(CutWith(actor, x, y))
xobj_held(CutWith(actor, z, x))

@before(CutWith(actor, x, y))
def _before_cut_default(actor, x, y, context) :
    raise AbortAction("{Bob|cap} can't do that.", actor=actor)

@before(CutWith(actor, Actor(x), y))
def _before_cut_actor(actor, x, y, context) :
    raise AbortAction("Violence isn't the answer to this one.")

##
# Eating
##

class Eat(BasicAction) :
    verb = "eat"
    gerund = "eating"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]
understand("eat [something x]", Eat(actor, x))
xobj_held(Eat(actor, x))
@before(Eat(actor, x))
def _before_eat_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't eat that.", actor=actor)

##
# Inserting
##

class InsertInto(BasicAction) :
    verb = "insert"
    gerund = ("inserting", "into")
    def __init__(self, actor, obj, dest) :
        self.args = [actor, obj, dest]
understand("insert [something x] into [something y]", InsertInto(actor, x, y))
understand("put [something x] into [something y]", InsertInto(actor, x, y))
understand("put [something x] in [something y]", InsertInto(actor, x, y))
understand("place [something x] into [something y]", InsertInto(actor, x, y))
understand("place [something x] in [something y]", InsertInto(actor, x, y))

xobj_held(InsertInto(actor, x, y))
xobj_accessible(InsertInto(actor, z, x))
@before(InsertInto(actor, x, y))
def _before_insertinto_default(actor, x, y, context) :
    raise AbortAction(str_with_objs("{Bob|cap} can't insert that into [the $y].", y=y),
                      actor=actor)

@verify(InsertInto(actor, BObject(x), Container(y)))
def _verify_insertinto_container(actor, x, y, context) :
    return VeryLogicalOperation()

@before(InsertInto(actor, BObject(x), Container(y)))
def _before_insertinto_container(actor, x, y, context) :
    raise ActionHandled()

@when(InsertInto(actor, BObject(x), Container(y)))
def _when_insertinto_container(actor, x, y, context) :
    x.move_to(y)

@after(InsertInto(actor, BObject(x), Container(y)))
def _after_insertinto_container(actor, x, y, context) :
    context.write_line("Inserted.")

##
# Climbing
##

class Climb(BasicAction) :
    verb = "climb"
    gerund = "climbing"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]
understand("climb [something x]", Climb(actor, x))
understand("go up [something x]", Climb(actor, x))

xobj_accessible(Climb(actor, x))
@before(Climb(actor, x))
def _before_climb_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't climb that.", actor=actor)

##
# Switching
##

class Switch(BasicAction) :
    verb = "switch"
    gerund = "switching"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]
understand("switch [something x]", Switch(actor, x))

xobj_accessible(Switch(actor, x))

@before(Switch(actor, x))
def _before_switch_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't switch that.", actor=actor)

@verify(Switch(actor, Device(x)))
def _verify_switch_device(actor, x, context) :
    return VeryLogicalOperation()

@before(Switch(actor, Device(x)))
def _before_switch_device(actor, x, context) :
    if x["switched_on"] :
        raise DoInstead(SwitchOff(actor, x))
    else :
        raise DoInstead(SwitchOn(actor, x))

# Switch on

class SwitchOn(BasicAction) :
    verb = "switch"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]
    def gerund_form(self, world) :
        return "switching %s on" % world[self.get_do()]["definite_name"]
understand("switch [something x] on", SwitchOn(actor, x))
understand("switch on [something x]", SwitchOn(actor, x))
understand("turn [something x] on", SwitchOn(actor, x))
understand("turn on [something x]", SwitchOn(actor, x))

xobj_accessible(SwitchOn(actor, x))

@before(SwitchOn(actor, x))
def _before_switchon_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't switch that on.", actor=actor)

@verify(SwitchOn(actor, Device(x)))
def _verify_switchon_device(actor, x, context) :
    if not x["switched_on"] :
        return VeryLogicalOperation()

@before(SwitchOn(actor, Device(x)))
def _before_switchon_device(actor, x, context) :
    if x["switched_on"] :
        raise AbortAction(x["no_switch_on_msg"])
    else :
        raise ActionHandled()

@when(SwitchOn(actor, Device(x)))
def _when_switchon_device(actor, x, context) :
    x["switched_on"] = True

@after(SwitchOn(actor, Device(x)))
def _after_switchon_device(actor, x, context) :
    context.write_line(x["switch_on_msg"], actor=actor)

# Switch off

class SwitchOff(BasicAction) :
    verb = "switch"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]
    def gerund_form(self, world) :
        return "switching %s off" % world[self.get_do()]["definite_name"]
understand("switch [something x] off", SwitchOff(actor, x))
understand("switch off [something x]", SwitchOff(actor, x))
understand("turn [something x] off", SwitchOff(actor, x))
understand("turn off [something x]", SwitchOff(actor, x))

xobj_accessible(SwitchOff(actor, x))

@before(SwitchOff(actor, x))
def _before_switchoff_default(actor, x, context) :
    raise AbortAction("{Bob|cap} can't switch that off.", actor=actor)

@verify(SwitchOff(actor, Device(x)))
def _verify_switchoff_device(actor, x, context) :
    if x["switched_on"] :
        return VeryLogicalOperation()

@before(SwitchOff(actor, Device(x)))
def _before_switchoff_device(actor, x, context) :
    if not x["switched_on"] :
        raise AbortAction(x["no_switch_off_msg"])
    else :
        raise ActionHandled()

@when(SwitchOff(actor, Device(x)))
def _when_switchoff_device(actor, x, context) :
    x["switched_on"] = False

@after(SwitchOff(actor, Device(x)))
def _after_switchoff_device(actor, x, context) :
    context.write_line(x["switch_off_msg"], actor=actor)

##
# Push
##

class Push(BasicAction) :
    verb = "push"
    gerund = "pushing"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("push [something x]", Push(actor, x))
understand("press [something x]", Push(actor, x))

xobj_accessible(Push(actor, x))

@before(Push(actor, x))
def _before_push_default(actor, x, context) :
    raise AbortAction("That can't be pushed.")

##
# Asking about
##

class AskAbout(BasicAction) :
    verb = "ask"
    gerund = ("asking", "about")
    def __init__(self, actor, questionee, obj) :
        self.args = [actor, questionee, obj]

understand("ask [something x] about [text y]", AskAbout(actor, x, y))

xobj_accessible(AskAbout(actor, x, y))

@before(AskAbout(actor, x, y))
def _before_ask_default(actor, x, y, context) :
    raise AbortAction("That doesn't seem like it would be interested.", actor=actor)

@before(AskAbout(actor, Actor(x), y))
def _before_ask_actor(actor, x, y, context) :
    """Actors have their own method to deal with these sorts of
    things."""
    raise ActionHandled()

@when(AskAbout(actor, Actor(x), y))
def _when_ask_actor(actor, x, y, context) :
    x.ask_about(y, context)
    raise ActionHandled()

##
# Giving to
##

class GiveTo(BasicAction) :
    verb = "give"
    gerund = ("giving", "to")
    def __init__(self, actor, obj, givee) :
        self.args = [actor, obj, givee]

understand("give [something x] to [something y]", GiveTo(actor, x, y))
xobj_held(GiveTo(actor, x, y))
xobj_accessible(GiveTo(actor, z, x))

@before(GiveTo(actor, x, y))
def _before_give_to_actor_default(actor, x, y, context) :
    raise AbortAction(str_with_objs("You can't give that to [the $y].", y=y), actor=actor)

@before(GiveTo(actor, x, Actor(y)))
def _before_give_to_actor_default(actor, x, y, context) :
    raise AbortAction(str_with_objs("[The $y] doesn't seem like [he $y] is interested in [the $x].",
                                    x=x, y=y), actor=actor)

###
### Commands which should be out of the game, but aren't yet.
###

##
# Help
##
class Help(BasicAction) :
    pass
understand("help", Help(actor))

@when(Help(actor))
def _help(actor, context) :
    context.write_line("""
So you want help?

You are controlling a character in the virtual world.  To play the
game, you must give the character commands to interact with its
surroundings.

Some examples of commands, which you may try out yourself to see what
they do, are:

look/l<br>
inventory/i<br>
examine/x (something)<br>
read (something)<br>
take (something)<br>
drop (something)<br>
go (direction)<br>
enter (enterable thing)<br>
open (something)<br>
close (something)<br>
unlock (something)<br>
unlock (something) with (something)<br>
ask (someone) about (something)<br>
give (something) to (someone)<br>
insert (something) into (something)

and so on.  Part of the fun is figuring out what you can do.

Since movement is something which is done quite often in these games,
"go (direction)" can be abbreviated to simply "(direction)", where the
cardinal directions "north", "south", ..., may be abbreviated to their
first letters "n", "s", ....

If you get stuck, don't forget to examine things, often times vital
clues are left in descriptions (it being a text-based game).
""")

##
# Quit
##
class Quit(BasicAction) :
    pass
understand("quit", Quit(actor))
understand("quit game", Quit(actor))

@when(Quit(actor))
def _quit(actor, context) :
    finish_game(ExitGame())


###
### Debugging words
###

##
# DebugDump (dump out object data, for testing)
##
class DebugDump(BasicAction) :
    verb = "dump"
    gerund = "dumping"
    def __init__(self, actor, obj) :
        self.args = [actor, obj]

understand("debug_dump [anything x]", DebugDump(actor, x))
understand("debug_dump", DebugDump(actor, None))

@when(DebugDump(actor, x))
def _when_dump(actor, x, context) :
    if x is None :
        context.write_line("** Dumping world **")
        context.write_line(escape_str(repr(context.world)))
        context.write_line("** End dump **")
    else :
        msg = "** Dumping %s **\n\n" % x.id
        msg += escape_str(repr(x._get_data()))
        msg += "\n\n** End dump **"
        context.write_line(msg)

##
# DebugWhatsHere
##
class DebugWhatsHere(BasicAction) :
    def __init__(self, actor) :
        self.args = [actor]

understand("debug_whats_here", DebugWhatsHere(actor))

@when(DebugWhatsHere(actor))
def _when_debug_here(actor, context) :
    msg = "* Objects: *<br>"
    msg += escape_str(repr(actor.get_location().get_objects()))
    msg += "\n\n* words; *<br>"
    msg += escape_str(repr([o["words"] for o in actor.get_location().get_objects()]))
    context.write_line(msg)

##
# DebugParser
##
class DebugParser(BasicAction) :
    def __init__(self, actor) :
        self.args = [actor]

understand("debug_parser", DebugParser(actor))

@when(DebugParser(actor))
def _when_debug_parser(actor, context) :
    context.write_line(escape_str(repr(context.parser)))


##
# MagicTake (take anything in the game)
##

class MagicTake(BasicAction) :
    verb = "magic-take"
    gerund = "magic-taking"

understand("magic_take [anything x]", MagicTake(actor, x))

@when(MagicTake(actor, BObject(x)))
def _when_magic_take(actor, x, context) :
    x.give_to(actor)
    x["reported"] = True
    context.write_line(str_with_objs("{Bob|cap} magically took [the $x].", x=x))

##
# MagicGo (goes anywhere in the game, using the id of the place)
##

class MagicGo(BasicAction) :
    verb = "magic-go"
    gerund = "magic-going to"

understand("magic_go [text x]", MagicGo(actor, x))

@when(MagicGo(actor, x))
def _when_magic_go(actor, x, context) :
    actor.move_to(x)
    context.write_line(str_with_objs("Poof, {bob} {is} at [the $x].", x=x), actor=actor)
