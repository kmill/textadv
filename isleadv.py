# isleadv.py
#
# by Kyle Miller, 2011
#
# a reimplementation of Island Adventure, which I had written before
# in Inform 7

from textadv.basiclibrary import *


##
## Fun and games
##

@when(StartGame())
def _when_game_start(context) :
    context.write_line("""
You decided to stop what you were doing and wash up on an island.

You're not quite sure how you got here, or what you're supposed to do,
but you feel that Adventure is afoot.

ISLAND ADVENTURE

a short work by Kyle Miller""")
    raise ActionHandled()


@before(Attack(actor, player))
def _before_suicide(actor, context) :
    raise AbortAction("Suicide is not the answer.", actor=actor)

remove_obj(hands)

##
## Properties
##


# Attachment

class AttachedTo(BasicPattern) :
    def __init__(self, attached, attacher) :
        self.args = [attached, attacher]

str_eval_register_relation("attachedto", AttachedTo)

def prop_set_attached(world, attached, attacher) :
    world.db["relations"].insert(AttachedTo(obj_to_id(attached), obj_to_id(attacher)))
def prop_detach(world, attached) :
    world.db["relations"].delete(AttachedTo(obj_to_id(attached), x))

@before(Take(actor, BObject(x)))
def _before_take_attached(actor, x, context) :
    a = x.s_R_x(AttachedTo)
    if a :
        raise AbortAction(str_with_objs("It's attached to [the $z].", z=a[0]))

# Fishing

class FishingRod(BObject) :
    pass

class Fish(BasicAction) :
    verb = "fish"
    gerund = "fishing"
class FishWith(BasicAction) :
    verb = "fish"
    gerund = "fishing with"

understand("fish", Fish(actor))
understand("fish with [something x]", FishWith(actor, x))
understand("catch fish with [something x]", FishWith(actor, x))

@before(Fish(actor))
def _before_fish_default(actor, context) :
    rods = context.world.lookup("relations", Has(actor, FishingRod(x)), res=get_x)
    if len(rods) > 1 :
        raise Ambiguous(rods)
    elif len(rods) == 1 :
        raise DoInstead(FishWith(actor, rods[0]))
    else :
        raise AbortAction("The last time I checked it was very hard to catch fish without a pole.")

xobj_held(FishWith(actor, BObject(x)))
@before(FishWith(actor, BObject(x)))
def _before_fishwith_default(actor, x, context) :
    if not isinstance(x, FishingRod) :
        if isinstance(x, Actor) :
            raise AbortAction(str_with_objs("""It doesn't look like [the $x] wants to help.""",
                                            x=x))
        else :
            raise AbortAction(str_with_objs("""{Bob|cap} would have a
                                            hard time catching fish with [the $x]""", x=x))

@before(FishWith(actor, FishingRod(x)))
def _before_fishwith_rod(actor, x, context) :
    if not context.world["fishing_dock"].s_R_x(In, actor.get_location()) :
        raise AbortAction("""You have to be on a fishing dock to have
        deep enough water to fish.""")
    elif actor.s_R_x(Has, "the_fish") :
        raise AbortAction("""You have a fish already. You don't need
        another.""")
    else :
        raise ActionHandled()

@when(FishWith(actor, FishingRod(x)))
def _when_fishwith_rod(actor, x, context) :
    context.world["the_fish"].give_to(actor)

@after(FishWith(actor, FishingRod(x)))
def _after_fishwith_rod(actor, x, context) :
    context.write_line("""As soon as the hook reaches the surface of
    the water, a swarm of fish swim at it.  One lucky fish bites and
    you pull.  You catch a fish.
    
    Taken.""")


the_fish = world.new_obj("the_fish", BObject, "fish", """It is a
flounder.  It doesn't look that appetizing, as both eyes are on one
side of its head.""")
@before(Eat(actor, the_fish))
def _before_eat_fish(actor, context) :
    raise AbortAction("It doesn't look that appetizing.")

# Sky region

region_sky = world.new_obj("region_sky", Region, "Sky Area")
region_sky.add_rooms(["region_beach", "region_village", "room_west_volcano"])

the_sky = world.new_obj("the_sky", Scenery, "sky",
"""The sky is cloudless and full of sun.  A bird flies by
occasionally.""")
the_sky.move_to(region_sky)

###
### Beach region
###

region_beach = world.new_obj("region_beach", Region, "Beach Area")
beach_ocean = world.new_obj("beach_ocean", Scenery, "ocean",
"""The water is aquamarine with perfect white sand underfoot.""")
beach_ocean.move_to(region_beach)

region_beach.add_rooms(["room_the_beach", "room_the_dock", "room_more_beach"])

@before(Go(actor, "south"))
def _before_south_beach_area(actor, context) :
    if actor.get_location().transitive_in("region_beach") :
        raise AbortAction("You can't just go swimming without a swim suit, heaven forbid!")

class Swim(BasicAction) :
    verb = "swim"
    gerund = "swimming"
class SwimIn(BasicAction) :
    verb = "swim"
    gerund = "swimming in"
understand("swim", Swim(actor))
understand("swim in [something x]", SwimIn(actor, x))

