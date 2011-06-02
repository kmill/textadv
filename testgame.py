# testgame.py
#
# a test of the game engine

from textadv.basiclibrary import *

##
## Rat region
##

rat_region = world.new_obj("rat_region", Region, "Rat region")
rat = world.new_obj("rat", Scenery, "big fat rat", """The rat looks like it's been eating quite a lot.  You are somewhat confused, though, since rats don't live on the fourth floor.""")
rat.move_to(rat_region)
rat["no_take_msg"] = "It moves too fast for you to catch it."
understand("catch rat", Take(actor, "rat"))
sky = world.new_obj("sky", Scenery, "sky", """You look out the window and see a bit of the Boston skyline.""")
sky.move_to(rat_region)
sky["words"] = ["boston", "@skyline", "@sky"]

##
## The Verifier
##

verifier = world.new_obj("verifier", Actor, "The Verifier", """
The Verifier always thinks what you do is a good idea.""")
@before(TagPattern(x, player, z))
def _verifier_whenever(x, z, context) :
    if context.world["player"].get_location() != context.world["verifier"].get_location() :
        return
    if x==Take :
        context.write_line(str_with_objs("\"My, I would have never thought of taking [the $z],\" notes The Verifier.", z=z))
    else :
        context.write_line("\"What a wonderful idea!\" cries The Verifier.")

#@when(EndTurn())
def _verifier_startturn(context) :
    player = context.world["player"]
    verifier = context.world["verifier"]
    if player.get_location() != verifier.get_location() :
        context.write_line("The Verifier follows.")
        verifier.move_to(player.get_location())

##
## Your pocket
##

pocket = world.new_obj("pocket", BObject, "pocket", "It's your pocket.")
pocket.give_to(player) # doesn't give to player, just attaches it so it's in context
pocket["reported"] = False
pocket["reference_objects"] = False

the_key = world.new_obj("the_key", BObject, "useful key", """
It looks like it can open anything.""")
the_key["indefinite_name"] = "a useful key"
the_key.move_to(pocket)

@before(Examine(actor, BObject(PVar("pocket", pocket))))
def _before_examine_pocket(actor, pocket, context) :
    if actor.id != context.actorid :
        return
    if context.world["the_key"].s_R_x(In, pocket) :
        context.write_line("The key was in your pocket all along.")
        context.world["the_key"].move_to(context.actor.get_location())
        raise DoInstead(Take(actor, "the_key"))

##
## Room 41
##

room_41 = world.new_obj("room_41", Room, "41","""
This is a room on the fourth floor of tep.  It is currently home to Kyle.  There is a bed and a loft.  There is an exit to the north.""")
room_41.move_to(rat_region)

player.move_to("room_41")
verifier.move_to("room2")

ball = world.new_obj("ball", BObject, "red ball","""
It's simply a red ball.  Round like a sphere.""")
ball.move_to(room_41)

ball2 = world.new_obj("ball2", BObject, "blue ball","""
It's a blue ball.  Like something blue.""")
ball2.move_to(room_41)

ball3 = world.new_obj("ball3", BObject, "green ball","""
It's a green ball.  Like grass, but not quite.""")
ball3.move_to(room_41)
ball3["indefinite_name"] = "an amazing green ball"
ball3["words"] = ["amazing", "green", "@ball"]
@before(Take(actor, ball3))
def _instead_take_ball3(actor, context) :
    context.write_line("{Bob} actually {wants} the blue ball.")
    raise DoInstead(Take(actor, "ball2"))

light = world.new_obj("light", BObject, "light", """It's a light.""")
light_bulb = world.new_obj("light_bulb", BObject, "light bulb", "It's a light bulb.")
light.move_to("room_41")
light_bulb.move_to("room_41")

zombocom = world.new_obj("zombocom", Room, "zombocom", """
[if [when in zombocom]]Welcome to zombocom.[else]This is zombocom.  It looks like you can enter it.[endif]""")
zombocom.move_to("room_41")
zombocom["reference_self"] = True

@before(Enter(actor, zombocom))
def _before_enter_zombocom(actor, context) :
    context.write_line("Anything is possible...")

##
## Room2
##

room2 = world.new_obj("room2", Room, "Another Room", """
It's another room.  I don't know what to say.  You can go south.""")
#room_41.connect(room2, "north")

door = world.new_obj("door", Door, "old door","""
It's a door.  It's made of wood, and has been here longer than you have.  It is [get door is_open_msg].""")
door.add_exit_for(room_41, "north")
door.add_exit_for(room2, "south")
door["lockable"] = True
door["locked"] = True
door.unlockable_with(the_key)

##
## Run game
##

print "World serialization is",len(world.serialize()),"bytes"
import zlib
print "World serialization is",len(zlib.compress(world.serialize())),"bytes compressed"
#import pickle
#pickle.dump(game_context, file("the_world.obj", "w"))


if __name__=="__main__" :
    #context2 = ActorContext(None, gameio, world.copy(), "player")
    basic_begin_game()
