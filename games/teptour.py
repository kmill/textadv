# teptour.py
#
# The tEp virtual house tour!
# (c) 2011 tEp, Xi chapter
#
# Authors: Kyle Miller

execfile("textadv/basicsetup.py")

world[Global("release_number")] = "0.0 (July 18, 2011)"

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
    filename = obs[0]
    css_class = "desc_img"
    if len(obs)>1 and obs[1] == "left" :
        css_class = "desc_img_left"
    return ["<img class=\""+css_class+"\" src=\"teptour/"+filename+"\">"]

###
### Irving Q. Tep
###

world.activity.put_in("player", "253 Commonwealth Ave.")

parser.understand("upstairs", "up", dest="direction")
parser.understand("downstairs", "down", dest="direction")

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
    return [make_action_link(text, "ask Irving Q. Tep about "+topic)]

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
### In front of tep (253 Commonwealth Ave.)
###

quickdef(world, "253 Commonwealth Ave.", "room", {
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
         put_in="253 Commonwealth Ave.")

quickdef(world, "park bench", "supporter", {
        Scenery : True,
        IsEnterable : True,
        Description : """[img front_bench.jpg left]It's a handmade
        park bench wrought from steel, built by a previous tEp.  After
        a few years of use, it's been bent quite out of whack."""
        },
         put_in="253 Commonwealth Ave.")
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
world.activity.connect_rooms("253 Commonwealth Ave.", "north", "front door")
world.activity.connect_rooms("front door", "northwest", "The Foyer")

quickdef(world, "doorbell", "thing", {
        Words : ["@doorbell", "door", "@bell"],
        Scenery : True,
        Description : """It's a small, black button, and you almost
        didn't notice it.  It turns out the FedEx guy enjoys this
        doorbell."""
        },
         put_in="253 Commonwealth Ave.")
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

@before(Going(actor, "north") <= PEquals("253 Commonwealth Ave.", Location(actor)))
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
        upstairs] to the second floor, [dir downstairs] to the
        basement, or [dir southeast] back to the foyer."""
        })
world[DirectionDescription("The Center Room", "up")] = "Looking up, you see the [ob <center stairwell>]."
world.activity.connect_rooms("The Center Room", "up", "The Second Landing")
world.activity.connect_rooms("The Center Room", "down", "Basement")
world.activity.connect_rooms("The Center Room", "south", "Front Room")
world.activity.connect_rooms("The Center Room", "north", "Dining Room")

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

quickdef(world, "center stairwell", "thing", {
        Scenery : True,
        Description : """[img center_stairwell_small.jpg left]The
        center stairwell is a three flights of stairs, capped with a
        skylight. The color-changing lights illuminate it
        dramatically."""
        },
         put_in="The Center Room")

###
### Front room
###

quickdef(world, "Front Room", "room", {
        Visited : True,
        Description : """[img front_room_small.jpg left]This is where
        the tEps play Super Smash Bros. after dinner every night.  You
        can go [dir north] to the center room."""
        })

###
### Dining room
###

quickdef(world, "Dining Room", "room")

####################
### Second landing ###
####################

quickdef(world, "The Second Landing", "room", {
        Visited : True,
        Description : """[img 2nd_landing_small.jpg left]This is the
        second landing.  You can go [dir southeast] to 21, [dir south]
        to 22, [dir north] to 23, [dir northeast] to 24, [dir
        upstairs], and [dir downstairs]."""
        })
world.activity.connect_rooms("The Second Landing", "southeast", "21")
world.activity.connect_rooms("The Second Landing", "south", "22")
world.activity.connect_rooms("The Second Landing", "north", "23")
world.activity.connect_rooms("The Second Landing", "northeast", "24")
world.activity.connect_rooms("The Second Landing", "up", "The Third Landing")

quickdef(world, "21", "room")

quickdef(world, "22", "room", {
        Visited : True,
        Description : """This is 22.  You can see some [ob
        <color-changing lights>].  You can go [dir north] back to the
        second landing."""
        })

quickdef(world, "22_lights", "thing", {
        Name : "color-changing lights",
        Scenery: True,
        Description : """[img 22_lights_small.jpg left]These are
        ethernet-controlled lights which can cycle through colors or
        follow music for a lightshow."""
        },
         put_in="22")

quickdef(world, "23", "room")
quickdef(world, "24", "room")

###################
### Third floor ###
###################

quickdef(world, "The Third Landing", "room", {
        Visited : True,
        Description : """[img 3rd_landing_small.jpg left]This is the
        third landing.  You can go [dir southeast] to 31, [dir south]
        to 32, [dir north] to 33, [dir northeast] to 34, [dir
        upstairs], and [dir downstairs]."""
        })
world.activity.connect_rooms("The Third Landing", "southeast", "31")
world.activity.connect_rooms("The Third Landing", "south", "32")
world.activity.connect_rooms("The Third Landing", "north", "33")
world.activity.connect_rooms("The Third Landing", "northeast", "34")
world.activity.connect_rooms("The Third Landing", "up", "The Fourth Landing")

quickdef(world, "31", "room")
quickdef(world, "32", "room")
quickdef(world, "33", "room")
quickdef(world, "34", "room")

####################
### Fourth floor ###
####################

quickdef(world, "The Fourth Landing", "room", {
        Visited : True,
        Description : """[img 4th_landing_small.jpg]This is the
        fourth landing.  You can go [dir southeast] to 41, [dir south]
        to 42, [dir north] to 43, [dir northeast] to 44, [dir
        upstairs], and [dir downstairs]."""
        })
world.activity.connect_rooms("The Fourth Landing", "southeast", "41")
world.activity.connect_rooms("The Fourth Landing", "south", "42")
world.activity.connect_rooms("The Fourth Landing", "north", "43")
world.activity.connect_rooms("The Fourth Landing", "northeast", "44")
world.activity.connect_rooms("The Fourth Landing", "up", "The Fifth Floor")

quickdef(world, "41", "room")
quickdef(world, "42", "room")
quickdef(world, "43", "room")
quickdef(world, "44", "room")

###################
### Fifth floor ###
###################

quickdef(world, "The Fifth Floor", "room", {
        Visited : True,
        Description : """This is the fifth floor.  You can go [dir
        southeast] to 51, [dir south] to the study room, [dir
        northwest] to 53, [dir north] to 54, [dir northeast] to 55,
        and [dir downstairs]."""
        })
world.activity.connect_rooms("The Fifth Floor", "southeast", "51")
world.activity.connect_rooms("The Fifth Floor", "south", "The Study Room")
world.activity.connect_rooms("The Fifth Floor", "northwest", "53")
world.activity.connect_rooms("The Fifth Floor", "north", "54")
world.activity.connect_rooms("The Fifth Floor", "northeast", "55")

quickdef(world, "51", "room")
quickdef(world, "53", "room")
quickdef(world, "54", "room")
quickdef(world, "55", "room")

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
        (which is the grassy area along Commonwealth Ave.).  You can
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

parser.understand("consult [object Irving Q. Tep] about [text y]", AskingAbout(actor, "Irving Q. Tep", Y))
parser.understand("ask about [text y]", AskingAbout(actor, "Irving Q. Tep", Y))

@report(AskingAbout(actor, "Irving Q. Tep", Y))
def asking_irving(actor, y, ctxt) :
    """Irving Q. Tep knows about various abstract ideas and can talk
    about them.  But, if he doesn't know about a topic, it's assumed
    that the player is asking about an object in the room, and we turn
    it into an Examining action.  Otherwise, if there's no relevant
    object, Irving 'has nothing to say about that.'"""
    text = y.strip().lower()
    if text in ["stupidball"] :
        ctxt.write("""Stupidball is a fine game in which contestants
        take a large exercise ball and throw it around the center room
        at a high energy.  This game has [ask eit eited] many things,
        such as the chandelier in the center room.""")
    elif text in ["eit", "eited"] :
        ctxt.write("""'Eit,' in short, means never having to say
        you're sorry.  For instance, let's say you're holding a cup of
        water.  I can then come up to you and knock the cup out of
        your hand whilst saying "eit!" (of course, I should help clean
        up).  The word can also be used when someone recognizes
        something eitful.  For instance, if you told me you didn't do
        well on an exam, I could say "eit, man."  However, what's not
        acceptible is to say 'eit' to the following: "My family just
        got eaten by a pack of wolves."  Remember, this is not an eit!

        [newline]There is a mural in 22 commemorating the sacrement of
        eit.""")
    elif text in ["rules", "rules of tep", "the rules", "the rules of tep"] :
        ctxt.write("""The rules of tEp are threefold:[break]
                   0. Don't die;[break]
                   1. Hobart is not a dishwasher;[break]
                   2. Don't date Pikan women;[break]
                   3. All explosions must be videotaped;[break]
                   Amendment 1. No [ask Sawzalls] without the express permission of
                   the [ask <house mangler>]; and[break]
                   Amendment 2. The house mangler is not allowed to permit the use of Sawzalls.""")
    elif text in ["sawzall", "sawzalls"] :
        ctxt.write("""A Sawzall is a hand-held reciprocating saw which
        can basically cut through anything.  Their prohibition was
        made into one of the [ask <rules of tep>] after one brother
        repeatedly cut down the wall between 51 and 52 during the
        summer months to make a mega room, where it was the duty of
        the [ask <house mangler>] to mend the wall at the end of each
        summer for [ask <work week>].""")
    elif text in ["work week"] :
        ctxt.write("""Work week occurs once at the end of the summer
        and once during winter break, and it's a time where tEps try
        to repair the house.""")
    elif text in ["house mangler", "house manager"] :
        ctxt.write("""The house mangler has one of the most important
        jobs in the house: to make sure the house doesn't fall down.
        The house mangler accomplishes this by attempting to get tEps
        to do their work assignments and to schedule [ask <work
        week>].""")
    else :
        # current words have already been init'd
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