@before(Swim(actor))
def _before_swimming(actor, context) :
    if actor.obj_accessible("beach_ocean") :
        raise DoInstead(SwimIn(actor, "beach_ocean"))
    else :
        raise AbortAction("There's no place to swim.")

xobj_accessible(SwimIn(actor, x))

@before(SwimIn(actor, x))
def _before_swimin(actor, x, context) :
    raise AbortAction("You can't just swim without a swimsuit. Heaven forbid!")

##
## The beach
##

player.move_to("room_the_beach")

room_the_beach = world.new_obj("room_the_beach", Room, "The Beach",
"""Crystal clear water and lots of sand.  The air is warm but not too
humid, and it seems it would be the perfect place to go swimming.
Some docks are visible to the west.""")
room_the_beach["no_go_msgs"]["east"] = """The beach just keeps going.
Long walks on the beach aren't going to solve anything."""
room_the_beach["no_go_msgs"]["north"] = """The jungle is too thick.
Besides, the wild animals might be dangerous."""

informational_plaque = world.new_obj("informational_plaque", Readable, "informational plaque",
"""Some writing can be made out, quite easily actually, since, by the
look of it, it is burnt into a sheet of titanium by a carbon dioxide
laser.""")
informational_plaque.move_to(room_the_beach)
informational_plaque["read_msg"] = """It reads 'Go to the volcano --
something insidious is occurring.  Good luck, bye.'"""
informational_plaque["takeable"] = False
informational_plaque["no_take_msg"] = """It's fairly securely affixed
to whatever it's securely affixed to."""

room_the_beach.connect("room_the_dock", "west")

##
## The dock
##

room_the_dock = world.new_obj("room_the_dock", Room, "The Dock",
"""Here is a long dock leading off into the ocean from the beach.  It
is made of driftwood tied together in such a manner that suggests
whoever made it was clearly not a boy scout.  Judging by the smell of
old fish, it seems like people fish here regularly.  Beaches lie to
the west and the east, and a dirt path leads to the north.""")

fishing_dock = world.new_obj("fishing_dock", Scenery, "long fishing dock",
"""There are many pieces of driftwood held together by some worn rope.""")
fishing_dock.move_to(room_the_dock)

old_rope = world.new_obj("old_rope", Scenery, "worn old rope",
"""It's just hanging in there keeping the dock together.""")
old_rope.move_to(room_the_dock)
old_rope["no_take_msg"] = """The driftwood is attached to the dock
with the rope."  Instead of taking the old rope when the old rope is
joined to the driftwood, say "It seems to be knotted up with no
beginning nor end.  It's a mobius rope."""

driftwood = world.new_obj("driftwood", BObject, "long piece of driftwood",
"""[if [when driftwood attachedto old_rope]]If it weren't attached to
the dock, it could be an excellent baseball bat or even a
lever.[else]An excellent baseball bat or lever.[endif]""")
driftwood["words"] = ["long", "piece", "of", "@driftwood", "@wood"]
driftwood.move_to(room_the_dock)
prop_set_attached(world, driftwood, old_rope)
driftwood["reported"] = False

@before(Cut(actor, "old_rope"))
def _before_cut_rope_default(actor, context) :
    raise AbortAction("What, with your hands?")

@before(CutWith(actor, old_rope, BObject(y)))
def _before_cutwith_rope_default(actor, y, context) :
    raise AbortAction(str_with_obj("[the $y] isn't sharp enough to cut cooked pasta.", y=y))

@before(CutWith(actor, old_rope, "knife"))
def _before_cutwith_rope_knife(actor, context) :
    raise ActionHandled()

@when(CutWith(actor, old_rope, "knife"))
def _when_cutwith_rope_knife(actor, context) :
    driftwood = context.world["driftwood"]
    driftwood["reported"] = True
    prop_detach(context.world, driftwood)
    driftwood.give_to(actor)
    remove_obj(context.world["old_rope"])
    context.write_line(str_with_objs("""After a few pulls of of [the
    $y], with a few of those said pulls passing through due to [the
    $y]'s lack of total existence, [the $x] completely disintegrates.
    The driftwood is freed.\n\nTaken.""", x="old_rope", y="knife"))

##
## More beach
##

room_more_beach = world.new_obj("room_more_beach", Room, "More Beach",
"""Again, more crystal clear water and a lot of sand, except in this
case sand dunes cover the beach.  Apparently, another person thought
the beach was to die for as, next to the shore soaking in the rays, is
a skeleton.""")
room_more_beach["no_go_msgs"]["west"] = """The beach just keeps going.
Long walks on the beach aren't going to solve anything."""
room_more_beach["no_go_msgs"]["north"] = """The jungle is too thick.
Besides, the wild animals might be dangerous."""
room_more_beach.connect(room_the_dock, "east")

class MySkeleton(Actor, Scenery) :
    def setup(self, name, desc) :
        Actor.setup(self, name, desc)
        Scenery.setup(self, name, desc)
    def ask_about(self, text, context) :
        res = parse_something(context, text)
        if context.world["knife"] in res :
            if context.world["skeleton_hand"].x_R_s(In, "knife") :
                context.write_line("""'Do you like it?  It's my
                favorite knife.  Though, the sun is a bit hot.  I
                might give it to you if you help me out a bit...'""")
            else :
                context.write_line("""'Isn't it a great knife?'""")
        else :
            context.write_line("""The skeleton seems unmoved by your question.""")

