print "Starting server..."

import tornado.ioloop
import tornado.web
from tornado.escape import json_encode, url_unescape, url_escape, xhtml_escape
import os
import os.path
import sys
import time
import stat
import mimetypes
import email
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

games = dict()
auxfiles = dict()
alt_indices = dict()

def add_game_path(path) :
    sys.path.append(path)

def add_game(package, name, auxfile_dir=None, altindex=None) :
    """altindex is with respect to auxfile_dir, if auxfile_dir is set."""
    if package == None :
        games[name] = __import__(name, fromlist=[name])
    else :
        games[name] = __import__(package+"."+name, fromlist=[name])
    if auxfile_dir :
        auxfiles[name] = auxfile_dir
    if altindex :
        alt_indices[name] = altindex

print "Loading games..."

add_game_path(os.path.join(os.path.dirname(__file__), "../.."))
add_game("games", "cloak")
add_game("games", "testgame")
add_game("games", "testgame2")
add_game("games", "continuations")
add_game("games", "isleadv")
#add_game("games", "teptour", auxfile_dir="games/teptour_files", altindex="tepindex.html")

add_game_path("/Users/kyle/Projects/teptour")
add_game(None, "teptour", auxfile_dir="/Users/kyle/Projects/teptour/teptour_files", altindex="tepindex.html")

print "Loaded."

class MainHandler(tornado.web.RequestHandler):
    def get(self) :
        self.write("<h1>Games</h1>")
        for game in games.iterkeys() :
            self.write("<a href=\"game/"+game+"\">"+game+"</a><br>")

class GameHandler(tornado.web.RequestHandler):
    def get(self, arg):
        import base64, uuid, datetime

        args = arg.split("/")
        game = args[0]
        auxfile = args[1:]
        if auxfile :
            print "retrieving for",game,auxfile
            try :
                filedir = auxfiles[game]
            except KeyError :
                raise tornado.web.HTTPError(404)
            root_path = os.path.abspath(filedir)
            auxfile_path = os.path.abspath(os.path.join(root_path, *auxfile))
            prefix = os.path.commonprefix([auxfile_path, root_path])
            if prefix != root_path :
                raise tornado.web.HTTPError(403)
            print " ->",auxfile_path
            if not os.path.isfile(auxfile_path) :
                raise tornado.web.HTTPError(404)

            ### From StaticFileHandler: ###
            stat_result = os.stat(auxfile_path)
            modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

            self.set_header("Last-Modified", modified)
            if "v" in self.request.arguments:
                self.set_header("Expires", datetime.datetime.utcnow() + \
                                    datetime.timedelta(days=365*10))
                self.set_header("Cache-Control", "max-age=" + str(86400*365*10))
            else:
                self.set_header("Cache-Control", "public")
            mime_type, encoding = mimetypes.guess_type(auxfile_path)
            if mime_type:
                self.set_header("Content-Type", mime_type)

            #self.set_extra_headers(path)

            # Check the If-Modified-Since, and don't send the result if the
            # content has not been modified
            ims_value = self.request.headers.get("If-Modified-Since")
            if ims_value is not None:
                date_tuple = email.utils.parsedate(ims_value)
                if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
                if if_since >= modified:
                    self.set_status(304)
                    return

            #if not include_body:
            #    return
            file = open(auxfile_path, "rb")
            try:
                self.write(file.read())
            finally:
                file.close()
            return

        if game not in games :
            self.write("No such game")
            return

        session = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).replace("+", "_")

        if self.get_argument("reload", False) :
            import textadv.gameworld.basiclibrary
            reload(textadv.gameworld.basiclibrary)
            the_game = reload(games[game])
        else :
            the_game = games[game]
        
        if self.get_argument("nolog", False) :
            t = GameThread(game, the_game, session=session, nolog=True)
        else :
            t = GameThread(game, the_game, session=session)
        t.daemon = True
        t.start()
        sessions_lock.acquire()
        sessions[session] = t
        sessions_timer[session] = time.time()
        sessions_lock.release()
        if alt_indices.has_key(game) :
            index_file = os.path.join(os.path.abspath(auxfiles.get(game, "")), alt_indices[game])
        else :
            index_file = 'static/index.html'
        print index_file
        self.render(index_file, session=session)

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
            command = self.get_argument("command", default="")
            t.game_context.io.receive_input(str(command))
            self.write("received")

