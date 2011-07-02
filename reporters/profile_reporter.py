from dexy.reporter import Reporter
import datetime
import lib.aplotter as aplotter
import os
import pstats
import shutil
import sqlite3
import uuid
import web

try:
    import matplotlib.pyplot as pyplot
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    MATPLOTLIB_AVAILABLE = False

class ProfileReporter(Reporter):

    REPORTS_DIR = 'logs/profile'
    DB_FILE = "profile.sqlite"
    DB_PATH = os.path.join(REPORTS_DIR, DB_FILE)

    def run(self):
        web.config.debug = False

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
        os.mkdir(report_dir)

        f = open(os.path.join(report_dir, "profile.html"), "w")


        # TODO this should only be run when we are actually profiling...
        if os.path.exists('dexy.prof'):
            p = pstats.Stats('dexy.prof')

            p.sort_stats('cumulative')
            for i, x in enumerate(p.fcn_list):
                filename, lineno, functionname = x
                ncalls, primcalls, tottime, cumtime, _ = p.stats[x]
                totpercall = tottime/ncalls
                cumpercall = cumtime/primcalls


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

                if i < 15:
                    f.write("<h2>%s</h2>\n" % functionname)

                    hist = []
                    f.write("<table style=\"font-family: Courier;\">\n<tr><th>timestamp</th><th>cumtime</th></tr>\n")
                    for row in db.select("profiles",
                            where=("filename=\"%s\" AND functionname=\"%s\"" % (filename, functionname)),
                            order=("batchtimestamp ASC")
                            ):
                        f.write("<tr><td>%s</td><td>%s</td></tr>\n" % (row.batchtimestamp, row.cumtime))
                        hist.append(row.cumtime)

                    f.write("</table>\n")
                    if MATPLOTLIB_AVAILABLE:
                        pyplot.clf()
                        pyplot.plot(hist)
                        figfilename = "%s.png" % str(uuid.uuid4())
                        figfile = open(os.path.join(report_dir, figfilename), "wb")
                        pyplot.savefig(figfile)
                        figfile.close()
                        f.write("<img src=\"%s\" />" % figfilename)

                    try:
                        f.write("<pre>\n%s\n</pre>" % aplotter.plot(hist))
                    except Exception as e:
                        pass

            f.close()

            latest_dir = os.path.join(self.REPORTS_DIR, "profile-latest")
            shutil.rmtree(latest_dir, ignore_errors = True)
            shutil.copytree(report_dir, latest_dir)

