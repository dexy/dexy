from dexy.dexy_filter import DexyFilter
import gdata.photos.service
import json
import mimetypes
import os

class PicasaFilter(DexyFilter):
    # TODO can support other input formats, but they get converted to jpeg, need to test implications
    # However within Dexy you should be able to control what format to produce.
    INPUT_EXTENSIONS = ['.jpg']
    OUTPUT_EXTENSIONS = ['.json']
    ALIASES = ['picasa']
    CONFIG_FILE = 'picasa-config.json'
    DEFAULT_CONF = {
        "access" : 'public', # You can set this to access : private in your config.
        "license" : None # Need to figure out how to specify license info.
    }

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE):
            raise Exception("Could not find config file called %s" % self.CONFIG_FILE)

        self.conf = self.DEFAULT_CONF
        f = open(self.CONFIG_FILE, "r")
        self.conf.update(json.load(f))
        f.close()

    def process_text(self, input_text):
        self.load_config()

        client = gdata.photos.service.PhotosService()

        client.email = self.conf['email']
        client.password = self.conf['password']
        client.source = 'dexy'
        client.ProgrammaticLogin()

        album_name = "Dexy: %s" % self.conf['project']

        # If an album for this project already exists, get it. Otherwise, create a new one.
        albums = client.GetUserFeed('album')

        username = albums.user.text
        matching_albums = [album for album in albums.entry if album.title.text == album_name]
        if len(matching_albums) == 0:
            print "Creating a new %s Picasa album called %s" % (self.conf['access'], album_name)
            album = client.InsertAlbum(
                    album_name,
                    "Files automatically uploaded by Dexy for the %s project." % self.conf['project'],
                    access=self.conf['access']
                    )
        else:
            album = matching_albums[0]


        photo_key = self.artifact.key.replace("/", "--")
        filename = self.artifact.previous_artifact_filepath
        mimetype = mimetypes.guess_type(filename)[0]

        # If a photo with this title in this album already exists, replace it. Otherwise, start from scratch.
        photos = client.GetUserFeed("photo")
        photo = None
        for photo in photos.entry:
            photo_in_album = album.id.text.split("/")[-1] == photo.albumid.text
            photo_tagged_dexy = photo.media.keywords and 'dexydocs' in photo.media.keywords.text
            title_matches = photo.title.text == photo_key

            if photo_in_album and photo_tagged_dexy and title_matches:
                break
            else:
                photo = None

        if photo:
            client.UpdatePhotoBlob(photo, filename, content_type=mimetype)
        else:
            photo = client.InsertPhotoSimple(album, photo_key, "", filename, content_type=mimetype)
            photo.media.keywords = gdata.media.Keywords()
            photo.media.keywords.text = "dexydocs"
            # TODO support geolocation to show where research is taking place
            client.UpdatePhotoMetadata(photo)

        photo_data = {
            "id" : photo.gphoto_id.text,
            "height" : photo.height.text,
            "width" : photo.width.text,
            "src" : photo.content.src,
            "url" : photo.GetHtmlLink().href
        }

        return json.dumps(photo_data)

