# isleadv.py
#
# by Kyle Miller, 2011
#
# a reimplementation of Island Adventure, which I had written before
# in Inform 7

execfile("textadv/basicsetup.py")
#from textadv.basicsetup import *

world[Global("game_title")] = "Island Adventure"
world[Global("game_author")] = "Kyle Miller"
world[Global("game_description")] = """
You decided to stop what you were doing and wash up on an island.[newline]
You're not quite sure how you got here, or what you're supposed to do,
but you feel that Adventure is afoot."""

##
## Fun and games
##


@before(Attacking(actor, X) <= PEquals(actor, X))
def _before_suicide(actor, x, ctxt) :
    raise AbortAction("Suicide is not the answer.", actor=actor)

##
## Properties
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

# Fishing

world.add_relation(KindOf("fishing rod", "thing"))

class Fishing(BasicAction) :
    verb = "fish"
    gerund = "fishing"
    numargs = 1
class FishingWith(BasicAction) :
    verb = "fish"
    gerund = "fishing with"
    numargs = 2

parser.understand("fish", Fishing(actor))
parser.understand("fish with [something x]", FishingWith(actor, X))
parser.understand("catch fish with [something x]", FishingWith(actor, X))

@before(Fishing(actor))
def before_fishing_default(actor, ctxt) :
    rods = [rod for rod in ctxt.world.query_relation(Has(actor, X), var=X) if ctxt.world[IsA(rod, "fishing rod")]]
    if len(rods) > 1 :
        raise Ambiguous(FishingWith(actor, X), {X : rods}, {X : "something"})
    elif len(rods) == 1 :
        raise DoInstead(FishingWith(actor, rods[0]))
    else :
        raise AbortAction("The last time I checked it was very hard to catch fish without a pole.")

require_xobj_held(actionsystem, FishingWith(actor, X))

@before(FishingWith(actor, X) <= PNot(IsA(X, "fishing rod")))
def before_fishingwith_default(actor, x, ctxt) :
    if ctxt.world[IsA(x, "person")] :
        raise AbortAction(str_with_objs("""It doesn't look like [the $x] wants to help.""",
                                        x=x))
    else :
        raise AbortAction(str_with_objs("""{Bob|cap} would have a
                                        hard time catching fish with [the $x]""", x=x))

@before(FishingWith(actor, X) <= IsA(X, "fishing rod"))
def before_fishingwith_rod(actor, x, ctxt) :
    if not ctxt.world[ContainingRoom(actor)] == "room_the_dock" :
        raise AbortAction("""You have to be on a fishing dock to have
        deep enough water to fish.""")
    elif ctxt.world.query_relation(Has(actor, "the_fish")) :
        raise AbortAction("""You have a fish already. You don't need
        another.""")
    else :
        raise ActionHandled()

@when(FishingWith(actor, X) <= IsA(X, "fishing rod"))
def when_fishingwith_rod(actor, x, ctxt) :
    ctxt.world.activity.give_to("the_fish", actor)

@report(FishingWith(actor, X) <= IsA(X, "fishing rod"))
def report_fishingwith_rod(actor, x, ctxt) :
    ctxt.write("""As soon as the hook reaches the surface of the
    water, a swarm of fish swim at it.  One lucky fish bites and you
    pull.  You catch a fish.[newline]Taken.""")


quickdef(world, "the_fish", "thing", {
        Name : "fish",
        Description : """It is a flounder.  It doesn't look that
appetizing, as both eyes are on one side of its head.""",
        })

@before(Eating(actor, "the_fish"))
def before_eating_fish(actor, ctxt) :
    raise AbortAction("It doesn't look that appetizing.")

# Sky region

quickdef(world, "region_sky", "region")
world.activity.put_in("region_beach", "region_sky")
world.activity.put_in("region_village", "region_sky")
world.activity.put_in("room_west_volcano", "region_sky")

quickdef(world, "the_sky", "backdrop", {
        Name : "sky",
        BackdropLocations : ["region_sky"],
        Description : """The sky is cloudless and full of sun.  A bird
        flies by occasionally.""",
        })

###
### Beach region
###

quickdef(world, "region_beach", "region")
world.activity.put_in("room_the_beach", "region_beach")
world.activity.put_in("room_the_dock", "region_beach")
world.activity.put_in("room_more_beach", "region_beach")

quickdef(world, "beach_ocean", "backdrop", {
        Name : "ocean",
        BackdropLocations : ["region_beach"],
        Description : """The water is aquamarine with perfect white
        sand underfoot.""",
        })

@before(Going(actor, "south") <= Contains("region_beach", actor))
def _before_going_south_beach_area(actor, ctxt) :
    raise DoInstead(SwimmingIn(actor, "beach_ocean"))


@before(Swimming(actor))
def _before_swimming(actor, ctxt) :
    if ctxt.world[AccessibleTo("beach_ocean", actor)] :
        raise DoInstead(SwimmingIn(actor, "beach_ocean"))

@before(SwimmingIn(actor, X))
def _before_swimming_in(actor, x, ctxt) :
    raise AbortAction("You can't just swim without a swimsuit. Heaven forbid!")

##
## The beach
##

world.activity.put_in("player", "room_the_beach")

quickdef(world, "room_the_beach", "room", {
        Name : "The Beach",
        Description : """Crystal clear water and lots of sand.  The
        air is warm but not too humid, and it seems it would be the
        perfect place to go swimming.  Some docks are visible to the
        [dir west]."""
        })
world[NoGoMessage("room_the_beach", "east")] = """The beach just keeps
going.  Long walks on the beach aren't going to solve anything."""
world[NoGoMessage("room_the_beach", "north")] = """The jungle is too
thick.  Besides, the wild animals might be dangerous."""

world.activity.connect_rooms("room_the_beach", "west", "room_the_dock")

