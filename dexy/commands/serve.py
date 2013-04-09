import SimpleHTTPServer
import SocketServer
import dexy.reporter
import socket
import os
import sys
from dexy.utils import file_exists

NO_OUTPUT_MSG = """Please run dexy first, or specify a directory to serve. \
For help run 'dexy help -on serve'"""

def serve_command(
        port=-1,
        reporters=['ws', 'output'], # Reporters whose output to try to serve (in order).
        directory=False # Custom directory to be served.
        ):
    """
    Runs a simple web server on dexy-generated files. Will look first to see if
    the Website Reporter has run, if so this content is served. If not the
    standard output/ directory contents are served. You can also specify
    another directory to be served. The port defaults to 8085, this can also be
    customized.
    """
    if not directory:
        for alias in reporters:
            reporter = dexy.reporter.Reporter.create_instance(alias)
            if file_exists(reporter.setting('dir')):
                directory = reporter.setting('dir')
                break

    if not directory:
        print NO_OUTPUT_MSG
        sys.exit(1)

    os.chdir(directory)

    if port < 0:
        ports = range(8085, 8100)
    else:
        ports = [port]

    p = None
    for p in ports:
        try:
            Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
            httpd = SocketServer.TCPServer(("", p), Handler)
        except socket.error:
            print "port %s already in use" % p
            p = None
        else:
            break

    if p:
        print "serving contents of %s on http://localhost:%s" % (directory, p)
        print "type ctrl+c to stop"
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.exit(1)
    else:
        print "could not find a free port to serve on, tried", ports
        sys.exit(1)
