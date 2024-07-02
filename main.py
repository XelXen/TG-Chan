# Import Core Libraries

import pyrogram
import time
import varfile
import database


# Initialize Pyrogram Client

app = pyrogram.Client(name=varfile.NAME, api_id=varfile.API_ID, api_hash=varfile.API_HASH, bot_token=varfile.BOT_TOKEN)
