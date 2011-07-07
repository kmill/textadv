import tornado.ioloop
import tornado.web
from tornado.escape import json_encode, url_unescape
import os.path
import sys
import time

sys.path.append("/Users/kyle/Projects/textadv")

games = {"cloak" : __import__("cloak"),
         "testgame2" : __import__("testgame2"),
         "isleadv" : __import__("isleadv")}

class MainHandler(tornado.web.RequestHandler):
    def get(self) :
        self.write("<h1>Games</h1>")
        for game in games.iterkeys() :
            self.write("<a href=\"game/"+game+"\">"+game+"</a><br>")

class GameHandler(tornado.web.RequestHandler):
    def get(self, game):
        import base64, uuid, datetime

        if game not in games :
            self.write("No such game")
            return

        session = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
        
        t = GameThread(games[game], session=session)
        t.daemon = True
        t.start()
        sessions_lock.acquire()
        sessions[session] = t
        sessions_timer[session] = time.time()
        sessions_lock.release()
        self.render('static/index.html', session=session)

class InputHandler(tornado.web.RequestHandler) :
    def post(self) :
        session = url_unescape(self.get_argument("session", None))
        sessions_lock.acquire()
        if (not session) or (session not in sessions):
            print "ignoring input from non-session"
            self.write("Error")
            self.finish()
            sessions_lock.release()
            return
        else :
            print "getting input"
            t = sessions[session]
            sessions_timer[session] = time.time()
            sessions_lock.release()
            command = self.get_argument("command", default=None)
            t.game_context.io.receive_input(str(command))
            self.write("received")

class OutputHandler(tornado.web.RequestHandler) :
    @tornado.web.asynchronous
    def get(self) :
        self.output_lock = threading.Semaphore(1)
        session = url_unescape(self.get_argument("session", None))
        self.ignore_output = False
        sessions_lock.acquire()
        if (not session) or (session not in sessions):
            print "ignoring output request for non-session"
            self.write("Error")
            self.finish()
            sessions_lock.release()
            return
        else :
            t = sessions[session]
            sessions_timer[session] = time.time()
            sessions_lock.release()
            self.game_thread = t
            print "waiting for output"
            t.game_context.io.register_wants_output(self.__finish_output)
    def __finish_output(self, out, prompt) :
        self.output_lock.acquire()
        if self.ignore_output :
            print "ignoring output, client has quit"
        else :
            self.write(json_encode({"text" : out,
                                    "prompt" : prompt}))
            print "wrote output."
            try :
                self.finish()
                print "gave output."
            except Exception as x :
                print "but failed to finish.  Exception:", x
        self.output_lock.release()
    def set_ignore_output(self) :
        self.output_lock.acquire()
        self.ignore_output = True
        self.output_lock.release()
    def on_connection_close(self) :
        tornado.web.RequestHandler.on_connection_close(self)
        self.set_ignore_output()
        self.game_thread.game_context.io.kill_io()

class PingHandler(tornado.web.RequestHandler) :
    def post(self) :
        session = url_unescape(self.get_argument("session", None))
        sessions_lock.acquire()
        if (not session) or (session not in sessions):
            print "ignoring ping from non-session"
            self.write("Error")
            self.finish()
            sessions_lock.release()
            return
        else :
            print "getting ping"
            t = sessions[session]
            sessions_timer[session] = time.time()
            sessions_lock.release()
            print "handled ping"

application = tornado.web.Application(
    [(r"/", MainHandler),
     (r"/game/(.*)", GameHandler),
     (r"/input", InputHandler),
     (r"/output", OutputHandler),
     (r"/ping", PingHandler),
     ],
    static_path=os.path.join(os.path.dirname(__file__), "static"))

import threading

class TornadoGameIO(object) :
    def __init__(self) :
        self.prompt = ">"
        self.main_lock = threading.BoundedSemaphore(1)
        self.input_lock = threading.Semaphore(0)
        self.to_flush = []
        self.commands = []
        self.to_output = ""
        self.wants_output = None
        self.die = False
    def register_wants_output(self, callback) :
        self.main_lock.acquire()
        if self.to_output :
            print "1"
            if self.wants_output :
                print "2"
                self.wants_output(self.to_output, self.prompt)
                print "2.1"
                self.wants_output = callback
                self.to_output = ""
            else :
                print "3"
                callback(self.to_output, self.prompt)
                print "3.1"
                self.to_output = ""
        else :
            print "4"
            if self.wants_output :
                print "4.1"
                self.wants_output("", self.prompt)
            print "4.2"
            self.wants_output = callback
        self.main_lock.release()
    def get_input(self, prompt=">") :
        if self.die :
            raise SystemExit("Thread death due to self.die.")
        self.main_lock.acquire()
        self.prompt = prompt
        self.main_lock.release()
        self.flush()
        self.input_lock.acquire()
        if self.die :
            raise SystemExit("Thread death due to self.die.")
        command = self.commands.pop()
        return command
    def kill_io(self) :
        self.main_lock.acquire()
        self.die = True
        if self.wants_output :
            self.wants_output("<i>Error: timeout</i>", "")
            self.wants_output = None
        self.main_lock.release()
        self.input_lock.release()
    def receive_input(self, input) :
        """Receives input to forward to someone who called
        'get_input'."""
        self.main_lock.acquire()
        self.commands.insert(0, input)
        self.main_lock.release()
        self.input_lock.release()
    def write(self, *data) :
        self.main_lock.acquire()
        self.to_flush.extend(data)
        self.main_lock.release()
    def flush(self) :
        self.main_lock.acquire()
        out = " ".join(self.to_flush).replace("[newline]", "</p><p>").replace("[break]", "<br>")
        out = out.replace("[indent]", "&nbsp;&nbsp;")
        self.to_output += "<p>"+out+"</p>"
        self.to_flush = []
        if self.wants_output :
            self.wants_output(self.to_output, self.prompt)
            self.to_output = ""
            self.wants_output = None
        self.main_lock.release()

class GameThread(threading.Thread) :
    def __init__(self, game, session) :
        self.game = game
        self.game_context = self.game.make_actorcontext_with_io(TornadoGameIO())
        self.session = session
        threading.Thread.__init__(self)
    def run(self) :
        self.game.basic_begin_game(self.game_context)
        self.game_context.io.kill_io()

class WatchdogThread(threading.Thread) :
    def run(self) :
        while True :
            time.sleep(10)
            sessions_lock.acquire()
            to_delete = []
            for session, t in sessions_timer.iteritems() :
                if sessions[session].game_context.io.die or time.time() - t > 30 :
                    to_delete.append(session)
            for session in to_delete :
                print "removing",session
                if not sessions[session].game_context.io.die :
                    sessions[session].game_context.io.kill_io()
                del sessions[session]
                del sessions_timer[session]
            print len(sessions),"clients are connected"
            sessions_lock.release()

sessions = {}
sessions_timer = {}
sessions_lock = threading.Semaphore(1)

if __name__ == "__main__":
    watchdog = WatchdogThread()
    watchdog.daemon = True
    watchdog.start()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
