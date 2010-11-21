#!/usr/bin/env python
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

try:
    import json # Included in Python 2.6 and up
except ImportError:
    import simplejson as json # For Python 2.5

import os
import re
import shutil
import sys
from dexy.version import VERSION


EXCLUDED_DIRS = ['.bzr', '.hg', '.git', '.svn', 'ignore']
EXCLUDE_DIR_HELP = """Exclude directories from processing by dexy, only relevant
if recursing. The directories designated for artifacts, logs and cache are
automatically excluded, as are %s.
""" % ", ".join(EXCLUDED_DIRS)


def setup_option_parser():
    project_base = os.path.abspath(os.curdir)
    os.chdir(project_base)

    def add_option(parser, *args, **kwargs):
        if hasattr(parser, 'add_option'):
            parser.add_option(*args, **kwargs)
        else:
            parser.add_argument(*args, **kwargs)
    
    try:
        import argparse
        option_parser = 'argparse'
        parser = argparse.ArgumentParser()
        
        parser.add_argument(
            'dir',
            help='directory of files to process with dexy'
        )
    
        parser.add_argument(
            '-x', '--exclude-dir',
            help=EXCLUDE_DIR_HELP,
            nargs='+'
        )
    
        parser.add_argument(
            '-v', '--version', 
            action='version', 
            version='%%(prog)s %s' % VERSION
        )
    
    except ImportError:
        import optparse
        option_parser = 'optparse'
        parser = optparse.OptionParser(version="%%prog %s" % VERSION)
        parser.add_option(
            '-x', '--exclude-dir',
            help=EXCLUDE_DIR_HELP + ' Separate multiple directories with commas.'
        )
    
    add_option(parser,
        '-n', '--no-recurse',
        dest='recurse',
        default=True,
        action='store_false',
        help='do not recurse into subdirectories (default: recurse)'
    )
    
    add_option(parser,
        '-u', '--utf8',
        default=False,
        action='store_true',
        help='switch encoding to UTF-8 (default: don\'t change encoding)'
    )
    
    add_option(parser,
        '-p', '--purge',
        default=False,
        action='store_true',
        help='purge the artifacts and cache directories before running dexy'
    )
    
    add_option(parser,
        '-a', '--artifacts-dir',
        default='artifacts',
        help='location of artifacts directory (default: artifacts)'
    )
    
    add_option(parser,
        '-l', '--logs-dir',
        default='logs',
        help='location of logs directory (default: logs) dexy will create a dexy.log file in this directory'
    )
    
    add_option(parser,
        '-c', '--cache-dir',
        default='cache',
        help='location of cache directory (default: cache)'
    )
    
    add_option(parser,
        '-s', '--short',
        default=False,
        action='store_true',
        help='Use short names in cache'
        )
    
    add_option(parser,
        '--setup',
        default=False,
        action='store_true',
        help='Create artifacts and logs directory and generic .dexy file'
        )

    if (option_parser == 'argparse'):
        args = parser.parse_args()
        dir_name = args.dir
        if args.exclude_dir:
            exclude_dir = args.exclude_dir
        else:
            exclude_dir = []
    
    elif (option_parser == 'optparse'):
        (args, argv) = parser.parse_args()
        dir_name = argv[0]
        if args.exclude_dir:
            exclude_dir = args.exclude_dir.split(',')
        else:
            exclude_dir = []
    else:
        raise Exception("unexpected option_parser %s" % option_parser)
    
    
    if args.utf8:
        if (sys.getdefaultencoding() == 'UTF-8'):
            print "encoding is already UTF-8"
        else:
            print "changing encoding from %s to UTF-8" % sys.getdefaultencoding()
            reload(sys)
            sys.setdefaultencoding("UTF-8")
    
    if not os.path.exists(dir_name):
        raise Exception("file %s not found!" % dir_name)

    if args.setup:
        if not os.path.exists(args.artifacts_dir):
            os.mkdir(args.artifacts_dir)
        if not os.path.exists(args.logs_dir):
            os.mkdir(args.logs_dir)
        if not os.path.exists(".dexy"):
            f = open(".dexy", "w")
            f.write("{\n}\n")
            f.close()

    if not os.path.exists(args.artifacts_dir):
        path_to_artifacts_dir = os.path.join(project_base, args.artifacts_dir)
        raise Exception(
            """artifacts directory not found at %s,
            please create a directory called %s if you want to use
            this location as a dexy project root""" % (path_to_artifacts_dir, args.artifacts_dir)
        )
    
    if not os.path.exists(args.logs_dir):
        path_to_logs_dir = os.path.join(project_base, args.logs_dir)
        raise Exception(
            """logs directory not found at %s,
            please create a directory called %s if you want to use
            this location as a dexy project root""" % (path_to_logs_dir, args.logs_dir)
        )


    if args.purge:
        log.warn("purging contents of %s" % args.artifacts_dir)
        shutil.rmtree(args.artifacts_dir)
        os.mkdir(args.artifacts_dir)
        
        if os.path.exists(args.cache_dir): 
            log.warn("purging contents of %s" % args.cache_dir)
            shutil.rmtree(args.cache_dir)
            os.mkdir(args.cache_dir)
    
    return args, dir_name, exclude_dir