@before(GiveTo(actor, "good_fronds", "skeleton"))
def _before_give_fronds(actor, context) :
    raise ActionHandled()
@when(GiveTo(actor, "good_fronds", "skeleton"))
def _when_give_fronds(actor, context) :
    context.world["good_fronds"].give_to("skeleton")
    context.world["knife"].give_to(actor)
    raise ActionHandled()
@after(GiveTo(actor, "good_fronds", "skeleton"))
def _after_give_fronds(actor, context) :
    context.write_line("""The skeleton covers himself in the fronds
    and says: 'Thank you.  These will work -- they seem to block the
    sun very well.  I'll give you my knife in return.'\n\nTaken.""")


skeleton = world.new_obj("skeleton", MySkeleton, "skeleton",
"""He appears to be enjoying himself, or, at least was enjoying
himself when he was still alive.[if [when knife in skeleton_hand]]
Something shiny is embedded in his hand.[endif][if [when skeleton has
good_fronds]] He is under some good, sun-blocking palm fronds.[endif]""")
skeleton.set_gender("male")
skeleton.move_to(room_more_beach)

skeleton_hand = world.new_obj("skeleton_hand", Openable, "hand",
"""Very white, and many bones, all phalanges, carpals, and metacarpals
are here in this [get skeleton_hand is_open_msg] hand.  It is quite
impressive how many parts there are.  [if [when knife in
skeleton_hand]]A strangely translucent metal knife is concealed
within.[endif]""")
skeleton_hand["words"] = ["@hand", "@hands"]
skeleton_hand.give_to(skeleton)

knife = world.new_obj("knife", BObject, "somewhat existant knife",
"""It is semi-transparent.  Maybe the guy tried to take it with him.
It seems to be a very high-quality knife, except for the lack of total
existance.""")
knife["words"] = ["strangely", "translucent", "metal", "somewhat", "existant", "@knife"]
knife.move_to(skeleton_hand)
#knife.give_to(player)

@before(Take(actor, knife))
def _before_take_knife(actor, context) :
    knife = context.world["knife"]
    hand = context.world["skeleton_hand"]
    if knife.s_R_x(In, hand) :
        if hand["open"] :
            hand["open"] = False
            raise AbortAction("""Surprisingly, the skeleton snaps his
            hand shut and begins to move his jaw, almost in
            anticipation of being asked about the knife perhaps.""")
        else :
            raise AbortAction("The hand is closed around the knife.")

sand_dunes = world.new_obj("sand_dunes", Scenery, "sand dunes", """Lots
of sand, and lots of dunes.  Some vegetation is growing on top of some
of them.""")
sand_dunes.move_to(room_more_beach)

###
### Village area
###

region_village = world.new_obj("region_village", Region, "Village Area")

@before(Go(actor, direction))
def _before_go_village_area(actor, direction, context) :
    if actor.transitive_in("region_village") :
        if not actor.get_location().get_exit(direction) :
            raise AbortAction("""I think it is evidence enough that if
            the villagers decided not to build a trail that way, you
            should not go that way either.""")

##
## Village
##

room_village = world.new_obj("room_village", Room, "The Village",
"""This is a small village consisting of exactly three and a half palm
huts.  One of them was smitten by an angry charged stream of ions.  At
least, that's what the explanatory sign in front of it says.  On the
remaining three, palm fronds line the roofs.  Well-used paths lead to
the west and south while to the north is a slight opening in the
jungle.""")
room_village.move_to(region_village)
room_village.connect(room_the_dock, "south")
room_village.connect("room_jungle", "north")

halfhut = world.new_obj("halfhut", Scenery, "half hut",
"""Only half of it is there, the rest is wreckage.  Some of the
previous owner's stuff is lying around.  Outside the hut is a sign
explaining what happened.""")
halfhut.move_to(room_village)

wreckage = world.new_obj("wreckage", Scenery, "wreckage",
"""Mostly rocks.[if [when fishing_rod in halfhut]] The only thing of
value is a fishing rod.[endif]""")
wreckage["words"] = ["@wreckage", "@stuff"]
wreckage.move_to(halfhut)

explanatory_sign = world.new_obj("explanatory_sign", Readable, "explanatory sign",
"""The sign says: 'The gods shot their blue spears at this hut because
he was too good at fishing.'""")
explanatory_sign["takeable"] = False
explanatory_sign.move_to(halfhut)

fishing_rod = world.new_obj("fishing_rod", FishingRod, "carbon fiber fishing rod",
"""A long, thin fish catching contraption.  Surprisingly it's carbon
fiber and not made of island materials as one would expect.""")
fishing_rod["words"] = ["carbon", "fiber", "fishing", "@rod", "@pole"]
fishing_rod.move_to(halfhut)

@before(Go(actor, "north"))
def _before_go_to_jungle_from_village(actor, context) :
    if actor.s_R_x(In, "room_village") :
        context.write_line("""The underbrush is almost completely
        unlike a stone wall.  You succeed in passing to make your way
        to...""")

