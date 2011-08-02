# teptour.py
#
# The tEp virtual house tour!
# (c) 2011 tEp, Xi chapter
#
# Authors: Kyle Miller

execfile("textadv/basicsetup.py")

world[Global("release_number")] = "0.0 (August 1, 2011)"

world[Global("game_title")] = "The tEp Virtual House Tour"
world[Global("game_headline")] = "A factual fantasy"
world[Global("game_author")] = "tEp, Xi chapter"
world[Global("game_description")] = """
<i><b>Note:</b> This is the development version of the house tour.
Please talk to Kyle if you have any suggestions, stories, or puzzles
to include.  If you come across any error messages, please e-mail them
to him.  Thanks.</i>[newline]

You've heard stories about tEp: the purple palace, a.k.a. the last stronghold
of the knights of the lambda calculus.  You've been meaning to get
over there to see what it's all about.

[newline]But, you are lazy.  Instead, you went to the tEp website and
opted for the <i>virtual</i> house tour.  We understand.

[newline]For your tour, we are providing you with [ob <Irving
Q. Tep>], the spirit of the house.  He'll be giving you the
descriptions and stories you will read during your tour.

[newline]Without further ado, we present"""

#####################
### Fun and games ###
#####################

###
### Images
###

@stringeval.add_eval_func("img")
def _str_eval_img(eval, act, ctxt, *obs) :
    """[img filename] takes an image and inserts it into the the
    description."""
    from PIL import Image
    import os.path
    filename = obs[0][0]
    css_class = "desc_img"
    if len(obs)>1 and obs[1][0] == "left" :
        css_class = "desc_img_left"
    width, height = Image.open(os.path.join(os.path.abspath("games/teptour_files"), filename)).size
    print "Image",filename,"is",width,"x",height
    return ["<img class=\""+css_class+"\" width=\""+str(width)+"\" height=\""+str(height)+"\" src=\"teptour/"+filename+"\">"]

###
### Eiting
###

class Eiting(BasicAction) :
    """Eiting(actor, x) for the actor eiting x."""
    verb = "eit"
    gerund = "eiting"
    numargs = 2
parser.understand("eit [something x]", Eiting(actor, X))

require_xobj_accessible(actionsystem, Eiting(actor, X))

@before(Eiting(actor, X))
def before_eiting_default(actor, x, ctxt) :
    raise AbortAction("{Bob} {doesn't} think it would be wise to eit that.", actor=actor)


class EitingWith(BasicAction) :
    """EitingWith(actor, x, y) for the actor eiting x with y."""
    verb = ("eit", "with")
    gerund = ("eiting", "with")
    numargs = 3
parser.understand("eit [something x] with [something y]", EitingWith(actor, X, Y))

require_xobj_accessible(actionsystem, EitingWith(actor, X, Y))
require_xobj_held(actionsystem, EitingWith(actor, Z, X))

@before(EitingWith(actor, X, Y))
def before_eiting_default(actor, x, y, ctxt) :
    raise AbortAction(str_with_objs("{Bob} {doesn't} think it would be wise to eit [the $x] that.", x=x),
                      actor=actor)

###
### Playing stupidball
###

class PlayingStupidball(BasicAction) :
    verb = "play stupidball"
    gerund = "playing stupidball"
    numargs = 1
parser.understand("play stupidball", PlayingStupidball(actor))

@before(PlayingStupidball(actor) <= PNot(AccessibleTo(actor, "ex_ball")))
def before_stupidball_need_ball(actor, ctxt) :
    raise AbortAction("{Bob} {doesn't} see anything around {him} with which {he} can play stupidball.", actor=actor)
@when(PlayingStupidball(actor))
def when_playing_stupidball(actor, ctxt) :
    ctxt.world.activity.put_in("ex_ball", ctxt.world[Location(actor)])
@report(PlayingStupidball(actor))
def report_playing_stupidball(actor, ctxt) :
    ctxt.write("""A couple of teps come out to join you as you throw
    [the ex_ball] around the room, and you nearly break a couple of
    things as the ball whizzes through the air at high velocities.
    After much merriment, you all get bored of the game, and put the
    ball down.""")

###
### Irving Q. Tep
###

world.activity.put_in("player", "253 Commonwealth Ave")

parser.understand("upstairs", "up", dest="direction")
parser.understand("downstairs", "down", dest="direction")
parser.understand("inside", "in", dest="direction")

quickdef(world, "Irving Q. Tep", "person", {
        Gender : "male",
        ProperNamed : True,
        Description : """It's Irving Q. Tep, spirit of the house.  He
        is giving you stories and such <i>telepathically</i> using
        images and text.  Quite amazing.

        [newline]You can ask Irving Q. Tep about various concepts. For
        instance "[action <ask about stupidball>]" (which is shorthand
        for "[action <ask Irving about stupidball>]").""" # developers: see [ask ...] for links
        },
         make_part_of="player")

