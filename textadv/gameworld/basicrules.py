### Not to be imported
## Should be execfile'd

# basicrules.py
#
# These are user and world rules which can be executed.



###
### Directions
###

# Defines a subparser named "direction" which is loaded with basic
# directions and their one- or two-letter synonyms.

parser.define_subparser("direction", "Represents one of the directions one may go.")

def define_direction(direction, synonyms) :
    for synonym in synonyms :
        understand(synonym, direction, dest="direction")

define_direction("north", ["north", "n"])
define_direction("south", ["south", "s"])
define_direction("east", ["east", "e"])
define_direction("west", ["west", "w"])
define_direction("northwest", ["northwest", "nw"])
define_direction("southwest", ["southwest", "sw"])
define_direction("northeast", ["northeast", "ne"])
define_direction("southeast", ["southeast", "se"])
define_direction("up", ["up", "u"])
define_direction("down", ["down", "d"])

###*
###* Property definitions
###*

###
### Defining: kind
###

##
# Property: Name
##

@world.define_property
class Name(Property) :
    """Represents the name of a kind.  Then, the id of a thing may be
    differentiated from what the user will call it (for shorthand)."""
    numargs = 1

@world.handler(Name(X) <= IsA(X, "kind"))
def default_Name(x, world) :
    """The default name of a thing is its id, X."""
    return str(x)

##
# Property: Description
##

@world.define_property
class Description(Property) :
    """Represents a textual description of a kind.  There is no
    default value of this for kinds."""
    numargs = 1

##
# Property: Words
##

@world.define_property
class Words(Property) :
    """This is a list of words which can describe the kind.  Words may
    be prefixed with @ to denote that they are nouns (and matching a
    noun gives higher priority to the disambiguator)."""
    numargs = 1

@world.handler(Words(X))
def default_Words(x, world) :
    """The default handler assumes that the words in Name(x) are
    suitable for the object, and furthermore that the last word is a
    noun (so "big red ball" returns ["big", "red", "@ball"])."""
    words = world[Name(x)].split()
    words[-1] = "@"+words[-1]
    return words

###
### Defining: room
###

world[Description(X) <= IsA(X, "room")] = None

#
# connecting rooms together
#

@world.define_relation
class Adjacent(DirectedManyToManyRelation) :
    """Used for searching for paths between rooms."""

@world.define_relation
class Exit(FreeformRelation) :
    """Used to denote an exit from one room to the next.  Exit(room1,
    dir, room2)."""

@world.to("connect_rooms")
def default_connect_rooms(room1, dir, room2, world, reverse=True) :
    """Called with connect_rooms(room1, dir, room2).  Gives room1 an
    exit to room2 in direction dir.  By default, also adds in reverse
    direction, unless the optional argument "reverse" is false."""
    world.add_relation(Adjacent(room1, room2))
    world.add_relation(Exit(room1, dir, room2))
    if reverse :
        world.add_relation(Adjacent(room2, room1))
        world.add_relation(Exit(room2, inverse_direction(dir), room1))

##
# Property: Visited
##

@world.define_property
class Visited(Property) :
    """Represents whether a room has been visited."""
    numargs = 1

world[Visited(X) <= IsA(X, "room")] = False

##
# Property: Contents
##

@world.define_property
class Contents(Property) :
    """Gets a list of things which are the contents of the object.
    Only goes one level deep."""
    numargs = 1

@world.handler(Contents(X) <= IsA(X, "room"))
def contents_room(x, world) :
    """Gets the immediate contents of a room."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

##
# Property: EffectiveContainer
##

@world.define_property
class EffectiveContainer(Property) :
    """Gets the object which effectively contain an object which is
    "inside" this one (change to "on top of" for supporters).
    Specifically, if the object is a closed box, then the box is the
    effective container.  Otherwise, if the box is open, the result is
    the effective container for the location of the box."""
    numargs = 1

@world.handler(EffectiveContainer(X) <= IsA(X, "room"))
def rule_EffectiveContainer_if_x_in_room(x, world) :
    """The effective container for a room is the room itself."""
    return x

##
# Property: ProvidesLight
##
@world.define_property
class ProvidesLight(Property) :
    """Represents whether the object is a source of light, and not
    because of its contents."""
    numargs = 1

# rooms provide light by default
world[ProvidesLight(X) <= IsA(X, "room")] = True

##
# Property: IsLit
##
@world.define_property
class IsLit(Property) :
    """Represents whether the object is lit from the inside, and not
    whether some outside source is lighting it (for this, we must
    instead look at the EffectiveContainer of the object)."""
    numargs = 1

@world.handler(IsLit(X) <= IsA(X, "room"))
def rul_IsLit_room_default_is_ProvidesLight(x, world) :
    """A room, by default, is lit if it provides light itself."""
    return world[ProvidesLight(x)]

@world.handler(IsLit(X) <= IsA(X, "room"))
def rule_IsLit_contents_can_light_room(x, world) :
    """A room is lit if any of its contents are lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