##
## Well
##
room_well = world.new_obj("room_well", Room, "The Well",
"""A circle of bare dirt encircles a lonely but well-visited well in
the middle.  The village is over to the east.""")
room_well.move_to(region_village)
room_well.connect(room_village, "east")

well_shaft = world.new_obj("well_shaft", Scenery, "well shaft",
"""A circle of stones with a cylindrical pit in the middle.  The water
in the cylinder isn't that deep.  [if [when key_card in well_shaft]]A
key card is floating in the water.[endif]""")
well_shaft["words"] = ["well", "@shaft", "water"]
well_shaft.move_to(room_well)

key_card = world.new_obj("key_card", BObject, "blue key card",
"""Like a blue credit card, but has super secret flotation protection.
Along the body of the key card is the writing 'Super Secret Express
Elevator Access Card.'""")
key_card["words"] = ["blue", "key", "@card", "@keycard"]
key_card.move_to(well_shaft)

@before(Take(actor, key_card))
def _before_take_key_card(actor, context) :
    if world["key_card"].transitive_in("well_shaft") :
        raise AbortAction("It is too far down in the well to reach.")

bucket = world.new_obj("bucket", BObject, "bucket",
"""It is a tin bucket and looks like it is mostly water tight, except
for [if [not [get bucket plugged]]]a hole[else]an insignificant
plugged hole[endif] near the bottom.[if [when bucket in animal_trap]]
It is hanging from a branch as part of the animal trap.[else][if [when
bucket attachedto animal_trap_catch]] It is still connected to the
catch by a rope.[else] It has a length of rope attached to its
handle.[endif][endif]""")
bucket["words"] = ["@bucket", "@pail"]
bucket["plugged"] = True
bucket.move_to("animal_trap") # putting code next to well for puzzle clarity

bucket_hole = world.new_obj("bucket_hole", Scenery, "hole",
"""[if [get bucket plugged]]Bits of stuff fill the hole, limiting any
water flow.[else]The hole is a good enough size to let the water out
of the bucket rather quickly.[endif]""")
bucket_hole.move_to(bucket)

class Unplug(BasicAction) :
    verb = "unplug"
    gerund = "unplugging"
understand("unplug [something x]", Unplug(actor, x))
understand("unclog [something x]", Unplug(actor, x))
xobj_held(Unplug(actor, x))

@before(Unplug(actor, BObject(x)))
def _before_unplug(actor, x, context) :
    try :
        plugged = x["plugged"]
        if not plugged :
            raise AbortAction(str_with_objs("[The $x] has already been unplugged.", x=x))
    except KeyError :
        raise AbortAction("That cannot be unplugged.")

@when(Unplug(actor, BObject(x)))
def _when_unplug(actor, x, context) :
    x["plugged"] = False

@after(Unplug(actor, BObject(x)))
def _after_unplug(actor, x, context) :
    context.write_line(str_with_objs("""You dislodge little twigs and
                                     bits of cloth from [the $x],
                                     unplugging the hole.""", x=x))

@verify(Unplug(actor, bucket_hole))
def _verify_unplug_bucket_hole(actor, context) :
    raise DoInstead(Unplug(actor, "bucket"))

understand("drop [object bucket] in [something x]", InsertInto(actor, "bucket", x))
understand("drop [object bucket] into [something x]", InsertInto(actor, "bucket", x))

@before(Drop(actor, bucket))
def _before_drop_bucket(actor, context) :
    if actor.s_R_x(In, "room_well") :
        raise DoInstead(InsertInto(actor, "bucket", "well_shaft"))

@before(InsertInto(actor, bucket, well_shaft))
def _before_insertinto_bucket_well(actor, context) :
    raise ActionHandled()

@when(InsertInto(actor, bucket, well_shaft))
def _when_insertinto_bucket_well(actor, context) :
    bucket = world["bucket"]
    context.write_line("You put [the bucket] into [the well_shaft].")
    bucket.move_to("well_shaft")
    key_card = world["key_card"]
    if key_card.s_R_x(In, "well_shaft") :
        key_card.move_to("bucket")
        context.write_line("The key card floats into the bucket.")

@before(InsertInto(actor, key_card, bucket))
def _before_insert_key_into_bucket(actor, context) :
    raise AbortAction("You don't want to put that back in.")

@when(Take(actor, bucket))
def _when_take_bucket(actor, context) :
    bucket = world["bucket"]
    key_card = world["key_card"]
    if key_card.s_R_x(In, bucket) and bucket.s_R_x(In, "well_shaft") :
        if bucket["plugged"] :
            key_card.move_to(well_shaft)
            context.write_line("""The key floated out of the bucket
            due to excess water on the way up.""")
        else :
            context.write_line("""The water drains through the hole
            and leaves the key card within the metallic walls of the
            bucket.""")

###
### The Jungle Area
###

region_jungle = world.new_obj("region_jungle", Region, "The Jungle Area")
region_jungle.add_rooms(["room_jungle", "room_helicopter_pad",
                         "room_clearing", "room_crevice"])

@before(Go(actor, direction))
def _before_go_village_area(actor, direction, context) :
    if actor.transitive_in("region_jungle") :
        if not actor.get_location().get_exit(direction) :
            raise AbortAction("""The jungle is too thick.  Besides,
            the wild animals might be dangerous.""")

##
## The Jungle
##