@stringeval.add_eval_func("ask")
def _str_eval_ob(eval, act, ctxt, *obs) :
    """[ask ob <text>] is for adding links which ask Irving Q. Tep
    about ob, where the optional text is the text of the link."""
    if len(obs) == 1 :
        topic = obs[0]
        text = obs[0]
    else :
        topic = obs[0]
        text = obs[1]
    return [make_action_link(text[0], "ask Irving Q. Tep about "+topic[0])]

# See section "Consulting Irving Q. Tep..." for adding things one can
# ask him about

####################
### The basement ###
####################

quickdef(world, "Basement", "room", {
        Description : """This is the basement of tEp.  You can go back
        [dir up] the stairs, [dir southwest] into the kitchen, or [dir
        northwest] into the bike room."""
        })
world.activity.connect_rooms("Basement", "southwest", "The Kitchen")
world.activity.connect_rooms("Basement", "northwest", "The Bike Room")

quickdef(world, "The Kitchen", "room", {
        Description : """This is a commercial-grade kitchen.  You can
        go [dir northeast] back to the basement."""
        })

quickdef(world, "The Bike Room", "room")

###################
### First floor ###
###################

###
### In front of tep (253 Commonwealth Ave)
###

quickdef(world, "253 Commonwealth Ave", "room", {
        Description : """[img front_small.jpg left]You are standing
        outside the illustrious Tau Epsilon Phi (Xi chapter), the
        veritable purple palace.  It is a hundred-year-old brownstone
        in the middle of Boston's Back Bay.  Outside the building is a
        [ob <purple tree>] and a [ob <park bench>].  To the [dir
        north] is the [ob door] to enter tEp."""
        })

quickdef(world, "purple tree", "thing", {
        Scenery : True,
        Description : """Looking both ways, you see that this is the
        only purple tree along the entire avenue.  It's very
        purple."""
        },
         put_in="253 Commonwealth Ave")

quickdef(world, "park bench", "supporter", {
        Scenery : True,
        IsEnterable : True,
        Description : """[img front_bench.jpg left]It's a handmade
        park bench wrought from steel, built by a previous tEp.  After
        a few years of use, it's been bent quite out of whack."""
        },
         put_in="253 Commonwealth Ave")
parser.understand("sit on [object park bench]", Entering(actor, "park bench"))

@report(Entering(actor, "park bench"))
def report_sitting_on_park_bench(actor, ctxt) :
    ctxt.write("You sit on [ob <park bench>], and the metal creaks and bends under your weight.")
    raise ActionHandled()

quickdef(world, "front door", "door", {
        Reported : False,
        Lockable : True,
        IsLocked : True,
        Description : """It's a big, old door.  Through the glass, you
        can see blinking LED lights hanging from the stairwell."""
        })
world[NoLockMessages("front door", "no_open")] = "It's locked.  Perhaps you should ring the [ob doorbell]."
world.activity.connect_rooms("253 Commonwealth Ave", "north", "front door")
world.activity.connect_rooms("front door", "northwest", "The Foyer")

@before(Going(actor, "in") <= PEquals(ContainingRoom(actor), "253 Commonwealth Ave"))
def rewrite_going_in_tep(actor, ctxt) :
    raise DoInstead(Going(actor, "north"), suppress_message=True)

quickdef(world, "doorbell", "thing", {
        Words : ["@doorbell", "door", "@bell"],
        Scenery : True,
        Description : """It's a small, black button, and you almost
        didn't notice it.  It turns out the FedEx guy enjoys this
        doorbell."""
        },
         put_in="253 Commonwealth Ave")
parser.understand("ring [object doorbell]", Pushing(actor, "doorbell"))

@before(Pushing(actor, "doorbell"))
def before_pushing_doorbell(actor, ctxt) :
    raise ActionHandled()
@when(Pushing(actor, "doorbell"))
def when_pushing_doorbell(actor, ctxt) :
    ctxt.world.activity.put_in(actor, "The Foyer")
@report(Pushing(actor, "doorbell"))
def report_pushing_doorbell(actor, ctxt) :
    ctxt.write("""You hear a loud subwoofer buzzing at 32 Hz, and,
    after a few moments, footsteps down the stairs.  A young tEp opens
    the door for you and leads you in.  "Ah, I see you're getting the
    virtual house tour from [ob <Irving Q. Tep>]," he says.  "Those
    are really good."  Before running off, he brings you to...[break]""")

