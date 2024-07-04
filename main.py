# Import Core Libraries
import pyrogram
import time
import config
import database
import os

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from pyrogram.enums.parse_mode import ParseMode


# Initialize Pyrogram Client and Database

app = pyrogram.Client(
    name=config.NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

db = database.DatabaseSession()


# Define Callback Functions


@app.on_message(filters=filters.command(commands=["start"]))
async def start(_: pyrogram.Client, message: Message) -> None:
    if len(message.command) == 1:
        await message.reply_text(
            text=(
                "Hello there! I am TG-Chan Posting Bot. I can help you post anonymous messages to TG-Chan.\n\n"
                "Command List:\n"
                "/start - Introduction & command list\n"
                "/post - Post an anonymous message (use as a reply to the message)\n"
                "/delete - Delete a message\n"
                "/hash - Get your unique hash id (SECRET - DO NOT SHARE!)\n"
                "/privacy - Get Privacy Policy of the bot"
            ),
            parse_mode=ParseMode.DISABLED,
        )
    else:
        key = message.command[1]

        file_path = f"media/{key[3:]}.{key[:3]}"
        if not os.path.exists(path=file_path):
            await message.reply_text(
                text=("Invalid media key! Please try again with a valid media key.")
            )

            return

        if key.startswith("img"):
            await message.reply_photo(
                photo=file_path,
                caption="Here is the media you requested.",
            )

        elif key.startswith("mp4"):
            await message.reply_video(
                video=file_path,
                caption="Here is the media you requested.",
            )


@app.on_message(filters=filters.command(commands=["post"]) & filters.reply)
async def post(client: pyrogram.Client, message: Message) -> None:
    db.reload()

    if message.from_user.id in db["user_timings"]:
        if (
            time.time() - db["user_timings"][message.from_user.id]
            < config.POST_INTERVAL
        ):
            await message.reply_text(
                text=(
                    "You are posting too fast! Please wait for a while before posting again."
                )
            )

            return

    # TODO : Clear the existing autodelete queue if it exceeds the limit

    message = message.reply_to_message

    if message.photo:
        if message.photo.file_size > config.MAX_IMAGE_SIZE:
            await message.reply_text(
                text=(
                    "The image size is too large! Please try again with a smaller/compressed image or add a link to the image instead."
                )
            )

            return

        await message.download(file_name=f"media/{message.photo.file_id}.jpg")
        command = f"https://t.me/{config.BOT_USERNAME}?start=img{message.photo.file_id}"
        caption = message.caption if message.caption else ""

        msg = await client.send_message(
            chat_id=config.POST_ID,
            text=caption
            + f"\n\n[Click here to view the photo]({command})"
            + f"\n\nHash: {database.hash_user(user_id=message.from_user.id)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👍",
                            callback_data="like",
                        ),
                        InlineKeyboardButton(
                            text="👎",
                            callback_data="dislike",
                        ),
                    ],
                ],
            ),
        )

    elif message.video:
        if message.video.file_size > config.MAX_VIDEO_SIZE:
            await message.reply_text(
                text=(
                    "The video size is too large! Please try again with a smaller/compressed video or add a link to the video instead."
                )
            )

            return

        await message.download(file_name=f"media/{message.video.file_id}.mp4")
        command = f"https://t.me/{config.BOT_USERNAME}?start=mp4{message.video.file_id}"
        caption = message.caption if message.caption else ""

        msg = await client.send_message(
            chat_id=config.POST_ID,
            text=caption
            + f"\n\n[Click here to view the video]({command})"
            + f"\n\nHash: {database.hash_user(user_id=message.from_user.id)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👍",
                            callback_data="like",
                        ),
                        InlineKeyboardButton(
                            text="👎",
                            callback_data="dislike",
                        ),
                    ],
                ],
            ),
        )

    elif message.text:
        await client.send_message(
            chat_id=config.POST_ID,
            text=message.text
            + f"\n\nHash: {database.hash_user(user_id=message.from_user.id)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👍",
                            callback_data="like",
                        ),
                        InlineKeyboardButton(
                            text="👎",
                            callback_data="dislike",
                        ),
                    ],
                ],
            ),
        )

    else:
        await message.reply_text(
            text=("Invalid message type! Please try again with a valid message type.")
        )

        return

    db["like_ratio"][msg.id] = 0
    db["user_timings"][message.from_user.id] = time.time()
    db["autodelete"].add(msg.id)
