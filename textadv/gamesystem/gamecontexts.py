# gamecontexts.py
#
# Supposedly handles making the game modal in some way (as in, make
# input and output change how it works, or start playing a subgame in
# the game).
#
# The objects in this module are able to encapsulate the game state, though.
#
# provides: execute_context and ActorContext

from textadv.gamesystem.utilities import eval_str, as_actor
from textadv.core.world import WObject
from textadv.core.events import AbortAction, ActionHandled
from textadv.gamesystem.eventsystem import event_notify, verify_action, run_action
from textadv.gamesystem.eventsystem import StartGame, StartTurn, GameIsEnding
from textadv.gamesystem.utilities import *
from textadv.gamesystem import parser
from textadv.gamesystem.basicpatterns import x, y, z

def execute_context(context) :
    """Takes a context and runs it.  If it returns anything, it is
    treated to be a context, and that is run, and so on."""
    ret = context.run()
    while ret is not None :
        ret = ret.run()

class GameContext(object) :
    """Provides a way to look at the world.  Handles all user input in
    a contextual way."""
    def run(self) :
        """Drives the context.  The return value is the new context to
        run, None if the game is over."""
        raise NotImplementedError("GameContext is abstract.")
    def write_line(self, *stuff) :
        """Handles output.  That way filters can be applied by the
        current context."""
        raise NotImplementedError("GameContext is abstract.")

## the io object for ActorContext must implement get_input which
## functions as raw_input, and write_line which functions as print
    
class ActorContext(GameContext) :
    def __init__(self, parentcontext, io, parser, world, actorid) :
        self.parentcontext = parentcontext
        self.io = io
        self.world = world
        if isinstance(actorid, WObject) :
            actorid = actorid.id
        self.actorid = actorid
        self.actor = self.world[self.actorid]
        self.parser = parser
    def write_line(self, *stuff, **kwargs) :
        """Writes a line by evaluating the string using the utilities
        module.  If there is an actor, then the text is wrapped so
        that the text is rendered as if the actor were doing it."""
        if kwargs.has_key("actor") :
            stuff = [as_actor(s, kwargs["actor"]) for s in stuff]
        newstuff = [eval_str(s, self) for s in stuff]
        self.io.write_line(*newstuff)
    def run(self) :
        self.actor = self.world[self.actorid]
        
        event_notify(StartGame(), self)
        self.write_line(self.actor.get_location().make_description())

        def _handlefn(action, **kwargs) :
            run_action(action, context=self, **kwargs)
        def _verifyfn(action) :
            return verify_action(action, context=self)

        while True :
            event_notify(StartTurn(), self) # this had better work and not throw exceptions.
            
            # set up the parser
            self.parser.reset_local_words()
            # local objects
            local_objects = self.actor.get_location().get_objects()
            objwords = [(o, o["words"]) for o in local_objects]
            self.parser.set_local_objects(objwords)
            # global objects
            global_objects = self.world.lookup_objs(x)
            objwords = [(o, o["words"]) for o in global_objects]
            self.parser.set_global_objects(objwords)
            #print self.parser

            try :
                input = self.io.get_input()
                
                try :
                    self.parser.handle_all(input, actor=self.actor,
                                           verifyfn=_verifyfn, handlefn=_handlefn)
                except parser.NoSuchWord as ex :
                    esc = escape_str(ex.word)
                    self.write_line("I don't know what you mean by %r." % esc)
                except parser.NoUnderstand :
                    self.write_line("Huh?")
                except parser.NoInput :
                    pass
                except parser.Ambiguous as ex :
                    options = ex.options
                    if len(options) == 0 :
                        self.write_line("That means too many things to me.")
                    elif len(options) == 1 :
                        res = serial_comma([self.world[o]["definite_name"]
                                            for o in options[0]],
                                           conj="or")
                        self.write_line("Do you mean "+res+"?")
                    else :
                        res = ["do you mean "+serial_comma([self.world[o]["definite_name"]
                                                            for o in ops],
                                                           conj="or")
                               for ops in options]
                        out = "I'm a bit confused: "+serial_comma(res, conj="and", comma=";",
                                                                  force_comma=True)+"?"
                        self.write_line(out)
                except AbortAction as ab :
                    if len(ab.args) > 0 :
                        self.write_line(*ab.args, **ab.kwargs)
                    #print "(aborted.)"
            except GameIsEnding as gis :
                event_notify(gis.msg, context=self)
                self.write_line("\n\n*** The game is over ***")
                return None
            except Exception :
                import traceback
                traceback.print_exc()
