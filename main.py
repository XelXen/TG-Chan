# Import Core Libraries
import pyrogram
import time
import config
import database
import os
import re
import random

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from pyrogram.enums.parse_mode import ParseMode


# Initialize Pyrogram Client

app = pyrogram.Client(
    name=config.NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)


# Define Core functions


def sanitize_str(string: str) -> str:
    return re.sub(pattern=r"[^a-zA-Z0-9-]", repl="", string=string)


def printlog(text: str) -> None:
    print(text)
    with open(file=config.LOG_FILE, mode="a") as f:
        f.write(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] {text}\n")


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
                "/post <x> - Post an anonymous reply to channel post link <x>\n"
                "/delete <n> - Delete a message of message id <n>\n"
                "/hash - Get your unique hash ID\n"
                "/privacy - Get Privacy Policy of the bot\n"
            ),
            parse_mode=ParseMode.DISABLED,
        )
    else:
        file_path = "media/" + sanitize_str(string=message.command[1]).replace("-mp4", ".mp4").replace("-jpg", ".jpg")

        if not os.path.exists(file_path):
            await message.reply_text(
                text=("Invalid media key! Please try again with a valid media key.")
            )

            return

        if message.command[1].endswith("jpg"):
            await message.reply_photo(
                photo=file_path,
                caption="Here is the media you requested.",
            )

        elif message.command[1].endswith("mp4"):
            await message.reply_video(
                video=file_path,
                caption="Here is the media you requested.",
            )