class OutputHandler(tornado.web.RequestHandler) :
    @tornado.web.asynchronous
    def get(self) :
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "Thu, 01 Jan 1970 00:00:00 GMT")
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
            def _output_handler(vars) :
                tornado.ioloop.IOLoop.instance().add_callback(lambda : self.__finish_output(vars))
            t.game_context.io.register_wants_output(_output_handler)
    def __finish_output(self, vars) :
        self.output_lock.acquire()
        if self.ignore_output :
            print "ignoring output, client has quit"
        else :
            self.ignore_output = True
            self.write(json_encode(vars))
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
            sessions_lock.release()
            return
        else :
            t = sessions[session]
            sessions_timer[session] = time.time()
            sessions_lock.release()
            print "handled ping"

class StatusHandler(tornado.web.RequestHandler) :
    def get(self, args) :
        args = args.split("/")
        result = ""
        if len(args) > 0 :
            if args[0] == "message" :
                s = url_unescape(self.get_argument("session", ""))
                m = url_unescape(self.get_argument("message", ""))
                print "messaging",s,"with",m
                sessions_lock.acquire()
                if m and s in sessions :
                    try :
                        sessions[s].game_context.io.write("<p><b>From admin:</b> %s</p>" % (m,))
                        sessions[s].game_context.io.flush()
                        result += "<p>Messaged %s with \"%s\"</p>" % (xhtml_escape(s), xhtml_escape(m))
                    except Exception as x :
                        result += "<p>Exception %r</p>" % (x,)
                sessions_lock.release()
            elif args[0] == "wactivity" :
                s = url_unescape(self.get_argument("session", ""))
                a = url_unescape(self.get_argument("activity", ""))
                args = [str(s2).strip() for s2 in url_unescape(self.get_argument("arguments", "")).split(",")]
                sessions_lock.acquire()
                print a,s,args
                if a and s in sessions :
                    try :
                        world = sessions[s].game_context.world
                        if a in world._activities :
                            world.call_activity(a, *args)
                            result += "<p>Called %s with args %r for %s.</p>" % (xhtml_escape(a), args, xhtml_escape(s))
                        else :
                            result += "<p>No such world activity %s.</p>" % (xhtml_escape(a))
                    except Exception as x :
                        result += "<p>Exception %r</p>" % (x,)
                sessions_lock.release()
            elif args[0] == "getprop" :
                s = url_unescape(self.get_argument("session", ""))
                p = url_unescape(self.get_argument("property", ""))
                args = [str(s2).strip() for s2 in url_unescape(self.get_argument("arguments", "")).split(",")]
                sessions_lock.acquire()
                print p,s,args
                if p and s in sessions :
                    try :
                        world = sessions[s].game_context.world
                        result += "<p>%s(%s) = %r</p>" % (p,",".join([repr(a) for a in args]),world.get_property(p, *args))
                    except Exception as x :
                        result += "<p>Exception %r</p>" % (x,)
                sessions_lock.release()
            elif args[0] == "setprop" :
                s = url_unescape(self.get_argument("session", ""))
                p = url_unescape(self.get_argument("property", ""))
                args = [str(s2).strip() for s2 in url_unescape(self.get_argument("arguments", "")).split(",")]
                v = str(url_unescape(self.get_argument("value", "")))
                if v == "None" : v = None
                if v == "True" : v = True
                if v == "False" : v = False
                sessions_lock.acquire()
                print p,s,args
                if p and s in sessions :
                    try :
                        world = sessions[s].game_context.world
                        world.set_property(p, *args, value=v)
                        result += "<p>set %s(%s) = %r</p>" % (p,",".join([repr(a) for a in args]),v)
                    except Exception as x :
                        result += "<p>Exception %r</p>" % (x,)
                sessions_lock.release()
            elif args[0] == "log" :
                s = url_unescape(self.get_argument("session", ""))
                print "log for",s
                sessions_lock.acquire()
                if s in sessions :
                    try :
                        fn = sessions[s].logfile_name
                        print fn
                        with open(fn, "r") as f :
                            self.write(f.read())
                            sessions_lock.release()
                            return
                    except Exception as x :
                        result += "<p>Exception %r</p>" % (x,)
                sessions_lock.release()
        sessions_lock.acquire()
        the_sessions = sessions.items()
        sessions_lock.release()
        self.render("static/status.html", result=result, sessions=the_sessions)

