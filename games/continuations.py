# continuations.py
#
# A puzzle based on continuations

execfile("textadv/basicsetup.py")

world[Global("game_title")] = "Continuations"
world[Global("game_headline")] = "A Puzzle"
world[Global("game_author")] = "Kyle Miller"

##
## Relation: Attachment
##

# Attachment
@world.define_relation
class AttachedTo(DirectedManyToManyRelation) :
    """AttachedTo(x, y) for x is attached to y (non-commutative)."""

@world.to("attach_to")
def prop_set_attached(x, y, world) :
    """Attaches x and y together.  Does not remove prior relations."""
    world.add_relation(AttachedTo(x, y))

@world.to("detach")
def prop_detach(x, world) :
    """Removes attachment of x to anything else."""
    world.remove_relation(AttachedTo(x, Y))

@before(Taking(actor, X))
def before_taking_attached(actor, x, ctxt) :
    a = ctxt.world.query_relation(AttachedTo(x, Y), var=Y)
    if a :
        raise AbortAction(str_with_objs("It's attached to [the $y].", y=a[0]))


##
## Defining: continuation
##

world.add_relation(KindOf("continuation", "container"))

@world.define_property
class ContinuationData(Property) :
    """A tuple (receiver, world_data)."""
    numargs = 1

world[ContinuationData(X)] = None

require_xobj_held(actionsystem, InsertingInto(actor, Z, X) <= IsA(X, "continuation"), only_hint=True)

@before(InsertingInto(actor, X, Y) <= IsA(Y, "continuation") & PNot(PEquals(Owner(Y), actor)))
def before_inserting_into_continuation_if_not_owner(actor, x, y, ctxt) :
    raise AbortAction("You have to be holding the continuation to put anything into it.")

@when(InsertingInto(actor, X, Y) <= IsA(Y, "continuation"))
def when_inserting_into_continuation(actor, x, y, ctxt) :
    old_world = ctxt.world
    (receiver, ctxt.world) = old_world[ContinuationData(y)]
    ctxt.world.activity.give_to(x, receiver)
    if old_world[ContinuationData(x)] : # for if the passed object is a continuation
        ctxt.world[ContinuationData(x)] = old_world[ContinuationData(x)]
    raise ActionHandled()

@report(InsertingInto(actor, X, Y) <= IsA(Y, "continuation"))
def report_inserting_into_continuation(actor, x, y, ctxt) :
    ctxt.write(str_with_objs("Bewildered, you find the world as it was, but {bob} {is} now holding [the $x].", x=x), actor=actor)
    raise ActionHandled()

@when(Taking(actor, X) <= IsA(X, "continuation")) # re-taking should clear data # & PNot(ContinuationData(X)))
def when_taking_continuation(actor, x, ctxt) :
    ctxt.world[ContinuationData(x)] = (actor, ctxt.world.copy())

@actoractivities.to("describe_object", insert_before=describe_object_default)
def describe_object_continuation(actor, o, ctxt) :
    if ctxt.world[IsA(o, "continuation")] and ctxt.world[ContinuationData(o)] :
        ctxt.write("The continuation seems ready for something to be inserted into it.")

##
## The Trophy Room
##

world.activity.put_in("player", "The Trophy Room")

quickdef(world, "The Trophy Room", "room", {
        Description : """This is your trophy room, where you keep all
        your trophies.  That is, if you had any.  It's for good
        reason, you think to yourself: you've been after the fabled
        [ob <Argentinian mongoose chair>] for some time, and it'll be
        yours.  It will be.  There's a [ob pedestal] here just waiting
        for it, and you feel today's the day you'll actually acquire
        it.  Yes, you can see how amazing the chair will be upon that
        pedestal.  To the [dir north] is where they've been keeping
        your Argentinian mongoose chair."""
        })

quickdef(world, "pedestal", "supporter", {
        Scenery : True,
        Description : """This is the pedestal you erected a couple of
        years ago to hold your [ob <Argentinian mongoose chair>].
        Yes, yes, it is yours.  Aimed at the pedestal is [ob <stage
        lighting>] to make your acquisition look even more brilliant,
        once it's on the pedestal."""
        },
         put_in="The Trophy Room")

