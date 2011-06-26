# basicpatterns.py
#
# Useful patterns which are used everywhere.  These let one write X
# instead of VarPattern("x") in patterns, for instance.
#
# gives: X, Y, Z, actor

from textadv.core.patterns import VarPattern

X = VarPattern("x")
Y = VarPattern("y")
Z = VarPattern("z")
actor = VarPattern("actor")