@app.on_message(filters=filters.command(commands=["post"]) & filters.reply)
async def post(client: pyrogram.Client, message: Message) -> None:
    db = database.load()

    uhash = database.hash(num=message.from_user.id)

    if uhash in db["user_timings"] and message.from_user.id != config.OWNER_ID:
        if db["user_timings"][uhash] > time.time():
            await message.reply_text(
                text=(
                    "Please wait for a while before posting another message! You can post a message every 5 minutes but if you still cannot post, you might have been temporarily restricted from posting due to a high dislike ratio."
                )
            )

            return
        
    seed = random.randint(a=-999_999, b=999_999)
    shash = database.hash(num=message.reply_to_message.from_user.id + seed)

    if len(message.command) == 2:
        reply_id = int(re.findall(r"\d+$", sanitize_str(message.command[1]))[0])
    elif len(message.command) == 1:
        reply_id = None
    else:
        await message.reply_text(
            text=("Invalid syntax!")
        )

        return
    
    # Check if the id is valid and on the channel

    try:
        if reply_id is not None:
            await client.get_messages(
                chat_id=config.POST_ID,
                message_ids=reply_id,
            )
    except:
        await message.reply_text(
            text=("Invalid reply id! Please try again with a valid reply id.")
        )

        return

    if len(db["autodelete"]) >= config.AUTODELETE_COUNT:
        if reply_id == db["autodelete"][0]:
            await message.reply_text("This is an invalid reply")
            return

        msg_id = db["autodelete"].pop(0)

        printlog(text=f"Auto-deleting message with id {db['autodelete'][0]}!")

        await client.delete_messages(
            chat_id=config.POST_ID,
            message_ids=msg_id,
        )

    message = message.reply_to_message

    if message.photo:
        if message.photo.file_size > config.MAX_IMAGE_SIZE:
            await message.reply_text(
                text=(
                    "The image size is too large! Please try again with a smaller/compressed image or add a link to the image instead."
                )
            )

            return

        await message.download(file_name=f"media/{shash}.jpg")

        caption = message.caption if message.caption else ""

        command = f"https://t.me/{config.BOT_USERNAME}?start={shash}-jpg"

        msg = await client.send_message(
            reply_to_message_id=reply_id,
            chat_id=config.POST_ID,
            text=caption
            + f"\n\n[Click here to view the photo]({command})"
            + f"\n\nHash: {shash}",
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

        db["media"][msg.id] = f"media/{shash}.jpg"

    elif message.video:
        if message.video.file_size > config.MAX_VIDEO_SIZE:
            await message.reply_text(
                text=(
                    "The video size is too large! Please try again with a smaller/compressed video or add a link to the video instead."
                )
            )

            return

        await message.download(file_name=f"media/{shash}.mp4")

        caption = message.caption if message.caption else ""

        command = f"https://t.me/{config.BOT_USERNAME}?start={shash}-mp4"

        msg = await client.send_message(
            reply_to_message_id=reply_id,
            chat_id=config.POST_ID,
            text=caption
            + f"\n\n[Click here to view the video]({command})"
            + f"\n\nHash: {shash}",
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

        db["media"][msg.id] = f"media/{shash}.mp4"

    elif message.text:
        msg = await client.send_message(
            reply_to_message_id=reply_id,
            chat_id=config.POST_ID,
            text=message.text + f"\n\nHash: {shash}",
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
    db["user_timings"][uhash] = time.time() + config.POST_INTERVAL
    db["autodelete"].append(msg.id)
    db["like_users"][msg.id] = set()

    await message.reply_text(
        text=(
            f"Your [message](https://t.me/{config.POST_USERNAME}/{msg.id}) has been successfully posted!\nTo delete your post using the `/delete {msg.id} {seed}` command."
        )
    )

    printlog(f"User {uhash} posted a message with id {msg.id}!")

    database.save(db=db)


@app.on_message(filters=filters.command(commands=["delete"]))
async def delete(client: pyrogram.Client, message: Message) -> None:
    db = database.load()

    if len(message.command) != 3:
        await message.reply_text(
            text=("Invalid syntax!")
        )

        return

    elif not message.command[1].isdigit() or not message.command[2].replace("-", "").isnumeric():
        await message.reply_text(
            text=("Invalid command!")
        )

        return

    try:
        msg = await client.get_messages(
            chat_id=config.POST_ID,
            message_ids=int(message.command[1]),
        )

        user_hash = msg.text.split("\n")[-1][6:]
    except:
        await message.reply_text(
            text=("Invalid message id! Please try again with a valid message id.")
        )

        return

    if user_hash != database.hash(num=message.from_user.id + int(message.command[2])):
        await message.reply_text(
            text=(
                "You are not authorized to delete this message! Please try again with a valid message id."
            )
        )

        return

    await client.delete_messages(
        chat_id=config.POST_ID,
        message_ids=msg.id,
    )

    if msg.id in db["media"]:
        os.remove(path=db["media"][msg.id])
        del db["media"][msg.id]

    del db["like_ratio"][msg.id]
    del db["like_users"][msg.id]

    if msg.id in db["autodelete"]:
        db["autodelete"].remove(msg.id)

    await message.reply_text(text=("The message has been successfully deleted!"))

    printlog(f"User {user_hash} deleted a message with id {msg.id}!")

    database.save(db=db)


@app.on_message(filters=filters.command(commands=["hash"]))
async def hash(_: pyrogram.Client, message: Message) -> None:
    await message.reply_text(
        text=(
            f"Your unique hash id is: `{database.hash(num=message.from_user.id)}`\n\n"
            "This hash id is used to authorize your actions on the bot. Even though it is not a secret, if corresponded with your user id, it can be used to verify your identity."
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_message(filters=filters.command(commands=["privacy"]))
async def privacy(_: pyrogram.Client, message: Message) -> None:
    await message.reply_text(
        text=(
            "Privacy Policy:\n\n"
            "1. Your messages are posted anonymously and are linked to your hash.\n"
            "2. Your user id is not stored or used for any purpose other than generating your hash.\n"
            "3. Your messages are not used for any other purpose than posting on TG-Chan.\n"
            "4. Your messages are not used to track you or your activities on the bot.\n"
            "5. Your hashes are generated in real-time for authentication and stored only for feedbacks.\n"
        ),
    )


@app.on_callback_query()
async def callback(_: pyrogram.Client, callback: CallbackQuery) -> None:
    db = database.load()

    if callback.message.id not in db["like_ratio"]:
        return
    elif (
        database.hash(num=callback.from_user.id)
        in db["like_users"][callback.message.id]
    ):
        await callback.answer(text="You have already given feedback to this message!")
        return
    else:
        db["like_users"][callback.message.id].add(
            database.hash(num=callback.from_user.id)
        )

    uhash = callback.message.text.split("\n")[-1][6:]

    if callback.data == "like":
        db["like_ratio"][callback.message.id] += 1

        if db["like_ratio"][callback.message.id] == config.PIN_LIKE_LIMIT:
            callback.message.pin()

        elif db["like_ratio"][callback.message.id] == config.AUTODELETE_LIKE_LIMIT:
            db["autodelete"].remove(callback.message.id)

    elif callback.data == "dislike":
        db["like_ratio"][callback.message.id] -= 1

        if db["like_ratio"][callback.message.id] == -config.RESTRICT_DISLIKE_LIMIT:
            db["user_timings"][uhash] = time.time() + 86400

        elif db["like_ratio"][callback.message.id] == -config.DELETE_DISLIKE_LIMIT:
            await callback.message.delete()

            if callback.message.id in db["media"]:
                os.remove(path=db["media"][callback.message.id])
                del db["media"][callback.message.id]

            del db["like_ratio"][callback.message.id]
            del db["like_users"][callback.message.id]

            if callback.message.id in db["autodelete"]:
                db["autodelete"].remove(callback.message.id)

            db["user_timings"][uhash] = time.time() + 172800

    await callback.answer(text="Thank you for your feedback!")

    database.save(db=db)


# Run the Bot

if __name__ == "__main__":
    print("Bot is running!")
    app.run()