@before(Going(actor, "north") <= PEquals("253 Commonwealth Ave", Location(actor)))
def ring_doorbell_instead(actor, ctxt) :
    ctxt.write("The door is locked.  Looking around the door, you find a doorbell, and you ring that instead.[newline]")
    raise DoInstead(Pushing(actor, "doorbell"), suppress_message=True)

###
### The Foyer
###

quickdef(world, "The Foyer", "room", {
        Visited : True,
        Description : """[img foyer_small.jpg left]This is the foyer.
        You can keep going [dir northwest] to the center room."""
        })
world.activity.connect_rooms("The Foyer", "northwest", "The Center Room")

@before(Going(actor, "south") <= PEquals("The Foyer", Location(actor)))
def dont_wanna_leave(actor, ctxt) :
    raise AbortAction("""Nah, you don't need to leave that way!  This
    is a virtual house: just close your web browser if you want to
    quit.""")


###
### Center Room
###

quickdef(world, "The Center Room", "room", {
        Visited : True,
        Description : """[img center_small.jpg]This is the center
        room, which is a common area at tEp.  Around you are composite
        photos from the past decade, and a [ob chandelier] that seems
        like it has seen better days.  Looking up, you can see the
        skylight and the [ob <center stairwell>]. You can go [dir
        south] to the front room, [dir north] to the dining room, [dir
        upstairs] to the second floor, [dir northeast] to the back
        stairwell, or [dir southeast] back to the foyer."""
        })
world[DirectionDescription("The Center Room", "up")] = "Looking up, you see the [ob <center stairwell>]."
world.activity.connect_rooms("The Center Room", "up", "The Second Landing")
world.activity.connect_rooms("The Center Room", "south", "The Front Room")
world.activity.connect_rooms("The Center Room", "north", "The Dining Room")
world.activity.connect_rooms("The Center Room", "northeast", "back_stairwell_1")

quickdef(world, "chandelier", "thing", {
        Scenery : True,
        Description : """This chandelier, which is affixed to the
        center of the ceiling, has clearly been [ask eit eited] many
        times over the years by the game of [ask stupidball].  One
        time, during one particularly rousing game of stupidball, all
        of the sconces exploded into a shower of glass.  It was really
        a sight to see."""
        },
         put_in="The Center Room")

quickdef(world, "broken chandelier", "thing", {
        Scenery : True,
        Description : """This chandelier, which is affixed to the
        center of the ceiling, has been [ask eited], and now half of
        the lights don't work any more.  Good job."""
        })
quickdef(world, "broken sconce", "thing", {
        Description : """It's half a sconce that fell from the [ask
        eit eiting] of the [ob chandelier]."""
        })

@before(Eiting(actor, "chandelier"))
def before_eiting_chandelier(actor, ctxt) :
    raise AbortAction("The chandelier is too high up for you to eit.  Maybe there's something you could eit it with.")
@before(Eiting(actor, "broken chandelier"))
def before_eiting_brokenchandelier(actor, ctxt) :
    raise AbortAction("The chandelier looks well eited already.")

quickdef(world, "ex_ball", "thing", {
        Name : "large green exercise ball",
        Words : ["big", "large", "green", "exercise", "@ball"],
        Description : """This is a large green exercise ball that is
        used to play [ask stupidball]."""
        }, put_in="The Center Room")
@report(Dropping(actor, "ex_ball"))
def report_dropping_ball(actor, ctxt) :
    ctxt.write("It bounces a few times before it settles down.")

@before(EitingWith(actor, "chandelier", "ex_ball"))
def before_eiting_chandelier_with_stupidball(actor, ctxt) :
    raise ActionHandled()
@when(EitingWith(actor, "chandelier", "ex_ball"))
def when_eiting_chandelier_with_stupidball(actor, ctxt) :
    ctxt.world.activity.remove_obj("chandelier")
    ctxt.world.activity.put_in("broken chandelier", "The Center Room")
    ctxt.world.activity.put_in("broken sconce", "The Center Room")
    ctxt.world.activity.put_in("ex_ball", "The Center Room")
@report(EitingWith(actor, "chandelier", "ex_ball"))
def report_eiting_chandelier(actor, ctxt) :
    ctxt.write("""Good plan.  You kick the large green exercise ball
    at high velocity into the chandelier, and half the sconces explode
    in a showering display of broken glass, one of which falls to the
    ground.  There didn't need to be that much light in this room,
    anyway.""")
@before(EitingWith(actor, "broken chandelier", Y))
def before_eitingwith_brokenchandelier(actor, y, ctxt) :
    raise AbortAction("The chandelier looks well eited already.")

quickdef(world, "center stairwell", "thing", {
        Scenery : True,
        Description : """[img center_stairwell_small.jpg left]The
        center stairwell is three flights of stairs, capped by a
        skylight. The color-changing lights illuminate it
        dramatically."""
        },
         put_in="The Center Room")