quickdef(world, "informational plaque", "thing", {
        Description : """Some writing can be made out, quite easily
        actually, since, by the look of it, it is burnt into a sheet
        of titanium by a carbon dioxide laser.  It reads 'Go to the
        volcano -- something insidious is occurring.  Good luck, bye.'""",
        FixedInPlace : True,
        NoTakeMessage : """It's fairly securely affixed to whatever
        it's securely affixed to."""
        })
world.activity.put_in("informational plaque", "room_the_beach")

##
## The dock
##

quickdef(world, "room_the_dock", "room", {
        Name : "The Dock",
        Description : """Here is a long dock leading off into the
        ocean from the beach.  It is made of [ob driftwood] tied
        together in such a manner that suggests whoever made it was
        clearly not a boy scout.  Judging by the smell of old fish, it
        seems like people fish here regularly.  Beaches lie to the
        [dir west] and the [dir east], and a dirt path leads to the
        [dir north]."""
        })

quickdef(world, "long fishing dock", "supporter", {
        Scenery : True,
        IsEnterable : True,
        Description : """There are many pieces of driftwood held
        together by some [ob <worn rope>]."""
        })
world.activity.put_in("long fishing dock", "room_the_dock")

quickdef(world, "old_rope", "thing", {
        Name : "worn old rope",
        Scenery : True,
        NoTakeMessage : """The rope is affixed to the dock.""",
        Description : """It's just hanging in there keeping the [ob
        dock] together."""
        })
world.activity.put_in("old_rope", "room_the_dock")


quickdef(world, "driftwood", "thing", {
        Name : "long piece of driftwood",
        Words : ["long", "piece", "of", "@driftwood", "@wood"],
        Reported : False,
        Description : """[if [when driftwood AttachedTo old_rope]]If
        it weren't attached to the [ob dock], it could be an excellent
        baseball bat or even a lever.[else]An excellent baseball bat
        or lever.[endif]"""
        })
world.activity.put_in("driftwood", "room_the_dock")
world.activity.attach_to("driftwood", "old_rope")

@before(Cutting(actor, "old_rope"))
def _before_cutting_rope_default(actor, ctxt) :
    raise AbortAction("What, with your hands?")

@before(CuttingWith(actor, "old_rope", Y))
def _before_cuttingwith_rope_default(actor, y, ctxt) :
    raise AbortAction(str_with_objs("[The $y] isn't sharp enough to cut cooked pasta.", y=y), actor=actor)

@before(CuttingWith(actor, "old_rope", "knife"))
def _before_cuttingwith_rope_knife(actor, ctxt) :
    if "knife" in ctxt.world[Contents(actor)] :
        raise ActionHandled()

@when(CuttingWith(actor, "old_rope", "knife"))
def _when_cuttingwith_rope_knife(actor, ctxt) :
    ctxt.world[Reported("driftwood")] = True
    ctxt.world.activity.detach("driftwood")
    ctxt.world.activity.give_to("driftwood", actor)
    ctxt.world.activity.remove_obj("old_rope")
    ctxt.write(str_with_objs("""After a few pulls of of [the $y], with
    a few of those said pulls passing through due to [the $y]'s lack
    of total existence, [the $x] completely disintegrates.  The
    [ob driftwood] is freed.[newline]Taken.""", x="old_rope", y="knife"), actor=actor)

##
## More beach
##

quickdef(world, "room_more_beach", "room", {
        Name : "More Beach",
        Description : """Again, more crystal clear water and a lot of
        sand, except in this case [ob <sand dunes>] cover the beach.
        You can go back [dir east eastward].  Apparently, another
        person thought the beach was to die for as, next to the shore
        soaking in the rays, is a [ob skeleton]."""
        })
world[NoGoMessage("room_more_beach", "west")] = """The beach just
keeps going.  Long walks on the beach aren't going to solve anything."""
world[NoGoMessage("room_more_beach", "north")] = """The jungle is too
thick.  Besides, the wild animals might be dangerous."""
world.activity.connect_rooms("room_more_beach", "east", "room_the_dock")

quickdef(world, "skeleton", "person", {
        Gender : "male",
        Reported : False,
        FixedInPlace : True,
        NoTakeMessage : "The skeleton wouldn't appreciate that.",
        Description : """He appears to be enjoying himself, or, at
        least was enjoying himself when he was still alive.[if [when
        skeleton_hand Contains knife]] Something shiny is embedded in
        his [ob hand].[endif][if [when skeleton Has good_fronds]] He
        is under some good, sun-blocking [ob palm fronds].[endif]"""
        })
world.activity.put_in("skeleton", "room_more_beach")

@before(AskingAbout(actor, "skeleton", Y))
def before_askingabout_knife(actor, y, ctxt) :
    res = ctxt.parser.run_parser("something",
                                 ctxt.parser.transform_text_to_words(y),
                                 ctxt)
    if "knife" in [r[0].value for r in res] :
        raise DoInstead(AskingFor(actor, "skeleton", "knife"), suppress_message=True)

@report(AskingAbout(actor, "skeleton", Y))
def report_askingabout_stuff(actor, y, ctxt) :
    words = y.lower().split()
    if "sun" in words :
        ctxt.write("'The sun's been up there all day.  I wish I had something to cover myself.'")
        raise ActionHandled()
    elif "help" in words or "helping" in words :
        ctxt.write("'You want to help me?  Please find something I could use to block the sun.'")
        raise ActionHandled()
        

@before(AskingFor(actor, "skeleton", Y))
def before_askingfor_knife(actor, y, ctxt) :
    if y == "knife" :
        if ctxt.world[Location("knife")] == "skeleton_hand" :
            ctxt.write("""'Do you like it? It's my favorite
            knife. Though, the sun is a bit hot.  I might give it to
            you if you help me out a bit...'""")
            raise ActionHandled()
        else :
            ctxt.write("""'Isn't it a great knife?  You didn't lose it, did you?'""")
            raise ActionHandled()
    else :
        ctxt.write("""The skeleton seems unmoved by your question.""")
        raise ActionHandled()