###
### Defining: thing
###

world[Description(X) <= IsA(X, "thing")] = None

# Most things don't provide light
world[ProvidesLight(X) <= IsA(X, "thing")] = False

@world.handler(IsLit(X) <= IsA(X, "thing"))
def rul_IsLit_thing_default_is_ProvidesLight(x, world) :
    """By default, a thing is lit if it provides light."""
    return world[ProvidesLight(x)]

@world.handler(IsLit(X) <= IsA(X, "thing"))
def rule_IsLit_if_parts_lit(x, world) :
    """A thing provides light if any of its constituent parts are lit up."""
    parts = world.query_relation(PartOf(Y, x), var=Y)
    if any(world[IsLit(o)] for o in parts) :
        return True
    else : raise NotHandled()


##
# Property: NotableDescription
##

@world.define_property
class NotableDescription(Property) :
    """Represents a special textual description of an object if it is
    notable enough to be put in a special paragraph in a location
    description.  If it is set to False, then it is taken to mean
    there is no such paragraph."""
    numargs = 1

world[NotableDescription(X)] = False


##
# Property: Report
##

@world.define_property
class Reported(Property) :
    """Represents whether the object should be automatically reported
    in room descriptions."""
    numargs = 1

world[Reported(X) <= IsA(X, "thing")] = True

##
# Properties: InhibitArticle, PrintedName, DefiniteName, IndefiniteName
##

@world.define_property
class InhibitArticle(Property) :
    """Tells the default DefiniteName and Indefinite name properties
    whether to put the article in front.  For instance, we don't want
    to be talking about the Bob."""
    numargs = 1

world[InhibitArticle(X) <= IsA(X, "thing")] = False

@world.define_property
class PrintedName(Property) :
    """Gives a textual representation of an object which can then be
    prefaced by an article (that is, unless InhibitArticle is true).
    This is separate from Name because it might be dynamic in some
    way.  (Note: it might be that this property isn't necessary)."""
    numargs = 1

@world.handler(PrintedName(X) <= IsA(X, "thing"))
def default_PrintedName(x, world) :
    """By default, PrintedName(X) is Name(X)."""
    return world[Name(x)]

@world.define_property
class DefiniteName(Property) :
    """Gives the definite name of an object.  For instance, "the ball"
    or "Bob"."""
    numargs = 1

@world.handler(DefiniteName(X) <= IsA(X, "thing"))
def default_DefiniteName(x, world) :
    """By default, DefiniteName is just the PrintedName with "the"
    stuck in front, unless InhibitArticle is true."""
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    else :
        return "the "+printed_name

@world.define_property
class IndefiniteName(Property) :
    """Gives the indefinite name of an object.  For instance, "a ball"
    or "Bob"."""
    numargs = 1

@world.handler(IndefiniteName(X) <= IsA(X, "thing"))
def default_IndefiniteName(x, world) :
    """By default, IndefiniteName is the PrintedName with "a" or "an"
    (depending on whether the PrintedName starts with a vowel) stuck
    to the front, unless InhibitArticle is true."""
    printed_name = world[PrintedName(x)]
    if world[InhibitArticle(x)] :
        return printed_name
    elif printed_name[0] in "aeoiu" :
        return "an "+printed_name
    else :
        return "a "+printed_name

##
# Properties: SubjectPronoun, ObjectPronoun, PossessivePronoun
##

@world.define_property
class SubjectPronoun(Property) :
    """Represents the pronoun for when the object is the subject of a
    sentence."""
    numargs = 1

@world.define_property
class ObjectPronoun(Property) :
    """Represents the pronoun for when the object is the object of a
    sentence."""
    numargs = 1

@world.define_property
class PossessivePronoun(Property) :
    """Represents the possesive pronoun of the object."""
    numargs = 1

world[SubjectPronoun(X) <= IsA(X, "thing")] = "it"
world[ObjectPronoun(X) <= IsA(X, "thing")] = "it"
world[PossessivePronoun(X) <= IsA(X, "thing")] = "its"


