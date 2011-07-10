# testgame.py
#
# a test of the game engine

execfile("textadv/basicsetup.py")

world[Global("game_title")] = "Test game"
world[Global("game_author")] = "Kyle Miller"

##
## Rat region
##

quickdef(world, "rat region", "region")

quickdef(world, "rat", "backdrop", {
        Name : "big fat rat",
        NoTakeMessage : "It moves too fast for you to catch it.",
        Description : """The rat looks like it's been eating quite a
        lot.  You are somewhat confused, though, since rats don't live
        on the fourth floor.""",
        BackdropLocations : ["rat region"]
        })

parser.understand("catch [object rat]", Taking(actor, "rat"))

quickdef(world, "sky", "backdrop", {
        Words : ["boston", "@skyline", "@sky"],
        Description : """You look out the window and see a bit of the
        Boston skyline.""",
        BackdropLocations : ["rat region"]
        })

##
## The Verifier
##

quickdef(world, "verifier", "person", {
        Name : "The Verifier",
        ProperNamed : True,
        Description : """The Verifier always thinks what you do is a
        good idea."""
        })

@report(X <= PEquals(Location("verifier"), Location("player")))
def _verifier_whenever(x, ctxt) :
    if x.get_actor() == ctxt.actor :
        if type(x) is Taking :
            ctxt.write(str_with_objs("[newline]\"My, I would have never thought of taking [the $z],\" notes The Verifier.", z=x.get_do()))
        else :
            ctxt.write("[newline]\"What a wonderful idea to "+x.infinitive_form(ctxt)+"!\" cries The Verifier.")

@actoractivities.to("step_turn")
def _verifier_step_turn(ctxt) :
    if ctxt.world[Location("player")] != ctxt.world[Location("verifier")] :
        ctxt.write("The Verifier follows.")
        ctxt.world.activity.put_in("verifier", ctxt.world[Location("player")])

##
## Your pocket
##

quickdef(world, "pocket", "container", {
        Description : """It's your pocket."""
        })
world.activity.make_part_of("pocket", "player")

quickdef(world, "key", "thing", {
        Name : "useful key",
        IndefiniteName : "a useful key",
        Description : """It looks like it can open anything."""
        })
world.activity.put_in("key", "pocket")

@before(Examining("player", "pocket") <= Contains("pocket", "key"))
def _before_examine_pocket_with_key(ctxt) :
    ctxt.write("The key was in your pocket all along.")
    raise DoInstead(Taking("player", "key"))

##
## The continuation
##

world.add_relation(KindOf("continuation", "container"))

quickdef(world, "purple continuation", "continuation", {
        Description : """It's a purple continuation.  Can this be?"""
        })
quickdef(world, "brown continuation", "continuation", {
        Description : """It's a purple continuation.  Can this be?"""
        })
world.activity.put_in("purple continuation", "room_41")
world.activity.put_in("brown continuation", "room_41")

@world.define_property
class ContinuationData(Property) :
    numargs = 1

world[ContinuationData(X)] = None

@before(InsertingInto(actor, X, Y) <= IsA(Y, "continuation") & PNot(PEquals(Owner(Y), actor)))
def _before_inserting_into_continuation_if_not_owner(actor, x, y, ctxt) :
    raise AbortAction("You have to be holding the continuation.")

@when(InsertingInto(actor, X, Y) <= IsA(Y, "continuation"))
def _when_inserting_into_continuation(actor, x, y, ctxt) :
    old_world = ctxt.world
    ctxt.world = old_world[ContinuationData(y)]
    ctxt.world.activity.give_to(x, actor)
    if old_world[ContinuationData(x)] : # for if the passed object is a continuation
        ctxt.world[ContinuationData(x)] = old_world[ContinuationData(x)]
    raise ActionHandled()

@report(InsertingInto(actor, X, Y) <= IsA(Y, "continuation"))
def _report_inserting_into_continuation(actor, x, y, ctxt) :
    ctxt.write(str_with_objs("Bewildered, you find the world as it was, but {bob} {is} now holding [the $x].", x=x), actor=actor)
    raise ActionHandled()

