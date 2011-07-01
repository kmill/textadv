### Not to be imported
## Should be execfile'd

# basicrules.py
#
# These are definitions of properties and their rules.  Part of the
# definition is all of the properties of the kinds.

###
### Defining: kind
###

##
# Property: Name
##

@world.define_property
class Name(Property) :
    """Represents the name of an instance of a kind.  Then, the id of
    a thing may be differentiated from what the user will call it (for
    shorthand)."""
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
    """Gets the immediate contents of a room along with its doors."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]+world.activity.get_room_doors(x)

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
# Property: VisibleContainer
##

@world.define_property
class VisibleContainer(Property) :
    """Gets the object which visibly is the outermost container of an
    object which is "inside" of x (change to "on top of" for
    supporters).  Specifically, if the object is a closed box (but
    opaque), then the box is the effective container.  Otherwise, if
    the box is open (or not opaque), the result is the effective
    container for the location of the box."""
    numargs = 1

@world.handler(VisibleContainer(X) <= IsA(X, "room"))
def rule_VisibleContainer_if_x_in_room(x, world) :
    """The visible container for a room is the room itself."""
    return x

##
# Property: MakesLight
##
@world.define_property
class MakesLight(Property) :
    """Represents whether the object is a source of light,
    irrespective of whether (in the case of a container) its contents
    provide light.  That is, an open box with a lightbulb in it does
    not make light."""
    numargs = 1

# rooms make light by default
world[MakesLight(X) <= IsA(X, "room")] = True


##
# Properties: ContributesLight, ContainsLight
##

@world.define_property
class ContributesLight(Property) :
    """Represents whether the object is a source of light to its
    location."""
    numargs = 1

@world.define_property
class ContainsLight(Property) :
    """Represents whether the object is illuminated from the inside
    due to some light source, which may be itself.  Something that
    contains light need not contribute light to its location."""
    numargs = 1

@world.handler(ContainsLight(X) <= IsA(X, "room"))
def rule_ContainsLight_room_default_is_MakesLight(x, world) :
    """A room, by default, contains light if it makes light itself."""
    return world[MakesLight(x)]

@world.handler(ContainsLight(X) <= IsA(X, "room"))
def rule_ContainsLight_contents_can_light_room(x, world) :
    """A room contains light if any of its contents contribute light."""
    if any(world[ContributesLight(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

##
# Property: NoGoMessage
##

@world.define_property
class NoGoMessage(Property) :
    """Takes a (room, direction) pair and gives the reason one can't
    go that way."""
    numargs = 2

world[NoGoMessage(X, direction) <= IsA(X, "room")] = "{Bob|cap} can't go that way."

###
### Defining: thing
###

world[Description(X) <= IsA(X, "thing")] = None

# Most things don't provide light
world[MakesLight(X) <= IsA(X, "thing")] = False

# Most things don't contribute light
world[ContributesLight(X) <= IsA(X, "thing")] = False

@world.handler(ContributesLight(X) <= IsA(X, "thing"))
def rule_ContributesLight_thing_default_is_MakesLight(x, world) :
    """By default, a thing contributes light if it makes light."""
    if world[MakesLight(x)] :
        return True
    else : raise NotHandled()

# Most things don't contain light
world[ContainsLight(X) <= IsA(X, "thing")] = False

@world.handler(ContainsLight(X) <= IsA(X, "thing"))
def rule_ContributesLight_if_parts_contribute(x, world) :
    """A thing contributes light if any of its constituent parts contribute light."""
    parts = world.query_relation(PartOf(Y, x), var=Y)
    if any(world[ContributesLight(o)] for o in parts) :
        return True
    else : raise NotHandled()

# @world.handler(ContributesLight(X) <= IsA(X, "thing"))
# def rule_ContributesLight_if_contains_light(x, world) :
#     """A thing contributes light if it contains light."""
#     if world[ContainsLight(x)] :
#         return True
#     else : raise NotHandled()

@world.handler(EffectiveContainer(X) <= IsA(X, "thing"))
def rule_EffectiveContainer_if_thing(x, world) :
    """We assume that we only care about whether a regular thing is
    the effective container if it has constituent parts.  With this
    assumption, we then say that the effective container of a thing is
    its location."""
    return world[EffectiveContainer(world[Location(x)])]


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
# Properties: ProperNamed, PrintedName, DefiniteName, IndefiniteName
##

@world.define_property
class ProperNamed(Property) :
    """Represents whether or not the name of something is a proper
    name.  Basically inhibits the article for DefiniteName and
    IndefiniteName."""
    numargs = 1

world[ProperNamed(X) <= IsA(X, "thing")] = False

@world.define_property
class PrintedName(Property) :
    """Gives a textual representation of an object which can then be
    prefaced by an article (that is, unless ProperNamed is true).
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
    stuck in front, unless ProperNamed is true."""
    printed_name = world[PrintedName(x)]
    if world[ProperNamed(x)] :
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
    to the front, unless ProperNamed is true."""
    printed_name = world[PrintedName(x)]
    if world[ProperNamed(x)] :
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
# VisibleTo
##

