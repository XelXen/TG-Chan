# Import required libraries
import re
import pyrogram as tg
from AShelve import AShelve
import config
import hashlib
import random
from rate_limiter import RateLimiter
import logging

# Configure basic logging with a FileHandler (which is thread‑safe)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# Initialize the backend
blacklist = AShelve(config.BLACKLIST_FILE)
seedlist = AShelve(config.SEEDLIST_FILE)
nicknames = AShelve(config.NICKNAMES_FILE)
rate_limiter = RateLimiter()


# Initialize the client
app = tg.Client(
    name=config.SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)


# Hashing function
def hash(value: int, seed: int = 0) -> tuple[str, int]:
    seed = random.randint(1, 100000000) if seed == -1 else seed
    return hashlib.sha3_224(string=str(value + seed).encode()).hexdigest(), seed


# ---| Post Generator Function |---


@app.on_message(
    tg.filters.private
    & ~tg.filters.command([
        "start",
        "info",
        "nick",
        "privacy",
        "delete",
        "blacklist",
        "unblacklist",
        "yank",
    ])
)
async def text_handler(_, message: tg.types.Message):
    if await rate_limiter.acquire(message.from_user.id, "text", config.COOLDOWN_READ):
        return
    try:
        uhash, _ = hash(message.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            await message.reply_text("Please use /start to first regenerate your seed.")
            return

        await message.reply_text(
            "Ready to post your message? Click the button down below to proceed, or keep editing if you're not satisfied.",
            reply_markup=tg.types.InlineKeyboardMarkup(
                [
                    [
                        tg.types.InlineKeyboardButton("Post", callback_data="post"),
                        tg.types.InlineKeyboardButton(
                            "Post (Anonymously)", callback_data="post_anon"
                        ),
                    ],
                    [tg.types.InlineKeyboardButton("Cancel", callback_data="cancel")],
                ],
            ),
            reply_to_message_id=message.id,
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# ---| Command Handlers |---


# Start command handler
@app.on_message(tg.filters.command("start") & tg.filters.private)
async def start_command(_, message: tg.types.Message):
    if await rate_limiter.acquire(message.from_user.id, "start", config.COOLDOWN_WRITE):
        return
    try:
        uhash, _ = hash(message.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            _, seed = hash(message.from_user.id, seed=-1)
            await seedlist.set(uhash, seed)

            logger.info(f"A new user ({uhash}) has been registered.")

        await message.reply_text(
            "Hi there! I am TG-Chan Handler Bot, and I can help you post messages on TG-Chan. **To post a message, just leave your message here :D**\n\nAdditional Commands:\n\n/info - Get your current hash, seed, and nickname\n/nick [x] - Change your nickname to [x] (ASCII symbols only)\n/privacy - Privacy Policy\n/delete [s] - Delete your stored data (To confirm, type your seed [s] after the command)\n\nIf you have any further questions, join @WazeChats",
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# Info command handler
@app.on_message(tg.filters.command("info") & tg.filters.private)
async def info_command(_, message: tg.types.Message):
    if await rate_limiter.acquire(message.from_user.id, "info", config.COOLDOWN_READ):
        return

    try:
        uhash, _ = hash(message.from_user.id)

        if (seed := await seedlist.get(uhash, None)) is None:
            if await blacklist.get(uhash, False):
                return

            await message.reply_text("Please use /start to first regenerate your seed.")
            return

        nickname = await nicknames.get(uhash)
        shash, _ = hash(message.from_user.id, seed=seed)

        await message.reply_text(
            f"**User Hash:** `{shash}`\n**Seed:** `{seed}`\n**Nickname:** `{nickname}`",
            reply_markup=tg.types.InlineKeyboardMarkup([
                [
                    tg.types.InlineKeyboardButton(
                        "Regenerate Seed", callback_data="rehash"
                    )
                ]
            ]),
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# Nick command handler
@app.on_message(tg.filters.command("nick") & tg.filters.private)
async def nick_command(_, message: tg.types.Message):
    if await rate_limiter.acquire(message.from_user.id, "nick", config.COOLDOWN_WRITE):
        return

    try:
        uhash, _ = hash(message.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            await message.reply_text("Please use /start to first regenerate your seed.")
            return

        nickname = " ".join(message.command[1:])

        if len(nickname) > 32 or len(nickname) < 2:
            await message.reply_text(
                "Invalid nickname length. Please keep it between 2 and 32 characters."
            )
            return
        elif not re.match(r"^[A-Za-z0-9 _-]+$", nickname):
            await message.reply_text("Nickname can only contain ASCII characters.")
            return

        await nicknames.set(uhash, nickname)
        await message.reply_text(f"Your nickname has been set to `{nickname}`.")

        logger.info(f"User ({uhash}) has set their nickname to {nickname}.")
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# Privacy command handler
@app.on_message(tg.filters.command("privacy") & tg.filters.private)
async def privacy_command(_, message: tg.types.Message):
    if await rate_limiter.acquire(
        message.from_user.id, "privacy", config.COOLDOWN_READ
    ):
        return

    try:
        await message.reply_text(
            "The bot does not store any personal data except for the user's hash, seed, and nickname. Everything else is computed on the go and is not stored for any longer than necessary."
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# Delete command handler
@app.on_message(tg.filters.command("delete") & tg.filters.private)
async def delete_command(_, message: tg.types.Message):
    if await rate_limiter.acquire(
        message.from_user.id, "delete", config.COOLDOWN_WRITE
    ):
        return

    try:
        uhash, _ = hash(message.from_user.id)

        if (seed := await seedlist.get(uhash, None)) is None:
            if await blacklist.get(uhash, False):
                return

            await message.reply_text("User not found.")
            return

        if len(message.command) == 1:
            await message.reply_text("Please confirm your nickname after the command.")
            return
        elif message.command[1] != str(seed):
            await message.reply_text(
                "Invalid seed. Please confirm your seed after the command."
            )
            return

        await seedlist.delete(uhash)
        await nicknames.delete(uhash)

        logger.info(f"User ({uhash}) has regenerated their seed.")

        await message.reply_text(
            "Your data has been deleted. To regenerate your seed, use /start."
        )
        logger.info(f"User ({uhash}) has deleted their data.")
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(message.from_user.id)


# ---| Callback Handlers |---


# Rehash handler
@app.on_callback_query(tg.filters.regex("rehash"))
async def rehash(_, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(query.from_user.id, "rehash", config.COOLDOWN_WRITE):
        return

    try:
        uhash, _ = hash(query.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            await query.answer("Please use /start to regenerate your seed.")
            return

        _, seed = hash(query.from_user.id, seed=-1)
        await seedlist.set(uhash, seed)
        logger.info(f"User ({uhash}) has regenerated their seed.")

        await query.answer("Done!")
        await query.message.edit_text(
            "Your seed has been regenerated. Use /info to view the changes."
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# Cancel handler
@app.on_callback_query(tg.filters.regex("cancel"))
async def cancel(_, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(query.from_user.id, "cancel", config.COOLDOWN_API):
        return

    try:
        uhash, _ = hash(query.from_user.id)

        if await blacklist.get(uhash, False):
            return

        await query.message.edit_text("Request has been cancelled.")
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# Post handler
@app.on_callback_query(tg.filters.regex("post") | tg.filters.regex("post_anon"))
async def post(client: tg.Client, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(query.from_user.id, "post", config.COOLDOWN_API):
        return
    try:
        uhash, _ = hash(query.from_user.id)

        if (seed := await seedlist.get(uhash, None)) is None:
            if await blacklist.get(uhash, False):
                return

            await query.answer("Please use /start to first regenerate your seed.")
            return

        msg = query.message.reply_to_message

        if (
            msg.reply_to_chat_id != config.CHANNEL_ID
            and msg.reply_to_message_id is not None
        ):
            await query.answer("You can only reply to posts from the channel.")
            return

        if msg.text is not None:
            if len(msg.text) > 4000:
                await query.answer(
                    "Message is too long. Please keep it under 4000 characters."
                )
                return

            if query.data == "post_anon":
                shash, seed = hash(query.from_user.id, seed=-1)
                post = await client.send_message(
                    config.CHANNEL_ID,
                    msg.text.markdown + f"\n\n~ Anonymous [​](tg://{shash})",
                    reply_to_message_id=msg.reply_to_message_id,
                )
            else:
                nickname = await nicknames.get(uhash) or "User"
                shash, _ = hash(query.from_user.id, seed=seed)
                post = await client.send_message(
                    config.CHANNEL_ID,
                    msg.text.markdown
                    + f"\n\n~ {nickname} : {shash[:6]} [​](tg://{shash})",
                    reply_to_message_id=msg.reply_to_message_id,
                )

        elif not (
            msg.video is None
            and msg.animation is None
            and msg.photo is None
            and msg.document is None
            and msg.audio is None
            and msg.voice is None
        ):
            if msg.caption is not None:
                if len(msg.caption) > 4000:
                    await query.answer(
                        "Message is too long. Please keep it under 4000 characters."
                    )
                    return

                caption = msg.caption.markdown
            else:
                caption = ""

            if query.data == "post_anon":
                shash, seed = hash(query.from_user.id, seed=-1)
                post = await msg.copy(
                    config.CHANNEL_ID,
                    caption=caption + f"\n\n~ Anonymous [​](tg://{shash})",
                    has_spoiler=True,
                    reply_to_message_id=msg.reply_to_message_id,
                )
            else:
                seed = await seedlist.get(uhash)
                nickname = await nicknames.get(uhash)
                shash, _ = hash(query.from_user.id, seed=seed)
                post = await msg.copy(
                    config.CHANNEL_ID,
                    caption=caption
                    + f"\n\n~ {nickname} : {shash[:6]} [​](tg://{shash})",
                    has_spoiler=True,
                    reply_to_message_id=msg.reply_to_message_id,
                )
        else:
            await query.answer("Invalid message")
            return

        logger.info(f"User ({uhash}) has posted a message.")
        await query.answer("Done!")
        await query.message.edit_text(
            f"[Message](https://t.me/{config.CHANNEL_USERNAME}/{post.id}) has been posted!",
            reply_markup=tg.types.InlineKeyboardMarkup([
                [
                    tg.types.InlineKeyboardButton(
                        "Delete", callback_data=f"vdelete_{post.id}_{seed}"
                    )
                ]
            ]),
        )

    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# Delete Verification handler
@app.on_callback_query(tg.filters.regex(r"vdelete_\d+_\d+"))
async def ver_delete(_, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(query.from_user.id, "vdelete", config.COOLDOWN_API):
        return

    try:
        uhash, _ = hash(query.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            await query.answer("Please use /start to first regenerate your seed.")
            return

        await query.edit_message_text(
            "Are you sure you want to delete this post? This action cannot be undone.",
            reply_markup=tg.types.InlineKeyboardMarkup([
                [
                    tg.types.InlineKeyboardButton("Yes", callback_data=query.data[1:]),
                    tg.types.InlineKeyboardButton("No", callback_data=f"c{query.data[1:]}"),
                ]
            ]),
        )

    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# Delete Cancel handler
@app.on_callback_query(tg.filters.regex(r"cdelete_\d+_\d+"))
async def del_cancel(_, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(query.from_user.id, "cdelete", config.COOLDOWN_API):
        return

    try:
        await query.edit_message_text(
            "Request has been cancelled.",
            reply_markup=tg.types.InlineKeyboardMarkup([
                [
                    tg.types.InlineKeyboardButton(
                        "Re-Delete", callback_data=f"v{query.data[1:]}"
                    )
                ]
            ]),
        )
    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# Delete post handler
@app.on_callback_query(tg.filters.regex(r"delete_\d+_\d+"))
async def delete_post(client: tg.Client, query: tg.types.CallbackQuery):
    if await rate_limiter.acquire(
        query.from_user.id, "delete_post", config.COOLDOWN_API
    ):
        return

    try:
        uhash, _ = hash(query.from_user.id)

        if await seedlist.get(uhash, None) is None:
            if await blacklist.get(uhash, False):
                return

            await query.answer("Please use /start to first regenerate your seed.")
            return

        commands = query.data.split("_")
        post_id = int(commands[1])
        seed = int(commands[2])

        post = await client.get_messages(config.CHANNEL_ID, post_id)
        post_shash = (
            post.caption.markdown[-57:-1]
            if post.text is None
            else post.text.markdown[-57:-1]
        )

        if post_shash != hash(query.from_user.id, seed=seed)[0]:
            await query.answer("You are not authorized to delete this post.")
            return

        await post.delete()
        logger.info(f"User ({uhash}) has deleted a post.")
        await query.answer("Post has been deleted.")
        await query.message.edit_text("Post has been deleted.")

    except Exception as e:
        logger.error(e)
    finally:
        await rate_limiter.release(query.from_user.id)


# ---| Admin Commands |---


# Blacklist command handler
@app.on_message(
    tg.filters.command("blacklist")
    & tg.filters.private
    & tg.filters.user(config.ADMINS)
)
async def blacklist_command(_, message: tg.types.Message):
    if len(message.command) == 1:
        await message.reply_text("Please provide a user ID.")
        return

    uhash = message.command[1]

    await blacklist.set(uhash, True)
    await seedlist.delete(uhash)
    await nicknames.delete(uhash)

    await message.reply_text("User has been blacklisted.")


# Unblacklist command handler
@app.on_message(
    tg.filters.command("unblacklist")
    & tg.filters.private
    & tg.filters.user(config.ADMINS)
)
async def unblacklist_command(_, message: tg.types.Message):
    if len(message.command) == 1:
        await message.reply_text("Please provide a user ID.")
        return

    uhash = message.command[1]

    await blacklist.delete(uhash)
    await message.reply_text("User has been unblacklisted.")


# Yank command handler
@app.on_message(
    tg.filters.command("yank") & tg.filters.private & tg.filters.user(config.ADMINS)
)
async def yank_command(_, message: tg.types.Message):
    if len(message.command) == 1:
        await message.reply_text("Please provide a message ID.")
        return

    post_id = int(message.command[1])

    try:
        await app.delete_messages(config.CHANNEL_ID, post_id)
        await message.reply_text("Message has been deleted.")
    except Exception as e:
        logger.error(e)
        await message.reply_text("Failed to delete message.")


if __name__ == "__main__":
    app.run()