@when(Taking(actor, X) <= IsA(X, "continuation") & PNot(ContinuationData(X)))
def _when_taking_continuation(actor, x, ctxt) :
    ctxt.world[ContinuationData(x)] = ctxt.world.copy()

@actoractivities.to("describe_object", insert_before=describe_object_default)
def describe_object_continuation(actor, o, ctxt) :
    if ctxt.world[IsA(o, "continuation")] and ctxt.world[ContinuationData(o)] :
        ctxt.write("The continuation is ready something to be inserted into it.")

##
## Room 41
##

quickdef(world, "room_41", "room", {
        Name : "41",
        Description : """This is a room on the fourth floor of tep.
        It is currently home to Kyle.  There is a bed and a loft.
        There is an exit to the [dir north]."""
        })
world.activity.put_in("room_41", "rat_region")

world.activity.put_in("player", "room_41")
world.activity.put_in("verifier", "room_41")

quickdef(world, "red ball", "thing", {
        Description : """It's simply a red ball.  Round like a
        sphere."""
        })
world.activity.put_in("red ball", "room_41")

quickdef(world, "blue ball", "thing", {
        Description : """It's a blue ball.  Like something blue."""
        })
world.activity.put_in("blue ball", "room_41")

quickdef(world, "green ball", "thing", {
        Words : ["amazing", "green", "@ball"],
        IndefiniteName : "an amazing green ball",
        Description : """It's a green ball.  Like grass, but not
        quite.""",
        })
world.activity.put_in("green ball", "room_41")

@before(Taking(actor, "green ball"))
def _instead_taking_green_ball(actor, ctxt) :
    ctxt.write("{Bob} actually {wants} the blue ball.", actor=actor)
    raise DoInstead(Taking(actor, "blue ball"))


quickdef(world, "light", "thing", {
        Description : "It's a light."
        })
world.activity.put_in("light", "room_41")

quickdef(world, "light bulb", "thing", {
        Description : "It's a light bulb."
        })
world.activity.put_in("light bulb", "room_41")

quickdef(world, "zombocom", "container", {
        IsEnterable : True,
        ProperNamed : True,
        Description : """[if [when zombocom Contains]]Welcome to
        zombocom.[else]This is zombocom.  It looks like you can enter
        it.[endif]"""
        })
world.activity.put_in("zombocom", "room_41")

world[NotableDescription("player") <= PEquals(Location("player"), "zombocom")] = "You are standing here, cognizant of the possibilities."

@report(Entering(actor, "zombocom"))
def _report_enter_zombocom(actor, ctxt) :
    ctxt.write("Anything is possible...")


quickdef(world, "compliant robot", "person", {
        Gender : "none",
        Description : "It's a robot that will do anything you ask of it."
        })
world.activity.put_in("compliant robot", "room_41")

@actoractivities.to("npc_is_willing")
def robot_is_willing_default(requester, action, ctxt) :
    """The robot is willing to do anything!"""
    if action.get_actor() == "compliant robot" :
        raise ActionHandled()

@actoractivities.to("npc_is_wanting")
def robot_is_wanting_default(giver, object, receiver, ctxt) :
    """The robot wants everything!"""
    if receiver=="compliant robot" :
        raise ActionHandled()

quickdef(world, "table", "supporter", {
        Scenery : True,
        Description : "It's a wood table."
        })
world.activity.put_in("table", "room_41")

quickdef(world, "peanuts", "thing", {
        IndefiniteName : "some peanuts",
        Description : "It's just a pile of peanuts."
        })
world.activity.put_on("peanuts", "table")

##
## Room2
##

quickdef(world, "room2", "room", {
        Name : "Another Room",
        Description : """It's another room.  I don't know what to say.
        You can go [dir south]."""
        })

quickdef(world, "old door", "door", {
        Lockable : True,
        IsLocked : True,
        KeyOfLock : "key",
        Description : """It's a door.  It's made of wood, and has been
        here longer than you have.  It is [get IsOpenMsg <old
        door>]."""
        })
world.activity.connect_rooms("old door", "south", "room_41")
world.activity.connect_rooms("old door", "north", "room2")