@world.define_property
class VisibleTo(Property) :
    """VisibleTo(X, actor) checks whether X is visible to the
    actor."""
    numargs = 2

# by default, things aren't visible
world[VisibleTo(X, actor)] = False

@world.handler(VisibleTo(X, actor))
def rule_VisibleTo_if_held(x, actor, world) :
    """Anything the actor has is visible."""
    if world.query_relation(Has(actor, x)) :
        return True
    else :
        raise NotHandled()

@world.handler(VisibleTo(X, actor))
def rule_VisibleTo_if_in_same_visible_container(x, actor, world) :
    """Anything in the same visible container to the actor is visible
    if the visible container is lit.  We treat doors specially: if x
    is in the get_room_doors of the visible container, then the door
    is visible, too."""
    actor_vis_cont = world[VisibleContainer(world[Location(actor)])]
    if x in world.activity.get_room_doors(actor_vis_cont) :
        return True
    if actor_vis_cont == x :
        # otherwise we'd be looking too many levels high
        x_vis_cont = x
    else :
        x_vis_cont = world[VisibleContainer(world[Location(x)])]
    if actor_vis_cont == x_vis_cont and world[ContainsLight(actor_vis_cont)] :
        return True
    raise NotHandled()

@world.handler(VisibleTo(X, actor))
def rule_VisibleTo_if_part_of(x, actor, world) :
    """If an object is part of something, and that something is
    visible, then the object is visible."""
    x_assembly = world.query_relation(PartOf(x, Y), var=Y)
    if x_assembly and world[VisibleTo(x_assembly[0], actor)] :
        return True
    raise NotHandled()


##
# Property: AccessibleTo
##

@world.define_property
class AccessibleTo(Property) :
    """AccessibleTo(X, actor) checks whether X is accessible to actor,
    where 'accessible to' roughly means whether the actor could reach
    it."""
    numargs = 2

# by default, things are accessible so that we can negate it with
# rules (lets us basically make an 'and' instead of an 'or')
world[AccessibleTo(X, actor)] = True

@world.handler(AccessibleTo(X, actor))
def rule_not_AccessibleTo_if_different_effective_containers(x, actor, world) :
    """If x and the actor are in the different effective containers,
    then x is not accessible.  We check if the effective container of
    the location of the actor is x in case x is a supporter or a
    container.  We treat doors specially: a door is accessible if it's
    in the get_room_doors of the effective container for the actor."""
    actor_eff_cont = world[EffectiveContainer(world[Location(actor)])]
    if x in world.activity.get_room_doors(actor_eff_cont) :
        return True
    if actor_eff_cont != x :
        if actor_eff_cont != world[EffectiveContainer(world[Location(x)])] :
            return False
    raise NotHandled()

@world.handler(AccessibleTo(X, actor))
def rule_not_AccessibleTo_if_not_visible(x, actor, world) :
    """If x is not visible to actor, then it's not accessible."""
    if not world[VisibleTo(x, actor)] :
        return False
    else : raise NotHandled()

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
# Property: IsEnterable
##
@world.define_property
class IsEnterable(Property) :
    """Is true if the object is something someone could enter."""
    numargs = 1

# By default it's false
world[IsEnterable(X) <= IsA(X, "thing")] = False


@world.define_property
class NoEnterMessage(Property) :
    """Gives a message for why one is unable to enter the object
    (usually because IsEnterable is not true)."""
    numargs = 1

world[NoEnterMessage(X) <= IsA(X, "thing")] = "{Bob|cap} can't enter that."

@world.define_property
class ParentEnterable(Property) :
    """Gives the next object in the chain of Location which is
    enterable.  Assumes that rooms also satisfy this condition."""
    numargs = 1

@world.handler(ParentEnterable(X) <= IsA(X, "thing"))
def rule_ParentEnterable_by_Location(x, world) :
    """Gets either the next room or enterable by repeated calling of
    Location."""
    loc = world[Location(x)]
    while not world[IsA(loc, "room")] :
        if world[IsEnterable(loc)] :
            return loc
        loc = world[Location(x)]
    return loc

##
# Property: LocaleDescription
##

@world.define_property
class LocaleDescription(Property) :
    """A locale description for enterables.  If it's none, then it is
    ignored."""
    numargs = 1

# By default it's none for enterables
world[LocaleDescription(X) <= IsA(X, "enterable")] = None


###
### Defining: door
###

@world.to("put_in", insert_first=True)
def rule_put_in_not_for_doors(x, y, world) :
    """Doors should not be put in anything directly.  Instead, they
    should be attached to rooms using the connect_rooms activity."""
    if world[IsA(x, "door")] :
        raise Exception("Use connect_rooms to put a door in a room.")

@world.handler(Location(X) <= IsA(X, "door"))
def rule_Location_of_door_is_error(x, world) :
    """There is no location of a door: we would have two choices for
    its location."""
    raise Exception("Doors have no location.")

world[FixedInPlace(X) <= IsA(X, "door")] = True


##
# Properties: Openable, IsOpen
##

