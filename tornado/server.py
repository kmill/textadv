import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
import os.path
import sys

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print "main get"
        import base64, uuid, datetime
        session = self.get_cookie("session")
        if (not session) or (session not in sessions) :
            unique_session = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=365)
            session = tornado.escape.json_encode(unique_session)
            self.set_cookie("session", value=session, expires=expires)
        
            t = GameThread()
            t.daemon = True
            t.start()        
            sessions[session] = t

        self.render('static/index.html')

class InputHandler(tornado.web.RequestHandler) :
    def post(self) :
        print "getting input"
        session = self.get_cookie("session")
        if (not session) or (session not in sessions):
            self.write("Error")
            self.finish()
            return
        t = sessions[session]
        command = self.get_argument("command", default=None)
        t.game_context.io.receive_input(command)
        self.write("received")

class OutputHandler(tornado.web.RequestHandler) :
    @tornado.web.asynchronous
    def get(self) :
        session = self.get_cookie("session")
        if (not session) or (session not in sessions):
            self.write("Error")
            self.finish()
            return
        t = sessions[session]
        print "waiting for output"
        t.game_context.io.register_wants_output(self.__finish_output)
    def __finish_output(self, out, prompt) :
        self.write(json_encode({"text" : out,
                                "prompt" : prompt}))
        print "gave output."
        self.finish()

application = tornado.web.Application(
    [(r"/", MainHandler),
     (r"/input", InputHandler),
     (r"/output", OutputHandler),
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
    def register_wants_output(self, callback) :
        self.main_lock.acquire()
        if self.to_output :
            if self.wants_output :
                self.wants_output(self.to_output, self.prompt)
                self.wants_output = callback
                self.to_output = ""
            else :
                callback(self.to_output, self.prompt)
                self.to_output = ""
        else :
            if self.wants_output :
                self.wants_output("", self.prompt)
            self.wants_output = callback
        self.main_lock.release()
    def get_input(self, prompt=">") :
        self.main_lock.acquire()
        self.prompt = prompt
        self.main_lock.release()
        self.flush()
        self.input_lock.acquire()
        command = self.commands.pop()
        return command
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
    def run(self) :
        game = __import__("cloak")
        self.game_context = game.make_actorcontext_with_io(TornadoGameIO())
        game.basic_begin_game(self.game_context)

sessions = {}

if __name__ == "__main__":
    sys.path.append("/Users/kyle/Projects/textadv")
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