@before(PlacingOn(actor, "good_fronds", "skeleton"))
def before_placingon_fronds(actor, ctxt) :
    raise DoInstead(GivingTo(actor, "good_fronds", "skeleton"), suppress_message=True)

@actoractivities.to("npc_is_wanting")
def npc_is_wanting_skeleton_fronds(giver, object, receiver, ctxt) :
    if object == "good_fronds" and receiver == "skeleton" :
        raise ActionHandled()

@when(GivingTo(actor, "good_fronds", "skeleton"))
def when_giving_fronds(actor, ctxt) :
    ctxt.world.activity.give_to("good_fronds", "skeleton")
    ctxt.world.activity.give_to("knife", actor)
    raise ActionHandled()

@report(GivingTo(actor, "good_fronds", "skeleton"))
def report_giving_fronds(actor, ctxt) :
    ctxt.write("""The skeleton covers himself in the fronds and says:
    'Thank you.  These will work -- they seem to block the sun very
    well.  I'll give you my [ob knife] in return.'[newline]Taken.""")
    raise ActionHandled()

quickdef(world, "skeleton_hand", "container", {
        Name : "hand",
        Words : ["@hand", "@hands"],
        Openable : True,
        IsOpen : False,
        IsOpaque : False,
        SuppressContentDescription : True,
        Description : """Very white, and many bones, all phalanges,
        carpals, and metacarpals are here in this [get IsOpenMsg
        skeleton_hand] hand.  It is quite impressive how many parts
        there are.  [if [when skeleton_hand Contains knife]]A
        strangely translucent [ob <metal knife>] is concealed
        within.[endif]"""
        })
world.activity.make_part_of("skeleton_hand", "skeleton")

quickdef(world, "knife", "thing", {
        Name : "somewhat existent knife",
        Words : ["strangely", "translucent", "metal", "somewhat", "existent", "@knife", "shiny", "thing"],
        Description : """It is semi-transparent.  Maybe the guy tried
        to take it with him.  It seems to be a very high-quality
        knife, except for the lack of total existence."""
        })
world.activity.put_in("knife", "skeleton_hand")

@before(Taking(actor, "knife"))
def _before_take_knife(actor, ctxt) :
    if ctxt.world.query_relation(Contains("skeleton_hand", "knife")) :
        if ctxt.world[IsOpen("skeleton_hand")] :
            ctxt.world[IsOpen("skeleton_hand")] = False
            raise AbortAction("""Surprisingly, the skeleton snaps his
            hand shut and begins to move his jaw, almost in
            anticipation of being asked about the knife perhaps.""")
        else :
            raise AbortAction("The hand is closed around the knife.")

quickdef(world, "sand dunes", "thing", {
        Scenery : True,
        Description : """Lots of sand, and lots of dunes.  Some
        vegetation is growing on top of some of them."""
        })
world.activity.put_in("sand dunes", "room_more_beach")

###
### Village area
###

quickdef(world, "region_village", "region")

world[NoGoMessage(X, direction) <= Contains("region_village", X)] = """
I think it is evidence enough that if the villagers decided not to
build a trail that way, you should not go that way either."""

world.activity.put_in("room_village", "region_village")
world.activity.put_in("room_well", "region_village")

##
## Village
##

quickdef(world, "room_village", "room", {
        Name : "The Village",
        Description : """This is a small village consisting of exactly
        three and a half palm huts.  The [ob <half hut>] was smitten
        by an angry charged stream of ions.  At least, that's what the
        [ob <explanatory sign>] in front of it says.  On the remaining
        three, palm fronds line the roofs.  Well-used paths lead to
        the [dir west] and [dir south] while to the [dir north] is a
        slight opening in the jungle."""
        })
world.activity.connect_rooms("room_village", "south", "room_the_dock")
world.activity.connect_rooms("room_village", "north", "room_jungle")

quickdef(world, "half hut", "container", {
        Words : ["half", "palm", "@hut", "@huts"],
        Scenery : True,
        SuppressContentDescription : True,
        Description : """Only half of it is there, the rest is [ob
        wreckage].  Some of the previous owner's stuff is lying
        around.  Outside the hut is a sign explaining what happened."""
        })
world.activity.put_in("half hut", "room_village")

quickdef(world, "wreckage", "thing", {
        Words : ["@wreckage", "@stuff"],
        Scenery : True,
        Description : """Mostly rocks.[if [when <half hut> Contains
        fishing_rod]] The only thing of value is a [ob <fishing
        rod>].[endif]"""
        })
world.activity.put_in("wreckage", "half hut")

quickdef(world, "explanatory sign", "thing", {
        Scenery : True,
        Description : """The sign says: 'The gods shot their blue
        spears at this hut because he was too good at fishing.'"""
        })
world.activity.put_in("explanatory sign", "half hut")

quickdef(world, "fishing_rod", "fishing rod", {
        Name : "carbon fiber fishing rod",
        Words : ["carbon", "fiber", "fishing", "@rod", "@pole"],
        Description : """A long, thin fish catching contraption.
        Surprisingly it's carbon fiber and not made of island
        materials as one would expect."""
        })
world.activity.put_in("fishing_rod", "half hut")

world[WhenGoMessage("room_village", "north")] = """The underbrush is
almost completely unlike a stone wall.  You succeed in passing to make
your way to..."""

##
## Well
##

quickdef(world, "room_well", "room", {
        Name : "The Well",
        Description : """A circle of bare dirt encircles a lonely but
        well-visited [ob well] in the middle.  The village is over to
        the [dir east]."""
        })
world.activity.connect_rooms("room_well", "east", "room_village")

