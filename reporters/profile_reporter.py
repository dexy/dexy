from dexy.reporter import Reporter
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

    REPORTS_DIR = 'logs/profile'
    DB_FILE = "profile.sqlite"
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

        f = open(os.path.join(report_dir, "index.html"), "w")

        if self.controller.args.profile:
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

                if i < 50:
                    # TODO use a HTML template instead of this.
                    short_filename = os.path.basename(filename)
                    f.write("<h2>%s) %s:%s</h2>\n" % (i+1, cgi.escape(short_filename), cgi.escape(functionname)))
                    f.write("<ul>\n")
                    f.write("<li>%s : %s</li>\n" % (filename, lineno))
                    f.write("<li>%s</li>\n" % cgi.escape(functionname))
                    f.write("<li>Function called %s times (%s primitive calls).</li>\n" % (ncalls, primcalls) )
                    f.write("<li>Total time in function %0.4f (%0.4f per call)</li>\n" % (tottime, totpercall) )
                    f.write("<li>Cumulative time in function %0.4f (%0.4f per call)</li>\n" % (cumtime, cumpercall) )
                    f.write("</ul>\n")

                    hist = []
                    f.write("<table style=\"font-family: Courier; width: 400px;\">\n<tr><th>timestamp</th><th>cumtime</th></tr>\n")
                    for row in db.select("profiles",
                            where=("filename=\"%s\" AND functionname=\"%s\"" % (filename, functionname)),
                            order=("batchtimestamp ASC")
                            ):
                        f.write("<tr><td>%s</td><td style=\"text-align:right;\">%0.4f</td></tr>\n" % (row.batchtimestamp, row.cumtime))
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

            shutil.copytree(report_dir, latest_dir)