@report(PlacingOn(actor, "Argentinian mongoose chair", "pedestal"))
def report_putting_chair_on_pedestal(actor, ctxt) :
    ctxt.write("""You carefully place your Argentinian mongoose chair
    on the pedestal and burst into tears.  "It's so beautiful," you
    say to yourself.  Your trophy room is now complete.""")
    ctxt.activity.end_game_saying("You have won")
    raise ActionHandled()

quickdef(world, "stage lighting", "thing", {
        Scenery : True,
        Description : """This is the stage lighting you installed a
        couple of years ago to illuminate your Argentinian mongoose
        chair.  It will be so wonderful to finally have your chair on
        that pedestal!"""
        },
         put_in="The Trophy Room")

@verify(Examining(actor, "Argentinian mongoose chair"))
def always_can_examine(actor, ctxt) :
    raise ActionHandled(LogicalOperation())

@when(Examining(actor, "Argentinian mongoose chair") <= PNot(VisibleTo("Argentinian mongoose chair", actor)))
def when_examining(actor, ctxt) :
    ctxt.write("""Although it's nowhere around, in your minds eye, you
    can see the Argentinian mongoose chair sitting smartly on that
    pedestal you built.  It will be yours.  No, no: it <i>is</i>
    yours.""")
    raise ActionHandled()

quickdef(world, "workbench", "supporter", {
        Scenery : True,
        Description : """This is the workbench where you've been
        putting together everything you need to finally acquire your
        Argentinian mongoose chair."""
        },
         put_in="The Trophy Room")

quickdef(world, "blue continuation", "continuation", {
        Description : """This is one of the two continuations you
        built to finally acquire your Argentinian mongoose chair.  You
        painted them different colors so you could tell them apart.
        To operate them, you first take one.  Then, if you put
        anything into it, you'll find that object in your possession
        rather than the continuation.  They reset every time you drop
        them."""
        },
         put_on="workbench")

quickdef(world, "red continuation", "continuation", {
        Description : """This is one of the two continuations you
        built to finally acquire your Argentinian mongoose chair.  You
        painted them different colors so you could tell them apart.
        To operate them, you first take one.  Then, if you put
        anything into it, you'll find that object in your possession
        rather than the continuation. They reset every time you drop
        them."""
        },
         put_on="workbench")

quickdef(world, "small coin", "thing", {
        Description : """It's a small coin which you've been using to
        experiment with your continuations."""
        },
         put_on="workbench")

quickdef(world, "wire snips", "thing", {
        Name : "pair of wire snips",
        Description : """These are standard-issue wire snips.  Very
        handy (and ergonomic!)"""
        },
         put_on="workbench")
parser.understand("snip [something x] with [something y]", CuttingWith(actor, X, Y))

world.activity.connect_rooms("The Trophy Room", "north", "The Store")

##
## The Store
##

quickdef(world, "The Store", "room", {
        Description : """This store is where they have your
        Argentinian mongoose chair.  Why it's not on your pedestal
        already, you do not know.  To the [dir north] is where they
        keep it."""
        })
world.activity.connect_rooms("The Store", "north", "The Storeroom")

quickdef(world, "store clerk", "person", {
        Gender : "female",
        Description : """This store clerk has been depriving you of
        your Argentinian mongoose chair for years.  Today's the day
        that you'll show her, though.  You will show her."""
        },
         put_in="The Store")

@before(Going(actor, "north") <= PEquals("The Store", Location(actor)) & PEquals("player", Owner("wire snips")))
def prevent_going_with_snips(actor, ctxt) :
    raise AbortAction("\"Hey! Where are you going with those wire snips!\" yells the store clerk.  \"Those are <i>not</i> allowed in the storeroom.\"[newline]Drat.")

@before(Going(actor, "south") <= PEquals("The Store", Location(actor)) & PEquals("player", Owner("Argentinian mongoose chair")))
def prevent_going_with_snips(actor, ctxt) :
    raise AbortAction("""The store clerk asks you, \"are you going to
    pay for that?  It'll be $10.\" You tell her that you do not plan
    to pay for the chair, because it's <i>your</i> chair.  She says
    that it is not your chair, but her chair, and that you are not to
    leave without paying first.  She looks scary, so you decide not to
    try leaving the store with the chair.""")

world[Global("fixed_wire")] = False
world[Global("took_snips")] = False
world[Global("snips_were_in_storeroom")] = False