##
# FixedInPlace
##

@world.define_property
class FixedInPlace(Property) :
    """Represents something which can't be taken because it's fixed in
    place.  For instance, scenery."""
    numargs = 1

# by default, things are not fixed in place
world[FixedInPlace(X) <= IsA(X, "thing")] = False


##
# AccessibleTo
##

@world.define_property
class AccessibleTo(Property) :
    """AccessibleTo(X, actor) checks whether X is accessible to the
    actor."""
    numargs = 2

# by default, things aren't accessible
world[AccessibleTo(X, actor)] = False
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_held(x, actor, world) :
    """Anything the actor has is accessible."""
    if world.query_relation(Has(actor, x)) :
        return True
    else :
        raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_in_same_effective_container(x, actor, world) :
    """Anything in the same effective container to the actor is
    accessible if the effective container is lit."""
    actor_eff_cont = world[EffectiveContainer(world[Location(actor)])]
    if actor_eff_cont == x :
        # otherwise we'd be looking too many levels high
        x_eff_cont = x
    else :
        x_eff_cont = world[EffectiveContainer(world[Location(x)])]
    if actor_eff_cont == x_eff_cont and world[IsLit(actor_eff_cont)] :
        return True
    raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_immediately_in_container(x, actor, world) :
    """If the actor is immediately in the container x, then x is
    accessible.  Prevents such things as closing a box around oneself
    and then not being able to refer to the box anymore."""
    if world[IsA(x, "container")] and world.query_relation(Contains(x, actor)) :
        return True
    else : raise NotHandled()
@world.handler(AccessibleTo(X, actor))
def rule_AccessibleTo_if_part_of(x, actor, world) :
    """If an object is part of something, and that something is
    accessible, then the object is accessible."""
    x_assembly = world.query_relation(PartOf(x, Y), var=Y)
    if x_assembly and world[AccessibleTo(x_assembly[0], actor)] :
        return True
    raise NotHandled()

##
# Property: IsOpaque
##

@world.define_property
class IsOpaque(Property) :
    """Represents whether the object cannot transmit light."""
    numargs = 1

# And, let's just say that things are usually opaque.
world[IsOpaque(X) <= IsA(X, "thing")] = True


##
# Property: Enterable
##
@world.define_property
class Enterable(Property) :
    """Is true if the object is something someone could enter."""
    numargs = 1

# By default it's false
world[Enterable(X) <= IsA(X, "thing")] = False

###
### Defining: door
###



###
### Defining: container
###

@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    """Gets the immediate contents of the container."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]

##
# Properties: Openable, IsOpen
##

@world.define_property
class Openable(Property) :
    """Represents whether an object is able to be opened and closed."""
    numargs = 1

world[Openable(X) <= IsA(X, "thing")] = False # by default, things aren't openable

@world.define_property
class IsOpen(Property) :
    """Represents whether an openable object is open."""
    numargs = 1

world[IsOpen(X) <= Openable(X)] = False # by default, openable things are closed

#
# Lighting for container
#

world[IsOpaque(X) <= IsA(X, "container")] = False


@world.handler(IsOpaque(X) <= IsA(X, "container"))
def rule_IsOpaque_if_openable_container_is_closed(x, world) :
    """A container is by default not opaque, but if it is openable,
    then it is not opaque if it is open."""
    if world[Openable(x)] and not world[IsOpen(x)]:
        return True
    else :
        raise NotHandled()

@world.handler(IsLit(X) <= IsA(X, "container"))
def rule_IsLit_for_container(x, world) :
    """A container is lit if it is not opaque and one of its contents
    is lit."""
    if not world[IsOpaque(x)] and any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(EffectiveContainer(X) <= IsA(X, "container"))
def rule_EffectiveContainer_if_x_in_container(x, world) :
    """The effective container for a container is the container itself
    if it is opaque, otherwise it is the effective container of the
    location of the container."""
    if world[IsOpaque(x)] :
        return x
    else :
        return world[EffectiveContainer(world[Location(x)])]

###
### Defining: supporter
###

@world.handler(Contents(X) <= IsA(X, "supporter"))
def supporter_contents(x, world) :
    """Gets the things the supporter immediately supports."""
    return [o["y"] for o in world.query_relation(Supports(x, Y))]


#
# Lighting for supporter
#

# A supporter doesn't block light.
world[IsOpaque(X) <= IsA(X, "supporter")] = False

@world.handler(IsLit(X) <= IsA(X, "supporter"))
def rule_IsLit_for_supporter(x, world) :
    """A supporter is lit if it is not opaque and one of its objects
    is lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(EffectiveContainer(X) <= IsA(X, "supporter"))
