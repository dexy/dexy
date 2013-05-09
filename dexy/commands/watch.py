import time
import logging
from dexy.commands.it import dexy_command

try:
    # Requires patched watchdog from https://github.com/ananelson/watchdog
    # or https://github.com/gorakhargosh/watchdog/pull/161
    from watchdog.observers import Observer
    from watchdog.events import LoggingEventHandler
    from watchdog.events import PatternMatchingEventHandler
    AVAILABLE = True
except ImportError:
    class PatternMatchingEventHandler:
        """
        Dummy class so everything doesn't have to be wrapped in try/catch block.
        """
        pass

    AVAILABLE = False

class DexyEventHandler(PatternMatchingEventHandler):
    last_dexy_run = None

    # hack to handle multiple change events at a time - so each one doesn't
    # trigger a separate dexy rebuild
    seconds_between_runs = 0.5

    def on_any_event(self, event):
        if (time.time() - self.last_dexy_run) > self.seconds_between_runs:
            print "running dexy because", event.src_path, "changed"
            dexy_command()
            self.last_dexy_run = time.time() 

def watch_command():
    """
    Sets up a watch to automatically run dexy if any files change.
    (using FORK of watchdog - https://github.com/ananelson/watchdog)
    """
    print "running dexy..."
    dexy_command()
    print "dexy is watching for changes to files"
    path = "."

    # TODO add all directories which dexy writes to
    event_handler = DexyEventHandler(patterns=["*.*"], ignore_patterns=[
        "*/.trash", "*/.trash/*", "*/.cache/*", "*/logs/dexy.log", "*/output-site/*", "*/output/*",
        "*/output-long/*"
        ]
        )

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    event_handler.last_dexy_run = time.time()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception:
        print "an exception happened!"
    observer.join()

def watchdemo_command():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = "."
    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