###
### Front room
###

quickdef(world, "The Front Room", "room", {
        Visited : True,
        Description : """[img front_room_small.jpg left]This is where
        the tEps play Super Smash Bros. after dinner every night.  You
        can go [dir north] to the center room."""
        })

###
### Dining room
###

quickdef(world, "The Dining Room", "room", {
        Visited : True,
        Description : """This is the dining room.  Where tEps eat.  To
        the [dir south] is the center room, and to the [dir east] is
        the upstairs kitchen."""
        })
world.activity.connect_rooms("The Dining Room", "east", "The Upstairs Kitchen")

###
### First floor of the back stairwell
###

quickdef(world, "back_stairwell_1", "room", {
        Name : "First Floor of the Back Stairwell",
        Visited : True,
        Description : """You are in the back stairwell.  You can go
        [dir upstairs] to the second floor, [dir southwest] to the
        center room, [dir north] to the upstairs kitchen, or [dir
        downstairs] into the basement."""
        })

world.activity.connect_rooms("back_stairwell_1", "down", "Basement")
world.activity.connect_rooms("back_stairwell_1", "north", "The Upstairs Kitchen")
world.activity.connect_rooms("back_stairwell_1", "up", "back_stairwell_2")

###
### Upstairs Kitchen
###

quickdef(world, "The Upstairs Kitchen", "room", {
        Description : """This is the upstairs kitchen.  To the [dir
        north] is the dining room, and to the [dir south] is the back
        stairwell."""
        })

####################
### Second floor ###
####################

quickdef(world, "The Second Landing", "room", {
        Visited : True,
        Description : """[img 2nd_landing_small.jpg left]This is the
        second landing.  You can go [dir southeast] to 21, [dir south]
        to 22, [dir north] to 23, [dir northeast] to the back
        stairwell, [dir upstairs], and [dir downstairs].  The
        bathrooms are to the [dir southwest] and [dir west]."""
        })
world.activity.connect_rooms("The Second Landing", "southeast", "21")
world.activity.connect_rooms("The Second Landing", "south", "22")
world.activity.connect_rooms("The Second Landing", "north", "23")
world.activity.connect_rooms("The Second Landing", "northeast", "back_stairwell_2")
world.activity.connect_rooms("The Second Landing", "southwest", "Second Front")
world.activity.connect_rooms("The Second Landing", "west", "Second Back")
world.activity.connect_rooms("The Second Landing", "up", "The Third Landing")

###
### 21
###
quickdef(world, "21", "room", {
        Visited : True,
        })

###
### 22
###
quickdef(world, "22", "room", {
        Visited : True,
        Description : """This is 22.  You can see some [ob
        <color-changing lights>].  You can go [dir north] back to the
        second landing."""
        })

quickdef(world, "22_lights", "thing", {
        Name : "color-changing lights",
        Scenery: True,
        Description : """[img 22_lights_small.jpg left]Known as
        "candyland," these are ethernet-controlled lights which can
        cycle through colors or follow music for a lightshow."""
        },
         put_in="22")

##
## The Closet in 22
##
quickdef(world, "The Closet in 22", "room", {
        Description : """It's a closet.  You can go [dir southeast]
        into 22."""
        })
world[DirectionDescription("The Closet in 22", "up")] = """Looking up, you
can see a ladder to a room above this closet."""

world.activity.connect_rooms("22", "northwest", "The Closet in 22")
world.activity.connect_rooms("The Closet in 22", "up", "The Batcave")

world[WhenGoMessage("The Closet in 22", "up")] = """With some
difficulty, you climb the ladder into..."""

###
### The Batcave
###
quickdef(world, "The Batcave", "room", {
        Description : """This is one of the secret rooms of tEp.  It's
        a room built into the interstitial space between the second
        and third floors by Batman, a tEp from the 80s.  People have
        actually lived in this room before.  The only things in here
        are a [ob mattress] and some [ob shelves][if [get IsOpen
        batcave_shelves]], which have been opened, revealing the
        second front interstitial space to the [dir north][endif].
        You can go [dir down] to the closet in 22 or [dir up] to the
        closet in 32."""
        })
world.activity.connect_rooms("The Batcave", "up", "The Closet in 32")

world[WhenGoMessage("The Batcave", "up")] = """You squeeze through the
hole in the floor and make your way to..."""
world[WhenGoMessage("The Batcave", "down")] = """You carefully climb
down the ladder into..."""

