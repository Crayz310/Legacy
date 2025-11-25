# ©️ Undefined & XDesai, 2025
# This file is a part of Legacy Userbot
# 🌐 https://github.com/Crayz310/Legacy
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Based on Dan Gazizullin's work
# 🌐 https://github.com/hikariatama/Hikka

from legacytl.errors import (
    FloodWaitError,
    PhoneNumberUnoccupiedError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
)
from legacytl.password import compute_check
from legacytl.sessions import MemorySession
from legacytl.tl.functions.account import GetPasswordRequest
from legacytl.tl.functions.auth import CheckPasswordRequest
from legacytl.utils import parse_phone

from . import main
from .tl_cache import CustomTelegramClient
from ._internal import restart
from .version import __version__

import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Handles user authentication for Telegram using legacytl (Telethon-based client)

    Features:
        - Sends authentication codes via Telegram
        - Signs in with code and optional 2FA password
        - Manages pending client state
        - Finalizes and stores the authenticated session
    """

    def __init__(self):
        """
        Initializes the authentication manager with API and connection settings
        """
        self._pending_client = None
        self._2fa_needed = None
        self.api_token = main.legacy.api_token
        self.connection = main.legacy.conn
        self.proxy = main.legacy.proxy

    def _get_client(self) -> CustomTelegramClient:
        """
        Creates a new temporary Telegram client using memory session

        Returns:
            CustomTelegramClient: A configured Telegram client instance
        """
        return CustomTelegramClient(
            MemorySession(),
            self.api_token.ID,
            self.api_token.HASH,
            connection=self.connection,
            proxy=self.proxy,
            connection_retries=None,
            device_model=main.get_app_name(),
            system_version=main.generate_random_system_version(),
            app_version=__version__,
            lang_code="en",
            system_lang_code="en-US",
        )

    def is_2fa_needed(self) -> bool:
        """
        Checks whether 2FA password is required for the current authentication session

        Returns:
            bool: True if a 2FA password is required, False otherwise
        """
        return bool(self._2fa_needed)

    async def send_tg_code(self, phone: str):
        """
        Sends a Telegram login code to the specified phone number

        Args:
            phone (str): The user's phone number in readable format

        Raises:
            ValueError: If the phone number is invalid or not registered
            RuntimeError: On flood wait or unexpected network errors
        """
        if self._pending_client:
            return

        parsed_phone = parse_phone(phone)

        if not parsed_phone:
            raise ValueError("Invalid phone number")

        client = self._get_client()

        self._pending_client = client

        await client.connect()

        try:
            await client.send_code_request(phone)
            logger.debug(f"The code was sent to {phone}")
        except PhoneNumberUnoccupiedError:
            self._pending_client = None
            raise ValueError("Phone number is not registered")
        except FloodWaitError as e:
            self._pending_client = None
            raise RuntimeError(f"Got FloodWait. Wait for {e.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during send code: {e}")

    async def sign_in(self, phone: str, code: str, password: str = None):
        """
        Attempts to sign in using the provided code and optionally a 2FA password

        Args:
            phone (str): The user's phone number
            code (str): The authentication code received from Telegram
            password (str, optional): The 2FA password if required

        Raises:
            ValueError: For invalid inputs or authentication failures
            RuntimeError: For flood wait or unexpected internal errors
        """
        if not self._pending_client:
            raise RuntimeError("No pending client")

        parsed_phone = parse_phone(phone)
        if not parsed_phone:
            raise ValueError("Invalid phone number")

        og_code = code.replace(".", "")
        if len(og_code) != 5 or not og_code.isdigit():
            raise ValueError("Invalid code format")

        if not password:
            try:
                await self._pending_client.sign_in(parsed_phone, code=og_code)
            except SessionPasswordNeededError:
                self._2fa_needed = True
                raise ValueError("2FA password required")
            except PhoneCodeInvalidError:
                raise ValueError("Invalid code")
            except PhoneCodeExpiredError:
                raise ValueError("Code has expired")
            except FloodWaitError as e:
                self._pending_client = None
                self._2fa_needed = False
                raise RuntimeError(f"Got FloodWait. Wait for {e.timeout} seconds")
            except Exception as e:
                self._pending_client = None
                self._2fa_needed = False
                raise RuntimeError(f"Unexpected error during sign in: {e}")
        else:
            try:
                pwd = await self._pending_client(GetPasswordRequest())
                pwd_hash = compute_check(pwd, password)
                await self._pending_client(CheckPasswordRequest(pwd_hash))
            except PasswordHashInvalidError:
                raise ValueError("Invalid 2FA password")
            except FloodWaitError as e:
                self._pending_client = None
                self._2fa_needed = False
                raise RuntimeError(f"Got FloodWait. Wait for {e.timeout} seconds")
            except Exception as e:
                self._pending_client = None
                self._2fa_needed = False
                raise RuntimeError(f"Unexpected error during sign in: {e}")

        await main.legacy.save_client_session(self._pending_client)

    async def finish_auth(self):
        """
        Finalizes authentication by saving the client session and restarting userbot

        Raises:
            RuntimeError: If no client session is available to finalize
        """
        if not self._pending_client:
            raise RuntimeError("No pending client to finalize")

        main.legacy.clients = list(set(main.legacy.clients + [self._pending_client]))

        self._pending_client = None
        self._2fa_needed = None

        restart()
