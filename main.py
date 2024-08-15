# Import Core Libraries

import hydrogram
import time
import config
import database
import asyncio
import os
import re
import random

from hydrogram import filters
from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from typing import Dict


# Initialize Client and Setup Memory

app = hydrogram.Client(
    name=config.NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

reply_mode: Dict[str, int] = {}


# Define Core functions


def sanitize_str(string: str) -> str:
    ## Sanitizes the string by only allowing alphanumeric characters and hyphens

    return re.sub(pattern=r"[^a-zA-Z0-9-]", repl="", string=string)


def printlog(text: str) -> None:
    ## Prints the text to the console and logs it to a file

    print(text)

    if not os.path.exists("logs"):
        os.mkdir("logs")

    name = os.path.join("logs", time.strftime("%Y%m%d") + ".log")

    with open(file=name, mode="a") as f:
        f.write(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] {text}\n")


# Define Callback Functions


@app.on_message(filters=filters.command(commands=["start"]))
async def start(_, message: Message) -> None:
    if len(message.command) == 1:
        ## Intro Function

        await message.reply_text(
            text="Hello there! I am TG-Chan Posting Bot. I can help you post anonymous messages to TG-Chan.\n\nTo get started, just send me a message to post on TG-Chan, to reply to an existing post, you can just click on the reply button on that post and send me a reply message\n\nYou can view the privacy policy using the /privacy command."
        )

    elif len(message.command) == 2:
        ## Media Function

        file_path = "media/" + sanitize_str(string=message.command[1])

        if file_path.endswith("-jpg"):
            file_path = file_path[:-4] + ".jpg"
            extension = "jpg"
        elif file_path.endswith("-mp4"):
            file_path = file_path[:-4] + ".mp4"
            extension = "mp4"
        else:
            extension = None

        if not os.path.exists(file_path):
            await message.reply_text(
                text=("Invalid media key! Please try again with a valid media key.")
            )
            return

        if extension == "jpg":
            msg = await message.reply_photo(
                photo=file_path,
                caption=(
                    f"Here is the photo you requested. It will be deleted in {config.AUTOPURGE_INTERVAL} seconds."
                    if config.AUTOPURGE_MEDIA
                    else "Here is the photo you requested."
                ),
            )

        elif extension == "mp4":
            msg = await message.reply_video(
                video=file_path,
                caption=(
                    f"Here is the video you requested. It will be deleted in {config.AUTOPURGE_INTERVAL} seconds."
                    if config.AUTOPURGE_MEDIA
                    else "Here is the video you requested."
                ),
            )

        if config.AUTOPURGE_MEDIA:
            await asyncio.sleep(config.AUTOPURGE_INTERVAL)
            await msg.delete()

    else:
        await message.reply_text(text=("Invalid syntax!"))


@app.on_message(filters=filters.private & ~filters.command(commands=["start", "delete", "privacy", "cancel"]))
async def post(client: hydrogram.Client, message: Message) -> None:
    await message.reply_text(
        text="Whenever you're ready, just click on the button down below to post your message to TG-Chan!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Post",
                        callback_data="post",
                    ),
                ],
            ],
        ),
        reply_to_message_id=message.id,
    )


@app.on_message(filters=filters.command(commands=["delete"]))
async def delete(client: hydrogram.Client, message: Message) -> None:
    db = database.load()

    if len(message.command) != 3:
        await message.reply_text(text=("Invalid syntax!"))
        return

    elif (
        not message.command[1].isdigit()
        or not message.command[2].replace("-", "").isnumeric()
    ):
        await message.reply_text(text=("Invalid command!"))
        return

    try:
        msg = await client.get_messages(
            chat_id=config.POST_ID,
            message_ids=int(message.command[1]),
        )

        uhash = msg.text.split("\n")[-1][6:]
    except Exception as e:
        print(f"Error: {e}")

        await message.reply_text(
            text=("Invalid message id! Please try again with a valid message id.")
        )

        return

    if (
        uhash != database.hash(num=message.from_user.id + int(message.command[2]))
        and message.from_user.id != config.OWNER_ID
    ):
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

    database.remove_post(db=db, id=msg.id)

    await message.reply_text(text=("The message has been successfully deleted!"))

    printlog(f"User {uhash} deleted a message with id {msg.id}!")

    database.save(db=db)