def rule_EffectiveContainer_if_supporter(x, world) :
    """The effective container of a supporter is the effective
    container of the location of the supporter."""
    return world[EffectiveContainer(world[Location(x)])]

###
### Defining: person
###

@world.handler(Contents(X) <= IsA(X, "person"))
def supporter_contents(x, world) :
    """Gets the things the person immediately has."""
    return [o["y"] for o in world.query_relation(Has(x, Y))]

@world.handler(EffectiveContainer(X) <= IsA(X, "person"))
def rule_EffectiveContainer_if_person(x, world) :
    """We assume that people aren't able to conceal their possessions
    very well, and the effective container is thus the location of the
    person."""
    return world[EffectiveContainer(world[Location(x)])]

##
# Property: Gender
##

@world.define_property
class Gender(Property) :
    """Represents the gender of a person.  Examples of options are
    "male", "female", and "unknown"."""
    numargs = 1

world[Gender(X) <= IsA(X, "person")] = "unknown" # other options are male and female

##
# Property: Pronouns
##

@world.handler(SubjectPronoun(X) <= IsA(X, "person"))
def person_SubjectPronoun(x, world) :
    """Gives a default subject pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "he"
    elif gender == "female" :
        return "she"
    else :
        return "they"
@world.handler(ObjectPronoun(X) <= IsA(X, "person"))
def person_ObjectPronoun(x, world) :
    """Gives a default object pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "them"
@world.handler(PossessivePronoun(X) <= IsA(X, "person"))
def person_PossessivePronoun(x, world) :
    """Gives a default possessive pronoun based on Gender."""
    gender = world[Gender(x)]
    if gender == "male" :
        return "him"
    elif gender == "female" :
        return "her"
    else :
        return "their"

##
# Properties: SubjectPronounIfMe, ObjectPronounIfMe, PossessivePronounIfMe
##

@world.define_property
class SubjectPronounIfMe(Property) :
    """Represents the subject pronoun, but when referring to the
    current actor."""
    numargs = 1
@world.define_property
class ObjectPronounIfMe(Property) :
    """Represents the object pronoun, but when referring to the
    current actor."""
    numargs = 1
@world.define_property
class PossessivePronounIfMe(Property) :
    """Represents the possessive pronoun, but when referring to the
    current actor."""
    numargs = 1

world[SubjectPronounIfMe(X) <= IsA(X, "person")] = "you"
world[ObjectPronounIfMe(X) <= IsA(X, "person")] = "you"
world[PossessivePronounIfMe(X) <= IsA(X, "person")] = "your"

#
# Light for a person
#