@actoractivities.to("step_turn")
def repair_when_not_in_room(ctxt) :
    drats = 0
    if "The Storeroom" != ctxt.world[ContainingRoom("player")] :
        if ctxt.world[Location("thick wire")] == None and ctxt.world[Location("Argentinian mongoose chair")] == "The Storeroom":
            ctxt.world.activity.put_in("thick wire", "The Storeroom")
            ctxt.world.activity.attach_to("Argentinian mongoose chair", "thick wire")
            ctxt.world[Global("fixed_wire")] = True
    if ctxt.world[Global("fixed_wire")] and ctxt.world[Location("player")] == "The Store" :
        ctxt.write("""The clerk leaves to go into the storeroom.  In a
        moment, she returns and says to you, "I don't know how you
        managed to cut that wire, but I've repaired it.  No more funny
        business, OK?"[newline]Drat.""")
        drats += 1
        ctxt.world[Global("fixed_wire")] = False
    if ctxt.world[Owner("wire snips")] != "player" and ctxt.world[ContainingRoom("player")] != ctxt.world[ContainingRoom("wire snips")] :
        if ctxt.world[ContainingRoom("wire snips")] in ["The Store", "The Storeroom"] and ctxt.world[Owner("wire snips")] != "store clerk" :
            ctxt.world[Global("snips_were_in_storeroom")] = (ctxt.world[Location("wire snips")] == "The Storeroom")
            ctxt.world.activity.give_to("wire snips", "store clerk")
            ctxt.world[Global("took_snips")] = True
    if ctxt.world[Global("took_snips")] and ctxt.world[Location("player")] == "The Store" :
        if drats :
            ctxt.write("""[newline]"I also found some [ob <wire
            snips>].  I don't want to see them in this store
            again."[newline]Double drat.""")
        elif ctxt.world[Global("snips_were_in_storeroom")] :
            ctxt.write("""The clerk leaves to go into the storeroom.
            In a moment, she returns and says to you, "I found some
            [ob <wire snips>].  I don't want to see them in this store
            again."[newline]Drat.""")
        else :
            ctxt.write(""" "I found some wire snips.  I don't want to
            see them in this store again."[newline]Drat.""")
        drats += 1
        ctxt.world[Global("took_snips")] = False

@actoractivities.to("npc_is_willing")
def let_clerk_give_snips(asker, action, ctxt) :
    if asker == "player" and type(action) == GivingTo and action.get_actor() == "store clerk" :
        if action.get_do() == "wire snips" :
            ctxt.write("\"I'll give them to you, but only because I don't want them in my store,\" she cautions.")
            raise ActionHandled()
        elif action.get_do() == "Argentinian mongoose chair" :
            raise AbortAction("\"That'll be $10 for the chair,\" replies the store clerk.  The nerve of her.")
        else :
            raise NotHandled()
    else : raise NotHandled()

class Paying(BasicAction) :
    verb = "pay"
    gerund = "paying"
    numargs = 2
parser.understand("pay [something x]", Paying(actor, X))

require_xobj_accessible(actionsystem, Paying(actor, X))

@before(Paying(actor, X))
def before_paying_cant(actor, x, ctxt) :
    raise AbortAction(str_with_objs("You need something with which to pay [the $x].", x=x), actor=actor)

class PayingWith(BasicAction) :
    verb = ("pay", "with")
    gerund = ("paying", "with")
    numargs = 3
parser.understand("pay [something x] with [something y]", PayingWith(actor, X, Y))

require_xobj_accessible(actionsystem, PayingWith(actor, X, Y))
require_xobj_held(actionsystem, PayingWith(actor, Z, X))

@before(PayingWith(actor, X, Y))
def before_payingwith_cant(actor, x, y, ctxt) :
    raise AbortAction(str_with_objs("[The $x] doesn't look interested in being paid.", x=x), actor=actor)
@before(PayingWith(actor, "store clerk", Y))
def before_payingwith_store_clerk_anything(actor, y, ctxt) :
    raise AbortAction("\"You call that currency?\" asks the store clerk, sneering at you.")
@before(PayingWith(actor, "store clerk", "small coin"))
def before_payingwith_store_clerk_coin(actor, ctxt) :
    raise AbortAction("The store clerk laughs.  \"That's hardly enough to pay for <i>anything</i> in this store.\"")

@before(GivingTo(actor, X, "store clerk"))
def before_givingto_clerk(actor, x, ctxt) :
    raise DoInstead(PayingWith(actor, "store clerk", x), suppress_message=True)