# the complexity is because I want the door to be different in each
# room, and there's no support for this in the engine, yet.
quickdef(world, "batcave_shelves", "door", {
        Name : """[if [== [get Location [current_actor_is]] <The
        Batcave>]]small shelves[else]small panel[endif]""",
        IndefiniteName : """[if [== [get Location [current_actor_is]]
        <The Batcave>]]some small shelves[else]a small panel[endif]""",
        Words : ["small", "wooden", "wood", "@shelves", "@panel"],
        Reported : False,
        Description : """[if [== [get Location [current_actor_is]]
        <The Batcave>]]These are small shelves next to the [ob bed],
        and nothing is on them.  [if [get IsOpen batcave_shelves]]The
        shelves are swung open, revealing the second front
        interstitial space to the [dir north][else]The shelves seem to
        be a bit wobbly.[endif][else][if [get IsOpen
        batcave_shelves]]The panel is open, revealing the Batcave to
        the [dir south][else]You can see some lights shining through
        cracks around this panel.[endif][endif]"""
        })
world.activity.connect_rooms("The Batcave", "north", "batcave_shelves")
world.activity.connect_rooms("batcave_shelves", "north", "2f_interstitial")

###
### 23
###
quickdef(world, "23", "room", {
        Visited : True,
        })

###
### Second floor of the back stairwell
###

quickdef(world, "back_stairwell_2", "room", {
        Name : "Second Floor of the Back Stairwell",
        Visited : True,
        Description : """You are in the back stairwell.  You can go
        [dir upstairs] to the third floor, [dir southwest] to second
        landing, [dir north] to 24, or [dir downstairs] to the first
        floor."""
        })

world.activity.connect_rooms("back_stairwell_2", "down", "back_stairwell_1")
world.activity.connect_rooms("back_stairwell_2", "north", "24")
world.activity.connect_rooms("back_stairwell_2", "up", "back_stairwell_3")

###
### 24
###
quickdef(world, "24", "room", {
        Visited : True,
        })

###
### Second Front
###
quickdef(world, "Second Front", "room", {
        Description : """This is second front, a bathroom named for
        its presence on the second floor and closer to the front of
        the house.  You can go [dir northeast] to the second
        landing."""
        })
world[DirectionDescription("Second Front", "up")] = """Looking up, you
see an [ob <access hatch>] in the ceiling."""

quickdef(world, "2f_ceiling_door", "door", {
        Name : "ceiling access hatch",
        Reported : False,
        Words : ["ceiling", "access", "@hatch", "@door"],
        Description : """[if [get IsOpen 2f_ceiling_door]]It's an open
        ceiling access hatch, revealing a ladder going from second
        front up to the interstitial space above it.[else]It's a
        ceiling access hatch, and it's closed.[endif]"""
        })
world.activity.connect_rooms("Second Front", "up", "2f_ceiling_door")
world.activity.connect_rooms("2f_ceiling_door", "up", "2f_interstitial")

###
### The Second Front Interstitial Space
###
quickdef(world, "2f_interstitial", "room", {
        Name : "The Second Front Interstitial Space",
        Description : """This is the interstitial space above second
        front.  You can go [dir down] through the [ob <access hatch>]
        into second front.[if [get IsOpen batcave_shelves]] Through
        the small wooden panel (which is open), you can go [dir south]
        to the batcave.[endif]"""
        })
world[DirectionDescription("2f_interstitial", "south")] = """Looking
south, you see some light shining around a [ob <small wooden
panel>]."""

quickdef(world, "safe", "container", {
        FixedInPlace : True,
        Openable : True,
        IsOpen : False,
        Lockable : True,
        IsLocked : True,
        Description : """It's a safe whose combination has long been
        forgotten.  It was used to store the house marshmallows to
        prevent tEps from eating them."""
        },
         put_in="2f_interstitial")

quickdef(world, "Second Back", "room")

###################
### Third floor ###
###################

quickdef(world, "The Third Landing", "room", {
        Visited : True,
        Description : """[img 3rd_landing_small.jpg left]This is the
        third landing.  You can go [dir southeast] to 31, [dir south]
        to 32, [dir north] to 33, [dir northeast] to the back
        stairwell, [dir upstairs], and [dir downstairs]."""
        })
world.activity.connect_rooms("The Third Landing", "southeast", "31")
world.activity.connect_rooms("The Third Landing", "south", "32")
world.activity.connect_rooms("The Third Landing", "north", "33")
world.activity.connect_rooms("The Third Landing", "northeast", "34")
world.activity.connect_rooms("The Third Landing", "up", "The Fourth Landing")

quickdef(world, "31", "room", {
        Visited : True,
        })

quickdef(world, "32", "room", {
        Visited : True,
        Description : """It's a room.  To the [dir northwest] is a
        closet, and you can go [dir north] to the third landing."""
        })

quickdef(world, "The Closet in 32", "room", {
        Description : """It's a closet.  You can go [dir southeast] into 32."""
        })