application = tornado.web.Application(
    [(r"/", MainHandler),
     (r"/game/(.+)", GameHandler),
     (r"/input", InputHandler),
     (r"/output", OutputHandler),
     (r"/ping", PingHandler),
     (r"/status/(.*)", StatusHandler),
     ],
    static_path=os.path.join(os.path.dirname(__file__), "static"))

import threading

class TornadoGameIO(object) :
    def __init__(self, outfile, frontispiece=None) :
        self.main_lock = threading.BoundedSemaphore(1)
        self.input_lock = threading.Semaphore(0)
        self.to_flush = []
        self.commands = []
        self.to_output = ""
        self.wants_output = None
        self.status_vars = {"prompt" : ">"}
        self.die = False
        self.outfile = outfile
        self.frontispiece = frontispiece
    def register_wants_output(self, callback) :
        self.main_lock.acquire()
        if self.to_output :
            if self.wants_output :
                self.status_vars["text"] = self.to_output
                self.wants_output(self.status_vars)
                self.status_vars = {"prompt" : self.status_vars["prompt"]}
                self.wants_output = callback
                self.to_output = ""
            else :
                self.status_vars["text"] = self.to_output
                callback(self.status_vars)
                self.status_vars = {"prompt" : self.status_vars["prompt"]}
                self.to_output = ""
        else :
            if self.wants_output :
                self.status_vars["text"] = ""
                self.wants_output(self.status_vars)
                self.status_vars = {"prompt" : self.status_vars["prompt"]}
            self.wants_output = callback
        self.main_lock.release()
    def get_input(self, prompt=">") :
        if self.die :
            raise SystemExit("Thread death due to self.die.")
        self.set_status_var("prompt", prompt)
        self.flush()
        self.input_lock.acquire()
        if self.die :
            raise SystemExit("Thread death due to self.die.")
        command = self.commands.pop()
        if self.frontispiece :
            print "[%s %s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),self.frontispiece,command)
        self.main_lock.acquire()
        if self.outfile :
            self.outfile.write("\n\n<p><b>"+self.status_vars["prompt"] + " "+command+"</b></p>")
            self.outfile.flush()
        self.main_lock.release()
        return command
    def set_status_var(self, key, value) :
        self.main_lock.acquire()
        self.status_vars[key] = value
        self.main_lock.release()
    def kill_io(self) :
        self.main_lock.acquire()
        self.die = True
        if self.wants_output :
            self.status_vars["text"] = "<i>Error: timeout</i>"
            self.wants_output(self.status_vars)
            self.status_vars = {"prompt" : self.status_vars["prompt"]}
            self.wants_output = None
        if self.outfile :
            self.outfile.flush()
            self.outfile.close()
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
        if self.outfile :
            self.outfile.write("\n\n<p>"+out+"</p>")
            self.outfile.flush()
        if self.wants_output :
            self.status_vars["text"] = self.to_output
            self.wants_output(self.status_vars)
            self.status_vars = {"prompt" : self.status_vars["prompt"]}
            self.to_output = ""
            self.wants_output = None
        self.main_lock.release()

class GameThread(threading.Thread) :
    def __init__(self, gamename, game, session, nolog=False) :
        self.gamename = gamename
        self.game = game
        dirname = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(dirname) :
            os.mkdir(dirname)
        if nolog :
            logfile = None
            self.logfile_name = None
        else :
            self.logfile_name = os.path.abspath(os.path.join(dirname, gamename+"_"+url_escape(session)+".html"))
            logfile = open(self.logfile_name, "w")
        self.game_context = self.game.make_actorcontext_with_io(TornadoGameIO(logfile, frontispiece=session[0:8]))
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
    port = 8888
    if len(sys.argv) > 1 :
        port = int(sys.argv[1])
    watchdog = WatchdogThread()
    watchdog.daemon = True
    watchdog.start()
    application.listen(port)
    print "Running loop."
    tornado.ioloop.IOLoop.instance().start()
