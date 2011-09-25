from dexy.reporter import Reporter
from jinja2 import Environment
from ordereddict import OrderedDict
from jinja2 import FileSystemLoader
import cgi # for escape
import datetime
import dexy.aplotter as aplotter
import os
import pstats
import shutil
import sqlite3
import uuid
import web

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as pyplot
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    MATPLOTLIB_AVAILABLE = False

class ProfileReporter(Reporter):
    DB_FILE = "profile.sqlite"
    DEFAULT = False
    REPORTS_DIR = 'logs/profile'
    DB_PATH = os.path.join(REPORTS_DIR, DB_FILE)

    def run(self):
        web.config.debug = False

        latest_dir = os.path.join(self.REPORTS_DIR, "profile-latest")
        shutil.rmtree(latest_dir, ignore_errors = True)

        if not os.path.exists(self.REPORTS_DIR):
            os.mkdir(self.REPORTS_DIR)

        db = web.database(dbn='sqlite', db=self.DB_PATH)
        try:
            db.query("""CREATE TABLE profiles(
                batchtimestamp text,
                filename text,
                lineno integer,
                functionname text,
                ncalls integer,
                primcalls integer,
                tottime real,
                cumtime real
            );""")
        except sqlite3.OperationalError:
            # table already exists, this is fine.
            pass

        ts = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        report_dir = os.path.join(self.REPORTS_DIR, "profile-%s" % ts)
        # Avoid collisions if we run Dexy more than once per second...
        i = 65
        while os.path.exists(report_dir):
            ts = "%s-%s" % (ts, chr(i))
            i += 1
            report_dir = os.path.join(self.REPORTS_DIR, "profile-%s" % ts)
        os.mkdir(report_dir)

        if self.controller.args.profile:
            p = pstats.Stats('dexy.prof')
            p.sort_stats('cumulative')

            env = Environment()
            env.loader = FileSystemLoader(os.path.dirname(__file__))
            template = env.get_template('profile_reporter_template.html')

            function_data = OrderedDict()
            overall_tot_time = 0
            p.print_callers()
            for i, x in enumerate(p.fcn_list):
                filename, lineno, functionname = x
                ncalls, primcalls, tottime, cumtime, _ = p.stats[x]
                totpercall = tottime/ncalls
                cumpercall = cumtime/primcalls
                overall_tot_time += tottime

                # insert data from this run into db
                db.insert("profiles",
                    batchtimestamp=ts,
                    filename=filename,
                    lineno=lineno,
                    functionname=functionname,
                    ncalls=ncalls,
                    primcalls=primcalls,
                    tottime=tottime,
                    cumtime=cumtime
                    )

                short_filename = os.path.basename(filename)
                function_id = "%s:%s" % (cgi.escape(short_filename), cgi.escape(functionname))

                hist_rows = db.select("profiles",
                    where=("filename=\"%s\" AND functionname=\"%s\"" % (filename, functionname)),
                    order=("batchtimestamp ASC")
                )

                cumtime_hist = []
                tottime_hist = []
                for row in hist_rows:
                    cumtime_hist.append(row.cumtime)
                    tottime_hist.append(row.tottime)

                if MATPLOTLIB_AVAILABLE and i < 10:
                    pyplot.clf()
                    pyplot.plot(cumtime_hist)
                    cumtime_fig_filename = "%s.png" % str(uuid.uuid4())
                    figfile = open(os.path.join(report_dir, cumtime_fig_filename), "wb")
                    pyplot.savefig(figfile)
                    figfile.close()

                    pyplot.clf()
                    pyplot.plot(tottime_hist)
                    tottime_fig_filename = "%s.png" % str(uuid.uuid4())
                    figfile = open(os.path.join(report_dir, tottime_fig_filename), "wb")
                    pyplot.savefig(figfile)
                    figfile.close()
                else:
                    cumtime_fig_filename = None
                    tottime_fig_filename = None

                try:
                    cumtime_text_plot = aplotter.plot(cumtime_hist)
                    tottime_text_plot = aplotter.plot(tottime_hist)
                    raise Exception()
                except Exception as e:
                    cumtime_text_plot = None
                    tottime_text_plot = None

                function_data[function_id] = {
                    'functionname' : cgi.escape(functionname),
                    'ncalls' : ncalls,
                    'primcalls' : primcalls,
                    'filename' : filename,
                    'lineno' : lineno,
                    'tottime' : tottime,
                    'totpercall' : totpercall,
                    'cumtime' : cumtime,
                    'cumpercall' : cumpercall,
                    'cumtime_hist' : cumtime_hist,
                    'tottime_hist' : tottime_hist,
                    'cumtime_fig_filename' : cumtime_fig_filename,
                    'tottime_fig_filename' : tottime_fig_filename,
                    'cumtime_text_plot' : cumtime_text_plot,
                    'tottime_text_plot' : tottime_text_plot
                }

            env_data = {
                'function_data' : function_data,
                'overall_tot_time' : overall_tot_time
            }
            template.stream(env_data).dump(os.path.join(report_dir, 'index.html'))
            shutil.copytree(report_dir, latest_dir)