quickdef(world, "well shaft", "container", {
        Words : ["well-visited", "well", "@shaft", "water"],
        Scenery : True,
        SuppressContentDescription : True,
        Description : """A circle of stones with a cylindrical pit in
        the middle.  The water in the cylinder isn't that deep.  [if
        [when <well shaft> Contains <key card>]]A [ob <key card>] is
        floating in the water.[endif]"""
        })
world.activity.put_in("well shaft", "room_well")

quickdef(world, "key card", "thing", {
        Name : "blue key card", 
        Words : ["blue", "key", "@card", "@keycard"],
        Description : """Like a blue credit card, but has super secret
        flotation protection.  Along the body of the key card is the
        writing 'Super Secret Express Elevator Access Card.'"""
        })
world.activity.put_in("key card", "well shaft")

@before(Taking(actor, "key card"))
def _before_taking_key_card(actor, ctxt) :
    if ctxt.world[Contains("well shaft", "key card")] :
        raise AbortAction("It is too far down in the well to reach.")

@world.define_property
class Plugged(Property) :
    """Represents whether the thing is plugged.  Used for the
    bucket."""
    numargs = 1

# putting bucket code next to well for puzzle clarity
quickdef(world, "bucket", "container", {
        Words : ["@bucket", "@pail"],
        Plugged : True,
        Description : """It is a tin bucket and looks like it is
        mostly water tight, except for [if [not [get Plugged
        bucket]]]a hole[else]an insignificant plugged hole[endif] near
        the bottom.[if [when <animal trap> Contains bucket]] It is
        hanging from a branch as part of the [ob animal
        trap].[else][if [when bucket AttachedTo animal_trap_catch]] It
        is still connected to the [ob catch] by a rope.[else] It has a
        length of rope attached to its handle.[endif][endif]"""
        })

world.activity.make_part_of("bucket", "animal trap")

quickdef(world, "bucket hole", "thing", {
        Name : "hole",
        Description : """[if [get Plugged bucket]]Bits of stuff fill
        the hole, limiting any water flow.[else]The hole is a good
        enough size to let the water out of the bucket rather
        quickly.[endif]"""
        })
world.activity.make_part_of("bucket hole", "bucket")

class Unplugging(BasicAction) :
    """Unplugging(actor, X)."""
    verb = "unplug"
    gerund = "unplugging"
    numargs = 2
parser.understand("unplug/unclog [something x]", Unplugging(actor, X))
require_xobj_held(actionsystem, Unplugging(actor, X))

@before(Unplugging(actor, X))
def _before_unplugging(actor, x, ctxt) :
    try :
        plugged = ctxt.world[Plugged(x)]
        if not plugged :
            raise AbortAction(str_with_objs("[The $x] has already been unplugged.", x=x))
    except KeyError :
        raise AbortAction("That cannot be unplugged.")

@when(Unplugging(actor, X))
def _when_unplugging(actor, x, ctxt) :
    ctxt.world[Plugged(x)] = False

@report(Unplugging(actor, X))
def _report_unplug(actor, x, ctxt) :
    ctxt.write(str_with_objs("""You dislodge little twigs and bits of
                             cloth from [the $x], unplugging the hole.""", x=x))

@verify(Unplugging(actor, "bucket hole"))
def _verify_unplugging_bucket_hole(actor, ctxt) :
    raise ActionHandled(ctxt.actionsystem.verify_action(Unplugging(actor, "bucket"), ctxt))

@before(Unplugging(actor, "bucket hole"))
def _before_unplugging_bucket_hole(actor, ctxt) :
    raise DoInstead(Unplugging(actor, "bucket"))

parser.understand("drop [something x] in/into [object well shaft]", InsertingInto(actor, X, "well shaft"))

@before(Dropping(actor, "bucket") <= PEquals(Location(actor), "room_well"))
def _before_dropping_bucket(actor, ctxt) :
    raise DoInstead(InsertingInto(actor, "bucket", "well shaft"))

@when(InsertingInto(actor, "bucket", "well shaft"))
def _when_insertinginto_bucket_well(actor, ctxt) :
    ctxt.write("You lower [the bucket] into [the <well shaft>].")
    if ctxt.world[Location("key card")] == "well shaft" :
        ctxt.world.activity.put_in("key card", "bucket")
        ctxt.write("The [ob <key card>] floats into the bucket.")

@report(InsertingInto(actor, "bucket", "well shaft"))
def _report_insertinginto_bucket_well(actor, ctxt) :
    """We needed to report it in the "when" because of the possibility
    of the key card floating into the bucket."""
    raise ActionHandled()

@when(Taking(actor, "bucket"))
def _when_taking_bucket(actor, ctxt) :
    if ctxt.world[Location("key card")] == "bucket" and ctxt.world[Location("bucket")] == "well shaft" :
        if ctxt.world[Plugged("bucket")] :
            ctxt.world.activity.put_in("key card", "well shaft")
            ctxt.write("""The [ob <key card>] floated out of the
            bucket due to excess water on the way up.[newline]""")
        else :
            ctxt.write("""The water drains through the hole and leaves
            the [ob <key card>] within the metallic walls of the bucket.[newline]""")

###
### The Jungle Area
###

quickdef(world, "region_jungle", "region")
world.activity.put_in("room_jungle", "region_jungle")
world.activity.put_in("room_helicopter_pad", "region_jungle")
world.activity.put_in("room_clearing", "region_jungle")
world.activity.put_in("room_crevice", "region_jungle")

world[NoGoMessage(X, direction) <= Contains("region_jungle", X)] = """
The jungle is too thick.  Besides, the wild animals might be
dangerous."""

##
## The Jungle
##

quickdef(world, "room_jungle", "room", {
        Name : "The Jungle",
        Description : """This is a crossroad of sorts in the middle of
        a bunch of nearly impenetrable [ob trees].  The trees occlude
        enough light to make it very dark.  An [ob <animal trap>] is
        dimly visible on a tree.  Trails lead [dir north], [dir
        south], [dir east], and [dir west]."""
        })