def dexy_command():
    args, dir_name, exclude_dir = setup_option_parser()

    # Only import these after making sure log dir exists
    from dexy.controller import Controller
    from dexy.logger import log 

    do_not_process_dirs = EXCLUDED_DIRS
    do_not_process_dirs += exclude_dir
    do_not_process_dirs.append(args.artifacts_dir)
    do_not_process_dirs.append(args.logs_dir)
    do_not_process_dirs.append(args.cache_dir)

    if args.recurse:
        log.info("running dexy with recurse")
        for root, dirs, files in os.walk(dir_name):
            process = True
            log.info("skipping directories named %s" % ", ".join(do_not_process_dirs))
            for x in do_not_process_dirs:
                if re.search(x, root):
                    process = False
                    break
    
            if not process:
                log.warn("skipping dir %s" % root)
            else:
                log.info("processing dir %s" % root)
                controller = Controller()
                controller.artifacts_dir = args.artifacts_dir
                for doc in controller.setup_and_run(root):
                    artifact = doc.artifacts[-1]
                    output_name = artifact.output_name(args.short)
                    log.info("saving %s to cache/%s" % (artifact.filename(), output_name))
                    artifact.write_cache_output_file(args.cache_dir, args.short)
    else:
        log.info("not recursing")
        log.info("processing dir %s" % dir_name)
        controller = Controller()
        controller.artifacts_dir = args.artifacts_dir
        for doc in controller.setup_and_run(dir_name):
            artifact = doc.artifacts[-1]
            output_name = artifact.output_name(args.short)
            log.info("saving %s to cache/%s" % (artifact.key, output_name))
            artifact.write_cache_output_file(args.cache_dir, args.short)


def dexy_live_server():
    args, dir_name, exclude_dir = setup_option_parser()

    # Only import these after making sure log dir exists
    from dexy.controller import Controller
    from dexy.logger import log 

    from mongrel2 import handler
    import signal
    
    def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    print 'Press Ctrl+C to Exit (may not take effect until next request received)'
    
    # TODO pass sender id, ports as options
    sender_id = "faffe356-ad9d-4ec1-ba74-09d784cf85a0"
    
    conn = handler.Connection(
        sender_id, 
        "tcp://127.0.0.1:9999",
        "tcp://127.0.0.1:9998"
    )
    
    from dexy.utils import ansi_output_to_html
    
    while True:
        print "WAITING FOR REQUEST"
    
        req = conn.recv()
    
        if req.is_disconnect():
            print "DISCONNECT"
            continue
        
        print req.path
        log.info("req.path: %s" % req.path)
        a = req.path
        while len(a) > 0 and a[0] == '/':
            a = a[1:]
    
        log.info("a: %s" % a)
    
        if not a:
          a = '.'
    
        if os.path.isdir(a):
            a_is_dir = True
            a_dir = a
        else:
            a_is_dir = False
            a_dir = os.path.dirname(a)
    
        if not a_dir:
          a_dir = '.'
    
        # Run Dexy, store array of artifacts
        artifacts = OrderedDict()
        controller = Controller()
        controller.artifacts_dir = args.artifacts_dir
        try:
            for doc in controller.setup_and_run(a_dir):
                artifact = doc.artifacts[-1]
                artifacts[artifact.output_name(args.short)] = artifact
            error = False
        except Exception as e:
            print e
            error_message = ""
            error_message += "<h1>%s</h1>" % type(e).__name__
            for line in sys.exc_info():
                error_message += "<pre>%s</pre>" % line
            log.warn(error_message)
            error = True
        
        if error:
            # TODO 500?
            response_text = error_message
        elif artifacts.has_key(a):
            # render the processed file
    	    log.debug(artifacts[a].filename())
    	    response_text = open(artifacts[a].filename(), "r").read()
        elif os.path.exists(a) and not a_is_dir:
            # render the raw source file
            response_text = open(a, "r").read()
        elif a_is_dir:
            # render a list of files
            response_text = "<html><body><h1>%s</h1>" % os.path.abspath(a)
    
    	    # List subdirectories.
    	    response_text += "<h2>Subdirectories</h2><ul>"
    	    for f in os.listdir(a):
    	        if os.path.isdir(f):
    	    	 url = os.path.join(req.path, f)
    	    	 response_text += """<li><a href="%s">%s</a></li>""" % (url, f)
    	    response_text += "</ul>"
    
            if len(artifacts) > 0:
    	        response_text += "<h2>Dexy Artifacts</h2><ul>"
                # TODO sort artifacts alphabetically
                for k, artifact in artifacts.items():
                    response_text += """<li><a href="/%s">%s</a></li>""" % (artifact.output_name(), artifact.doc.key())
                    if hasattr(artifact, 'stdout'):
                        stdout = ansi_output_to_html(artifact.stdout)
                        response_text += """<pre>\n%s\n</pre>""" % stdout
                response_text += "</ul>"
            response_text += "</body></html>"
        else:
            # TODO make a real 404
            response_text = "404 not found!"
    
        response = "<pre>\nSENDER: %r\nIDENT:%r\nPATH: %r\nHEADERS:%r\nBODY:%r</pre>" % (
            req.sender, req.conn_id, req.path, 
            json.dumps(req.headers), req.body)
        response += response_text 
        conn.reply_http(req, response_text)
    
