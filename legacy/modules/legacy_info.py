# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import git
from legacytl.types import InputMediaWebPage
from legacytl.utils import get_display_name
from .. import loader, utils, version
import platform as lib_platform
import getpass
import distro
import subprocess


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
                "neofetch_args",
                "--stdout",
                lambda: "Аргументы для neofetch",
            ),
        )

    async def _get_neofetch_output(self) -> str:
        try:
            args = self.config["neofetch_args"].split()
            result = subprocess.run(
                ["neofetch"] + args,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return f"{utils.escape_html(result.stdout)}"
            else:
                return f"Ошибка neofetch: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "neofetch: timeout"
        except FileNotFoundError:
            return "neofetch не установлен"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    async def _render_info(self, args: list, custom_prefix: str) -> str:
        if "--neofetch" in args or "-n" in args:
            return await self._get_neofetch_output()

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

        for emoji, icon in [
            ("🍊", "<emoji document_id=5449599833973203438>🧡</emoji>"),
            ("🍇", "<emoji document_id=5449468596952507859>💜</emoji>"),
            ("🍀", "<emoji document_id=5395325195542078574>🍀</emoji>"),
            ("🚂", "<emoji document_id=5359595190807962128>🚂</emoji>"),
            ("🐳", "<emoji document_id=5431815452437257407>🐳</emoji>"),
            ("🕶", "<emoji document_id=5407025283456835913>📱</emoji>"),
            ("💎", "<emoji document_id=5471952986970267163>💎</emoji>"),
            ("🛡", "<emoji document_id=5422712776059534305>🌩</emoji>"),
            ("☕️", "<emoji document_id=6025967359716497965>☕️</emoji>"),
            ("🌼", "<emoji document_id=5224219153077914783>❤️</emoji>"),
            ("🎡", "<emoji document_id=5226711870492126219>🎡</emoji>"),
            ("🐧", "<emoji document_id=5361541227604878624>🐧</emoji>"),
            ("🦊", "<emoji document_id=5283051451889756068>🦊</emoji>"),
            ("🧨", "<emoji document_id=5379774338733994368>🧨</emoji>"),
        ]:
            platform = platform.replace(emoji, icon)

        neofetch = await self._get_neofetch_output()

        return (
            self.config["custom_message"].format(
                me=me,
                version=_version,
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
                neofetch=neofetch,
            )
            if self.config["custom_message"] and "-d" not in args
            else (
                f"<b>{{}}</b>\n\n<b>{{}} {self.strings('owner')}:</b> {me}\n\n<b>{{}}"
                f" {self.strings['version']}:</b> {_version} {build}\n<b>{{}}"
                f" {self.strings['branch']}:"
                f"</b> <code>{version.branch}</code>\n{upd}\n\n<b>{{}}"
                f" {self.strings['prefix']}:</b> {prefix}\n<b>{{}}"
                f" {self.strings['uptime']}:"
                f"</b> {utils.formatted_uptime()}\n\n<b>{{}}"
                f" {self.strings['cpu_usage']}:"
                f"</b> <i>~{await utils.get_cpu_usage_async()} %</i>\n<b>{{}}"
                f" {self.strings['ram_usage']}:"
                f"</b> <i>~{utils.get_ram_usage()} MB</i>\n<b>{{}}</b>"
            ).format(
                (
                    utils.get_platform_emoji()
                    if self._client.legacy_me.premium
                    else "🌙 Legacy"
                ),
                "<emoji document_id=5373141891321699086>😎</emoji>",
                "<emoji document_id=5469741319330996757>💫</emoji>",
                "<emoji document_id=5449918202718985124>🌳</emoji>",
                "<emoji document_id=5472111548572900003>⌨️</emoji>",
                "<emoji document_id=5451646226975955576>⌛️</emoji>",
                "<emoji document_id=5431449001532594346>⚡️</emoji>",
                "<emoji document_id=5359785904535774578>💼</emoji>",
                platform,
            )
        )

    @loader.command()
    async def infocmd(self, message):
        args = utils.get_args(message)
        custom_prefix = self.get_prefix(message.sender_id)
        await utils.answer(
            message,
            await self._render_info(args, custom_prefix),
            media=(
                InputMediaWebPage(self.config["banner_url"])
                if self.config["banner_url"]
                else None
            ),
            invert_media=True,
        )

    @loader.command()
    async def ubinfo(self, message):
        await utils.answer(message, self.strings("desc"))

    @loader.command()
    async def setinfo(self, message):
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))
