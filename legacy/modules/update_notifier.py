# пасхалка
# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib

import git

from .. import loader, utils, version
from ..inline.types import InlineCall
from ..types import Message


@loader.tds
class UpdateNotifier(loader.Module):
    strings = {"name": "UpdateNotifier"}

    def __init__(self):
        self._notified = None
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "disable_notifications",
                doc=lambda: self.strings("_cfg_doc_disable_notifications"),
                validator=loader.validators.Boolean(),
            )
        )

    def get_changelog(self) -> str:
        try:
            repo = git.Repo()

            for remote in repo.remotes:
                remote.fetch()

            if not (
                diff := repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            ):
                return False
        except Exception:
            return False

        res = "\n".join(
            f"<b>{commit.split()[0]}</b>:"
            f" <i>{utils.escape_html(' '.join(commit.split()[1:]))}</i>"
            for commit in diff.splitlines()[:10]
        )

        if diff.count("\n") >= 10:
            res += self.strings("more").format(len(diff.splitlines()) - 10)

        return res

    def get_latest(self) -> str:
        try:
            return next(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            ).hexsha
        except Exception:
            return ""

    async def client_ready(self):
        try:
            git.Repo()
        except Exception as e:
            raise loader.LoadError("Can't load due to repo init error") from e

        self._markup = lambda: self.inline.generate_markup(
            [
                {"text": self.strings("update"), "data": "legacy/update"},
                {"text": self.strings("ignore"), "data": "legacy/ignore_upd"},
            ]
        )

    @loader.loop(interval=60, autostart=True)
    async def poller(self):
        if self.config["disable_notifications"] or not self.get_changelog():
            return

        self._pending = self.get_latest()

        if (
            self.get("ignore_permanent", False)
            and self.get("ignore_permanent") == self._pending
        ):
            await asyncio.sleep(60)
            return

        if self._pending not in {utils.get_git_hash(), self._notified}:
            m = await self.inline.bot.send_photo(
                self.tg_id,
                "https://i.postimg.cc/1RWpKs8z/legacy-update-banner.png",
                caption=self.strings("update_required").format(
                    utils.get_git_hash()[:6],
                    '<a href="https://github.com/Crayz310/Legacy/compare/{}...{}">{}</a>'.format(
                        utils.get_git_hash()[:12],
                        self.get_latest()[:12],
                        self.get_latest()[:6],
                    ),
                    self.get_changelog(),
                ),
                reply_markup=self._markup(),
            )

            self._notified = self._pending
            self.set("ignore_permanent", False)

            await self._delete_all_upd_messages()

            self.set("upd_msg", m.message_id)

    async def _delete_all_upd_messages(self):
        for client in self.allclients:
            with contextlib.suppress(Exception):
                await client.loader.inline.bot.delete_message(
                    client.tg_id,
                    client.loader.db.get("UpdateNotifier", "upd_msg"),
                )

    @loader.callback_handler()
    async def update(self, call: InlineCall):
        if call.data not in {"legacy/update", "legacy/ignore_upd"}:
            return

        if call.data == "legacy/ignore_upd":
            self.set("ignore_permanent", self.get_latest())
            await call.answer(self.strings("latest_disabled"))
            return

        await self._delete_all_upd_messages()

        with contextlib.suppress(Exception):
            await call.delete()

        await self.invoke("update", "-f", peer=self.inline.bot_username)

    @loader.command()
    async def changelog(self, message: Message):
        with open("CHANGELOG.md", mode="r", encoding="utf-8") as f:
            changelog = f.read().split("##")[1].strip()
        if (await self._client.get_me()).premium:
            changelog.replace(
                "🌑 Legacy",
                "<emoji document_id=5192765204898783881>🌘</emoji><emoji document_id=5195311729663286630>🌘</emoji><emoji document_id=5195045669324201904>🌘</emoji>",
            )

        await utils.answer(message, self.strings("changelog").format(changelog))