quickdef(world, "jungle_tree", "thing", {
        Name : "tree",
        Words : ["@tree", "@trees"],
        Scenery : True,
        Description : """It is very... woody... and has leaves.
        Hanging from the tree is a [ob trap]."""
        })
world.activity.put_in("jungle_tree", "room_jungle")

@before(Climbing(actor, "jungle_tree"))
def _before_climb_tree(actor, ctxt) :
    raise AbortAction("That would be far too simple.")

quickdef(world, "animal trap", "thing", {
        Scenery : True,
        Description : """[if [when bucket AttachedTo <new rope>]]It
        consists of a [ob bucket] hanging from a branch with a loop of
        [ob rope] running down to a [ob catch].  It is rough but
        workable.[else]It's been set off, and you can't see any way to
        reset it.[endif]"""
        })
world.activity.put_in("animal trap", "room_jungle")

quickdef(world, "animal_trap_catch", "thing", {
        Name : "catch",
        Description : """It looks like it would be set off by
        something roughly fish sized.  That's odd engineering -- when
        would a fish be running through a jungle?"""
        })
world.activity.make_part_of("animal_trap_catch", "animal trap")

quickdef(world, "new rope", "thing", {
        Description : """It is attached to the [ob bucket] and the
        catch and is used as the bucket retainer when the [ob trap] is
        set."""
        })
world.activity.make_part_of("new rope", "animal trap")

world.activity.attach_to("bucket", "new rope")

class MakingTrapGoWith(BasicAction) :
     verb = "make trap go"
     gerund = "making the trap go with"
     numargs = 2
parser.understand("make [object animal trap] go with [something x]", MakingTrapGoWith(actor, X))
parser.understand("set [object animal trap] with [something x]", MakingTrapGoWith(actor, X))
parser.understand("set [object animal trap] off with [something x]", MakingTrapGoWith(actor, X))
parser.understand("throw [something x] in/on/into [object animal trap]", MakingTrapGoWith(actor, X))
parser.understand("make [object animal_trap_catch] go with [something x]", MakingTrapGoWith(actor, X))
parser.understand("set [object animal_trap_catch] with [something x]", MakingTrapGoWith(actor, X))
parser.understand("set [object animal_trap_catch] off with [something x]", MakingTrapGoWith(actor, X))
parser.understand("throw [something x] in/on/into [object animal_trap_catch]", MakingTrapGoWith(actor, X))

@before(InsertingInto(actor, X, Y))
@before(PlacingOn(actor, X, Y))
def _before_insert_or_placing_animal_trap(actor, x, y, ctxt) :
    if y in ["animal trap", "animal_trap_catch"] :
        raise DoInstead(MakingTrapGoWith(actor, x), suppress_message=True)

require_xobj_held(actionsystem, MakingTrapGoWith(actor, X))

@before(MakingTrapGoWith(actor, X))
def _before_makingtrapgo(actor, x, ctxt) :
    if ctxt.world[Location(actor)] == "room_jungle" :
        if ctxt.world.query_relation(PartOf("bucket", "animal trap")) :
            if x == "the_fish" :
                raise ActionHandled()
            else :
                raise AbortAction("That won't set off a roughly fish-sized [ob catch].")
        else :
            raise AbortAction("The [ob trap] has already been used.")
    else :
        raise AbortAction("You don't see a trap around here.")

@when(MakingTrapGoWith(actor, X))
def _when_makingtrapgo(actor, x, ctxt) :
    ctxt.world.activity.remove_obj("the_fish")
    ctxt.world.activity.put_in("bucket", "room_jungle")

@report(MakingTrapGoWith(actor, X))
def _report_makingtrapgo(actor, x, ctxt) :
    ctxt.write("""Upon putting the fish on the catch, the rope was
    released and the [ob bucket] fell with a clang from the tree,
    landing on the ground, just missing the fish.  It didn't even land
    open-mouth-side-down.  As soon as this happened, a small jungle
    animal ran by and absconded with the flounder.""")

@before(Cutting(actor, "new rope"))
def _before_cutting_rope_default(actor, ctxt) :
    raise AbortAction("What, with your hands?")

@before(CuttingWith(actor, "new rope", Y))
def _before_cuttingwith_rope_default(actor, y, ctxt) :
    raise AbortAction(str_with_objs("[The $y] isn't sharp enough to cut cooked pasta.", y=y), actor=actor)

@before(CuttingWith(actor, "new rope", "knife"))
def _before_cuttingwith_rope_knife(actor, ctxt) :
    if ctxt.world.query_relation(PartOf("bucket", "animal trap")) :
        raise AbortAction("You can't get to it while it's hanging up in the tree.")
    else :
        raise ActionHandled()

@when(CuttingWith(actor, "new rope", "knife"))
def _when_cuttingwith_rope_knife(actor, ctxt) :
    ctxt.world.activity.detach("bucket")
    ctxt.world.activity.give_to("bucket", actor)
    ctxt.world.activity.remove_obj("new rope")
    ctxt.write(str_with_objs("""It takes a bit of time, as [the $y] is
    only somewhat existent, but eventually the rope is severed,
    freeing the [ob bucket].[newline]Taken.""", y="knife"), actor=actor)

##
## Helicopter pad
##

quickdef(world, "room_helicopter_pad", "room", {
        Name : "The Helicopter Pad",
        Description : """Lying on the ground is a small [ob tarmac],
        square in shape, and it has the markings as that of a
        helicopter pad -- a large circle with an inscribed capital
        letter H.  This previous information is unnecessary for the
        determination of the tarmac being a helicopter pad as a large
        [ob helicopter] is presently sitting on the said tarmac.  A
        trail leads [dir south]."""
        })
world.activity.connect_rooms("room_helicopter_pad", "south", "room_jungle")