world[DirectionDescription("The Closet in 32", "down")] = """Looking down,
you can see a passageway into a room below this closet."""

world[WhenGoMessage("The Closet in 32", "down")] = """You squeeze
through a small opening in the floor to get into...""" # goes to batcave

world.activity.connect_rooms("32", "northwest", "The Closet in 32")
world.activity.connect_rooms("The Closet in 32", "down", "The Batcave")

quickdef(world, "33", "room", {
        Visited : True,
        Description : """This is a room.  You see a [ob <large net>]
        hanging in the room, and a collection of [ob <bad ties>]."""
        })

quickdef(world, "authentic Free Willy net", "container", {
        Words : ["large", "red", "purple", "authentic", "Free", "Willy", "fishing", "@net"],
        IsEnterable : True,
        Scenery : True,
        Description : """This large fishing net is one of the nets
        from the movie Free Willy.  It was purchased on eBay for about
        two-hundred twenty-two dollars some time ago, and installed in
        this room at the advice of a fisherman over at the wharf.
        There was a failed attempt to die the net purple, and it ended
        up being a reddish color instead.
        [newline]
        While this net was from the production of Free Willy, it never
        actually touched the whale; rather, it was the spare.  When
        the idea of buying the net came up at a house meeting, the
        house vegans were outraged at the idea of putting a net that
        touched the whale in the house.  That, and the fact that the
        spare net was much cheaper than the primary net, led to this
        net hanging in 33.
        [newline]
        It's said that the net is limited by volume, and not weight.
        There was one time when there were over thirty people in the
        net at once!  It's also said that once you enter the net, you
        never want to leave, so be careful."""
        }, put_in="33")

quickdef(world, "bad tie collection", "thing", {
        Words : ["bad", "tie", "ties", "collection"],
        Scenery : True,
        Description : """This is a collection of many remarkably bad
        ties.  They've been used successfully for a couple of Google
        interviews to land tEps jobs."""
        }, put_in="33")


###
### Third floor of the back stairwell
###

quickdef(world, "back_stairwell_3", "room", {
        Name : "Third Floor of the Back Stairwell",
        Visited : True,
        Description : """You are in the back stairwell.  You can go
        [dir upstairs] to the fourth floor, [dir southwest] to third
        landing, [dir north] to 34, or [dir downstairs] to the second
        floor."""
        })
world[DirectionDescription("back_stairwell_3", "east")] = """Looking
[dir east], you see a [ob <closet door> door] into a closet."""

world.activity.connect_rooms("back_stairwell_3", "down", "back_stairwell_2")
world.activity.connect_rooms("back_stairwell_3", "north", "34")
world.activity.connect_rooms("back_stairwell_3", "up", "back_stairwell_4")

quickdef(world, "34", "room", {
        Visited : True,
        })

###
### Porn closet
###
quickdef(world, "porn_closet_door", "door", {
        Name : "closet door",
        Reported : False,
        Description : """It's a wooden door, around which are dinosaur
        figures possibly depicting various sexual positions.  It is
        currently [get IsOpenMsg porn_closet_door]."""
        })
world.activity.connect_rooms("back_stairwell_3", "east", "porn_closet_door")
world.activity.connect_rooms("porn_closet_door", "east", "The Porn Closet")

quickdef(world, "The Porn Closet", "room", {
        Description : """This is a closet full of study materials for
        introductory classes at MIT.  There is surprisingly little
        porn in this closet."""
        })
world[DirectionDescription("The Porn Closet", "up")] = """There's a
[ob ladder] going up."""
world[DirectionDescription("The Porn Closet", "north")] = """You see a
[ob ladder] here going up."""
world.activity.connect_rooms("The Porn Closet", "up", "porn_closet_ladder")

quickdef(world, "porn_closet_ladder", "door", {
        Name : "wood ladder",
        Reported : False,
        Description : """This is a ladder going from the porn closet
        [dir up] into the reading room."""
        })
world.activity.connect_rooms("porn_closet_ladder", "up", "The Reading Room")

###
### The Reading Room
###
quickdef(world, "The Reading Room", "room", {
        Description : """This is the reading room, a secret room of
        tEp.  You can go back [dir down] [ob <the ladder>] to the porn
        closet."""
        })

####################
### Fourth floor ###
####################

quickdef(world, "The Fourth Landing", "room", {
        Visited : True,
        Description : """[img 4th_landing_small.jpg]This is the fourth
        landing.  You can go [dir southeast] to 41, [dir south] to 42,
        [dir north] to 43, [dir northeast] to the back stairwell, and
        [dir downstairs]."""
        })
