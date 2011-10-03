from PythonMagick import Image
from PythonMagick import _PythonMagick
from dexy.dexy_filter import DexyFilter

class PythonMagickFilter(DexyFilter):
    """Base class which reads previous artifact, calls a do_magick method,
    saves the output. Can be inherited. Default action is to flip an image,
    pointless in itself but a useful demo to know things are working."""
    OUTPUT_EXTENSIONS = [".png"]
    INPUT_EXTENSIONS = [".png"]
    ALIASES = ['pm-flip']
    BINARY = True

    def do_magick(self, image):
        image.flip()

    def process(self):
        wf = str(self.artifact.previous_artifact_filepath) # complains when unicode
        image = Image()
        image.read(wf)
        self.do_magick(image)
        image.write(self.artifact.filepath())

class MagickFlopFilter(PythonMagickFilter):
    ALIASES = ['pm-flop']

    def do_magick(self, image):
        image.flop()

class MagickGridFilter(PythonMagickFilter):
    ALIASES = ['pm-grid']
    # This does not work due to PythonMagick issues, maybe fixed in later version of PM?
    def do_magick(self, image):
        for i in xrange(10, 100, 10):
            for j in xrange(10, 100, 10):
                print "i: %s j: %s" % (i, j)
                dl = _PythonMagick.DrawableLine(0, 0, i, j)
                image.draw(dl)


