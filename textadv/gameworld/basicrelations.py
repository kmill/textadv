### Not to be imported
## Should be execfile'd

# basicrelations.py

# These are definitions of relations in the game world.
#
# Table of contents
# * Basic position relations
# * Kinds and instances

###
### Basic position relations
###

# The following five are mutually exclusive relations which have to do
# with the position of an object in the world.

@world.define_relation
@world.define_property
class Contains(OneToManyRelation, Property) :
    """Contains(x,y) for "x Contains y".  As a property, represents
    whether something contains something transitively."""
    numargs = 2

@world.handler(Contains(X,Y))
def property_handler_IsA(x, y, world) :
    """Lets one ask whether X contains Y transitively."""
    return world.r_path_to(Contains, x, y)

@world.define_relation
class Supports(OneToManyRelation) :
    """Supports(x,y) for "x Supports y"."""

@world.define_relation
class Has(OneToManyRelation) :
    """Has(x,y) for "x Has y"."""

@world.define_relation
class PartOf(ManyToOneRelation) :
    """PartOf(x,y) for "x PartOf y"."""

@world.define_relation
class Wears(OneToManyRelation) :
    """Wears(x,y) for "x Wears y"."""


# The following are helper activities to make it easy to use these
# position relations while maintaining mutual exclusivity.

# put X in Y (so then Y Contains X)
@world.to("put_in")
def default_put_in(x, y, world) :
    """Called with put_in(x, y).  Puts x into y, first removing all
    Contains, Supports, Has, PartOf, and Wears relations.  This should
    be used for y being a container or a room."""
    world.activity.remove_obj(x)
    world.add_relation(Contains(y, x))

# put X on Y (so then Y Supports X)
@world.to("put_on")
def default_put_on(x, y, world) :
    """Called with put_on(x, y).  Puts x onto y, first removing all
    Contains, Supports, Has, PartOf, and Wears relations."""
    world.activity.remove_obj(x)
    world.add_relation(Supports(y, x))

# give X to Y (so then Y Has X)
@world.to("give_to")
def default_give_to(x, y, world) :
    """Called with give_to(x, y).  Gives x to y, first removing all
    Contains, Supports, Has, PartOf, and Wears relations."""
    world.activity.remove_obj(x)
    world.add_relation(Has(y, x))

# make X part of Y (so then X PartOf Y)
@world.to("make_part_of")
def default_make_part_of(x, y, world) :
    """Called with make_part_of(x, y).  Makes x a part of y, first
    removing all Contains, Supports, Has, PartOf, and Wears
    relations."""
    world.activity.remove_obj(x)
    world.add_relation(PartOf(x, y))

# make X wear Y (so then X Wears Y)
@world.to("make_wear")
def default_make_part_of(x, y, world) :
    """Called with make_wear(x, y).  Makes x wear y, first removing
    all Contains, Supports, Has, PartOf, and Wears relations."""
    world.activity.remove_obj(y)
    world.add_relation(Wears(x, y))

@world.to("remove_obj")
def default_remove_obj(obj, world) :
    """Effectively removes an object from play by making it have no
    positional location."""
    world.remove_relation(Contains(Z, obj))
    world.remove_relation(Supports(Z, obj))
    world.remove_relation(Has(Z, obj))
    world.remove_relation(PartOf(obj, Z))
    world.remove_relation(Wears(Z, obj))


@world.define_property
class Location(Property) :
    """Location(X) is the current immediate location in which X
    resides.  Usually used to get the location of the actor."""
    numargs = 1

world[Location(X)] = None
@world.handler(Location(X))
def object_location_Contains(x, world) :
    """Gets the location of an object by what currently contains it."""
    locs = world.query_relation(Contains(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_Has(x, world) :
    """Gets the location of an object by what currently has it."""
    locs = world.query_relation(Has(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_Supports(x, world) :
    """Gets the location of an object by what currently supports it."""
    locs = world.query_relation(Supports(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_PartOf(x, world) :
    """Gets the location of an object by what it is currently part of."""
    locs = world.query_relation(PartOf(x, Y), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()
@world.handler(Location(X))
def object_location_Wears(x, world) :
    """Gets the location of an object by what currently wears it."""
    locs = world.query_relation(Wears(Y, x), var=Y)
    if locs : return locs[0]
    else : raise NotHandled()


@world.define_property
class Owner(Property) :
    """Gets the owner of the object."""
    numargs = 1

@world.handler(Owner(X))
def rule_Owner_default(x, world) :
    """We assume that the owner of an object is the first object which
    Has some object which in some chain of containment (containment
    optional).  Returns None if no owner was found."""
    poss_owner = world.query_relation(Has(Y, x), var=Y)
    if poss_owner :
        return poss_owner[0]
    poss_container = world.query_relation(Contains(Y, x), var=Y)
    if poss_container :
        return world[Owner(poss_container[0])]
    return None


###
### Kinds and instances
###

@world.define_relation
class KindOf(ManyToOneRelation) :
    """Represents a class-like hierarchy."""

@world.define_property
@world.define_relation
class IsA(ManyToOneRelation, Property) :
    """Represents inheriting from a kind.  As a relation, represents a
    direct inheritence.  As a property, represents the transitive IsA
    relation."""
    numargs=2

@world.handler(IsA(X,Y))
def property_handler_IsA(x, y, world) :
    """Lets one ask whether a particular object is of a particular
    kind, searching up the KindOf tree."""
    kind = world.query_relation(IsA(x, Z), var=Z)
    if not kind :
        return False
    else :
        return world.r_path_to(KindOf, kind[0], y)

world.define_activity("referenceable_things", accumulator=list_append)
@world.to("referenceable_things")
def referenceable_things_Default(world) :
    """Gets all things in the world (that is, all objects which
    inherit from "thing")."""
    objects = world.query_relation(IsA(X, Y), var=X)
    things = [o for o in objects if world[IsA(o, "thing")]]
    return things

world.define_activity("objects_of_kind", accumulator=list_append)
@world.to("objects_of_kind")
def objects_of_type_Default(kind, world) :
    """Gets all objects of a given kind."""
    objects = world.query_relation(IsA(X, Y), var=X)
    return [o for o in objects if world[IsA(o, kind)]]

###
### Connecting rooms and doors together
###

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