world.activity.connect_rooms("The Fourth Landing", "southeast", "41")
world.activity.connect_rooms("The Fourth Landing", "south", "42")
world.activity.connect_rooms("The Fourth Landing", "north", "43")
world.activity.connect_rooms("The Fourth Landing", "northeast", "back_stairwell_4")
world[NoGoMessage("The Fourth Landing", "up")] = """There aren't any
more stairs up from here.  You'll have to first go [dir northeast] to
the back stairwell."""

quickdef(world, "41", "room", {
        Visited : True,
        })
quickdef(world, "42", "room", {
        Visited : True,
        })
quickdef(world, "43", "room", {
        Visited : True,
        })

###
### Third floor of the back stairwell
###

quickdef(world, "back_stairwell_4", "room", {
        Name : "Fourth Floor of the Back Stairwell",
        Visited : True,
        Description : """You are in the back stairwell.  You can go
        [dir upstairs] to the fifth floor, [dir southwest] to fourth
        landing, [dir north] to 44, or [dir downstairs] to the third
        floor."""
        })

world.activity.connect_rooms("back_stairwell_4", "down", "back_stairwell_3")
world.activity.connect_rooms("back_stairwell_4", "north", "44")
world.activity.connect_rooms("back_stairwell_4", "up", "The Fifth Landing")

quickdef(world, "44", "room", {
        Visited : True,
        })

###################
### Fifth floor ###
###################

quickdef(world, "The Fifth Landing", "room", {
        Visited : True,
        Description : """This is the fifth landing.  You can go [dir
        southeast] to 51, [dir south] to the study room, [dir
        northwest] to 53, [dir north] to 54, [dir northeast] to 55,
        and [dir downstairs]."""
        })
world.activity.connect_rooms("The Fifth Landing", "southeast", "51")
world.activity.connect_rooms("The Fifth Landing", "south", "The Study Room")
world.activity.connect_rooms("The Fifth Landing", "northwest", "53")
world.activity.connect_rooms("The Fifth Landing", "north", "54")
world.activity.connect_rooms("The Fifth Landing", "northeast", "55")

quickdef(world, "51", "room", {
        Visited : True,
        })
quickdef(world, "53", "room", {
        Visited : True,
        })
quickdef(world, "54", "room", {
        Visited : True,
        })
quickdef(world, "55", "room", {
        Visited : True,
        })

quickdef(world, "The Study Room", "room", {
        Visited : True,
        Description : """This is the study room.  You can go [dir
        north] to the rest of the fifth floor, or [dir south] to the
        poop deck."""
        })
world.activity.connect_rooms("The Study Room", "south", "The Poop Deck")

quickdef(world, "The Poop Deck", "room", {
        Visited : True,
        Description : """This is the roof deck immediately outside the
        study room.  From here you can see a nice view of the mall
        (which is the grassy area along Commonwealth Ave).  You can
        go [dir south] back into the study room, or [dir up] to the
        roof."""
        })
world.activity.connect_rooms("The Poop Deck", "up", "The Roof")


################
### The roof ###
################

quickdef(world, "The Roof", "room", {
        Visited : True,
        Description : """This is the roof of tEp.  To the north is a
        view of the MIT campus, and to the south is the Boston
        skyline.  You can go back [dir down] to the poopdeck."""
        })


###################################
### Consulting Irving Q. Tep... ###
###################################

# We define a new kind to the game called "lore" which represents
# stories which Irving Q. Tep can talk about.  Lore acts just like
# things in that they have a Name, their Words, and a Description.  We
# also modify the parser to have a somelore subparser.  To know what
# is and what is not a word in the game, we must add an object class
# "somelore" so that init_current_objects pulls in anything which has
# kind "lore."  The definition of the subparser is the basic
# definition used by something and somewhere (at the end of
# parser.py).

world.add_relation(KindOf("lore", "kind"))

parser.define_subparser("somelore", "A parser to match against lore in the game.")
parser.add_object_class("somelore", "lore")

@parser.add_subparser("somelore")
def default_somelore(parser, var, input, i, ctxt, actor, next) :
    """Tries to parse as if the following input were a room."""
    return list_append([parser.parse_thing.notify([parser, "somelore", var, name, words,input,i,ctxt,next],{})
                        for name,words in zip(parser.current_objects["somelore"], parser.current_words["somelore"])])

# Finally, we modify the parser to add some synonyms for asking Irving about things.

parser.understand("consult [object Irving Q. Tep] about [text y]", AskingAbout(actor, "Irving Q. Tep", Y))
parser.understand("ask about [text y]", AskingAbout(actor, "Irving Q. Tep", Y))

