from dexy.commands.utils import init_wrapper
from dexy.utils import file_exists
import dexy.load_plugins
import dexy.reporter
import http.server
import os
import socket
import socketserver
import sys

NO_OUTPUT_MSG = """Please run dexy first, or specify a directory to serve. \
For help run 'dexy help -on serve'"""

class SimpleHTTPAuthRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        if self.headers.getheader('Authorization') == None:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="%s"' % self.__class__.realm)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("no authorization received")

        elif self.headers.getheader('Authorization') != "Basic %s" % self.__class__.authcode:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="%s"' % self.__class__.realm)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("not authenticated")

        else:
            path = self.translate_path(self.path)
            f = None
            if os.path.isdir(path):
                if not self.path.endswith('/'):
                    # redirect browser - doing basically what apache does
                    self.send_response(301)
                    self.send_header("Location", self.path + "/")
                    self.end_headers()
                    return None
                for index in "index.html", "index.htm":
                    index = os.path.join(path, index)
                    if os.path.exists(index):
                        path = index
                        break
                else:
                    return self.list_directory(path)
            ctype = self.guess_type(path)
            try:
                # Always read in binary mode. Opening files in text mode may cause
                # newline translations, making the actual size of the content
                # transmitted *less* than the content-length!
                f = open(path, 'rb')
            except IOError:
                self.send_error(404, "File not found")
                return None
            self.send_response(200)
            self.send_header("Content-type", ctype)
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f

def serve_command(
        port=-1,
        reporters=['ws', 'output'], # Reporters whose output to try to serve (in order).
        username='', # http auth username to use (if provided)
        password='', # http auth password to use (if provided)
        realm='Dexy', # http auth realm to use (if username and password are provided)
        directory=False, # Custom directory to be served.
        **kwargs
        ):
    """
    Runs a simple web server on dexy-generated files.
    
    Will look first to see if the Website Reporter has run, if so this content
    is served. If not the standard output/ directory contents are served. You
    can also specify another directory to be served. The port defaults to 8085,
    this can also be customized. If a username and password are provided, uses
    HTTP auth to access pages.
    """

    if not directory:
        wrapper = init_wrapper(locals(), True)

        for alias in reporters:
            report_dir = dexy.reporter.Reporter.create_instance(alias).setting("dir")
            print("report dir", report_dir)
            if report_dir and file_exists(report_dir):
                directory = report_dir
                break

    if not directory:
        print(NO_OUTPUT_MSG)
        sys.exit(1)

    os.chdir(directory)

    if port < 0:
        ports = range(8085, 8100)
    else:
        ports = [port]

    p = None
    for p in ports:
        try:
            if username and password:
                import base64
                authcode = base64.b64encode("%s:%s" % (username, password))
                Handler = SimpleHTTPAuthRequestHandler
                Handler.authcode = authcode
                Handler.realm = realm
            else:
                Handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", p), Handler)
        except socket.error:
            print("port %s already in use" % p)
            p = None
        else:
            break

    if p:
        print("serving contents of %s on http://localhost:%s" % (directory, p))
        if username and password and Handler.authcode:
            print("username '%s' and password '%s' are required to access contents" % (username, password))
        print("type ctrl+c to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.exit(1)
    else:
        print("could not find a free port to serve on, tried", ports)
        sys.exit(1)