@world.handler(IsLit(X) <= IsA(X, "person"))
def rule_IsLit_possessions_can_light_person(x, world) : # maybe should handle concealment at some point?
    """A person is lit if any of their posessions are lit."""
    if any(world[IsLit(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

##
# The default player
##

def_obj("player", "person")
world[PrintedName("player")] = "[if [current_actor_is player]]yourself[else]the player[endif]"
world[InhibitArticle("player")] = True
world[Words("player")] = ["yourself", "self", "AFGNCAAP"]
world[Description("player")] = """{Bob|cap} {is} an ageless, faceless,
gender-neutral, culturally-ambiguous adventure-person.  {Bob|cap}
{does} stuff sometimes."""
world[Reported("player")] = False


###
### Other properties
###



###
### Other properties
###

##
## Scenery
##

@world.define_property
class Scenery(Property) :
    """Scenery refers to things which are fixed in place and not
    referred to in room descriptions."""
    numargs = 1

# things aren't in general scenery
world[Scenery(X) <= IsA(X, "thing")] = False

# scenery is fixed in place
world[FixedInPlace(X) <= Scenery(X)] = True
# scenery is not reported
world[Reported(X) <= Scenery(X)] = False


###*
###* Activities
###*

###
### Activity: location descriptions
###

@actoractivities.to("describe_current_location")
def describe_current_location_default(ctxt) :
    """Calls describe_location using the Location and the
    EffectiveContainer of the current actor."""
    loc = ctxt.world[Location(ctxt.actor)]
    eff_cont = ctxt.world[EffectiveContainer(loc)]
    ctxt.activity.describe_location(ctxt.actor, loc, eff_cont)

__DESCRIBE_LOCATION_notables = []
__DESCRIBE_LOCATION_mentioned = []

@actoractivities.to("describe_location")
def describe_location_init(actor, loc, eff_cont, ctxt) :
    """Initializes the global variables __DESCRIBE_LOCATION_notables
    and __DESCRIBE_LOCATION_mentioned."""
    global __DESCRIBE_LOCATION_notables, __DESCRIBE_LOCATION_mentioned
    __DESCRIBE_LOCATION_notables = []
    __DESCRIBE_LOCATION_mentioned = []

@actoractivities.to("describe_location")
def describe_location_Heading(actor, loc, eff_cont, ctxt) :
    """Constructs the heading using describe_location_heading.  If the
    room is in darkness, then, writes "Darkness"."""
    if ctxt.world[IsLit(eff_cont)] :
        ctxt.activity.describe_location_heading(actor, loc, eff_cont)
    else :
        ctxt.write("Darkness")
    ctxt.write("[newline]")

@actoractivities.to("describe_location")
def describe_location_Description(actor, loc, eff_cont, ctxt) :
    """Prints the description property of the effective container if
    it is a room, unless the room is in darkness.  Darkness stops
    further description of the location."""
    if ctxt.world[IsLit(eff_cont)] :
        
        if ctxt.world[IsA(eff_cont, "room")] :
            d = ctxt.world[Description(eff_cont)]
            if d : ctxt.write(d)
    else :
        ctxt.write("You can't see a thing; it's incredibly dark.")
        raise ActionHandled()

@actoractivities.to("describe_location")
def describe_location_Objects(actor, loc, eff_cont, ctxt) :
    """Prints descriptions of the notable objects in the contents of
    the effective container."""
    obs = ctxt.world[Contents(eff_cont)]
    raw_notables = list_append(ctxt.activity.get_notable_objects(actor, o) for o in obs)
    to_ignore = [o for o,n in raw_notables if n==0]
    filtered_notables = [(o,n) for o,n in raw_notables if o not in to_ignore]
    filtered_notables.sort(key=lambda x : x[1], reverse=True)
    notables = [o for o,n in filtered_notables]
    mentioned = []

    unnotable_messages = []
    current_location = None
    is_first_sentence = True
    current_start = None
    current_descs = None
    for o in notables :
        if o not in mentioned :
            msg = ctxt.activity.terse_obj_description(actor, o, notables, mentioned)
            mentioned.append(o)
            if not msg : # the object printed its own description
                pass
            else :
                o_loc = ctxt.world[Location(o)]
                if o_loc != current_location :
                    if current_descs :
                        unnotable_messages.append((current_start, current_descs))
                    current_location = o_loc
                    if o_loc == eff_cont :
                        if is_first_sentence :
                            current_start = "You see "
                            is_first_sentence = False
                        else :
                            current_start = "You also see "
                    elif ctxt.world[IsA(o_loc, "container")] :
                        mentioned.append(o_loc)
                        if is_first_sentence :
                            current_start = "In "+ctxt.world[DefiniteName(o_loc)]+" you see "
                            is_first_sentence = False
                        else :
                            current_start = "In "+ctxt.world[DefiniteName(o_loc)]+" you also see "
                    elif ctxt.world[IsA(o_loc, "supporter")] :
                        mentioned.append(o_loc)
                        if is_first_sentence :
                            current_start = "On "+ctxt.world[DefiniteName(o_loc)]+" you see "
                            is_first_sentence = False
                        else :
                            current_start = "On "+ctxt.world[DefiniteName(o_loc)]+" you also see "
                    else :
                        raise Exception("Unknown kind of location for "+o_loc)
                    current_descs = []
                current_descs.append(msg)
    if current_descs :
        unnotable_messages.append((current_start, current_descs))

    if unnotable_messages :
        ctxt.write("[newline]"+"[newline]".join(start+serial_comma(msgs)+"." for start,msgs in unnotable_messages))

@actoractivities.to("describe_location")
def describe_location_set_visited(actor, loc, eff_cont, ctxt) :
    """If the effective container is a room, then we set it to being
    visited."""
    if ctxt.world[IsA(eff_cont, "room")] :
        ctxt.world[Visited(eff_cont)] = True


@actoractivities.to("describe_location_heading")
def describe_location_heading_Name(actor, loc, eff_cont, ctxt) :
    """Prints the name of the effective container."""
    ctxt.write(ctxt.world[Name(eff_cont)])

@actoractivities.to("describe_location_heading")
def describe_location_property_heading_location(actor, loc, eff_cont, ctxt) :
    """Creates a description of where the location is with respect to
    the effective container."""
    while loc != eff_cont :
        if ctxt.world[IsA(loc, "container")] :
            ctxt.write("(in",world[DefiniteName(loc)]+")")
            __DESCRIBE_LOCATION_mentioned.append(loc)
        elif ctxt.world[IsA(loc, "supporter")] :
            ctxt.write("(on",world[DefiniteName(loc)]+")")
            __DESCRIBE_LOCATION_mentioned.append(loc)
        else :
            return
        loc = ctxt.world[Location(loc)]

def join_with_spaces(xs) :
    return " ".join(xs)

actoractivities.define_activity("terse_obj_description", accumulator=join_with_spaces,
                           doc="""Should give a terse description of
                           an object while modifying mentioned as
                           objects are mentioned.  Should raise
                           ActionHandled() if want to signal no
                           message to be given (for if wanting to
                           print out a paragraph).""")

@actoractivities.to("terse_obj_description")
def terse_obj_description_DefiniteName(actor, o, notables, mentioned, ctxt) :
    """Describes the object based on its indefinite name.  Except, if
    the NotableDescription is set, that is printed instead, and makes
    terse_obj_description return the empty string."""
    mentioned.append(o)
    d = ctxt.world[NotableDescription(o)]
    if d :
        ctxt.write(d)
        raise ActionHandled()
    else :
        return ctxt.world[IndefiniteName(o)]

@actoractivities.to("terse_obj_description")
def terse_obj_description_container(actor, o, notables, mentioned, ctxt) :
    """Describes the contents of a container, giving information of
    whether it is open or closed as needed (uses IsOpaque for if the
    container is openable and closed)."""
    if ctxt.world[IsA(o, "container")] :
        if ctxt.world[IsOpaque(o)] and ctxt.world[Openable(o)] and not ctxt.world[IsOpen(o)] :
            return "(which is closed)"
        else :
            contents = ctxt.world[Contents(o)]
            msgs = []
            for c in contents :
                if c in notables and c not in mentioned :
                    msg = ctxt.activity.terse_obj_description(actor, c, notables, mentioned)
                    if msg : msgs.append(msg)
            if msgs :
                state = "which is closed and " if ctxt.world[Openable(o)] and not ctxt.world[IsOpen(o)] else ""
                return "("+state+"in which "+is_are_list(msgs)+")"
            elif not contents :
                return "(which is empty)"
            else :
                raise NotHandled()
    else : raise NotHandled()

@actoractivities.to("terse_obj_description")
def terse_obj_description_supporter(actor, o, notables, mentioned, ctxt) :
    if ctxt.world[IsA(o, "supporter")] :
        contents = ctxt.world[Contents(o)]
        msgs = []
        for o in contents :
            if o in notables and o not in mentioned :
                msg = ctxt.activity.terse_obj_description(actor, o, notables, mentioned)
                if msg : msgs.append(msg)
        if msgs :
            return "(on which "+is_are_list(msgs)+")"
    raise NotHandled()


actoractivities.define_activity("get_notable_objects", accumulator=list_append,
                           doc="""Returns a list of objects which are
                           notable in a description as (obj,n) pairs,
                           where n is a numeric value from 0 onward
                           denoting notability.  n=1 is default, and
                           n=0 disables.  Repeats are fine.""")

@actoractivities.to("get_notable_objects")
def get_notable_objects_no_for_scenery(actor, x, ctxt) :
    """Scenery is not notable, and neither are its contents, so
    returns [(x,0)] and stops executing the rest of the activity."""
    if ctxt.world[Scenery(x)] :
        raise ActionHandled([(x, 0)])
    else : raise NotHandled()
@actoractivities.to("get_notable_objects")
def get_notable_objects_thing(actor, x, ctxt) :
    """By default, returns (x, 1) to represent x not being very
    notable, but notable enough to be mentioned."""
    if ctxt.world[IsA(x, "thing")] :
        return [(x, 1)]
    else : raise NotHandled()
@actoractivities.to("get_notable_objects")
def get_notable_objects_container(actor, x, ctxt) :
    """Gets objects from the container"""
    if ctxt.world[IsA(x, "container")] :
        obs = ctxt.world[Contents(x)]
        return list_append(ctxt.activity.get_notable_objects(actor, o) for o in obs if ctxt.world[AccessibleTo(o, actor)])
    else : raise NotHandled()
@actoractivities.to("get_notable_objects")
def get_notable_objects_supporter(actor, x, ctxt) :
    if ctxt.world[IsA(x, "supporter")] :
        obs = ctxt.world[Contents(x)]
        return list_append(ctxt.activity.get_notable_objects(actor, o) for o in obs)
    else : raise NotHandled()
@actoractivities.to("get_notable_objects")
def get_notable_objects_not_reported(actor, x, ctxt) :
    if not ctxt.world[Reported(x)] :
        return [(x, 0)]
    else : raise NotHandled()

##
# Describing objects
##

actoractivities.define_activity("describe_object",
                           doc="""Describes an object for the purpose of examining.""")

__DESCRIBE_OBJECT_described = False

@actoractivities.to("describe_object")
def describe_object_init(actor, o, ctxt) :
    """Initialize the global variable __DESCRIBE_OBJECT_described,
    which represents whether any description was uttered."""
    global __DESCRIBE_OBJECT_described
    __DESCRIBE_OBJECT_described = False
@actoractivities.to("describe_object")
def describe_object_description(actor, o, ctxt) :
    """Writes the Description if there is one defined."""
    d = ctxt.world[Description(o)]
    if d :
        global __DESCRIBE_OBJECT_described
        __DESCRIBE_OBJECT_described = True
        ctxt.write(d+"[newline]", actor=actor)
@actoractivities.to("describe_object")
def describe_object_container(actor, o, ctxt) :
    """Writes a line about the contents of a container if the container is not opaque."""
    global __DESCRIBE_OBJECT_described
    if ctxt.world[IsA(o, "container")] :
        if not ctxt.world[IsOpaque(o)] :
            contents = [ctxt.world[DefiniteName(c)] for c in ctxt.world[Contents(o)] if ctxt.world[Reported(c)]]
            if contents :
                __DESCRIBE_OBJECT_described = True
                ctxt.write("In "+ctxt.world[DefiniteName(o)]+" "+is_are_list(contents)+".[newline]", actor=actor)
        elif ctxt.world[Openable(o)] and not ctxt.world[IsOpen(o)] :
            __DESCRIBE_OBJECT_described = True
            ctxt.write(str_with_objs("[The $o] is closed.", o=o), actor=actor)
@actoractivities.to("describe_object")
def describe_object_supporter(actor, o, ctxt) :
    """Writes a line about the contents of a supporter."""
    if ctxt.world[IsA(o, "supporter")] :
        contents = [c for c in ctxt.world[Contents(o)] if ctxt.world[Reported(c)]]
        if contents :
            global __DESCRIBE_OBJECT_described
            __DESCRIBE_OBJECT_described = True
            ctxt.write("On "+ctxt.world[DefiniteName(o)]+" "+is_are_list(contents)+".[newline]", actor=actor)
@actoractivities.to("describe_object")
def describe_object_default(actor, o, ctxt) :
    """Runs if none of the previous were successful.  Prints a default message."""
    global __DESCRIBE_OBJECT_described
    if not __DESCRIBE_OBJECT_described :
        ctxt.write(str_with_objs("{Bob|cap} {sees} nothing special about [the $o].", o=o), actor=actor)

##
# Describing possessions
##

actoractivities.define_activity("describe_possession",
                           doc="""Describes an object as if it were a possession.""")

@actoractivities.to("describe_possession")
def describe_possession_indefinite_name(actor, o, numtabs, ctxt) :
    """Prints the indefinite name of the object preceded by numtabs
    indentations."""
    ctxt.write("[indent]"*numtabs+ctxt.world[IndefiniteName(o)])
@actoractivities.to("describe_possession")
def describe_possession_openable(actor, o, numtabs, ctxt) :
    """Prints (open) or (closed) if the thing is openable."""
    if ctxt.world[Openable(o)] :
        if ctxt.world[IsOpen(o)] :
            ctxt.write("(open)")
        else :
            ctxt.write("(closed)")
@actoractivities.to("describe_possession")
def describe_possession_supporter(actor, o, numtabs, ctxt) :
    """Prints the contents of a supporter."""
    if ctxt.world[IsA(o, "supporter")] :
        cont = ctxt.world[Contents(o)]
        for c in cont :
            ctxt.write("[break]"+"[indent]"*numtabs)
            ctxt.activity.describe_possession(actor, c, numtabs+1)
@actoractivities.to("describe_possession")
def describe_possession_container(actor, o, numtabs, ctxt) :
    """Prints the contents of a container if it's not opaque."""
    if ctxt.world[IsA(o, "container")] and not ctxt.world[IsOpaque(o)] :
        cont = ctxt.world[Contents(o)]
        for c in cont :
            ctxt.write("[break]"+"[indent]"*numtabs)
            ctxt.activity.describe_possession(actor, c, numtabs+1)

###*
###* Actions by a person
###*

###
### Oft-used requirements on actions
###

def require_xobj_accessible(action) :
    """Adds a rule which ensures that x is accessible to the actor in
    the action."""
    @verify(action)
    @docstring("Ensures the object x in "+repr(action)+" is accessible to the actor.  Added by require_xobj_accessible.")
    def _verify_xobj_accessible(actor, x, ctxt, **kwargs) :
        if not ctxt.world[AccessibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))

def require_xobj_held(action, only_hint=False, transitive=True) :
    """Adds rules which check if the object x is held by the actor in
    the action, and if only_hint is not true, then if the thing is not
    already held, an attempt is made to take it."""
    def __is_held(actor, x, ctxt) :
        if transitive :
            return actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)]
        else :
            return ctxt.world.query_relation(Has(actor, x))
    @verify(action)
    @docstring("Makes "+repr(action)+" more logical if object x is held by the actor.  Also ensures that x is accessible to the actor. Added by require_xobj_held.")
    def _verify_xobj_held(actor, x, ctxt, **kwargs) :
        if ctxt.world.query_relation(Has(actor, x)) :
            return VeryLogicalOperation()
        elif not ctxt.world[AccessibleTo(x, actor)] :
            return IllogicalOperation(as_actor("{Bob|cap} {can} see no such thing.", actor=actor))
    if only_hint :
        @before(action)
        @docstring("A check that the actor is holding the x in "+repr(action)+".  The holding may be transitive.")
        def _before_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {isn't} holding that.", actor=actor)
    else :
        @trybefore(action)
        @docstring("An attempt is made to take the object x from "+repr(action)+" if the actor is not already holding it")
        def _trybefore_xobj_held(actor, x, ctxt, **kwargs) :
            if not __is_held(actor, x, ctxt) :
                do_first(Take(actor, x), ctxt=ctxt)
            # just in case it succeeds, but we don't yet have the object
            if transitive :
                can_do = (actor == ctxt.world[Owner(x)] and ctxt.world[AccessibleTo(x, actor)])
            else :
                can_do = ctxt.world.query_relation(Has(actor, x))
            if not __is_held(actor, x, ctxt) :
                raise AbortAction("{Bob|cap} {doesn't} have that.", actor=actor)

def hint_xobj_notheld(action) :
    """Adds a rule which makes the action more logical if x is not
    held by the actor of the action."""
    @verify(action)
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
understand("look/l", Look(actor))

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
understand("inventory/i", Inventory(actor))

@when(Inventory(actor))
def when_inventory(actor, ctxt) :
    possessions = ctxt.world[Contents(actor)]
    if possessions :
        ctxt.write("{Bob|cap} {is} carrying:[break]")
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
understand("examine/x [something x]", Examine(actor, X))

require_xobj_accessible(Examine(actor, X))

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
understand("take/get [something x]", Take(actor, X))
understand("pick up [something x]", Take(actor, X))

require_xobj_accessible(Take(actor, X))
hint_xobj_notheld(Take(actor, X))

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
                raise AbortAction(str_with_objs("{Bob|cap}'d {have} to get out of [the $x] first.", x=x), actor=actor)
            elif ctxt.world[IsA(x, "supporter")] :
                raise AbortAction(str_with_objs("{Bob|cap}'d {have} to get off [the $x] first.", x=x), actor=actor)
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
understand("drop [something x]", Drop(actor, X))

require_xobj_held(Drop(actor, X), only_hint=True)

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
understand("go [direction x]", Go(actor, X))
understand("[direction x]", Go(actor, X))

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
understand("ask [something x] to [action y]", AskTo(actor, X, Y))

class GiveTo(BasicAction) :
    verb = ("give", "to")
    gerund = ("giving", "to")
    numargs = 3
understand("give [something x] to [something y]", GiveTo(actor, X, Y))

class Destroy(BasicAction) :
    verb = "destroy"
    gerund = "destroying"
    numargs = 2
understand("destroy [something x]", Destroy(actor, X))

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
understand("open [something x]", Open(actor, X))

require_xobj_accessible(Open(actor, X))

@when(Open(actor, X))
def when_open(actor, x, ctxt) :
    ctxt.world[IsOpen(x)] = True

@report(Open(actor, X))
def report_open(actor, x, ctxt) :
    ctxt.write("Opened.")