quickdef(world, "tarmac", "supporter", {
        Words : ["small", "@tarmac"],
        Scenery : True,
        IsEnterable : True,
        SuppressContentDescription : True,
        Description : """A cement helicopter landing square of a good
        size with the standard writing signifying it is a cement
        helicopter landing square."""
        })
world.activity.put_in("tarmac", "room_helicopter_pad")

quickdef(world, "Bell helicopter", "container", {
        Words : ["bell", "@helicopter", "@copter"],
        Scenery : True,
        NoTakeMessage : "That's too big to take.",
        IsEnterable : True,
        Description : "A large helicopter."
        })
world.activity.put_on("Bell helicopter", "tarmac")

class Flying(BasicAction) :
    verb = "fly"
    gerund = "flying"
    numargs = 2
parser.understand("fly [something x]", Flying(actor, X))

require_xobj_accessible(actionsystem, Flying(actor, X))

@before(Flying(actor, X))
def before_flying_default(actor, x, ctxt) :
    raise AbortAction("You can't fly that!")

@before(Flying(actor, "bell helicopter"))
def before_flying_default(actor, ctxt) :
    raise AbortAction("You don't have a license!")


quickdef(world, "penny", "thing", {
        Description : """A small copper penny.  It was made long
        before the 70s so there is no zinc center, making this a great
        conductor.  Plus, you're lucky: Lincoln is face up."""
        })
world.activity.put_in("penny", "room_helicopter_pad")

##
## The Clearing
##

quickdef(world, "room_clearing", "room", {
        Name : "The Clearing",
        Description : """Not much to see here except for a single [ob
        manhole] exactly in the center of the cleared jungle.  [if
        [get IsSwitchedOn valve]]You can hear the hissing of steam
        coming from the [ob pipe] running from the [dir west] into the
        ground.[else]A [ob pipe] runs from the [dir west] into the
        ground.[endif]  A path leads [dir east]."""
        })
world.activity.connect_rooms("room_clearing", "east", "room_jungle")

quickdef(world, "good_fronds", "thing", {
        Name : "good palm fronds",
        NotableDescription : "A few [ob <palm fronds>] litter the ground.",
        Description : """It seems they were cut right from the tree,
        and it looks like they'd block sunlight very well.""",
        IndefiniteName : "some good palm fronds"
        })
world.activity.put_in("good_fronds", "room_clearing")

quickdef(world, "clearing_pipe", "thing", {
        Name : "brass pipe",
        Scenery : True,
        Description : """The brass pipe runs into the ground from the
        west[if [get IsSwitchedOn valve]], and it is
        hissing[endif]."""
        })
world.activity.put_in("clearing_pipe", "room_clearing")

quickdef(world, "manhole", "door", {
        Words : ["rotary", "@handle", "@manhole"],
        Reported : False,
        Lockable : True,
        IsLocked : True,
        KeyOfLock : "driftwood",
        NoEnterMessage : """You try and you try, but you can not seem
        to pass through solid metal.  Try opening it first.""",
        Description : """A circular metal covering with a circular
        rotary handle which happens to look a little weathered and
        rusty.  It is [get IsOpenMsg manhole]."""
        })
world[NoLockMessages("manhole", "no_open")] = """The manhole door and
handle are too rusty to open by hand.  Maybe something could be used
for leverage."""
world[WrongKeyMessages("manhole", X)] = """That doesn't give you
enough leverage."""
world.activity.connect_rooms("room_clearing", "down", "manhole")

parser.understand("go down/up [object manhole]", Entering(actor, "manhole"))

world[WhenGoMessage("room_clearing", "down")] = """You climb some ways
down a ladder into..."""

@when(UnlockingWith(actor, "manhole", "driftwood"))
def _when_unlock_manhole(actor, ctxt) :
    ctxt.world[Lockable("manhole")] = False
    ctxt.world.activity.remove_obj("driftwood")
    # manhole is set to unlocked by UnlockWith handler
    ctxt.world[IsOpen("manhole")] = True
@report(UnlockingWith(actor, "manhole", "driftwood"))
def _report_unlock_manhole(actor, ctxt) :
    ctxt.write("""The extra torque garnered by the length of the
    driftwood frees the handle from the rust.  The manhole opens, but
    your driftwood splinters.[newline]Opened.""")
    raise ActionHandled()

##
## The Crevice
##

quickdef(world, "room_crevice", "room", {
        Name : "The Crevice",
        Description : """Wisps of steam are emanating from a deep [ob
        fissure] in the ground.  They dissolve among a pleasantly
        annoying hiss.  A single [ob pipe] runs [dir east] toward the
        nondescript clearing.  [if [get IsSwitchedOn valve]]It sounds
        like steam is rushing through the pipe.[endif]"""
        })
world.activity.connect_rooms("room_crevice", "east", "room_clearing")

quickdef(world, "fissure", "thing", {
        Words : ["deep", "@fissure", "@crevice"],
        Scenery : True,
        Description : """The fissure is very deep.  The [ob pipe]
        extends down farther than the eye can see with steam swirling
        about.  It may seem crazy, but it almost seems like there are
        stars and entire universes far below.  Maybe they are just
        fireflies."""
        })
world.activity.put_in("fissure", "room_crevice")

quickdef(world, "pipe", "thing", {
        Name : "brass pipe",
        Scenery : True,
        Description : """A[if [get IsSwitchedOn valve]] hissing[endif]
        brass pipe runs from deep within the earth to the east.[if
        [when room_crevice Contains pile_palm_fronds]] A [ob <pile of
        palm fronds>] is covering a segment of the pipe.[else] Partway
        down the pipe is a matching [ob <brass valve>].[endif]"""
        })
world.activity.put_in("pipe", "room_crevice")

quickdef(world, "pile_palm_fronds", "thing", {
        Name : "pile of palm fronds",
        Description : """A pile of palm fronds covering the [ob
        pipe]."""
        })
