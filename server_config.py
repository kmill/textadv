# This is a file for server settings, especially for adding games to
# the server

print "Loading games..."

add_game_path(os.path.join(os.path.dirname(__file__), "../.."))
add_game("games", "cloak")
add_game("games", "testgame")
add_game("games", "testgame2")
add_game("games", "continuations")
add_game("games", "isleadv")