room_jungle = world.new_obj("room_jungle", Room, "The Jungle",
"""This is a crossroad of sorts in the middle of a bunch of nearly
impenetrable trees.  The trees occlude enough light to make it very
dark.  An animal trap is dimly visible on a tree.  Trails lead north,
south, east, and west.""")

jungle_tree = world.new_obj("jungle_tree", Scenery, "tree",
"""It is very... woody... and has leaves.  Hanging from the tree is a
trap.""")
jungle_tree.move_to(room_jungle)

@before(Climb(actor, jungle_tree))
def _before_climb_tree(actor, context) :
    raise AbortAction("That would be too simple.")

animal_trap = world.new_obj("animal_trap", BObject, "animal trap",
"""It consists of a bucket hanging from a branch with a loop of rope
running down to a catch.  It is rough but workable.""")
animal_trap["takeable"] = False
animal_trap.move_to(jungle_tree)

animal_trap_catch = world.new_obj("animal_trap_catch", BObject, "catch",
"""It looks like it would be set off by something roughly fish sized.
That's odd engineering -- when would a fish be running through a
jungle?""")
animal_trap_catch.move_to(animal_trap)

new_rope = world.new_obj("new_rope", Scenery, "new rope",
"""It is attached to the bucket and the catch and is used as the
bucket retainer when the trap is set.""")
new_rope.move_to(animal_trap)
prop_set_attached(world, new_rope, animal_trap)

prop_set_attached(world, bucket, new_rope)

class MakeTrapGoWith(BasicAction) :
    verb = "make trap go"
    gerund = "making the trap go with"
understand("make [object animal_trap] go with [something x]", MakeTrapGoWith(actor, x))
understand("set [object animal_trap] with [something x]", MakeTrapGoWith(actor, x))
understand("set [object animal_trap] off with [something x]", MakeTrapGoWith(actor, x))
understand("put [something x] in [object animal_trap]", MakeTrapGoWith(actor, x))
understand("throw [something x] on [object animal_trap]", MakeTrapGoWith(actor, x))
understand("make [object animal_trap_catch] go with [something x]", MakeTrapGoWith(actor, x))
understand("set [object animal_trap_catch] with [something x]", MakeTrapGoWith(actor, x))
understand("set [object animal_trap_catch] off with [something x]", MakeTrapGoWith(actor, x))
understand("put [something x] on [object animal_trap_catch]", MakeTrapGoWith(actor, x))
understand("throw [something x] on [object animal_trap_catch]", MakeTrapGoWith(actor, x))

@before(InsertInto(actor, x, BObject(y)))
def _before_insert_animal_trap(actor, x, y, context) :
    if y == "animal_trap" or y == "animal_trap_catch" :
        raise DoInstead(MakeTrapGoWith(x), suppress_message=True)

xobj_held(MakeTrapGoWith(actor, x))

@before(MakeTrapGoWith(actor, BObject(x)))
def _before_maketrapgo(actor, x, context) :
    if actor.get_location() == "room_jungle" :
        if world["bucket"].s_R_x(In, "animal_trap") :
            if x == "the_fish" :
                raise ActionHandled()
            else :
                raise AbortAction("That won't set off a roughly fish-sized catch.")
        else :
            raise AbortAction("The trap has already been used.")
    else :
        raise AbortAction("You don't see a trap around here.")

@when(MakeTrapGoWith(actor, x))
def _when_maketrapgo(actor, x, context) :
    remove_obj(context.world["the_fish"])
    context.world["bucket"].move_to("room_jungle")

@after(MakeTrapGoWith(actor, x))
def _after_maketrapgo(actor, x, context) :
    context.write_line("""Upon putting the fish on the catch, the rope
    was released and the bucket fell with a clang from the tree,
    landing on the ground, just missing the fish.  It didn't even land
    open-mouth-side-down.  As soon as this happened, a small jungle
    animal ran by and absconded with the flounder.""")

@before(Cut(actor, "new_rope"))
def _before_cut_rope_default(actor, context) :
    raise AbortAction("What, with your hands?")

@before(CutWith(actor, new_rope, BObject(y)))
def _before_cutwith_rope_default(actor, y, context) :
    raise AbortAction(str_with_obj("[the $y] isn't sharp enough to cut cooked pasta.", y=y))

@before(CutWith(actor, new_rope, "knife"))
def _before_cutwith_rope_knife(actor, context) :
    if world["bucket"].s_R_x(In, "animal_trap") :
        raise AbortAction("You can't get to it while it's hanging from the branch.")
    else :
        raise ActionHandled()

@when(CutWith(actor, new_rope, "knife"))
def _when_cutwith_rope_knife(actor, context) :
    bucket = context.world["bucket"]
    prop_detach(context.world, bucket)
    bucket.give_to(actor)
    remove_obj(context.world["new_rope"])
    context.write_line(str_with_objs("""It takes a bit of time, as
    [the $y] is only somewhat existent, but eventually the rope is
    severed, freeing the bucket.\n\nTaken.""", y="knife"))

##
## Helicopter pad
##

