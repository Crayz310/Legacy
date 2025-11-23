"""Entry point. Checks for user and starts main script"""

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import getpass
import os
import subprocess
import sys
import time


def deps():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-q",
            "--disable-pip-version-check",
            "--no-warn-script-location",
            "-r",
            "requirements.txt",
        ],
        check=True,
    )


def start():
    from . import log, main
    from ._internal import restart

    if (
        getpass.getuser() == "root"
        and "--root" not in " ".join(sys.argv)
        and all(trigger not in os.environ for trigger in {"DOCKER", "GOORM", "NO_SUDO"})
    ):
        print("🚫" * 15)
        print("You attempted to run Legacy on behalf of root user")
        print("Please, create a new user and restart script")
        print("If this action was intentional, pass --root argument instead")
        print("🚫" * 15)
        print()
        print("Type force_insecure to ignore this warning")
        print("Type no_sudo if your system has no sudo (Debian vibes)")
        inp = input("> ").lower()
        if inp != "force_insecure":
            sys.exit(1)
        elif inp == "no_sudo":
            os.environ["NO_SUDO"] = "1"
            print("Added NO_SUDO in your environment variables")
            restart()

    if sys.version_info < (3, 8, 0):
        print("🚫 Error: you must use at least Python version 3.8.0")
        sys.exit(1)

    if __package__ != "legacy":
        print(
            "🚫 Error: you cannot run this as a script; you must execute as a package"
        )
        sys.exit(1)

    try:
        import legacytl

        if tuple(map(int, legacytl.__version__.split("."))) < (1, 7, 5):
            raise ImportError
    except Exception:
        deps()
        restart()

    log.init()

    os.environ.pop("HIKKA_DO_NOT_RESTART", None)
    os.environ.pop("HIKKA_DO_NOT_RESTART2", None)

    main.legacy.main()


try:
    start()
except ImportError as e:
    print("📦 Trying to install missing dependencies from requirements.txt...")
    try:
        deps()
    except subprocess.CalledProcessError as deps_err:
        print("❌ Failed to install requirements")
        raise deps_err

    start()
except Exception as e2:
    print("❌ Failed to start Legacy")
    print(e2)

    if "DOCKER" in os.environ:
        time.sleep(9999)

    sys.exit(1)
