# basicpatterns.py
#
# Useful patterns which are used everywhere.  These let one write x
# instead of PVar("x") in patterns, for instance.
#
# gives x, y, z, actor
# and result accessors get_x, get_y, get_z, and get_actor

from textadv.core.patterns import PVar

x = PVar("x")
y = PVar("y")
z = PVar("z")
def get_v(var) :
    def _get_v(**args) :
        return args[var]
    return _get_v
get_x = get_v("x")
get_y = get_v("y")
get_z = get_v("z")
