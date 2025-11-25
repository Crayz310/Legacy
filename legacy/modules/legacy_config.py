# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import ast
import contextlib
import functools
import typing
from math import ceil

import legacytl
from legacytl.tl.types import Message

from .. import loader, translations, utils
from ..inline.types import InlineCall

# Everywhere in this module, we use the following naming convention:
# `obj_type` of non-core module = False
# `obj_type` of core module = True
# `obj_type` of library = "library"


@loader.tds
class LegacyConfigMod(loader.Module):
    strings = {"name": "LegacyConfig"}

    @staticmethod
    def prep_value(value: typing.Any, _cut: bool = False) -> typing.Any:
        if isinstance(value, str):
            val = (
                f"{utils.escape_html(str(value)[:24])}..."
                if _cut and len(str(value)) > 24
                else utils.escape_html(str(value).strip())
            )
            return f"</b><code>{val}</code><b>"

        if isinstance(value, list) and value:
            val = [
                (
                    f"<code>{utils.escape_html(str(item)[:16]).strip()}...</code>"
                    if _cut and len(str(item)) > 16
                    else f"<code>{utils.escape_html(str(item)).strip()}</code>"
                )
                for item in value
            ]
            return "</b><code>[</code>" + ", ".join(val) + "<code>]</code><b>"
        return f"</b><code>{utils.escape_html(f'{str(value)[:24]}...') if len(str(value)) > 24 else utils.escape_html(str(value))}</code><b>"

    def hide_value(self, value: typing.Any) -> str:
        if isinstance(value, list) and value:
            return self.prep_value(["*" * len(str(i)) for i in value], True)

        return self.prep_value("*" * len(str(value)), True)

    def _get_value(self, mod: str, option: str) -> str:
        return (
            self.prep_value(self.lookup(mod).config[option], True)
            if (
                not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
            )
            else self.hide_value(self.lookup(mod).config[option])
        )

    def _split_long_config(
        self, text: str, page: int = 0
    ) -> typing.Tuple[str, int, bool]:
        parse_mode = legacytl.utils.sanitize_parse_mode("html")
        _txt, entities = parse_mode.parse(text)  # type: ignore
        entities = [
            e
            for e in entities
            if not isinstance(e, legacytl.tl.types.MessageEntityBlockquote)  # type: ignore
        ]
        pages = list(utils.smart_split(_txt, entities, 2048))
        total_pages = len(pages)
        has_pagination = total_pages > 1

        if page >= total_pages:
            page = total_pages - 1
        elif page < 0:
            page = 0

        current_text = pages[page]

        if has_pagination:
            current_text += self.strings["page_num"].format(page + 1, total_pages)

        return current_text, total_pages, has_pagination

    async def inline__config_page(
        self,
        call: InlineCall,
        page: int,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
        force_hidden: bool = False,
    ):
        await self.inline__configure_option(
            call, mod, option, force_hidden, obj_type, page
        )

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings[
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__reset_default(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        mod_instance = self.lookup(mod)
        mod_instance.config[option] = mod_instance.config.getdef(option)

        await call.edit(
            self.strings[
                "option_reset" if isinstance(obj_type, bool) else "option_reset_lib"
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
        )

    async def inline__set_bool(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator
        doc = utils.escape_html(
            next(
                (
                    validator.doc[lang]
                    for lang in self._db.get(translations.__name__, "lang", "en").split(
                        " "
                    )
                    if lang in validator.doc
                ),
                validator.doc["en"],
            )
        )

        config_text = self.strings[
            (
                "configuring_option"
                if isinstance(obj_type, bool)
                else "configuring_option_lib"
            )
        ].format(
            utils.escape_html(option),
            utils.escape_html(mod),
            utils.escape_html(self.lookup(mod).config.getdoc(option)),
            self.prep_value(self.lookup(mod).config.getdef(option)),
            (
                self.prep_value(self.lookup(mod).config[option])
                if not validator or validator.internal_id != "Hidden"
                else self.hide_value(self.lookup(mod).config[option])
            ),
            (
                self.strings["typehint"].format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
                if doc
                else ""
            ),
        )

        formatted_text, total_pages, has_pagination = self._split_long_config(
            config_text
        )

        markup = self._generate_bool_markup(mod, option, obj_type)

        if has_pagination:
            pagination_row = self.inline.build_pagination(
                callback=functools.partial(
                    self.inline__config_page,
                    mod=mod,
                    option=option,
                    obj_type=obj_type,
                    force_hidden=(validator and validator.internal_id == "Hidden"),
                ),
                total_pages=total_pages,
                current_page=1,
            )
            markup = pagination_row + markup

        await call.edit(
            formatted_text,
            reply_markup=markup,
        )

        await call.answer("✅")

    def _generate_bool_markup(
        self,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        return [
            [
                *(
                    [
                        {
                            "text": f"❌ {self.strings['set']} `False`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, False),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    else [
                        {
                            "text": f"✅ {self.strings['set']} `True`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, True),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                )
            ],
            [
                *(
                    [
                        {
                            "text": self.strings["set_default_btn"],
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings["back_btn"],
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings["close_btn"], "action": "close"},
            ],
        ]

    async def inline__add_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            with contextlib.suppress(Exception):
                query = ast.literal_eval(query)

            if isinstance(query, (set, tuple)):
                query = list(query)  # type: ignore

            if not isinstance(query, list):
                query = [query]  # type: ignore

            self.lookup(mod).config[option] = self.lookup(mod).config[option] + query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings[
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__remove_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            with contextlib.suppress(Exception):
                query = ast.literal_eval(query)

            if isinstance(query, (set, tuple)):
                query = list(query)  # type: ignore

            if not isinstance(query, list):
                query = [query]  # type: ignore

            query = list(map(str, query))  # type: ignore

            old_config_len = len(self.lookup(mod).config[option])

            self.lookup(mod).config[option] = [
                i for i in self.lookup(mod).config[option] if str(i) not in query
            ]

            if old_config_len == len(self.lookup(mod).config[option]):
                raise loader.validators.ValidationError(
                    f"Nothing from passed value ({self.prep_value(query)}) is not in"
                    " target list"
                )
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings[
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    def _generate_series_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        return [
            [
                {
                    "text": self.strings["enter_value_btn"],
                    "input": self.strings["enter_value_desc"],
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            [
                *(
                    [
                        {
                            "text": self.strings["remove_item_btn"],
                            "input": self.strings["remove_item_desc"],
                            "handler": self.inline__remove_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"obj_type": obj_type},
                        },
                        {
                            "text": self.strings["add_item_btn"],
                            "input": self.strings["add_item_desc"],
                            "handler": self.inline__add_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"obj_type": obj_type},
                        },
                    ]
                    if self.lookup(mod).config[option]
                    else []
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings["set_default_btn"],
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings["back_btn"],
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings["close_btn"], "action": "close"},
            ],
        ]

    async def _choice_set_value(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings[
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
        )

        await call.answer("✅")

    async def _multi_choice_set_value(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            current_val = self.lookup(mod).config._config[option].value.copy()
            if value in current_val:
                current_val.remove(value)
            else:
                current_val.append(value)
            self.lookup(mod).config._config[option].value = current_val

            self.lookup(mod).config.reload()
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings["validation_error"].format(e.args[0]),
                reply_markup={
                    "text": self.strings["try_again"],
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await self.inline__configure_option(call, mod, option, False, obj_type)
        await call.answer("✅")

    def _generate_choice_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        possible_values = list(
            self.lookup(mod)
            .config._config[option]
            .validator.validate.keywords["possible_values"]
        )
        return [
            [
                {
                    "text": self.strings["enter_value_btn"],
                    "input": self.strings["enter_value_desc"],
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            *utils.chunks(
                [
                    {
                        "text": (
                            f"{'☑️' if self.lookup(mod).config[option] == value else '🔘'} "
                            f"{value if len(str(value)) < 20 else str(value)[:20]}"
                        ),
                        "callback": self._choice_set_value,
                        "args": (mod, option, value, obj_type),
                    }
                    for value in possible_values
                ],
                2,
            )[
                : (
                    6
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else 7
                )
            ],
            [
                *(
                    [
                        {
                            "text": self.strings["set_default_btn"],
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings["back_btn"],
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings["close_btn"], "action": "close"},
            ],
        ]

    def _generate_multi_choice_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        possible_values = list(
            self.lookup(mod)
            .config._config[option]
            .validator.validate.keywords["possible_values"]
        )
        return [
            [
                {
                    "text": self.strings["enter_value_btn"],
                    "input": self.strings["enter_value_desc"],
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            *utils.chunks(
                [
                    {
                        "text": (
                            f"{'☑️' if value in self.lookup(mod).config[option] else '◻️'} "
                            f"{value if len(str(value)) < 20 else str(value)[:20]}"
                        ),
                        "callback": self._multi_choice_set_value,
                        "args": (mod, option, value, obj_type),
                    }
                    for value in possible_values
                ],
                2,
            )[
                : (
                    6
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else 7
                )
            ],
            [
                *(
                    [
                        {
                            "text": self.strings["set_default_btn"],
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings["back_btn"],
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings["close_btn"], "action": "close"},
            ],
        ]

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
        force_hidden: bool = False,
        obj_type: typing.Union[bool, str] = False,
        page: int = 0,
    ):
        module = self.lookup(mod)
        args = [
            utils.escape_html(config_opt),
            utils.escape_html(mod),
            utils.escape_html(module.config.getdoc(config_opt)),
            self.prep_value(module.config.getdef(config_opt)),
            (
                self.prep_value(module.config[config_opt])
                if not module.config._config[config_opt].validator
                or module.config._config[config_opt].validator.internal_id != "Hidden"
                or force_hidden
                else self.hide_value(module.config[config_opt])
            ),
        ]

        if (
            module.config._config[config_opt].validator
            and module.config._config[config_opt].validator.internal_id == "Hidden"
        ):
            additonal_button_row = (
                [
                    [
                        {
                            "text": self.strings["hide_value"],
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, False, obj_type, page),
                        }
                    ]
                ]
                if force_hidden
                else [
                    [
                        {
                            "text": self.strings["show_hidden"],
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, True, obj_type, page),
                        }
                    ]
                ]
            )
        else:
            additonal_button_row = []

        try:
            validator = module.config._config[config_opt].validator
            doc = utils.escape_html(
                next(
                    (
                        validator.doc[lang]
                        for lang in self._db.get(
                            translations.__name__, "lang", "en"
                        ).split(" ")
                        if lang in validator.doc
                    ),
                    validator.doc["en"],
                )
            )
        except Exception:
            doc = None
            validator = None
            args += [""]
        else:
            args += [
                self.strings["typehint"].format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
            ]

        config_text = self.strings[
            (
                "configuring_option"
                if isinstance(obj_type, bool)
                else "configuring_option_lib"
            )
        ].format(*args)

        formatted_text, total_pages, has_pagination = self._split_long_config(
            config_text, page
        )

        main_markup = []
        if validator:
            if validator.internal_id == "Boolean":
                main_markup = self._generate_bool_markup(mod, config_opt, obj_type)
            elif validator.internal_id == "Series":
                main_markup = self._generate_series_markup(
                    call, mod, config_opt, obj_type
                )
            elif validator.internal_id == "Choice":
                main_markup = self._generate_choice_markup(
                    call, mod, config_opt, obj_type
                )
            elif validator.internal_id == "MultiChoice":
                main_markup = self._generate_multi_choice_markup(
                    call, mod, config_opt, obj_type
                )
            else:
                main_markup = [
                    [
                        {
                            "text": self.strings["enter_value_btn"],
                            "input": self.strings["enter_value_desc"],
                            "handler": self.inline__set_config,
                            "args": (mod, config_opt, call.inline_message_id),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ],
                    [
                        {
                            "text": self.strings["set_default_btn"],
                            "callback": self.inline__reset_default,
                            "args": (mod, config_opt),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ],
                    [
                        {
                            "text": self.strings["back_btn"],
                            "callback": self.inline__configure,
                            "args": (mod,),
                            "kwargs": {"obj_type": obj_type},
                        },
                        {"text": self.strings["close_btn"], "action": "close"},
                    ],
                ]
        else:
            main_markup = [
                [
                    {
                        "text": self.strings["enter_value_btn"],
                        "input": self.strings["enter_value_desc"],
                        "handler": self.inline__set_config,
                        "args": (mod, config_opt, call.inline_message_id),
                        "kwargs": {"obj_type": obj_type},
                    }
                ],
                [
                    {
                        "text": self.strings["set_default_btn"],
                        "callback": self.inline__reset_default,
                        "args": (mod, config_opt),
                        "kwargs": {"obj_type": obj_type},
                    }
                ],
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ],
            ]

        if has_pagination:
            pagination_row = self.inline.build_pagination(
                callback=functools.partial(
                    self.inline__config_page,
                    mod=mod,
                    option=config_opt,
                    obj_type=obj_type,
                    force_hidden=force_hidden,
                ),
                total_pages=total_pages,
                current_page=page + 1,
            )
            main_markup = pagination_row + main_markup

        await call.edit(
            formatted_text,
            reply_markup=additonal_button_row + main_markup,
        )

    async def inline__configure(
        self,
        call: InlineCall,
        mod: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        btns = [
            {
                "text": param,
                "callback": self.inline__configure_option,
                "args": (mod, param),
                "kwargs": {"obj_type": obj_type},
            }
            for param in self.lookup(mod).config
        ]

        await call.edit(
            self.strings[
                "configuring_mod" if isinstance(obj_type, bool) else "configuring_lib"
            ].format(
                utils.escape_html(mod),
                "\n".join(
                    [
                        "▫️ <code>{}</code>: <b>{}</b>".format(
                            utils.escape_html(key),
                            self._get_value(mod, key),
                        )
                        for key in self.lookup(mod).config
                    ]
                ),
            ),
            reply_markup=list(utils.chunks(btns, 2))
            + [
                [
                    {
                        "text": self.strings["back_btn"],
                        "callback": self.inline__global_config,
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings["close_btn"], "action": "close"},
                ]
            ],
        )

    async def inline__choose_category(self, call: typing.Union[Message, InlineCall]):
        await utils.answer(
            call,  # type: ignore
            self.strings["choose_core"],
            reply_markup=[
                [
                    {
                        "text": self.strings["builtin"],
                        "callback": self.inline__global_config,
                        "kwargs": {"obj_type": True},
                    },
                    {
                        "text": self.strings["external"],
                        "callback": self.inline__global_config,
                    },
                ],
                *(
                    [
                        [
                            {
                                "text": self.strings["libraries"],
                                "callback": self.inline__global_config,
                                "kwargs": {"obj_type": "library"},
                            }
                        ]
                    ]
                    if self.allmodules.libraries  # type: ignore
                    and any(hasattr(lib, "config") for lib in self.allmodules.libraries)  # type: ignore
                    else []
                ),
                [{"text": self.strings["close_btn"], "action": "close"}],
            ],
        )

    async def inline__global_config(
        self,
        call: InlineCall,
        page: int = 0,
        obj_type: typing.Union[bool, str] = False,
    ):
        if isinstance(obj_type, bool):
            to_config = [
                mod.strings("name")
                for mod in self.allmodules.modules  # type: ignore
                if hasattr(mod, "config")
                and callable(mod.strings)
                and (mod.__origin__.startswith("<core") or not obj_type)
                and (not mod.__origin__.startswith("<core") or obj_type)
            ]
        else:
            to_config = [
                lib.name
                for lib in self.allmodules.libraries
                if hasattr(lib, "config")  # type: ignore
            ]

        to_config.sort()  # type: ignore

        kb = []
        for mod_row in utils.chunks(
            to_config[page * 5 * 3 : (page + 1) * 5 * 3],
            3,
        ):
            row = [
                {
                    "text": btn,
                    "callback": self.inline__configure,
                    "args": (btn,),
                    "kwargs": {"obj_type": obj_type},
                }
                for btn in mod_row
                if self.lookup(btn) is not False
            ]
            kb += [row]

        if len(to_config) > 5 * 3:
            kb += self.inline.build_pagination(
                callback=functools.partial(
                    self.inline__global_config, obj_type=obj_type
                ),
                total_pages=ceil(len(to_config) / (5 * 3)),
                current_page=page + 1,
            )

        kb += [
            [
                {
                    "text": self.strings["back_btn"],
                    "callback": self.inline__choose_category,
                },
                {"text": self.strings["close_btn"], "action": "close"},
            ]
        ]

        await call.edit(
            self.strings[
                "configure" if isinstance(obj_type, bool) else "configure_lib"
            ],
            reply_markup=kb,
        )

    @loader.command(alias="cfg")
    async def configcmd(self, message: Message):
        args = utils.get_args_raw(message)  # type: ignore
        if self.lookup(args) and hasattr(self.lookup(args), "config"):
            form = await self.inline.form("🌙", message, silent=True)
            mod = self.lookup(args)
            if isinstance(mod, loader.Library):
                type_ = "library"
            else:
                type_ = mod.__origin__.startswith("<core")

            await self.inline__configure(form, args, obj_type=type_)
            return

        await self.inline__choose_category(message)

    @loader.command(alias="fcfg")
    async def fconfig(self, message: Message):
        args = utils.get_args_raw(message).split(maxsplit=2)  # type: ignore

        if len(args) < 3:
            await utils.answer(message, self.strings["args"])  # type: ignore
            return

        mod, option, value = args

        if not (instance := self.lookup(mod)):
            await utils.answer(message, self.strings["no_mod"])  # type: ignore
            return

        if option not in instance.config:
            await utils.answer(message, self.strings["no_option"])  # type: ignore
            return

        instance.config[option] = value
        await utils.answer(
            message,  # type: ignore
            self.strings[
                (
                    "option_saved"
                    if isinstance(instance, loader.Module)
                    else "option_saved_lib"
                )
            ].format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self._get_value(mod, option),
            ),
        )
