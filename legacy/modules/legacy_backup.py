# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import datetime
import io
import logging
import os
import time
import zipfile
from pathlib import Path

import ujson
from aiogram.types import BufferedInputFile

from .. import loader, main, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)


@loader.tds
class LegacyBackupMod(loader.Module):
    strings = {"name": "LegacyBackup"}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self.tg_id,
                photo="https://i.postimg.cc/8PPXPyK5/legacy-unit-alpha.png",
                caption=self.strings["period"],
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {
                                "text": f"🕰 {i} h",
                                "callback": self._set_backup_period,
                                "args": (i,),
                            }
                            for i in [1, 2, 4, 6, 8, 12, 24, 48, 168]
                        ],
                        3,
                    )
                    + [
                        [
                            {
                                "text": "🚫 Never",
                                "callback": self._set_backup_period,
                                "args": (0,),
                            }
                        ]
                    ]
                ),
            )

        self._content_channel_id = await utils.wait_for_content_channel(self._db)

        self._backup_topic = await utils.asset_forum_topic(
            client=self._client,
            db=self._db,
            peer=self._content_channel_id,
            title="Backups",
            description="📼 Your database backups will appear here",
            icon_emoji_id=6024106569430472546,
        )

    async def _set_backup_period(self, call: BotInlineCall, value: int):
        if not value:
            self.set("period", "disabled")
            await call.answer(
                self.strings["never"].format(self.get_prefix()),
                show_alert=True,
            )
            await call.delete()
            return

        self.set("period", value * 60 * 60)
        self.set("last_backup", round(time.time()))

        await call.answer(
            self.strings["saved"].format(self.get_prefix()),
            show_alert=True,
        )
        await call.delete()

    @loader.command()
    async def set_backup_period(self, message):
        if (
            not (args := utils.get_args_raw(message))
            or not args.isdigit()
            or int(args) not in range(200)
        ):
            await utils.answer(message, self.strings["invalid_args"])
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(
                message,
                self.strings["never"].format(self.get_prefix(message.sender_id)),
            )
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(
            message, self.strings["saved"].format(self.get_prefix(message.sender_id))
        )

    @loader.loop(interval=1, autostart=True)
    async def handler(self):
        try:
            if self.get("period") == "disabled":
                raise loader.StopLoop

            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            db_dump = ujson.dumps(self._db).encode()

            result = io.BytesIO()

            with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(loader.LOADED_MODULES_DIR):
                    for file in files:
                        if file.endswith(f"{self.tg_id}.py"):
                            with open(os.path.join(root, file), "rb") as f:
                                zipf.writestr(file, f.read())

                zipf.writestr("db-backup.json", db_dump)

            outfile = io.BytesIO(result.getvalue())
            outfile.name = f"legacy-{datetime.datetime.now():%d-%m-%Y-%H-%M}.backup"

            await self.inline.bot.send_document(
                int(f"-100{self._content_channel_id}"),
                BufferedInputFile(outfile.getvalue(), outfile.name),
                caption=self.strings["backup_caption"].format(
                    prefix=self.get_prefix(),
                ),
                reply_markup=self.inline.generate_markup(
                    [
                        [
                            {
                                "text": self.strings["restore_this"],
                                "data": "legacy/backup/restore/confirm",
                            },
                        ],
                    ],
                ),
                message_thread_id=self._backup_topic.id,
            )

            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("LegacyBackup failed")
            await asyncio.sleep(60)

    @loader.callback_handler()
    async def restore_inl(self, call: BotInlineCall):
        if not call.data.startswith("legacy/backup/restore"):
            return

        if call.data == "legacy/backup/restore/confirm":
            await utils.answer(
                call,
                self.strings["confirm"],
                reply_markup=[
                    {
                        "text": self.strings["_btn_yes"],
                        "data": "legacy/backup/restore",
                    },
                    {
                        "text": self.strings["_btn_no"],
                        "data": "legacy/backup/restore/cancel",
                    },
                ],
            )
            return

        if call.data == "legacy/backup/restore/cancel":
            await utils.answer(
                call,
                self.strings["backup_caption"].format(
                    prefix=self.get_prefix(),
                ),
                reply_markup=[
                    {
                        "text": self.strings["restore_this"],
                        "data": "legacy/backup/restore/confirm",
                    },
                ],
            )
            return

        file = await (
            await self._client.get_messages(
                self._content_channel_id, ids=call.message.message_id
            )
        ).download_media(bytes)

        try:
            file = io.BytesIO(file)
            file.name = "backup.zip"

            with zipfile.ZipFile(file) as zf:
                with zf.open("db-backup.json", "r") as db_file:
                    new_db = ujson.loads(db_file.read().decode())

                    with contextlib.suppress(KeyError):
                        new_db["legacy.inline"].pop("bot_token")

                    if not self._db.process_db_autofix(new_db):
                        raise RuntimeError("Attempted to restore broken database")

                    self._db.clear()
                    self._db.update(**new_db)
                    self._db.save()

                for name in zf.namelist():
                    if name == "db-backup.json":
                        continue

                    path = loader.LOADED_MODULES_PATH / Path(name).name
                    with zf.open(name, "r") as module:
                        path.write_bytes(module.read())
        except Exception:
            logger.exception("Unable to restore backup")
            return

        await call.answer(self.strings["backup_restored"], show_alert=True)
        await self.invoke("restart", "-f", peer=self.inline.bot_id)

    @loader.command()
    async def backup(self, message):
        db_dump = ujson.dumps(self._db).encode()

        result = io.BytesIO()

        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(loader.LOADED_MODULES_DIR):
                for file in files:
                    if file.endswith(f"{self.tg_id}.py"):
                        with open(os.path.join(root, file), "rb") as f:
                            zipf.writestr(file, f.read())

            zipf.writestr("db-backup.json", db_dump)

        outfile = io.BytesIO(result.getvalue())
        outfile.name = f"legacy-{datetime.datetime.now():%d-%m-%Y-%H-%M}.backup"

        backup_msg = await self.inline.bot.send_document(
            int(f"-100{self._content_channel_id}"),
            BufferedInputFile(outfile.getvalue(), outfile.name),
            caption=self.strings["backup_caption"].format(
                prefix=self.get_prefix(message.sender_id),
            ),
            reply_markup=self.inline.generate_markup(
                [
                    [
                        {
                            "text": self.strings["restore_this"],
                            "data": "legacy/backup/restore/confirm",
                        },
                    ],
                ],
            ),
            message_thread_id=self._backup_topic.id,
        )

        await utils.answer(
            message,
            self.strings["backup_sent"].format(
                f"https://t.me/c/{self._content_channel_id}/{self._backup_topic.id}/{backup_msg.message_id}"
            ),
        )

    @loader.command()
    async def restore(self, message):
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(message, self.strings["reply_to_file"])
            return

        logger.info("📚 Trying to restore backup")

        file = await reply.download_media(bytes)

        try:
            file = io.BytesIO(file)
            file.name = "backup.zip"

            with zipfile.ZipFile(file) as zf:
                with zf.open("db-backup.json", "r") as db_file:
                    new_db = ujson.loads(db_file.read().decode())

                    with contextlib.suppress(KeyError):
                        new_db["legacy.inline"].pop("bot_token")

                    if not self._db.process_db_autofix(new_db):
                        raise RuntimeError("Attempted to restore broken database")

                    self._db.clear()
                    self._db.update(**new_db)
                    self._db.save()

                for name in zf.namelist():
                    if name == "db-backup.json":
                        continue

                    path = loader.LOADED_MODULES_PATH / Path(name).name
                    with zf.open(name, "r") as module:
                        path.write_bytes(module.read())
        except Exception:
            logger.exception("Unable to restore backup")
            await utils.answer(message, self.strings["reply_to_file"])
            return

        await utils.answer(message, self.strings["backup_restored"])
        await self.invoke("restart", "-f", peer=message.peer_id)