world.activity.put_in("pile_palm_fronds", "room_crevice")
parser.understand("move [object pile_palm_fronds]", Taking(actor, "pile_palm_fronds"))

@when(Taking(actor, "pile_palm_fronds"))
def _when_taking_pile_palms(actor, ctxt) :
    ctxt.world.activity.remove_obj("pile_palm_fronds")
    ctxt.world.activity.make_part_of("valve", "pipe")
    raise ActionHandled()
@report(Taking(actor, "pile_palm_fronds"))
def _report_take_pile_palms(actor, ctxt) :
    ctxt.write("""The palm fronds just disperse in every direction,
    revealing a small [ob <brass valve>].""")
    raise ActionHandled()

quickdef(world, "valve", "thing", {
        Name : "brass valve",
        Switchable : True,
        IsSwitchedOn : False,
        Description : """A standard small-handled valve."""
        })

@report(SwitchingOn(actor, "valve"))
def report_switching_on_valve(actor, ctxt) :
    ctxt.write("""Opening the valve releases a continuous hiss of
    steam into the [ob pipe].""")
    raise ActionHandled()

@report(SwitchingOff(actor, "valve"))
def report_switching_on_valve(actor, ctxt) :
    ctxt.write("""The hissing abruptly stops.""")
    raise ActionHandled()

parser.understand("open [object valve]", SwitchingOn(actor, "valve"))
parser.understand("close [object valve]", SwitchingOff(actor, "valve"))

###
### Underground area
###

quickdef(world, "region_underground", "region")
world.activity.put_in("room_power_station", "region_underground")
world.activity.put_in("room_transmission", "region_underground")

quickdef(world, "conduit", "backdrop", {
        Name : "thick metal conduit",
        Words : ["think", "metal", "@conduit", "@conduits", "@cable", "@cables"],
        BackdropLocations : ["region_underground"],
        Description : """Each cable is as thick as and in the general
        form of a twinkie and is covered in as many layers of
        insulation and packing materials."""
        })

@world.handler(Global("transformer_on"))
def global_transformer_on(world) :
    return (world[IsSwitchedOn("valve")]
            and world[Location("penny")] == "fuse_receptacle"
            and world[IsSwitchedOn("knife_switch")])

##
## Power station
##

quickdef(world, "room_power_station", "room", {
        Name : "The Power Station",
        Description : """The pipes from above run along the ladder you
        came down into a large [ob <steam turbine>].  The air is very
        murky with swirls of steam percolating through the myriad of
        pipes.  The turbine is [if [get IsSwitchedOn valve]]currently
        clattering and sputtering from the flow of steam from
        above[else]ominously silent[endif]. You can go [dir up] the
        ladder, and a shielded pair of [ob cables] runs from the
        turbine to the [dir north]."""
        })
world.activity.connect_rooms("manhole", "down", "room_power_station")

quickdef(world, "ladder", "thing", {
        Scenery : True,
        Description : """It's the ladder you came down."""
        })
world.activity.put_in("ladder", "room_power_station")

@before(Climbing(actor, "ladder"))
def _before_climb_ladder(actor, ctxt) :
    raise DoInstead(Going(actor, "up"), suppress_message=True)

world[WhenGoMessage("room_power_station", "up")] = "You climb up the ladder to..."

quickdef(world, "steam_generator", "thing", {
        Name : "steam turbine",
        Words : ["large", "steam", "@generator", "@turbine"],
        Scenery : True,
        Description : """A brass power generation relic riveted
        together.[if [get IsSwitchedOn valve]] From within the depths
        of the device, the sound of spinning and banging metal can be
        heard.  Signs of electricity can be seen in the form of
        sparks.[else] It is silent.[endif] A thick metal [ob conduit]
        runs out of the device."""
        })
world.activity.put_in("steam_generator", "room_power_station")

##
## Transmission room
##

quickdef(world, "room_transmission", "room", {
        Name : "The Transmission Room",
        Description : """[if [get Global transformer_on]]A low
        frequency hum permeates the room; it could make a person go
        crazy. [endif]A single [ob transformer] sits in the middle of
        a room with many [ob conduits] and wires going to and from the
        device.  The transformer has some controls.  You can go [dir
        south]."""
        })
world.activity.connect_rooms("room_transmission", "south", "room_power_station")

quickdef(world, "transformer", "thing", {
        Words : ["@transformer", "@controls"],
        Scenery : True,
        Description : """It is a large, iron-cored transformer wrapped
        in thousands of turns of fine copper wire.  Next to the
        windings are a few devices: a [ob <knife switch>] and an [ob
        <emergency fuse receptacle>].  The conduits run from the power
        station into the transformer, and others run from the
        transformer into the ground toward the east.[if [get Global
        transformer_on]] A low hum is emanating from the vibrating
        magnetic coils.[endif]"""
        })
world.activity.put_in("transformer", "room_transmission")

quickdef(world, "fuse_receptacle", "container", {
        Name : "emergency fuse receptacle",
        Description : """It looks like the last fuse burned out.  It
        takes circular fuses, but if safety is ignored briefly, any
        circular conductor will do.[if [get Contents fuse_receptacle]]
        Currently inside the receptacle [is_are_list [get Contents
        fuse_receptacle]][endif]."""
        })
world.activity.make_part_of("fuse_receptacle", "transformer")

quickdef(world, "knife_switch", "thing", {
        Name : "knife switch",
        Switchable : True,
        IsSwitchedOn : True,
        Description : """A sheet of metal with a handle that is moved
        between a pair of metal contacts to make or break a circuit.
        This one is a single-pole, single-throw switch.  It is
        currently [get IsSwitchedOnMsg knife_switch]."""
        })
world.activity.make_part_of("knife_switch", "transformer")