@app.on_message(filters=filters.command(commands=["privacy"]))
async def privacy(_: hydrogram.Client, message: Message) -> None:
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
async def callback(client: hydrogram.Client, callback: CallbackQuery) -> None:
    db = database.load()
    uhash = database.hash(num=callback.from_user.id)

    if callback.data == "like":
        if callback.message.id not in db["posts"]:
            await callback.answer(text="Invalid message!")
            return
    
        if uhash in db["posts"][callback.message.id]["feedbacks"]:
            if db["posts"][callback.message.id]["feedbacks"][uhash] == database.Feedback.LIKE:
                await callback.answer(text="You have already liked this message!")
                return
            else:
                db["posts"][callback.message.id]["rating"] += 1
                dislike = -1
        else:
            dislike = 0
    
        db["posts"][callback.message.id]["feedbacks"][uhash] = database.Feedback.LIKE
        db["posts"][callback.message.id]["rating"] += 1
        like = 1

        existing_reply_markup = callback.message.reply_markup.inline_keyboard

        for row in existing_reply_markup:
            for button in row:
                if button.text.startswith("👍"):
                    current = int(button.text.split(" : ")[1])
                    button.text = f"👍 : {current + like}"
                elif button.text.startswith("👎"):
                    current = int(button.text.split(" : ")[1])
                    button.text = f"👎 : {current + dislike}"

        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=existing_reply_markup))

        if db["posts"][callback.message.id]["rating"] >= config.AUTODELETE_LIKE_LIMIT:
            if callback.message.id in db["autodelete"]:
                del db["autodelete"][callback.message.id]
            
        if db["posts"][callback.message.id]["rating"] >= config.PIN_LIKE_LIMIT:
            await callback.message.pin()

        await callback.answer(text="Thank you for your feedback!")

    elif callback.data == "dislike":
        if callback.message.id not in db["posts"]:
            await callback.answer(text="Invalid message!")
            return
    
        if uhash in db["posts"][callback.message.id]["feedbacks"]:
            if db["posts"][callback.message.id]["feedbacks"][uhash] == database.Feedback.DISLIKE:
                await callback.answer(text="You have already disliked this message!")
                return
            else:
                db["posts"][callback.message.id]["rating"] -= 1
                like = -1
        else:
            like = 0

        db["posts"][callback.message.id]["feedbacks"][uhash] = database.Feedback.DISLIKE
        db["posts"][callback.message.id]["rating"] -= 1
        dislike = 1

        existing_reply_markup = callback.message.reply_markup.inline_keyboard

        for row in existing_reply_markup:
            for button in row:
                if button.text.startswith("👍"):
                    current = int(button.text.split(" : ")[1])
                    button.text = f"👍 : {current + like}"
                elif button.text.startswith("👎"):
                    current = int(button.text.split(" : ")[1])
                    button.text = f"👎 : {current + dislike}"

        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=existing_reply_markup))

        if db["posts"][callback.message.id]["rating"] <= -config.UNPIN_DISLIKE_LIMIT:
            await callback.message.unpin()

        if db["posts"][callback.message.id]["rating"] <= -config.DELETE_DISLIKE_LIMIT:
            if callback.message.id in db["autodelete"]:
                del db["autodelete"][callback.message.id]

            await callback.message.delete()
            database.remove_post(db=db, id=callback.message.id)

        await callback.answer(text="Thank you for your feedback!")

    elif callback.data == "reply":
        if callback.message.id not in db["posts"]:
            await callback.answer(text="Invalid message!")
            return

        reply_mode[uhash] = callback.message.id

        await callback.answer(text="Reply mode activated! Please send your reply message via bot. You can exit reply mode by sending /cancel.")

        return
    
    elif callback.data == "post":
        ## Post Function

        uhash = database.hash(num=callback.from_user.id)

        if uhash in db["timings"] and callback.from_user.id != config.OWNER_ID:
            if db["timings"][uhash] > time.time():
                await callback.answer(
                    text=(
                        "Please wait for a while before posting another message!"
                    )
                )

                return
            else:
                del db["timings"][uhash]

        seed = random.randint(a=-999_999, b=999_999)
        shash = database.hash(num=callback.from_user.id + seed)

        reply_id = reply_mode.pop(uhash) if uhash in reply_mode else None
        try:
            if reply_id is not None:
                await client.get_messages(
                    chat_id=config.POST_ID,
                    message_ids=reply_id,
                )
        except Exception as e:
            print(f"Error: {e}")
            await callback.answer(
                text=("Invalid reply id! Please try again with a valid reply id.")
            )
            return

        if len(db["autodelete"]) >= config.AUTODELETE_COUNT:
            if reply_id == db["autodelete"][0]:
                await callback.answer(
                    "Reply message is in the auto-delete queue! Please try again with a different message."
                )
                del db["reply_mode"][uhash]

            msg_id = db["autodelete"].pop(0)
            database.remove_post(db=db, id=msg_id)

            printlog(text=f"Auto-deleting message with id {db['autodelete'][0]}!")

            await client.delete_messages(
                chat_id=config.POST_ID,
                message_ids=msg_id,
            )

        message = callback.message.reply_to_message

        if message.photo:
            if message.photo.file_size > config.MAX_IMAGE_SIZE:
                await message.reply_text(
                    text=(
                        "The image size is too large! Please try again with a smaller/compressed image or add a link to the image instead."
                    )
                )

                return

            await message.download(file_name=f"media/{shash}.jpg")

            msg = await client.send_message(
                reply_to_message_id=reply_id,
                chat_id=config.POST_ID,
                text=message.caption + f"\n\nHash: {shash}" if message.caption else f"\n\nHash: {shash}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="View attached photo",
                                url=f"https://t.me/{config.BOT_USERNAME}?start={shash}-jpg",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="👍 : 0",
                                callback_data="like",
                            ),
                            InlineKeyboardButton(
                                text="👎 : 0",
                                callback_data="dislike",
                            ),
                            InlineKeyboardButton(
                                text="Reply",
                                callback_data="reply",
                            ),
                        ],
                    ],
                ),
            )

            database.add_post(db=db, id=msg.id, media=f"media/{shash}.jpg")

        elif message.video:
            if message.video.file_size > config.MAX_VIDEO_SIZE:
                await message.reply_text(
                    text=(
                        "The video size is too large! Please try again with a smaller/compressed video or add a link to the video instead."
                    )
                )

                return

            await message.download(file_name=f"media/{shash}.mp4")

            msg = await client.send_message(
                reply_to_message_id=reply_id,
                chat_id=config.POST_ID,
                text=message.caption + f"\n\nHash: {shash}" if message.caption else f"\n\nHash: {shash}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="View attached video",
                                url=f"https://t.me/{config.BOT_USERNAME}?start={shash}-mp4",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="👍 : 0",
                                callback_data="like",
                            ),
                            InlineKeyboardButton(
                                text="👎 : 0",
                                callback_data="dislike",
                            ),
                            InlineKeyboardButton(
                                text="Reply",
                                callback_data="reply",
                            ),
                        ],
                    ],
                ),
            )

            database.add_post(db=db, id=msg.id, media=f"media/{shash}.mp4")

        elif message.text:
            msg = await client.send_message(
                reply_to_message_id=reply_id,
                chat_id=config.POST_ID,
                text=message.text + f"\n\nHash: {shash}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="👍 : 0",
                                callback_data="like",
                            ),
                            InlineKeyboardButton(
                                text="👎 : 0",
                                callback_data="dislike",
                            ),
                            InlineKeyboardButton(
                                text="Reply",
                                callback_data="reply",
                            ),
                        ],
                    ],
                ),
            )

            database.add_post(db=db, id=msg.id)

        else:
            await message.reply_text(
                text=("Invalid message type! Please try again with a valid message type.")
            )

            return
        
        db["timings"][uhash] = time.time() + config.POST_INTERVAL
        db["autodelete"].append(msg.id)

        await callback.message.edit_text(
            text=(
                f"Your [message](https://t.me/{config.POST_USERNAME}/{msg.id}) has been successfully posted!\n\nTo delete your post, use the `/delete {msg.id} {seed}` command."
            )
        )

        printlog(f"{uhash} posted a message with id {msg.id}!")

    else:
        await callback.answer(text="Invalid action!")
        return

    database.save(db=db)


@app.on_message(filters=filters.command(commands=["cancel"]))
async def cancel(_: hydrogram.Client, message: Message) -> None:
    uhash = database.hash(num=message.from_user.id)

    if uhash in reply_mode:
        del reply_mode[uhash]
        await message.reply_text(text="Reply mode deactivated!")
    else:
        await message.reply_text(text="You are not in reply mode!")


# Run the Bot

if __name__ == "__main__":
    print("Bot is running!")
    app.run()
