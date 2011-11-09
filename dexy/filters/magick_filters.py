from dexy.dexy_filter import DexyFilter
from kaa import imlib2
import re

class Imlib2Filter(DexyFilter):
    """
    Base class which reads previous artifact, calls a do_im method, saves the
    output. Can be inherited. Default action is to flip an image, pointless in
    itself but a useful demo to know things are working.
    """
    ALIASES = ['im-flipv']
    BINARY = True
    FINAL = True
    FONT_PATHS = ["/usr/share/fonts/truetype/", "/usr/share/fonts/truetype/freefont/"]
    INPUT_EXTENSIONS = [".png", ".jpg", ".gif", ".tiff", ".bmp"]
    OUTPUT_EXTENSIONS = [".png", ".jpg", ".gif", ".tiff", ".bmp"]

    def do_im(self, image):
        image.flip_vertical()

    def process(self):
        font_paths = self.FONT_PATHS
        if self.artifact.args.has_key('font-path'):
            font_paths.extend(self.artifact.args['font-path'])

        for path in font_paths:
            imlib2.add_font_path(path)

        self.default_font = imlib2.load_font("FreeSans", 20)

        wf = self.artifact.previous_artifact_filepath
        image = imlib2.open(wf)
        new_image = self.do_im(image)

        # Most of the time, we can just modify the image in do_im, but in some
        # cases we need to return a new image object, i.e. when cropping. So,
        # if do_im returns anything replace the image with the returned image.
        if new_image:
            image = new_image

        image.save(self.artifact.filepath())

class Imlib2FlipHorizontalFilter(Imlib2Filter):
    ALIASES = ['im-fliph']

    def do_im(self, image):
        image.flip_horizontal()

class Imlib2GridFilter(Imlib2Filter):
    ALIASES = ['im-grid']

    def do_im(self, image):
        line_width = 3

        # draw vertical lines
        for i in xrange(100, image.width, 100):
            image.draw_rectangle((i, 0), (line_width, image.height), (0, 255, 0))
            image.draw_text((i+10, 0), "%s" % i, (255,0,0), self.default_font)

        # draw horizontal lines
        for j in xrange(100, image.height, 100):
            image.draw_rectangle((0, j), (image.width, line_width), (0, 0, 255))
            image.draw_text((0, j+10), "%s" % j, (255,0,0), self.default_font)

        for i in xrange(500, image.width, 500):
            for j in xrange(500, image.height, 500):
                image.draw_ellipse((i, j), (10, 10), (255,0,0))
                image.draw_text((i+15, j+15), "(%s,%s)" % (i, j), (255,0,0), self.default_font)

class Imlib2ScaleFilter(Imlib2Filter):
    ALIASES = ['im-scale']

    def do_im(self, image):
        if self.artifact.args.has_key('im-scale'):
            region_width, region_height = self.artifact.args['im-scale'].split("x")
        else:
            self.log.debug("Using default cropping region for im-scale, specify in args if you want something else")
            region_width=500
            region_height=500

        image = image.scale((int(region_width), int(region_height)))
        return image

class Imlib2Crop(Imlib2Filter):
    ALIASES = ['im-crop']

    def do_im(self, image):
        if self.artifact.args.has_key('im-crop'):
            crop_args = self.artifact.args['im-crop']
            regex = "([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)"
            if not re.match(regex, crop_args):
                raise Exception("Specify im-crop like 300x300+50+50.")

            region_size, start_x, start_y = crop_args.split("+")
            region_width, region_height = region_size.split("x")
            self.log.debug("Using custom cropping region for im-crop of width: %s height: %s x: %s y: %s" % (region_width, region_height, start_x, start_y))
        else:
            self.log.debug("Using default cropping region for im-crop, specify in args if you want something else")
            region_width=500
            region_height=500
            start_x=100
            start_y=100

        image = image.crop((int(start_x), int(start_y)), (int(region_width), int(region_height)))
        return image

class Imlib2Thumb(Imlib2Filter):
    ALIASES = ['im-thumb']

    def do_im(self, image):
        text_top = None
        width = None

        if self.artifact.args.has_key('im-thumb'):
            region_size, start_x, start_y = self.artifact.args['im-thumb']['crop'].split("+")
            region_width, region_height = region_size.split("x")
            text = self.artifact.args['im-thumb']['title']

            if self.artifact.args['im-thumb'].has_key('width'):
                width = self.artifact.args['im-thumb']['width']
            if self.artifact.args['im-thumb'].has_key('text-top'):
                text_top = self.artifact.args['im-thumb']['text-top']
        else:
            self.log.debug("Using default cropping region and text for im-thumb, specify in args if you want something else")
            region_width=500
            region_height=500
            start_x=100
            start_y=100
            text="Example"

        if not text_top:
            text_top = 10
        if not width:
            width=150 #final width

        image = image.crop((int(start_x), int(start_y)), (int(region_width), int(region_height)))
        image = image.scale((width, width))

        text_left = len(text)/2+30

        # Draw mock blank text to calculate height + width of text
        t_w, t_h, t_ha, t_va = image.draw_text((text_left, text_top), text, (255,255,255), self.default_font)

        # Draw white ellipse bigger than the ellipse people will see so it
        # doesn't run into neighboring text confusingly
        image.draw_ellipse((text_left+t_w/2, text_top+t_h/2), (t_w/2+25, t_h/2+20), (255,255,255), True)

        # Draw background ellipse
        image.draw_ellipse((text_left+t_w/2, text_top+t_h/2), (t_w/2+10, t_h/2+5), (238,221,130), True)

        # Draw actual text on top of ellipse
        image.draw_text((text_left, text_top), text, (0,0,0), self.default_font)

        return image

