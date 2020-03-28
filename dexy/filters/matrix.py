from dexy.filters.api import ApiFilter
from bs4 import BeautifulSoup
import asyncio

try:
    from nio import AsyncClient
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

async def main_nio(homeserver, user, password, room_id, content):
    client = AsyncClient(homeserver, user)

    await client.login(password)
    await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content=content
    )
    await client.close()

class MatrixFilter(ApiFilter):
    """
    Filter for posting text to a matrix room. Uses matrix-nio
    """
    aliases = ['matrix']

    _settings = {
            'room-id' : ("The room id (NOT the room name!) to post to.", "!yMPKbtdRlqJWpwCcvg:matrix.org"),
            'api-key-name' : 'matrix',
            'input-extensions' : ['.*'],
            'output-extensions' :  ['.txt']
            }

    def is_active(self):
        return AVAILABLE

    def process_text(self, text):
        if self.input_data.ext in ('.html'):
            soup = BeautifulSoup(text, 'html.parser')
            content = {
                    'msgtype' : 'm.text',
                    'format' : 'org.matrix.custom.html',
                    'body' : soup.get_text(),
                    'formatted_body' : text.replace("<div", "<span").replace("</div>", "</span>").replace("style=\"color: ", "data-mx-color=\"").replace("style=\"background: ", "data-mx-bg-color=\"")

                    }
        else:
            content = {
                    'msgtype' : "m.text",
                    'body' : text
                    }

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_nio(
            homeserver=self.read_param('homeserver'),
            user=self.read_param('username'),
            password=self.read_param('password'),
            room_id=self.setting('room-id'),
            content=content,
            ))
        return "complete"