##
## the Storeroom
##

quickdef(world, "The Storeroom", "room", {
        Description : """Ah, yes.  This is where they keep it.  Why
        they keep it under such terrible [ob <fluorescent lighting>],
        you have no idea."""
        })

quickdef(world, "fluorescent lighting", "thing", {
        Scenery : True,
        Description : """In the tradition of having terrible light
        pollution in stores, there are too many fluorescent lights,
        ruining the view of your [ob <Argentinian mongoose chair>]."""
        },
         put_in="The Storeroom")

quickdef(world, "Argentinian mongoose chair", "supporter", {
        IsEnterable : True,
        Description : """It's beautiful!  Tears come to your eyes just
        looking at it.  You ogle at its back support.  You rub you
        hand across the smooth, black leather.  You are glad that it
        is yours, despite what the store clerk thinks."""
        },
         put_in="The Storeroom")

parser.understand("sit on/in [object Argentinian mongoose chair]", Entering(actor, "Argentinian mongoose chair"))

@before(Dropping(actor, "Argentinian mongoose chair") <= PEquals("The Store", ContainingRoom(actor)))
def cant_drop_chair_in_store(actor, ctxt) :
    ctxt.world.activity.put_in("Argentinian mongoose chair", "The Storeroom")
    raise AbortAction("\"Hey!\" yells the store clerk.  \"What do you think you're doing?  I'll take that chair, thank you very much.\"")

quickdef(world, "eye bolt", "thing", {
        Scenery : True,
        NoTakeMessage : """It's firmly cemented into the floor.
        There's no chance of taking that.""",
        Description : """This eyebolt was installed after you tried
        taking the [ob <Argentinian mongoose chair>] by more
        conventional means."""
        },
         put_in="The Storeroom")
            

quickdef(world, "thick wire", "thing", {
        Scenery : True,
        NoTakeMessage : """It is wrapped around the [ob <Argentinian
        mongoose chair>] and the [ob <eye bolt>].  There is no chance
        you'll be able to remove it without a tool.""",
        Description : """This thick wire is wrapped through the eye
        bolt, around the [ob <Argentinian mongoose chair>], and welded
        back onto itself.  It was installed after you tried to walk
        off with your chair.  The nerve of that store clerk."""
        },
         put_in="The Storeroom")

world.activity.attach_to("Argentinian mongoose chair", "thick wire")

@before(Cutting(actor, "thick wire"))
def before_cutting_default(actor, ctxt) :
    raise AbortAction("You can't cut the thick wire without some tool.  It's thick!")

@trybefore(CuttingWith(actor, "thick wire", Y) <= PEquals(actor, Y))
def trybefore_cancel_taking_self(actor, y, ctxt) :
    """This is trybefore to prevent trying to take self."""
    raise AbortAction("That sounds like it would hurt.")

@before(CuttingWith(actor, "thick wire", Y))
def before_cutting_wire_with_default(actor, y, ctxt) :
    raise AbortAction(str_with_objs("You try to cut the thick wire with [the $y] for a while, but then give up out of frustration.", y=y), actor=actor)

@before(CuttingWith(actor, "thick wire", "wire snips"))
def before_cutting_wire_with_snips(actor, ctxt) :
    raise ActionHandled()

@when(CuttingWith(actor, "thick wire", "wire snips"))
def when_cutting_wire_with_snips(actor, ctxt) :
    ctxt.world.activity.detach("Argentinian mongoose chair")
    ctxt.world.activity.remove_obj("thick wire")

@report(CuttingWith(actor, "thick wire", "wire snips"))
def report_cutting_wire_with_snips(actor, ctxt) :
    ctxt.write("""You snip the wire here and there, and free your
    Argentinian mongoose chair.  All you need to do is bring your
    chair back to your pedestal!  So that nobody is the wiser, you
    hide the remnants of the thick wire where nobody can see them.""")

@trybefore(Cutting(actor, "Argentinian mongoose chair"))
@trybefore(CuttingWith(actor, "Argentinian mongoose chair", Y))
@trybefore(Attacking(actor, "Argentinian mongoose chair"))
def disallow_hurting_chair(actor, ctxt, y=None) :
    """These are trybefore to prevent trying to take anything."""
    raise AbortAction("You would <i>never</i> even consider such a thing.")
