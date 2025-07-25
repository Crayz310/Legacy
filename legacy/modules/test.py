# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import logging
import os
import random
import time
import typing
from io import BytesIO
import platform as lib_platform
import getpass

from legacytl.tl.types import Message

from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")

if not os.path.isdir(DEBUG_MODS_DIR):
    os.mkdir(DEBUG_MODS_DIR, mode=0o755)

for mod in os.scandir(DEBUG_MODS_DIR):
    os.remove(mod.path)


@loader.tds
class TestMod(loader.Module):
    strings = {"name": "Tester"}

    def __init__(self):
        self._memory = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "force_send_all",
                False,
                (
                    "⚠️ Do not touch, if you don't know what it does!\nBy default, "
                    " Legacy will try to determine, which client caused logs. E.g. there"
                    " is a module TestModule installed on Client1 and TestModule2 on"
                    " Client2. By default, Client2 will get logs from TestModule2, and"
                    " Client1 will get logs from TestModule. If this option is enabled,"
                    " Legacy will send all logs to Client1 and Client2, even if it is"
                    " not the one that caused the log."
                ),
                validator=loader.validators.Boolean(),
                on_change=self._pass_config_to_logger,
            ),
            loader.ConfigValue(
                "tglog_level",
                "INFO",
                (
                    "⚠️ Do not touch, if you don't know what it does!\n"
                    "Minimal loglevel for records to be sent in Telegram."
                ),
                validator=loader.validators.Choice(
                    ["INFO", "WARNING", "ERROR", "CRITICAL"]
                ),
                on_change=self._pass_config_to_logger,
            ),
            loader.ConfigValue(
                "ignore_common",
                True,
                "Ignore common errors (e.g. 'TypeError' in legacytl)",
                validator=loader.validators.Boolean(),
                on_change=self._pass_config_to_logger,
            ),
            loader.ConfigValue(
                "Text_Of_Ping",
                "<emoji document_id=5920515922505765329>⚡️</emoji> <b>𝙿𝚒𝚗𝚐: </b><code>{ping}</code><b> 𝚖𝚜 </b>\n<emoji document_id=5900104897885376843>🕓</emoji><b> 𝚄𝚙𝚝𝚒𝚖𝚎: </b><code>{uptime}</code>",
                lambda: self.strings["configping"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "hint",
                None,
                lambda: self.strings["hint"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "ping_emoji",
                "<emoji document_id=5253521692008917018>🌙</emoji>",
                lambda: self.strings["ping_emoji"],
                validator=loader.validators.String(),
            ),
        )

    def _pass_config_to_logger(self):
        logging.getLogger().handlers[0].force_send_all = self.config["force_send_all"]
        logging.getLogger().handlers[0].tg_level = {
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }[self.config["tglog_level"]]
        logging.getLogger().handlers[0].ignore_common = self.config["ignore_common"]

    @loader.command()
    async def clearlogs(self, message: Message):
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    @loader.loop(interval=1, autostart=True)
    async def watchdog(self):
        if not os.path.isdir(DEBUG_MODS_DIR):
            return

        try:
            for module in os.scandir(DEBUG_MODS_DIR):
                last_modified = os.stat(module.path).st_mtime
                cls_ = module.path.split("/")[-1].split(".py")[0]

                if cls_ not in self._memory:
                    self._memory[cls_] = last_modified
                    continue

                if self._memory[cls_] == last_modified:
                    continue

                self._memory[cls_] = last_modified
                logger.debug("Reloading debug module %s", cls_)
                with open(module.path, "r") as f:
                    try:
                        await next(
                            module
                            for module in self.allmodules.modules
                            if module.__class__.__name__ == "LoaderMod"
                        ).load_module(
                            f.read(),
                            None,
                            save_fs=False,
                        )
                    except Exception:
                        logger.exception("Failed to reload module in watchdog")
        except Exception:
            logger.exception("Failed debugging watchdog")
            return

    @loader.command()
    async def debugmod(self, message: Message):
        args = utils.get_args_raw(message)
        instance = None
        for module in self.allmodules.modules:
            if (
                module.__class__.__name__.lower() == args.lower()
                or module.strings["name"].lower() == args.lower()
            ):
                if os.path.isfile(
                    os.path.join(
                        DEBUG_MODS_DIR,
                        f"{module.__class__.__name__}.py",
                    )
                ):
                    os.remove(
                        os.path.join(
                            DEBUG_MODS_DIR,
                            f"{module.__class__.__name__}.py",
                        )
                    )

                    try:
                        delattr(module, "legacy_debug")
                    except AttributeError:
                        pass

                    await utils.answer(message, self.strings("debugging_disabled"))
                    return

                module.legacy_debug = True
                instance = module
                break

        if not instance:
            await utils.answer(message, self.strings("bad_module"))
            return

        with open(
            os.path.join(
                DEBUG_MODS_DIR,
                f"{instance.__class__.__name__}.py",
            ),
            "wb",
        ) as f:
            f.write(inspect.getmodule(instance).__loader__.data)

        await utils.answer(
            message,
            self.strings("debugging_enabled").format(instance.__class__.__name__),
        )

    async def _inline_back(self, call):
        await utils.answer(
            call,
            self.strings("choose_loglevel"),
            reply_markup=utils.chunks(
                [
                    {
                        "text": name,
                        "callback": self.logs,
                        "args": (False, level),
                    }
                    for name, level in [
                        ("☢️ Critical", 50),
                        ("🚫 Error", 40),
                        ("⚠️ Warning", 30),
                        ("ℹ️ Info", 20),
                        ("🐞 Debug", 10),
                        ("🧑‍💻 All", 0),
                    ]
                ],
                2,
            )
            + [[{"text": self.strings("cancel"), "action": "close"}]],
        )
        await call.answer()

    @loader.command()
    async def logs(
        self,
        message: typing.Union[Message, InlineCall],
        force: bool = False,
        lvl: typing.Union[int, None] = None,
    ):
        if not isinstance(lvl, int):
            args = utils.get_args_raw(message)
            try:
                try:
                    lvl = int(args.split()[0])
                except ValueError:
                    lvl = getattr(logging, args.split()[0].upper(), None)
            except IndexError:
                lvl = None

        if not isinstance(lvl, int):
            try:
                if not self.inline.init_complete or not await self.inline.form(
                    text=self.strings("choose_loglevel"),
                    reply_markup=utils.chunks(
                        [
                            {
                                "text": name,
                                "callback": self.logs,
                                "args": (False, level),
                            }
                            for name, level in [
                                ("☢️ Critical", 50),
                                ("🚫 Error", 40),
                                ("⚠️ Warning", 30),
                                ("ℹ️ Info", 20),
                                ("🐞 Debug", 10),
                                ("🧑‍💻 All", 0),
                            ]
                        ],
                        2,
                    )
                    + [[{"text": self.strings("cancel"), "action": "close"}]],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                "\n".join(
                    handler.dumps(lvl, client_id=self._client.tg_id)
                    if "client_id" in inspect.signature(handler.dumps).parameters
                    else handler.dumps(lvl)
                )
                for handler in logging.getLogger().handlers
            ]
        )

        named_lvl = (
            lvl
            if lvl not in logging._levelToName
            else logging._levelToName[lvl]  # skipcq: PYL-W0212
        )

        if (
            lvl < logging.WARNING
            and not force
            and (
                not isinstance(message, Message)
                or "force_insecure" not in message.raw_text.lower()
            )
        ):
            try:
                if not self.inline.init_complete:
                    raise

                cfg = {
                    "text": self.strings("confidential").format(named_lvl),
                    "reply_markup": [
                        {
                            "text": self.lookup("LegacyConfig").strings["back_btn"],
                            "callback": self._inline_back,
                        },
                        {
                            "text": self.strings("send_anyway"),
                            "callback": self.logs,
                            "args": [True, lvl],
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                }
                if isinstance(message, Message):
                    if not await self.inline.form(**cfg, message=message):
                        raise
                else:
                    await message.edit(**cfg)
            except Exception:
                await utils.answer(
                    message,
                    self.strings("confidential_text").format(named_lvl),
                )

            return

        if len(logs) <= 2:
            if isinstance(message, Message):
                await utils.answer(
                    message,
                    self.strings("no_logs").format(named_lvl),
                    reply_markup=[
                        {
                            "text": self.lookup("LegacyConfig").strings["back_btn"],
                            "callback": self._inline_back,
                        }
                    ],
                )
            else:
                await message.edit(
                    self.strings("no_logs").format(named_lvl),
                    reply_markup=[
                        {
                            "text": self.lookup("LegacyConfig").strings["back_btn"],
                            "callback": self._inline_back,
                        }
                    ],
                )
                await message.unload()

            return

        logs = self.lookup("evaluator").censor(logs)

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = "legacy-logs.txt"

        ghash = utils.get_git_hash()

        other = (
            utils.get_version_raw(),
            (
                " <a"
                f' href="https://github.com/Crayz310/Legacy/commit/{ghash}">@{ghash[:8]}</a>'
                if ghash
                else ""
            ),
        )

        await message.delete()

        if isinstance(message, Message):
            await utils.answer(
                message,
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )
        else:
            await self._client.send_file(
                message.form["chat"],
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
                reply_to=message.form["top_msg_id"],
            )

    @loader.command()
    async def suspend(self, message: Message):
        try:
            time_sleep = float(utils.get_args_raw(message))
            await utils.answer(
                message,
                self.strings("suspended").format(time_sleep),
            )
            time.sleep(time_sleep)
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time"))

    @loader.command()
    async def ping(self, message: Message):
        start = time.perf_counter_ns()
        message = await utils.answer(message, self.config["ping_emoji"])

        await utils.answer(
            message,
            self.config["Text_Of_Ping"].format(
                ping=f"{round((time.perf_counter_ns() - start) / 10**6, 3)} ms",
                uptime=f"{utils.formatted_uptime()}",
                ping_hint=(
                    (self.config["hint"]) if random.choice([0, 0, 1]) == 1 else ""
                ),
                hostname=lib_platform.node(),
                user=getpass.getuser(),
            ),
        )

    async def client_ready(self):
        chat, _ = await utils.asset_channel(
            self._client,
            "legacy-logs",
            "🌙 Your Legacy logs will appear in this chat",
            silent=True,
            invite_bot=True,
            avatar=f"{main.LOGS_PATH}",
        )

        self.logchat = int(f"-100{chat.id}")

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug("Bot logging installed for %s", self.logchat)

        self._pass_config_to_logger()