room_helicopter_pad = world.new_obj("room_helicopter_pad", Room, "The Helicopter Pad",
"""Lying on the ground is a small tarmac, square in shape, and it has
the markings as that of a helicopter pad -- a large circle with an
inscribed capital letter H.  This previous information is unnecessary
for the determination of the tarmac being a helicopter pad as a large
helicopter is presently sitting on the said tarmac.  A trail leads
south.""")
room_helicopter_pad.connect(room_jungle, "south")

tarmac = world.new_obj("tarmac", Scenery, "tarmac",
"""A cement helicopter landing square of a good size with the standard
writing signifying it is a cement helicopter landing square.""")
tarmac.move_to(room_helicopter_pad)

bell_helicopter = world.new_obj("bell_helicopter", BObject, "Bell helicopter",
"A large helicopter.")
bell_helicopter["words"] = ["bell", "@helicopter", "@copter"]
bell_helicopter["takeable"] = False
bell_helicopter.move_to(room_helicopter_pad)

penny = world.new_obj("penny", BObject, "penny",
"""A small copper penny.  It was made long before the 70s so there is
no zinc center, making this a great conductor.  Plus, you're lucky:
Lincoln is face up.""")
penny.move_to(room_helicopter_pad)

##
## The Clearing
##

room_clearing = world.new_obj("room_clearing", Room, "The Clearing",
"""Not much to see here except for a single manhole exactly in the
center of the cleared jungle.  [if [get valve switched_on]]You can
hear the hissing of steam coming from the pipe running from the west
into the ground.[else]A pipe runs from the west into the ground.
[endif][if [when good_fronds in room_clearing]] A few palm fronds
litter the ground.[endif]""")
room_clearing.connect(room_jungle, "east")

good_fronds = world.new_obj("good_fronds", BObject, "good palm fronds",
"""It looks like they were cut right from the tree.  It looks like
they'd block sunlight very well.""")
good_fronds["indefinite_name"] = "some good palm fronds"
good_fronds.move_to(room_clearing)
good_fronds["reported"] = False
@when(Take(actor, good_fronds))
def _when_take_fronds(actor, context) :
    context.world["good_fronds"]["reported"] = True

clearing_pipe = world.new_obj("clearing_pipe", Scenery, "brass pipe",
"""The brass pipe runs into the ground from the west[if [get valve
switched_on]], and it is hissing[endif].""")
clearing_pipe.move_to(room_clearing)

manhole = world.new_obj("manhole", Door, "manhole",
"""A circular metal covering with a circular rotary handle which
happens to look a little weathered and rusty.  It is [get manhole
is_open_msg].""")
manhole["words"] = ["rotary", "@handle", "@manhole"]
manhole["lockable"] = True
manhole["locked"] = True
manhole.add_exit_for(room_clearing, "down")
manhole.unlockable_with(driftwood)
manhole["no_enter_msg"] = """You try and you try, but you can not seem
to pass through solid metal.  Try opening it first."""
manhole["unlock_needs_key_msg"] = manhole["no_open_msg"] = """
The manhole door and handle are too rusty to open by hand.  Maybe
something could be used for leverage."""
manhole["wrong_key_msg"] = """That doesn't give you enough leverage."""

@when(Go(actor, "down"))
def _when_after_down_manhole(actor, context) :
    if actor.get_location() == "room_clearing" :
        context.write_line("You climb some ways down a ladder into...")

@before(OpenWith(actor, "manhole", "driftwood"))
def _before_openwith_manhole(actor, context) :
    raise DoInstead(UnlockWith(actor, "manhole", "driftwood"), suppress_message=True)

@when(UnlockWith(actor, "manhole", "driftwood"))
def _when_unlock_manhole(actor, context) :
    manhole = context.world["manhole"]
    manhole["lockable"] = False
    remove_obj(world["driftwood"])
    # manhole is set to unlocked by UnlockWith handler
    manhole["open"] = True
@after(UnlockWith(actor, "manhole", "driftwood"))
def _after_unlock_manhole(actor, context) :
    context.write_line("""The extra torque garnered by the length of
    the driftwood frees the handle from the rust.  The manhole
    opens, but your driftwood splinters.\n\nOpened.""")
    raise ActionHandled()

##
## The Crevice
##

room_crevice = world.new_obj("room_crevice", Room, "The Crevice",
"""Wisps of steam are eminating from a deep fissure in the ground.
They dissolve among a pleasantly annoying hiss.  A single pipe runs
east toward the nondescript clearing.  [if [get valve switched_on]]It
sounds like steam is rushing through the pipe.[endif]""")
room_crevice.connect(room_clearing, "east")

fissure = world.new_obj("fissure", Scenery, "fissure",
"""The fissure is very deep.  The pipe extends down farther than the
eye can see with steam swirling about.  It may seem crazy, but it
almost seems like there are stars and entire universes far below.
Maybe they are just fireflies.""")
fissure["words"] = ["@fissure", "@crevice"]
fissure.move_to(room_crevice)

pipe = world.new_obj("pipe", Scenery, "brass pipe",
"""A[if [get valve switched_on]]hissing[endif] brass pipe runs from
deep within the earth to the east.[if [when pile_palm_fronds in
room_crevice]] A pile of fronds is covering a segment of the
pipe.[else] Partway down the pipe is a matching brass valve.[endif]""")
pipe.move_to(room_crevice)