@report(AskingAbout(actor, "Irving Q. Tep", Y))
def asking_irving(actor, y, ctxt) :
    """Irving Q. Tep knows about various abstract ideas ("lore") and
    can talk about them.  But, if he doesn't know about a topic, it's
    assumed that the player is asking about an object in the room, and
    we turn it into an Examining action.  Otherwise, if there's no
    relevant object, Irving 'has nothing to say about that.'"""
    # current words have already been init'd since we're parsing
    res = ctxt.parser.run_parser("somelore",
                                 ctxt.parser.transform_text_to_words(y),
                                 ctxt)
    if len(res) == 1 :
        desc = ctxt.world[Description(res[0][0].value)]
        if desc :
            ctxt.write(desc)
        else : # just in case, for debugging
            ctxt.write("""Irving Q. Tep has nothing to say about that.""")
    elif len(res) > 1 :
        raise Ambiguous(AskingAbout(actor, "Irving Q. Tep", X), {X : [r[0].value for r in res]}, {X : "somelore"})
    else :
        res = ctxt.parser.run_parser("something",
                                     ctxt.parser.transform_text_to_words(y),
                                     ctxt)
        if not res :
            ctxt.write("""Irving Q. Tep has nothing to say about that.""")
        elif len(res) == 1 :
            ctxt.actionsystem.run_action(Examining(actor, res[0][0].value), ctxt)
        else :
            raise Ambiguous(Examining(actor, X), {X : [r[0].value for r in res]}, {X : "something"})
    raise ActionHandled()


###
### Lore
###

# These are basically short entries for a wiki-like system of things
# about the house that you couldn't learn about by just looking at
# objects.
#
# Links are created by [ask x] for a link to x, ore [ask x text] for a
# link to x with prettier link text.
#
# The naming scheme is to have the id be "lore: unique name" (it
# doesn't really matter), and then put the actual name in the name
# field.  This way if there actually a sawzall lying around (which
# there shouldn't), the description of the sawzall lore won't eit it.

quickdef(world, "lore: stupidball", "lore", {
        Name : "stupidball",
        Description : """Stupidball is a fine game in which
        contestants take a large exercise ball and throw it around the
        center room at a high energy.  This game has [ask eit eited]
        many things, such as the chandelier in the center room."""
        })

quickdef(world, "lore: eit", "lore", {
        Name : "eit",
        Words : ["@eit", "@eited"],
        Description : """'Eit,' in short, means never having to say
        you're sorry.  For instance, let's say you're holding a cup of
        water.  I can then come up to you and knock the cup out of
        your hand whilst saying "eit!" (of course, I should help clean
        up).  The word can also be used when someone recognizes
        something eitful.  For instance, if you told me you didn't do
        well on an exam, I could say "eit, man."  However, what's not
        acceptible is to say 'eit' to the following: "My family just
        got eaten by a pack of wolves."  Remember, this is not an eit!

        [newline]There is a mural in 22 commemorating the sacrament of
        eit."""
        })

quickdef(world, "lore: rules of tep", "lore", {
        Name : "rules of tEp",
        Words : ["rules", "of", "tep", "@rules"],
        Description : """The rules of tEp are threefold:[break]
        0. Don't die;[break]
        1. Hobart is not a dishwasher;[break]
        2. Don't date Pikan women;[break]
        3. All explosions must be videotaped;[break]
        Amendment 1. No [ask Sawzalls] without the express permission of
        the [ask <house mangler>]; and[break]
        Amendment 2. The house mangler is not allowed to permit the use of Sawzalls."""
        })

quickdef(world, "lore: sawzall", "lore", {
        Name : "sawzall",
        Words : ["@sawzall", "@sawzalls"],
        Description : """A Sawzall is a hand-held reciprocating saw
        which can basically cut through anything.  Their prohibition
        was made into one of the [ask <rules of tep>] after one
        brother repeatedly cut down the wall between 51 and 52 during
        the summer months to make a mega room, where it was the duty
        of the [ask <house mangler>] to mend the wall at the end of
        each summer for [ask <work week>]."""
        })

quickdef(world, "lore: work week", "lore", {
        Name : "work week",
        Description : """Work week occurs once at the end of the
        summer and once during winter break, and it's a time where
        tEps try to repair the house."""
        })

quickdef(world, "lore: house mangler", "lore", {
        Name : "house mangler",
        Words : ["house", "@mangler", "@manager"],
        Description : """The house mangler has one of the most important
        jobs in the house: to make sure the house doesn't fall down.
        The house mangler accomplishes this by attempting to get tEps
        to do their work assignments and to schedule [ask <work
        week>]."""
        })

quickdef(world, "lore: 22", "lore", {
        Name : "22",
        Words : ["@22", "@twenty-two", "twenty", "@two"],
        Description : """The number 22 is a number of cosmic
        significance.  If you look around you, you will invariably see
        it everywhere."""
        })
