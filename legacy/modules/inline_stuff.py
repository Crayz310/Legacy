# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import re
import string

import aiohttp
from legacytl.errors.rpcerrorlist import YouBlockedUserError
from legacytl.tl.functions.contacts import UnblockRequest

from .. import loader, utils
from ..auth_manager import AuthManager
from ..inline.types import BotInlineMessage

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuff(loader.Module):
    strings = {"name": "InlineStuff"}

    async def client_ready(self, client, db):
        self._auth_sessions = {}
        self._tokens = []
        self._temp_data = {}

    def reset_state(self, user_id):
        self.inline.fsm.pop(str(user_id), None)

    @loader.watcher(
        "out",
        "only_inline",
        contains="This message will be deleted automatically",
    )
    async def watcher(self, message):
        if message.via_bot_id == self.inline.bot_id:
            await message.delete()

    @loader.watcher("out", "only_inline", contains="Opening gallery...")
    async def gallery_watcher(self, message):
        if message.via_bot_id != self.inline.bot_id:
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text)[1]

        await message.delete()

        m = await message.respond("🌙", reply_to=utils.get_topic(message))

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    @loader.command()
    async def ch_legacy_bot(self, message):
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings["bot_username_invalid"])
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings["bot_username_occupied"])
                return

        self._db.set("legacy.inline", "custom_bot", args)
        self._db.set("legacy.inline", "bot_token", None)
        await utils.answer(message, self.strings["bot_updated"])

    @loader.command()
    async def ch_bot_token(self, message):
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings["token_not_provided"])
            return

        url = f"https://api.telegram.org/bot{args}/getMe"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            await self.inline._stop()
                            self.inline._token = args
                            self._db.set("legacy.inline", "bot_token", args)
                            await self.inline.register_manager(ignore_token_checks=True)
                            return await utils.answer(
                                message, self.strings["token_changed"]
                            )
                    logger.error("Token validation failed!")
                    return await utils.answer(
                        message, self.strings["invalid_token_format"]
                    )
            except aiohttp.ClientConnectionError as e:
                logger.error(f"Connection error during token validation: {e}")
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during token validation: {e}"
                )

    @loader.command()
    async def iauth(self, message, force: bool = False):
        host = utils.get_current_platform() or utils._platforms.get("vds")
        if host.get("single_session", False):
            return await utils.answer(message, self.strings["forbid"])
        args = utils.get_args_raw(message)
        force = force or "-f" in args

        if not force:
            try:
                if not await self.inline.form(
                    self.strings["privacy_leak_nowarn"].format(
                        f"{self.get_prefix(message.sender_id)}iauth -f"
                    ),
                    message=message,
                    reply_markup=[
                        {
                            "text": self.strings["btn_yes"],
                            "callback": self.iauth,
                            "args": (True,),
                        },
                        {"text": self.strings["btn_no"], "action": "close"},
                    ],
                ):
                    raise Exception
            except Exception:
                await utils.answer(message, self.strings["privacy_leak"])

            return

        token = utils.rand(16)
        self._tokens.append(token)
        link = f"https://t.me/{self.inline.bot_username}?start=auth-{token}"
        await utils.answer(message, self.strings["auth"].format(link))

    async def aiogram_watcher(self, message: BotInlineMessage):
        user_id = message.from_user.id
        state = self.inline.gs(user_id)
        if not message.text:
            return

        if message.text == "/start":
            await message.answer_animation(
                "https://i.postimg.cc/90QXwWJN/legacy-userbot.gif",
                caption=self.strings["this_is_legacy"],
            )

        if message.text.startswith("/start auth-"):
            token = re.search(r"auth-([a-zA-Z0-9]+)", message.text)
            token = token.group(1) if token else None

            if not token or token not in self._tokens:
                return

            self._auth_sessions[user_id] = AuthManager()
            self._tokens.remove(token)
            await message.answer(self.strings["enter_phone"])
            self.inline.ss(user_id, "phone")
            return

        if state == "phone":
            phone = message.text

            try:
                await self._auth_sessions[user_id].send_tg_code(phone)
                self._temp_data[user_id] = {"phone": phone}
                await message.answer(self.strings["received_code"])
                self.inline.ss(user_id, "code")
            except ValueError:
                logger.error("Error on sending code", exc_info=True)
                self._auth_sessions.pop(user_id, None)
                self.reset_state(user_id)
                await message.answer(self.strings["wrong_number"])
            except Exception:
                logger.error("Error on sending code", exc_info=True)
                await message.answer(self.strings["unknown_err"])
                self._auth_sessions.pop(user_id, None)
                self._temp_data.pop(user_id, None)
                self.reset_state(user_id)
            return

        if state == "code":
            code = message.text
            phone = self._temp_data.get(user_id, {}).get("phone")

            if not phone:
                await message.answer(self.strings["no_phone"])
                self.reset_state(user_id)
                return

            try:
                await self._auth_sessions[user_id].sign_in(phone, code)
                await self._auth_sessions[user_id].finish_auth()
                await message.answer(self.strings["success_auth"])
                self.reset_state(user_id)
            except ValueError as e:
                if "Invalid code" in str(e):
                    await message.answer(self.strings["wrong_code"])
                    return

                if "2FA" in str(e):
                    self._temp_data[user_id].update({"code": code})
                    await message.answer(self.strings["enter_2fa"])
                    self.inline.ss(user_id, "2fa")
                    return
                logger.error("Error on sign in", exc_info=True)
                await message.answer(self.strings["unknown_err"])
                self._temp_data.pop(user_id, None)
                self.reset_state(user_id)
            except Exception:
                logger.error("Error on sign in", exc_info=True)
                await message.answer(self.strings["unknown_err"])
                self._temp_data.pop(user_id, None)
                self.reset_state(user_id)
            return

        if state == "2fa":
            password = message.text
            phone = self._temp_data.get(user_id, {}).get("phone")
            code = self._temp_data.get(user_id, {}).get("code")

            if not phone:
                await message.answer(self.strings["no_phone"])
                self.reset_state(user_id)
                return

            if not code:
                await message.answer(self.strings["no_code"])
                self.reset_state(user_id)
                return

            try:
                await self._auth_sessions[user_id].sign_in(phone, code, password)
                await message.answer(self.strings["success_auth"])
                await self._auth_sessions[user_id].finish_auth()
                self.reset_state(user_id)
            except ValueError:
                await message.answer(self.strings["wrong_2fa"])
            except Exception:
                logger.error("Error on 2FA", exc_info=True)
                self._temp_data.pop(user_id, None)
                self.reset_state(user_id)
            return
