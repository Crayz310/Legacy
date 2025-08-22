# ©️ Undefined & XDesai, 2025
# This file is a part of Legacy Userbot
# 🌐 https://github.com/Crayz310/Legacy
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Based on Dan Gazizullin's work
# 🌐 https://github.com/hikariatama/Hikka

import re

def compat(code: str) -> str:
    """
    Reformats modules, built for Hikka to work with Legacy
    :param code: code to reformat
    :return: reformatted code
    :rtype: str
    """

    # utils.get_platform_name → utils.get_named_platform
    code = re.sub(
        r"\butils\.get_platform_name\b",
        "utils.get_named_platform",
        code,
    )

    # import hikka.something → import legacy.something
    code = re.sub(
        r"\bimport\s+hikka(\.[\w\.]*)",
        r"import legacy\1",
        code,
    )

    # from hikka import ... → from legacy import ...
    code = re.sub(
        r"\bfrom\s+hikka\b",
        "from legacy",
        code,
    )

    # hikka. → legacy.
    code = re.sub(
        r"\bhikka\.",
        "legacy.",
        code,
    )

    # *.hikka_me → *.legacy_me
    code = re.sub(
        r"\b([\w\.-]+)\.hikka_me\b",
        r"\1.legacy_me",
        code,
    )

    return code