@world.define_property
class Openable(Property) :
    """Represents whether an object is able to be opened and closed."""
    numargs = 1

@world.define_property
class IsOpen(Property) :
    """Represents whether an openable object is open."""
    numargs = 1

world[Openable(X) <= IsA(X, "thing")] = False # by default, things aren't openable
world[IsOpen(X) <= Openable(X)] = False # by default, openable things are closed

world[Openable(X) <= IsA(X, "door")] = True # doors are openable by default.

@world.define_property
class NoOpenMessages(Property) :
    """Represents the messages for not being able to open or close an
    unopenable object."""
    numargs = 2

world[NoOpenMessages(X, "no_open")] = "{Bob|cap} can't open that."
world[NoOpenMessages(X, "no_close")] = "{Bob|cap} can't close that."
world[NoOpenMessages(X, "already_open")] = "That's already open."
world[NoOpenMessages(X, "already_closed")] = "That's already closed."

##
# Property: Lockable, IsLocked
##

@world.define_property
class Lockable(Property) :
    """Represents whether an object can be locked and unlocked."""
    numargs = 1

@world.define_property
class IsLocked(Property) :
    """Represents whether a lockable object is locked."""
    numargs = 1

world[Lockable(X) <= IsA(X, "thing")] = False

@world.define_property
class KeyOfLock(Property) :
    """This is the object which can unlock a Lockable item.  By
    default, it's None, representing there being no key."""
    numargs = 1

world[KeyOfLock(X) <= Lockable(X)] = None


@world.define_property
class NoLockMessages(Property) :
    """Represents the messages for not being able to lock or unlock an
    unlockable object, or if it's the wrong key."""
    numargs = 2

world[NoLockMessages(X, "no_lock")] = "That doesn't appear to be lockable."
world[NoLockMessages(X, "no_unlock")] = "That doesn't appear to be unlockable."
world[NoLockMessages(X, "wrong_key")] = "That key doesn't fit the lock."
world[NoLockMessages(X, "no_open")] = "That's locked."


###
### Defining: container
###

@world.handler(Contents(X) <= IsA(X, "container"))
def container_contents(x, world) :
    """Gets the immediate contents of the container."""
    return [o["y"] for o in world.query_relation(Contains(x, Y))]


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

@world.handler(ContainsLight(X) <= IsA(X, "container"))
def rule_ContainsLight_for_container(x, world) :
    """A container contains light if any of its contents contribute light."""
    if any(world[ContributesLight(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(ContributesLight(X) <= IsA(X, "container"))
def rule_ContributesLight_for_container(x, world) :
    """A container contributes light if it is not opaque and it contains light."""
    if not world[IsOpaque(x)] and world[ContainsLight(x)] :
        return True
    else : raise NotHandled()


@world.handler(VisibleContainer(X) <= IsA(X, "container"))
def rule_VisibleContainer_if_x_in_container(x, world) :
    """The visible container for a container is the container itself
    if it is opaque, otherwise it is the visible container of the
    location of the container."""
    if world[IsOpaque(x)] :
        return x
    else :
        return world[VisibleContainer(world[Location(x)])]

#
# The effective container of a container
#

@world.handler(EffectiveContainer(X) <= IsA(X, "container"))
def rule_EffectiveContainer_if_x_in_container(x, world) :
    """The effective container for a container is the container itself
    if it is closed, otherwise it is the effective container of the
    location of the container."""
    if world[Openable(x)] :
        if world[IsOpen(x)] :
            return world[EffectiveContainer(world[Location(x)])]
        else :
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

@world.handler(ContainsLight(X) <= IsA(X, "supporter"))
def rule_ContainsLight_for_supporter(x, world) :
    """A supporter contains light if it any of its objects contribute
    light."""
    if any(world[ContributesLight(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()

@world.handler(ContributesLight(X) <= IsA(X, "supporter"))
def rule_ContributesLight_for_supporter(x, world) :
    """A supporter contributes light if it contains light."""
    if world[ContainsLight(x)] :
        return True
    else : raise NotHandled()

@world.handler(VisibleContainer(X) <= IsA(X, "supporter"))
def rule_VisibleContainer_if_supporter(x, world) :
    """The visible container of a supporter is the visible container
    of the location of the supporter."""
    return world[VisibleContainer(world[Location(x)])]

#
# The effective container of a supporter
#

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

@world.handler(VisibleContainer(X) <= IsA(X, "person"))
def rule_VisibleContainer_if_person(x, world) :
    """We assume that people aren't able to conceal their possessions
    very well, and the visible container is thus the location of the
    person."""
    return world[VisibleContainer(world[Location(x)])]


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

@world.handler(ContributesLight(X) <= IsA(X, "person"))
def rule_ContributesLight_possessions_can_light_person(x, world) : # maybe should handle concealment at some point?
    """A person contributes light if any of their posessions contribute light."""
    if any(world[ContributesLight(o)] for o in world[Contents(x)]) :
        return True
    else : raise NotHandled()


###
### Other properties
###

##
# Scenery
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