pile_palm_fronds = world.new_obj("pile_palm_fronds", BObject, "pile of palm fronds",
"""A pile of palm fronds covering the pipe.""")
pile_palm_fronds.move_to(room_crevice)
understand("move [object pile_palm_fronds]", Take(actor, "pile_palm_fronds"))

@when(Take(actor, pile_palm_fronds))
def _when_take_pile_palms(actor, context) :
    remove_obj(context.world["pile_palm_fronds"])
    context.world["valve"].move_to("room_crevice")
    raise ActionHandled()
@after(Take(actor, pile_palm_fronds))
def _after_take_pile_palms(actor, context) :
    context.write_line("""The palm fronds just disperse in every
    direction, revealing a small brass valve.""")
    raise ActionHandled()

valve = world.new_obj("valve", Device, "brass valve",
"""A standard small-handled valve.""")
valve["switched_on"] = False
valve["switch_on_msg"] = """Opening the valve releases a continuous
hiss of steam into the pipe."""
valve["switch_off_msg"] = """The hiss abruptly stops."""

understand("turn [object valve]", Switch(actor, "valve"))
understand("open [object valve]", SwitchOn(actor, "valve"))
understand("close [object valve]", SwitchOff(actor, "valve"))

###
### Underground area
###

region_underground = world.new_obj("region_underground", Region, "Underground Area")
region_underground.add_rooms(["room_power_station", "room_transmission"])

conduit = world.new_obj("conduit", Scenery, "thick metal conduit",
"""Each cable is as thick as and in the general form of a twinkie and
is covered in as many layers of insulation and packing materials.""")
conduit["words"] = ["think", "metal", "@conduit", "@cable", "@cables"]
conduit.move_to(region_underground)

class UndergroundDefinitions(NonGameObject) :
    @addproperty()
    def transformer_on(self) :
        return (self.world["valve"]["switched_on"]
                and self.world["penny"].s_R_x(In, "fuse_receptacle")
                and self.world["knife_switch"]["switched_on"])
underground_defs = world.new_obj("underground_defs", UndergroundDefinitions)

##
## Power station
##

room_power_station = world.new_obj("room_power_station", Room, "The Power Station",
"""The pipes from above run along the ladder you came down into a
large steam turbine.  The air is very murky with swirls of steam
percolating from the myriad of pipes.  The turbine is [if [get valve
switched_on]]currently clattering and sputtering from the flow of
steam from above[else]ominously silent[endif]. A shielded pair of
cables runs from the generator to the north.""")

manhole.add_exit_for(room_power_station, "up")

ladder = world.new_obj("ladder", Scenery, "ladder",
"""It's the ladder you came down.""")
ladder.move_to(room_power_station)

@before(Climb(actor, "ladder"))
def _before_climb_ladder(actor, context) :
    raise DoInstead(Go(actor, "up"), suppress_message=True)

@when(Go(actor, "up"))
def _when_after_down_manhole(actor, context) :
    if actor.get_location() == "room_power_station" :
        context.write_line("You climb up the ladder to...")

steam_generator = world.new_obj("steam_generator", Scenery, "steam turbine",
"""A brass power generation relic riveted together.[if [get valve
switched_on]] From within the depths of the device, the sound of
spinning and banging metal can be heard.  Signs of electricity can be
seen in the form of sparks.[else] It is silent.[endif] A thick metal
conduit runs out of the device.""")
steam_generator["words"] = ["steam", "@generator", "@turbine"]
steam_generator.move_to(room_power_station)

##
## Transmission room
##

room_transmission = world.new_obj("room_transmission", Room, "The Transmission Room",
"""[if [get underground_defs transformer_on]]A low frequency hum
permeates the room; it could make a person go crazy. [endif]A single
transformer sits in the middle of a room with many conduits and wires
going to and from the device.  The transformer has some controls.""")
room_transmission.connect(room_power_station, "south")

transformer = world.new_obj("transformer", Scenery, "transformer",
"""It is a large, iron-cored transformer wrapped in thousands of turns
of fine copper wire.  Next to the windings are a few devices: a knife
switch and an emergency fuse receptacle.  The conduits run from the
power station into the transformer, and others run from the
transformer into the ground toward the east.[if [get underground_defs
transformer_on]] A low hum is eminating from the vibrating magnetic
coils.[endif]""")
transformer.move_to(room_transmission)

fuse_receptacle = world.new_obj("fuse_receptacle", Container, "emergency fuse receptacle",
"""It looks like the last fuse burned out.  It takes circular fuses,
but if safety is ignored briefly, any circular conductor will do.[if
[get fuse_receptacle contents]] Currently inside the receptacle
[is_are_list [get fuse_receptacle contents]][endif].""")
fuse_receptacle["takeable"] = False
fuse_receptacle.move_to(transformer)

knife_switch = world.new_obj("knife_switch", Device, "knife switch",
"""A sheet of metal with a handle that is moved between a pair of
metal contacts to make or break a circuit.  This one is a single-pole,
single-throw switch.  It is currently [get knife_switch
is_switched_msg].""")
knife_switch["takeable"] = False
knife_switch["switched_on"] = True
knife_switch.move_to(transformer)