@before(InsertingInto(actor, X, "fuse_receptacle") <= IsSwitchedOn("knife_switch"))
def _before_inserting_fuse(actor, x, ctxt) :
    raise AbortAction("To prevent electrical shock, you ought to turn off the knife switch.")

@before(InsertingInto(actor, X, "fuse_receptacle") <= Contents("fuse_receptacle")) # that is, if contents not empty
def _before_insert_fuse(actor, x, ctxt) :
    raise AbortAction("There's already something in the fuse receptacle.")

@report(SwitchingOn(actor, "knife_switch"))
def _report_switchingon_knifeswitch(actor, ctxt) :
    ctxt.write("You switch on [the knife_switch].", actor=actor)
    if ctxt.world[Global("transformer_on")] :
        ctxt.write("A low hum permeates the underground complex.")
    else :
        ctxt.write("Nothing happens.")
    raise ActionHandled()

###
### The Volcano
###

##
## West side of volcano
##

quickdef(world, "room_west_volcano", "room", {
        Name : "The Western Side of the Volcano",
        Description : """This is one side of a [ob volcano].  [ob
        <Acrid smoke>] is billowing from the top of the cinder cone
        and rolling down the sides. You can go [dir west]."""
        })
world[NoGoMessage("room_west_volcano", X)] = "Sulfur-laden rocks bar the way."

world.activity.connect_rooms("room_west_volcano", "west", "room_jungle")

quickdef(world, "smoke", "thing", {
        Name : "acrid smoke",
        Scenery : True,
        Description : """The smoke smells strangly of rocket fuel."""
        })
world.activity.put_in("smoke", "room_west_volcano")

quickdef(world, "volcano", "thing", {
        Words : ["cinder", "cone", "@volcano"],
        Scenery : True,
        Description : """It's a big cinder cone with a [ob door] on
        the side."""
        })
world.activity.put_in("volcano", "room_west_volcano")

quickdef(world, "elevator_door", "door", {
        Name : "secret elevator door",
        Lockable : True,
        IsLocked : True,
        KeyOfLock : "key card",
        NotableDescription : """A [ob secret door] is hidden on the
        side of the volcano.""",
        Description : """It's secret and express, as the [ob sign]
        above the door does not say."""
        })
world.activity.connect_rooms("room_west_volcano", "east", "elevator_door")

quickdef(world, "secret sign", "thing", {
        Scenery : True,
        Description : """In bold, clear writing in carbon dioxide
        laser writing on titanium, the sign says: 'This is not a
        secret and express elevator door.'"""
        })
world.activity.put_in("secret sign", "room_west_volcano")

##
## Secret Express Elevator
##

quickdef(world, "room_secret_elevator", "room", {
        Name : "The Secret Express Elevator",
        Description : """Next to the [get IsOpenMsg elevator_door] [ob
        <elevator door>] is a small [ob <control panel>] with a single
        [ob button] and a [ob <small indicator light>] which is
        currently [if [get Global transformer_on]]on[else]off[endif]."""
        })
world.activity.connect_rooms("elevator_door", "east", "room_secret_elevator")

quickdef(world, "control panel", "thing", {
        Words : ["small", "control", "@panel"],
        Scenery : True,
        Description : """A brushed aluminum panel.  It is very sparse
        with only two features: a [ob <small blue button>], and an [ob
        <indicator light>] which [if [get Global
        transformer_on]]is[else]isn't[endif] currently lit."""
        })
world.activity.put_in("control panel", "room_secret_elevator")

quickdef(world, "indicator_light", "thing", {
        Name : "small indicator light",
        Description : """It is a pilot light, red in color.  [if [get
        Global transformer_on]]It is shining brightly.[else]No light
        is being emitted.[endif]"""
        })
world.activity.make_part_of("indicator_light", "control panel")

quickdef(world, "blue_button", "thing", {
        Name : "small blue button",
        Description : """It's a small blue button on the [ob <control
        panel>].  It's glowing slightly, eager for you to push it."""
        })
world.activity.make_part_of("blue_button", "control panel")

@before(Pushing(actor, "blue_button"))
def _before_pushing_blue_button(actor, ctxt) :
    if ctxt.world[Global("transformer_on")] :
        if ctxt.world[IsOpen("elevator_door")] :
            raise AbortAction("""A voice booms from the control panel:
                                 'Please close the [ob <elevator door>].'""")
        else :
            raise ActionHandled()
    else :
        raise AbortAction("Nothing happens.")

@when(Pushing(actor, "blue_button"))
def _when_pushing_blue_button(actor, ctxt) :
    ctxt.world.activity.put_in(actor, "room_lab")

@report(Pushing(actor, "blue_button"))
def _report_pushing_blue_button(actor, ctxt) :
    ctxt.write("""The red light begins to blink, and, without warning,
    a trap door opens up underneath you and deposits you in...[newline]""")
    ctxt.activity.describe_current_location(actor)
    ctxt.write("""[newline]You get up and recover from the fall.""")

##
## The lab
##

quickdef(world, "room_lab", "room", {
        Name : "The Lab",
        Description : """Lots of equipment, all evil.  The
        horror..."""
        })

quickdef(world, "red_button", "thing", {
        Name : "large red button",
        FixedInPlace : True,
        Description : """It looks like nothing good will come out of
        pushing this button that has inscribed lettering of 'Do not
        push.'"""
        })
world.activity.put_in("red_button", "room_lab")

@before(Pushing(actor, "red_button"))
def _before_pushing_red_button(actor, ctxt) :
    raise ActionHandled()

@when(Pushing(actor, "red_button"))
def _when_push_red_button(actor, ctxt) :
    ctxt.write("""Just kidding, the button actually said 'Do push for
    a party.'  There was a surprise party for you.  The whole thing
    was set up because you like adventures.  You ate a lot of cake.""")
    ctxt.activity.end_game_saying("You have won")
    raise ActionHandled()
