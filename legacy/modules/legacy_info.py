# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import getpass
import platform as lib_platform

import distro
import git
import legacytl
from legacytl.types import InputMediaWebPage
from legacytl.utils import get_display_name

from .. import loader, utils, version


@loader.tds
class LegacyInfoMod(loader.Module):
    strings = {"name": "LegacyInfo"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings["_cfg_cst_msg"],
            ),
            loader.ConfigValue(
                "banner_url",
                "https://i.postimg.cc/9MTZgB2j/legacy-info.gif",
                lambda: self.strings["_cfg_banner"],
            ),
            loader.ConfigValue(
                "media_quote",
                True,
                lambda: self.strings["_cfg_media_quote"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "hide_platform_emoji",
                False,
                validator=loader.validators.Boolean(),
            ),
        )

    async def _render_info(self, args: list, custom_prefix: str) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required").format(custom_prefix)
                if diff
                else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.legacy_me.id,
            utils.escape_html(get_display_name(self._client.legacy_me)),
        )
        build = utils.get_commit_url()
        _version = f"<i>{version.__version__}</i>"
        prefix = f"«<code>{utils.escape_html(custom_prefix)}</code>»"

        platform = utils.get_named_platform()

        if not self.config["hide_platform_emoji"]:
            for emoji, icon in [
                ("🍊", "<emoji document_id=5449599833973203438>🧡</emoji>"),
                ("🍇", "<emoji document_id=5449468596952507859>💜</emoji>"),
                ("🍌", "<emoji document_id=5091424266138682339>🍌</emoji>"),
                ("🍀", "<emoji document_id=5395325195542078574>🍀</emoji>"),
                ("🚂", "<emoji document_id=5359595190807962128>🚂</emoji>"),
                ("🐳", "<emoji document_id=5431815452437257407>🐳</emoji>"),
                ("💎", "<emoji document_id=5983589445687841895>🖥</emoji>"),
                ("🛡", "<emoji document_id=5422712776059534305>🌩</emoji>"),
                ("🌼", "<emoji document_id=5224219153077914783>❤️</emoji>"),
                ("🐧", "<emoji document_id=5361541227604878624>🐧</emoji>"),
                ("🧨", "<emoji document_id=5379774338733994368>🧨</emoji>"),
            ]:
                platform = platform.replace(emoji, icon)
        else:
            platform = platform[2:]

        return (
            self.config["custom_message"].format(
                me=me,
                version=_version,
                tlversion=f"<i>{legacytl.__version__}</i>",
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=f"{utils.formatted_uptime()}",
                cpu_usage=f"{await utils.get_cpu_usage_async()}%",
                ram_usage=f"{utils.get_ram_usage()} MB",
                branch=version.branch,
                hostname=lib_platform.node(),
                user=getpass.getuser(),
                kernel=lib_platform.uname().release,
                os=distro.name(pretty=True),
                label=(
                    utils.get_platform_emoji()
                    if self._client.legacy_me.premium
                    else "🌙 <b>Legacy</b>"
                ),
            )
            if self.config["custom_message"] and "-d" not in args
            else (
                f"<blockquote><b>{{}}</b></blockquote>\n\n<blockquote><b>{{}} {self.strings['owner']}:</b> {me}</blockquote>\n\n<blockquote><b>{{}}"
                f" {self.strings['version']}:</b> {_version} {build}\n<b>{{}}"
                f" {self.strings['branch']}:"
                f"</b> <code>{version.branch}</code>\n{upd}</blockquote>\n\n<blockquote><b>{{}}"
                f" {self.strings['prefix']}:</b> {prefix}\n<b>{{}}"
                f" {self.strings['uptime']}:"
                f"</b> {utils.formatted_uptime()}</blockquote>\n\n<blockquote><b>{{}}"
                f" {self.strings['cpu_usage']}:"
                f"</b> <i>~{await utils.get_cpu_usage_async()} %</i>\n<b>{{}}"
                f" {self.strings['ram_usage']}:"
                f"</b> <i>~{utils.get_ram_usage()} MB</i></blockquote>\n\n<blockquote><b>{{}}</b></blockquote>"
            ).format(
                (
                    utils.get_platform_emoji()
                    if self._client.legacy_me.premium
                    else "🌙 Legacy"
                ),
                "<emoji document_id=4904565554943099861>👾</emoji>",
                "<emoji document_id=4904936030232117798>⚙️</emoji>",
                "<emoji document_id=5172453033245672405>🌱</emoji>",
                "<emoji document_id=5220053623211305785>❓</emoji>",
                "<emoji document_id=5123230779593196220>⏰</emoji>",
                "<emoji document_id=5085022089103016925>⚡️</emoji>",
                "<emoji document_id=5118686540985271080>💼</emoji>",
                platform,
            )
        )

    @loader.command()
    async def infocmd(self, message):
        args = utils.get_args(message)
        custom_prefix = self.get_prefix(message.sender_id)
        media = self.config["banner_url"]
        if self.config["media_quote"]:
            await utils.answer(
                message,
                await self._render_info(args, custom_prefix),
                media=InputMediaWebPage(media, optional=True) if media else None,
                invert_media=True,
            )
        else:
            await utils.answer(
                message, await self._render_info(args, custom_prefix), file=media
            )

    @loader.command()
    async def ubinfo(self, message):
        await utils.answer(message, self.strings["desc"])

    @loader.command()
    async def setinfo(self, message):
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings["setinfo_no_args"])

        self.config["custom_message"] = args
        await utils.answer(message, self.strings["setinfo_success"])