@before(InsertInto(actor, x, "fuse_receptacle"))
def _before_insert_fuse(actor, x, context) :
    if context.world["knife_switch"]["switched_on"] :
        raise AbortAction("To prevent electrical shock, you ought to turn off the knife switch.")

@before(InsertInto(actor, x, "fuse_receptacle"))
def _before_insert_fuse(actor, x, context) :
    if context.world["fuse_receptacle"]["contents"] :
        raise AbortAction("There's already something in the fuse receptacle.")

@after(InsertInto(actor, x, "fuse_receptacle"))
def _after_insert_fuse(actor, x, context) :
    context.write_line(str_with_objs("You put [the $x] into [the fuse_receptacle].", x=x))
    raise ActionHandled()

@after(SwitchOn(actor, "knife_switch"))
def _after_switchon_knifeswitch(actor, context) :
    context.write_line("You switch [the knife_switch] on.")
    if context.world["underground_defs"]["transformer_on"] :
        context.write_line("A low hum permeates the underground complex.")
    else :
        context.write_line("Nothing happens.")
    raise ActionHandled()

###
### The Volcano
###

##
## West side of volcano
##

room_west_volcano = world.new_obj("west_volcano", Room, "The Western Side of the Volcano",
"""This is one side of a volcano.  Acrid smoke is billowing from the
top of the cinder cone and rolling down the sides.  A secret door is
hidden on the side of the volcano.""")
room_west_volcano["no_go_msg"] = "Sulfur-laden rocks bar the way."
room_west_volcano.connect(room_jungle, "west")

smoke = world.new_obj("smoke", Scenery, "acrid smoke",
"""The smoke smells strangly of rocket fuel.""")
smoke.move_to(room_west_volcano)

elevator_door = world.new_obj("elevator_door", Door, "secret elevator door",
"""It's secret and express, as the sign above the door does not say.""")
elevator_door.add_exit_for(room_west_volcano, "east")
elevator_door["lockable"] = True
elevator_door["locked"] = True
elevator_door.unlockable_with(key_card)

secret_sign = world.new_obj("secret_sign", Readable, "secret sign",
"""In bold, clear writing in carbon dioxide laser writing on titanium,
the sign says: 'This is not a secret and express elevator door.'""")
secret_sign["takeable"] = False
secret_sign["reported"] = False
secret_sign.move_to(room_west_volcano)

##
## Secret Express Elevator
##

room_secret_elevator = world.new_obj("room_secret_elevator", Room, "The Secret Express Elevator",
"""Next to the [get elevator_door is_open_msg] elevator door is a
small control panel with a single button and a small indicator light
which is currently [if [get underground_defs transformer_on]]on[else]off[endif].""")
elevator_door.add_exit_for(room_secret_elevator, "west")

control_panel = world.new_obj("control_panel", Scenery, "control panel",
"""A brushed aluminum panel.  It is very sparse with only two
features: a small blue button, and an indicator light which [if [get
underground_defs transformer_on]]is[else]isn't[endif] currently
lit.""")
control_panel.move_to(room_secret_elevator)

indicator_light = world.new_obj("indicator_light", Scenery, "small indicator light",
"""It is a pilot light, red in color.  [if [get underground_defs
transformer_on]]It is shining brightly.[else]No light is being
emitted.[endif]""")
indicator_light.move_to(control_panel)

blue_button = world.new_obj("blue_button", BObject, "small blue button",
"""It's a small blue button on the control panel.  It's glowing
slightly, eager for you to push it.""")
blue_button["takeable"] = False
blue_button.move_to(control_panel)

@before(Push(actor, blue_button))
def _before_push_blue_button(actor, context) :
    if context.world["underground_defs"]["transformer_on"] :
        if world["elevator_door"]["open"] :
            raise AbortAction("""A voice booms from the control panel:
                                 'Please close the elevator door.'""")
        else :
            raise ActionHandled()
    else :
        raise AbortAction("Nothing happens.")

@when(Push(actor, blue_button))
def _when_push_blue_button(actor, context) :
    actor.move_to("room_lab")

@after(Push(actor, blue_button))
def _after_push_blue_button(actor, context) :
    context.write_line("""The red light begins to blink, and, without
    warning, a trap door opens up underneath you and deposits you
    in...""")
    run_action(Look(actor), context=context)
    context.write_line("""You get up and recover from the fall.""")

##
## The lab
##

room_lab = world.new_obj("room_lab", Room, "The Lab",
"""Lots of equipment, all evil.  The horror...""")

red_button = world.new_obj("red_button", BObject, "large red button",
"""It looks like nothing good will come out of pushing this button
that has inscribed lettering of 'Do not push.'""")
red_button["takeable"] = False
red_button.move_to(room_lab)

@before(Push(actor, red_button))
def _before_push_red_button(actor, context) :
    raise ActionHandled()

@when(Push(actor, red_button))
def _when_push_red_button(actor, context) :
    finish_game(EndGameWin())


###
### Game endings
###

@when(EndGameWin())
def _end_game_win(context) :
    context.write_line("""Just kidding, the button actually said 'Do
    push for a party.'  There was a surprise party for you.  The whole
    thing was set up because you like adventures.  You ate a lot of
    cake.

    You won!""")

###
### Begin the game
###

if __name__=="__main__" :
    basic_begin_game(see_world_size=False)
