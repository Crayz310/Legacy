# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import re
import difflib
import inspect
import logging

from legacytl.extensions.html import CUSTOM_EMOJIS
from legacytl.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class Help(loader.Module):
    strings = {"name": "Help"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "core_emoji",
                "<emoji document_id=6030550768426159669>🛡</emoji>",
                lambda: "Core module bullet",
            ),
            loader.ConfigValue(
                "plain_emoji",
                "<emoji document_id=5861640841524680405>✅</emoji>",
                lambda: "Plain module bullet",
            ),
            loader.ConfigValue(
                "empty_emoji",
                "<emoji document_id=5251741320690551495>👎</emoji>",
                lambda: "Empty modules bullet",
            ),
            loader.ConfigValue(
                "desc_icon",
                "<emoji document_id=5253521692008917018>🌙</emoji>",
                lambda: "Desc emoji",
            ),
            loader.ConfigValue(
                "expandable",
                True,
                lambda: "If the blockquote will be expandable",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "hide_core_modules",
                False,
                lambda: "Hide all core modules",
                on_change=lambda: (
                    self.set(
                        "hide",
                        (
                            list(
                                {
                                    *self.get("hide", []),
                                    *[
                                        m.__class__.__name__
                                        for m in self.allmodules.modules
                                        if getattr(m, "__origin__", None) == "<core>"
                                    ],
                                }
                            )
                            if self.config["hide_core_modules"]
                            else [
                                m
                                for m in self.get("hide", [])
                                if getattr(self.lookup(m), "__origin__") != "<core>"
                            ]
                        ),
                    )
                ),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "show_cmds",
                True,
                lambda: "Displays a short list of commands next to the module",
                validator=loader.validators.Boolean(),
            ),
        )

    @loader.command()
    async def helphide(self, message: Message):
        if not (modules := utils.get_args_split_by(message, ["\n", ","])):
            await utils.answer(message, self.strings("no_mod"))
            return

        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in filter(lambda module: self.lookup(module), modules):
            module = self.lookup(module)
            module_origin = module.__origin__
            module = module.__class__.__name__

            if self.config["hide_core_modules"] and module_origin == "<core>":
                continue

            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings("hidden_shown").format(
                len(hidden),
                len(shown),
                "\n".join([f"👁‍🗨 <i>{m}</i>" for m in hidden]),
                "\n".join([f"👁 <i>{m}</i>" for m in shown]),
            ),
        )

    def find_aliases(self, command: str) -> list:
        """Find aliases for command"""
        aliases = []
        _command = self.allmodules.commands[command]
        if getattr(_command, "alias", None) and not (
            aliases := getattr(_command, "aliases", None)
        ):
            aliases = [_command.alias]
        if getattr(_command, "aliases", None):
            aliases = _command.aliases

        return aliases or []

    async def modhelp(self, message: Message, args: str):
        exact = True
        if not (module := self.lookup(args)):
            if method := self.allmodules.dispatch(
                args.lower().strip(self.get_prefix(message.sender_id))
            )[1]:
                module = method.__self__
            else:
                module = self.lookup(
                    next(
                        (
                            reversed(
                                sorted(
                                    [
                                        module.strings["name"]
                                        for module in self.allmodules.modules
                                    ],
                                    key=lambda x: difflib.SequenceMatcher(
                                        None,
                                        args.lower(),
                                        x,
                                    ).ratio(),
                                )
                            )
                        ),
                        None,
                    )
                )

                exact = False

        try:
            name = module.strings("name")
        except (KeyError, AttributeError):
            name = getattr(module, "name", "ERROR")

        _name = (
            "{} (v{}.{}.{})".format(
                utils.escape_html(name),
                module.__version__[0],
                module.__version__[1],
                module.__version__[2],
            )
            if hasattr(module, "__version__")
            else utils.escape_html(name)
        )

        reply = "{} <b>{}</b>:".format(
            "<emoji document_id=5253521692008917018>🌙</emoji>", _name, ""
        )
        if module.__doc__:
            reply += (
                "\n<i><emoji document_id=5879813604068298387>ℹ️</emoji> "
                + utils.escape_html(inspect.getdoc(module))
                + "\n</i>"
            )
        if isinstance(self.lookup(args), loader.Library):
            return await utils.answer(
                message,
                self.strings["lib_help"].format(name),
            )

        commands = {
            name: func
            for name, func in module.commands.items()
            if await self.allmodules.check_security(message, func)
        }

        if hasattr(module, "inline_handlers"):
            for name, fun in module.inline_handlers.items():
                reply += (
                    "\n<emoji document_id=5372981976804366741>🤖</emoji>"
                    " <code>{}</code> {}".format(
                        f"@{self.inline.bot_username} {name}",
                        (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc")
                        ),
                    )
                )

        for name, fun in commands.items():
            reply += (
                "\n<emoji document_id=5197195523794157505>▫️</emoji>"
                " <code>{}{}</code>{} {}".format(
                    utils.escape_html(self.get_prefix(message.sender_id)),
                    name,
                    (
                        " ({})".format(
                            ", ".join(
                                "<code>{}{}</code>".format(
                                    utils.escape_html(
                                        self.get_prefix(message.sender_id)
                                    ),
                                    alias,
                                )
                                for alias in self.find_aliases(name)
                            )
                        )
                        if self.find_aliases(name)
                        else ""
                    ),
                    (
                        utils.escape_html(inspect.getdoc(fun))
                        if fun.__doc__
                        else self.strings("undoc")
                    ),
                )
            )

        await utils.answer(
            message,
            reply
            + (f"\n\n{self.strings('not_exact')}" if not exact else "")
            + (
                f"\n\n{self.strings('core_notice')}"
                if module.__origin__.startswith("<core")
                else ""
            ),
        )

    @loader.command()
    async def help(self, message: Message):
        args = utils.get_args_raw(message)
        force = False
        only_hidden = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True
        if "-h" in args:
            args = args.replace(" -h", "").replace("-h", "")
            only_hidden = True

        if args:
            await self.modhelp(message, args)
            return

        hidden = self.get("hide", [])

        plain_ = []
        core_ = []
        no_commands_ = []

        for mod in self.allmodules.modules:
            if not hasattr(mod, "commands"):
                logger.debug("Module %s is not inited yet", mod.__class__.__name__)
                continue

            if len(mod.commands) == 0 and len(mod.inline_handlers) == 0:
                no_commands_ += [
                    "{} <code>{}</code>\n".format(
                        self.config["empty_emoji"], mod.strings["name"]
                    )
                ]
                continue

            if mod.__class__.__name__ in self.get("hide", []) and not force:
                continue

            tmp = ""

            try:
                name = mod.strings["name"]
            except KeyError:
                name = getattr(mod, "name", "ERROR")

            core = mod.__origin__.startswith("<core")
            tmp += "{} <code>{}</code>".format(
                self.config["core_emoji"] if core else self.config["plain_emoji"], name
            )
            first = True

            commands = [
                name
                for name, func in mod.commands.items()
                if await self.allmodules.check_security(message, func) or force
            ]

            if self.config["show_cmds"]:
                for cmd in commands:
                    if first:
                        tmp += f": ( {cmd}"
                        first = False
                    else:
                        tmp += f" | {cmd}"

            icommands = [
                name
                for name, func in mod.inline_handlers.items()
                if await self.inline.check_inline_security(
                    func=func,
                    user=message.sender_id,
                )
                or force
            ]

            if self.config["show_cmds"]:
                for cmd in icommands:
                    if first:
                        tmp += f": ( <emoji document_id=6030400221232501136>🤖</emoji> {cmd}"
                        first = False
                    else:
                        tmp += f" | <emoji document_id=6030400221232501136>🤖</emoji> {cmd}"

            if commands or icommands:
                tmp += " )\n" if self.config["show_cmds"] else "\n"
                if core:
                    core_ += [tmp]
                else:
                    plain_ += [tmp]

        def extract_name(line):
            match = re.search(
                r"[\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF]*\s*(name.*)", line
            )
            return match.group(1) if match else line

        hidden_mods = []
        if only_hidden:
            mod_names = []
            for mod in self.allmodules.modules:
                mod_names += [mod.__class__.__name__]
            for mod in hidden:
                if mod in mod_names:
                    hidden_mods += [
                        "{} <code>{}</code>\n".format(self.config["empty_emoji"], mod)
                    ]
        hidden_mods.sort(key=extract_name)

        plain_.sort(key=extract_name)
        core_.sort(key=extract_name)
        no_commands_.sort(key=extract_name)

        reply = self.strings("all_header").format(
            len(self.allmodules.modules),
            (
                0
                if force
                else sum(
                    module.__class__.__name__ in hidden
                    for module in self.allmodules.modules
                )
            ),
            len(no_commands_),
        )
        full_list = (
            core_ + plain_ + no_commands_
            if force
            else hidden_mods + no_commands_
            if only_hidden
            else core_ + plain_
        )
        await utils.answer(
            message,
            (self.config["desc_icon"] + " {}\n {}{}").format(
                reply,
                f"<blockquote {'expandable' if self.config['expandable'] else ''}>{''.join(full_list)}</blockquote>",
                (
                    ""
                    if self.lookup("Loader").fully_loaded
                    else f"\n\n{self.strings['partial_load']}"
                ),
            ),
        )

    @loader.command()
    async def support(self, message):
        await utils.answer(
            message,
            self.strings["support"].format(
                (
                    utils.get_platform_emoji()
                    if self._client.legacy_me.premium and CUSTOM_EMOJIS
                    else "🌙"
                )
            ),
        )
