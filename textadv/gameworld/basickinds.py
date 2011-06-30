### Not to be imported
## Should be execfile'd

# basickinds.py

# These are definitions of the core kinds in the world, where a kind
# is something like a class of objects.  The definitions of KindOf and
# IsA are in basicrelations.py

world.add_relation(KindOf("room", "kind"))
world.add_relation(KindOf("thing", "kind"))
world.add_relation(KindOf("door", "thing"))
world.add_relation(KindOf("container", "thing"))
world.add_relation(KindOf("supporter", "thing"))
world.add_relation(KindOf("person", "thing"))
world.add_relation(KindOf("backdrop", "thing"))
world.add_relation(KindOf("region", "kind"))

# The choice of these kinds was greatly influenced by Inform 7.  The
# kind "kind" is the root of this structure just so that there is a
# root.  The following are basic properties of the other kinds.
#
# A room represents a place.  These are not contained in anything, and
# can be a part of an Exit relation.
#
# A thing represents some object that can be interacted with.
#
# A door is a thing which can be in two rooms and which also can be
# part of the Exit relation.
# 
# Containers and supporters are things which can contain and support
# things, respectively.  These are distinct because it simplifies the
# core library.
#
# Persons represent objects with which one can communicate.  This also
# encompasses the player character.
#
# Backdrops are things which can be present in multiple rooms (that
# is, there is a rule which moves backdrop to an appropriate room),
# effectively breaking the rule that things can't be in more than one
# room.
#
# Regions are kinds which can contain rooms, which breaks the rule
# that rooms are not contained in anything.  These are used to group
# together rooms.
