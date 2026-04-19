# meta developer: @limokanews
# requires: whoosh cryptography


from collections import Counter, defaultdict
import shutil
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, OrGroup
from whoosh.query import FuzzyTerm, Wildcard
from whoosh.writing import LockError
import aiohttp
import random
import logging
import os
import html
import json
import re
import asyncio
from typing import Iterable, Union, List, Dict, Any, Optional
import hashlib
from telethon.types import Message
from telethon.errors.rpcerrorlist import WebpageMediaEmptyError
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon import functions

try:
    from aiogram.utils.exceptions import BadRequest
except ImportError:
    from aiogram.exceptions import TelegramBadRequest as BadRequest
from .. import utils, loader
from ..types import InlineCall

logger = logging.getLogger("Limoka")
__version__ = (1, 4, 2)

WEIGHTS = {
    "inline.token_obtainment": 15,
    "main": 10,
    "inline": 7,
    "translations": 5,
    "security": 3,
}

DEFAULT_WEIGHT = 1

BASE_DIR = os.getcwd()


def _get_lang_value(data: Dict[str, Any], lang: str) -> str:
    if not isinstance(data, dict):
        return str(data) if data else ""
    return data.get(lang, data.get("default", data.get("en", "")))


class Search:
    def __init__(self, query, ix):
        self.schema = Schema(
            title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True)
        )
        self.query = query
        self.ix = ix

    def search_module(self):
        with self.ix.searcher() as searcher:
            parser = QueryParser("content", self.ix.schema, group=OrGroup.factory(0.8))
            query = parser.parse(self.query)
            wildcard_query = Wildcard("content", f"*{self.query}*")
            fuzzy_query = FuzzyTerm("content", self.query, maxdist=2, prefixlength=1)
            for search_query in [query, wildcard_query, fuzzy_query]:
                results = searcher.search(search_query)
                if results:
                    return list(set(result["path"] for result in results))
        return []


class LimokaAPI:
    async def fetch_json(self, base_url, path):
        url = f"{base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return json.loads(await response.text())


@loader.tds
class Limoka(loader.Module):
    """Modules are now in one place with easy searching!"""

    strings = {
        "name": "Limoka",
        "wait": (
            "<blockquote>Just wait\n"
            "<emoji document_id=5404630946563515782>🔍</emoji> A search is underway among {count} modules "
            "for the query: <code>{query}</code>\n"
            "<i>{fact}</i></blockquote>"
        ),
        "found_header": (
            "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> Found module <b>{name}</b> "
            "by query: <b>{query}</b>\n\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Description:</b> {description}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Developer:</b> {username}\n\n"
            "<b><emoji document_id=5418376169055602355>🏷</emoji> Tags:</b> {tags}\n\n</blockquote>"
        ),
        "found_body": ("{commands}"),
        "found_footer": (
            "<blockquote>\n<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code></blockquote>"
        ),
        "caption_short": (
            "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>{safe_name}</b>\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Description:</b> {safe_desc}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Dev:</b> {dev_username}\n"
            "<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {module_path}</code></blockquote>"
        ),
        "command_template": "{emoji} <code>{prefix}{command}</code> — {description}\n",
        "inline_handler_template": "{inline_bot} {command} — {description}\n",
        "emojis": {
            1: "<emoji document_id=5416037945909987712>1️⃣</emoji>",
            2: "<emoji document_id=5413855071731470617>2️⃣</emoji>",
            3: "<emoji document_id=5416068826724850291>3️⃣</emoji>",
            4: "<emoji document_id=5415843998071803071>4️⃣</emoji>",
            5: "<emoji document_id=5415684843763686989>5️⃣</emoji>",
            6: "<emoji document_id=5415975458430796879>6️⃣</emoji>",
            7: "<emoji document_id=5415769763857060166>7️⃣</emoji>",
            8: "<emoji document_id=5416006506749383505>8️⃣</emoji>",
            9: "<emoji document_id=5415963015910544694>9️⃣</emoji>",
        },
        "404": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>Not found by query: <i>{query}</i></b></blockquote>",
        "noargs": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>No args</b></blockquote>",
        "?": "<blockquote><emoji document_id=5951895176908640647>🔎</emoji> Request too short / not found</blockquote>",
        "no_info": "<blockquote>No information</blockquote>",
        "facts": [
            "<blockquote><emoji document_id=5472193350520021357>🛡</emoji> The limoka catalog is carefully moderated!</blockquote>",
            "<blockquote><emoji document_id=5940434198413184876>🚀</emoji> Limoka performance allows you to search for modules quickly!</blockquote>",
        ],
        "inline404": "<blockquote>Not found</blockquote>",
        "inline?": "<blockquote>Request too short / not found</blockquote>",
        "inlinenoargs": "<blockquote>Please, enter query</blockquote>",
        "history": (
            "<blockquote><emoji document_id=5879939498149679716>🔎</emoji> <b>Your search history:</b>\n"
            "{history}</blockquote>"
        ),
        "filter_menu": "Choose filters",
        "filter_cat": "📑 Filter by Category",
        "apply_filters": "✅ Apply Filters",
        "clear_filters": "🗑 Clear Filters",
        "back_to_results": "🔙 Back to Results",
        "empty_history": "<blockquote><emoji document_id=5879939498149679716>🔎</emoji> <b>Your search history is empty!</b></blockquote>",
        "enter_query": "<blockquote>🔍 Enter new search query:</blockquote>",
        "global_search": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> Global search for <b>{query}</b> — found <b>{count}</b> modules</blockquote>",
        "change_query": "🔍 Change query",
        "no_modules": "<blockquote>No modules available.</blockquote>",
        "filter_title": "🏷 Filters",
        "category_title": "📂 Categories",
        "selected_categories": "<blockquote>✅ Selected categories: {categories}</blockquote>",
        "no_categories": "<blockquote>No categories found in the module database</blockquote>",
        "select_category": "<blockquote>Select categories for query: <code>{query}</code>\n(You can select multiple)</blockquote>",
        "back": "🔙 Back",
        "category": "📁 {category}",
        "no_category": "<blockquote>No category</blockquote>",
        "global_button": "🌍 Results",
        "filtered_button": "🏷️ Filtered search",
        "inline_search": "🔍 Search in Limoka",
        "inline_no_results": "<blockquote>❌ No modules found</blockquote>",
        "inline_error": "<blockquote>❌ Search error occurred</blockquote>",
        "inline_short_query": "<blockquote>❌ Query too short (min 2 chars)</blockquote>",
        "inline_switch_pm": "💬 Open in chat",
        "inline_switch_pm_text": "🔍 Results for: {query}",
        "inline_start_message": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Limoka Search</b>\nType module name or keyword</blockquote>",
        "first_page": "<blockquote>This is the first page!</blockquote>",
        "last_page": "<blockquote>This is the last page!</blockquote>",
        "display_error": "<blockquote>Error displaying module. Please try again.</blockquote>",
        "error_occurred": "<blockquote>An error occurred. Please try again.</blockquote>",
        "start_search_form": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Limoka Search</b>\nEnter your query to search for modules:</blockquote>",
        "global_search_form": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Global Search</b>\nEnter your query to search ALL modules without filters:</blockquote>",
        "history_cleared": "<blockquote><emoji document_id=5427009710268689068>🧹</emoji> <b>Search history cleared!</b></blockquote>",
        "invalid_history_arg": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>Invalid argument for history command. Use:</b>\n<code>.lshistory</code> - show history\n<code>.lshistory clear</code> - clear history</blockquote>",
        "close": "❌ Close",
        "watcher_no_tag": "<blockquote>❌ Invalid message format. No #limoka tag found.</blockquote>",
        "watcher_invalid_format": "<blockquote>❌ Invalid format. Expected: #limoka:path:signature</blockquote>",
        "watcher_signature_invalid": "<blockquote>❌ Signature invalid! Installation aborted.</blockquote>",
        "watcher_loader_missing": "<blockquote>❌ Loader module not found.</blockquote>",
        "watcher_module_not_found": "<blockquote>❌ Module not found in Limoka database: <code>{path}</code></blockquote>",
        "watcher_critical": "<blockquote>❌ Critical error: {error}</blockquote>",
        "tags": {
            "herokutrusted": "Heroku Trusted",
            "hikkatrusted": "Hikka Trusted",
            "nonactive": "Non-Active Repository",
            "nonlongermaintained": "No Longer Maintained Repository",
            "newbie": "Newbie",
        },
        "indexing_in_progress": (
            "<blockquote>⚠️ Database is busy, "
            "try again later. "
            "If issue persists, try "
            "removing limoka_index in the userbot's root folder. "
            "If error persists again, report to developers</blockquote>"
        ),
        "body_page": "Commands",
    }
    strings_ru = {
        "name": "Limoka",
        "wait": (
            "<blockquote>Подождите\n"
            "<emoji document_id=5404630946563515782>🔍</emoji> Идёт поиск среди {count} модулей по запросу: <code>{query}</code>\n"
            "<i>{fact}</i></blockquote>"
        ),
        "found_header": (
            "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> Найден модуль <b>{name}</b> "
            "по запросу: <b>{query}</b></blockquote>\n\n"
            "<blockquote><b><emoji document_id=5418376169055602355>ℹ️</emoji> Описание:</b> {description}</blockquote>\n"
            "<blockquote><b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Разработчик:</b> {username}</blockquote>\n\n"
            "<blockquote><b><emoji document_id=5418376169055602355>🏷</emoji> Теги:</b> {tags}</blockquote>\n\n"
        ),
        "found_body": ("{commands}"),
        "found_footer": (
            "\n<blockquote><emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code></blockquote>"
        ),
        "caption_short": (
            "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>{safe_name}</b>\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Описание:</b> {safe_desc}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Разработчик:</b> {dev_username}\n"
            "<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {module_path}</code></blockquote>"
        ),
        "command_template": "<blockquote>{emoji} <code>{prefix}{command}</code> — {description}</blockquote>\n",
        "inline_handler_template": "{inline_bot} {command} — {description}\n",
        "emojis": {
            1: "<emoji document_id=5416037945909987712>1️⃣</emoji>",
            2: "<emoji document_id=5413855071731470617>2️⃣</emoji>",
            3: "<emoji document_id=5416068826724850291>3️⃣</emoji>",
            4: "<emoji document_id=5415843998071803071>4️⃣</emoji>",
            5: "<emoji document_id=5415684843763686989>5️⃣</emoji>",
            6: "<emoji document_id=5415975458430796879>6️⃣</emoji>",
            7: "<emoji document_id=5415769763857060166>7️⃣</emoji>",
            8: "<emoji document_id=5416006506749383505>8️⃣</emoji>",
            9: "<emoji document_id=5415963015910544694>9️⃣</emoji>",
            10: "<emoji document_id=5415642160378696377>🔟</emoji>",
        },
        "404": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>Не найдено по запросу: <i>{query}</i></b></blockquote>",
        "noargs": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>Нет аргументов</b></blockquote>",
        "?": "<blockquote><emoji document_id=5951895176908640647>🔎</emoji> Запрос слишком короткий / не найден</blockquote>",
        "no_info": "<blockquote>Нет информации</blockquote>",
        "facts": [
            "<blockquote><emoji document_id=5472193350520021357>🛡</emoji> Каталог Limoka тщательно модерируется!</blockquote>",
            "<blockquote><emoji document_id=5940434198413184876>🚀</emoji> Limoka позволяет искать модули с невероятной скоростью!</blockquote>",
            (
                "<blockquote><emoji document_id=5188311512791393083>🔎</emoji> Limoka имеет лучший поиск*!\n"
                "<i>* В сравнении с предыдущей версией Limoka</i></blockquote>"
            ),
        ],
        "inline404": "<blockquote>Не найдено</blockquote>",
        "inline?": "<blockquote>Запрос слишком короткий / не найден</blockquote>",
        "inlinenoargs": "<blockquote>Введите запрос</blockquote>",
        "history": (
            "<blockquote><emoji document_id=5879939498149679716>🔎</emoji> <b>История поиска:</b>\n"
            "{history}</blockquote>"
        ),
        "filter_menu": "Выберите фильтры",
        "filter_cat": "📑 Фильтр по категориям",
        "apply_filters": "✅ Применить фильтры",
        "clear_filters": "🗑 Очистить фильтры",
        "back_to_results": "🔙 Вернуться к результатам",
        "empty_history": "<blockquote><emoji document_id=5879939498149679716>🔎</emoji> <b>История поиска пуста!</b></blockquote>",
        "enter_query": "<blockquote>🔍 Введите новый поисковый запрос:</blockquote>",
        "global_search": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> Глобальный поиск по <b>{query}</b> — найдено <b>{count}</b> модулей</blockquote>",
        "change_query": "🔍 Изменить запрос",
        "no_modules": "<blockquote>Модули недоступны.</blockquote>",
        "filter_title": "🏷 Фильтры",
        "category_title": "📂 Категории",
        "selected_categories": "<blockquote>✅ Выбранные категории: {categories}</blockquote>",
        "no_categories": "<blockquote>Категории не найдены в базе модулей</blockquote>",
        "select_category": "<blockquote>Выберите категории для запроса: <code>{query}</code>\n(Можно выбрать несколько)</blockquote>",
        "back": "🔙 Назад",
        "category": "📁 {category}",
        "no_category": "<blockquote>Без категории</blockquote>",
        "global_button": "🌍 Результаты",
        "filtered_button": "🏷️ Поиск с фильтрами",
        "inline_search": "🔍 Поиск в Limoka",
        "inline_no_results": "<blockquote>❌ Модули не найдены</blockquote>",
        "inline_error": "<blockquote>❌ Ошибка поиска</blockquote>",
        "inline_short_query": "<blockquote>❌ Запрос слишком короткий (мин. 2 символа)</blockquote>",
        "inline_switch_pm": "💬 Открыть в чате",
        "inline_switch_pm_text": "🔍 Результаты для: {query}",
        "inline_start_message": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Limoka Поиск</b>\nВведите название модуля или ключевое слово</blockquote>",
        "first_page": "<blockquote>Это первая страница!</blockquote>",
        "last_page": "<blockquote>Это последняя страница!</blockquote>",
        "display_error": "<blockquote>Ошибка отображения модуля. Пожалуйста, попробуйте еще раз.</blockquote>",
        "error_occurred": "<blockquote>Произошла ошибка. Пожалуйста, попробуйте еще раз.</blockquote>",
        "start_search_form": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Limoka Поиск</b>\nВведите ваш запрос для поиска модулей:</blockquote>",
        "global_search_form": "<blockquote><emoji document_id=5413334818047940135>🔍</emoji> <b>Глобальный Поиск</b>\nВведите запрос для поиска ВСЕХ модулей без фильтров:</blockquote>",
        "history_cleared": "<blockquote><emoji document_id=5427009710268689068>🧹</emoji> <b>История поиска очищена!</b></blockquote>",
        "invalid_history_arg": "<blockquote><emoji document_id=5210952531676504517>❌</emoji> <b>Неверный аргумент для команды истории. Используйте:</b>\n<code>.lshistory</code> - показать историю\n<code>.lshistory clear</code> - очистить историю</blockquote>",
        "close": "❌ Закрыть",
        "watcher_no_tag": "<blockquote>❌ Неверный формат сообщения. Тег #limoka не найден.</blockquote>",
        "watcher_invalid_format": "<blockquote>❌ Неверный формат. Ожидается: #limoka:path:signature</blockquote>",
        "watcher_signature_invalid": "<blockquote>❌ Неверная подпись! Установка отменена.</blockquote>",
        "watcher_loader_missing": "<blockquote>❌ Модуль загрузчика не найден.</blockquote>",
        "watcher_module_not_found": "<blockquote>❌ Модуль не найден в базе Limoka: <code>{path}</code></blockquote>",
        "watcher_critical": "<blockquote>❌ Критическая ошибка: {error}</blockquote>",
        "tags": {
            "herokutrusted": "Heroku Trusted",
            "hikkatrusted": "Hikka Trusted",
            "nonactive": "Неактивный репозиторий",
            "nonlongermaintained": "Неподдерживаемый репозиторий",
            "newbie": "Новичок",
        },
        "indexing_in_progress": (
            "<blockquote>\u26a0\ufe0f База данных занята, "
            "попробуйте снова через несколько секунд. "
            "Если ошибка сохраняется, попробуйте "
            "удалить limoka_index в корневой папке юзербота. "
            "Если ошибка сохраняется снова, сообщите разработчикам</blockquote>"
        ),
        "body_page": "Команды",
        "_cls_doc": "Модули теперь в одном месте с простым и удобным поиском!",
    }

    def __init__(self):
        self.api = LimokaAPI()
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "limokaurl",
                "https://raw.githubusercontent.com/MuRuLOSE/limoka/refs/heads/main/",
                lambda: (
                    "Mirror (doesn't work): https://raw.githubusercontent.com/MuRuLOSE/limoka-mirror/refs/heads/main/"
                ),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "external_install_allowed",
                True,
                lambda: (
                    "If enabled, module installation can be handled via external Limoka bot (@limoka_bbot) for better reliability."
                ),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "filter_newbies_modules",
                False,
                lambda: (
                    "If enabled, modules from developers with newbies tag will be not shown."
                ),
                validator=loader.validators.Boolean(),
            ),
        )
        self.name = self.strings["name"]
        self._invalid_banners = set()
        self._bot_username = "limoka_bbot"
        self._base_url = self.config["limokaurl"]

        # Search session states
        self.SEARCH_STATES = {
            "no_banner": "no_banner",  # 404 - No banner
            "global_search": "global_search",  # Global search
            "not_found": "not_found",  # Not found (module)
            "filter_select": "filter_select",  # Select categories (filters)
        }

        # State banners
        self.state_banners = {
            "no_banner": "https://raw.githubusercontent.com/MuRuLOSE/hikka-assets/refs/heads/main/Limoka%20-%20No%20banner.png",
            "global_search": "https://raw.githubusercontent.com/MuRuLOSE/hikka-assets/main/Limoka%20-%20Global%20Search.png",
            "not_found": "https://raw.githubusercontent.com/MuRuLOSE/hikka-assets/main/Limoka%20-%20Not%20Found.png",
            "filter_select": "https://raw.githubusercontent.com/MuRuLOSE/hikka-assets/main/Limoka%20-%20Categories.png",
        }

    def _filter_newbies(self, modules: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out modules which belong to repositories tagged as 'newbie'.
        Returns the original dict when the feature is disabled or repositories
        metadata is not available.
        """
        try:
            if not self.config.get("filter_newbies_modules"):
                return modules
        except Exception:
            return modules

        if not getattr(self, "repositories", None):
            return modules

        filtered: Dict[str, Any] = {}
        for path, info in modules.items():
            repo_key = "/".join(path.split("/")[:2]) if "/" in path else path
            repo = self.repositories.get(repo_key)
            tags = repo.get("tags", []) if repo else []
            if "newbie" in tags:
                continue
            filtered[path] = info
        return filtered

    def _create_search_session(
        self,
        state: str,
        query: str = "",
        filters: Optional[Dict[str, List[str]]] = None,
        results: Optional[List[str]] = None,
        current_index: int = 0,
    ) -> Dict[str, Any]:
        """Create a search session dictionary to track state across callbacks.

        Args:
            state: Current search state (one of SEARCH_STATES values)
            query: Current search query
            filters: Active category filters
            results: Search results list
            current_index: Index of current result being displayed
            banner_url: Banner image URL for current state

        Returns:
            Dictionary containing the complete session state
        """
        return {
            "state": state,
            "query": query,
            "filters": filters or {},
            "results": results or [],
            "current_index": current_index,
        }

    def _get_banner_for_state(self, state: str) -> str:
        return self.state_banners.get(state)

    async def client_ready(self, client, db):
        self.client: TelegramClient = client
        self.db = db
        self.api = LimokaAPI()
        self.schema = Schema(
            title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True)
        )
        os.makedirs("limoka_search", exist_ok=True)
        if not os.path.exists("limoka_search/index"):
            self.ix = create_in("limoka_search", self.schema)
        else:
            self.ix = open_dir("limoka_search")
        self._history = self.pointer("history", [])
        self.modules = (await self.api.fetch_json(self._base_url, "modules.json")).get(
            "modules", {}
        )
        raw = (await self.api.fetch_json(self._base_url, "repositories.json")).get(
            "repositories", []
        )
        self.repositories = {repo["url"]: repo for repo in raw}
        # Apply newbie filter if enabled
        try:
            self.modules = self._filter_newbies(self.modules)
        except Exception:
            pass
        self._service_bot_id = (await self.client.get_entity(self._bot_username)).id

        loop = asyncio.get_running_loop()
        self.ix_task = loop.run_in_executor(
            None, lambda: asyncio.run(self._update_index())
        )

        if self.config["external_install_allowed"]:
            try:
                message = await self.client.get_messages(self._bot_username, limit=1)
                if not message:
                    message = await self.client.send_message(
                        self._bot_username, "/start"
                    )
                    await message.delete()
                    await self.client(
                        functions.messages.DeleteHistoryRequest(
                            peer=self._bot_username,
                            max_id=0,
                            just_clear=True,
                            revoke=True,
                        )
                    )

            except YouBlockedUserError:
                logger.warning(
                    f"Please unblock {self._bot_username} to enable external installation feature. Or disable external_install_allowed in Limoka settings to get rid of this message."
                )
        self._userbot_bot_username = (await self.inline.bot.get_me()).username

    @loader.loop(interval=3600)
    async def _update_modules_loop(self):
        self.modules = await self.api.fetch_json(self._base_url, "modules.json")
        # Re-apply newbie filter after modules refresh
        try:
            self.modules = self._filter_newbies(self.modules)
        except Exception:
            pass
        await self._update_index()

    async def _update_index(self):
        try:
            writer = self.ix.writer()
            modules_to_index = self._filter_newbies(self.modules)
            for module_path, module_data in modules_to_index.items():
                writer.add_document(
                    title=module_data.get("name", "Unknown"),
                    path=module_path,
                    content=module_data["name"]
                    + " "
                    + (
                        module_data.get("description")
                        or ""
                        + " "
                        + (
                            (module_data.get("meta").get("developer") or "")
                            if module_data.get("meta")
                            else ""
                        )
                    ),
                )
                for func in module_data.get("commands", []):
                    for command, description in func.items():
                        writer.add_document(
                            title=module_data["name"],
                            path=module_path,
                            content=f"{command} {description}",
                        )
            writer.commit()
        except LockError:
            folder = os.path.join(BASE_DIR, "limoka_search")

            if os.path.commonpath([folder, BASE_DIR]) == BASE_DIR and os.path.exists(
                folder
            ):
                shutil.rmtree(folder)
                await self._update_index()
            else:
                logger.error(
                    (
                        f"Skipping unsafe rmtree for {folder}. Please, report this to developer. ",
                        f"Debug info: folder={folder}, base_dir={BASE_DIR}, common_path={os.path.commonpath([folder, BASE_DIR])}, exists={os.path.exists(folder)}",
                    )
                )

    async def _validate_url(self, url: str) -> Optional[str]:
        if not url or url in self._invalid_banners:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    url, timeout=5, allow_redirects=True
                ) as response:
                    if response.status != 200:
                        self._invalid_banners.add(url)
                        return None
                    ct = response.headers.get("Content-Type", "").lower()
                    if not ct.startswith("image/"):
                        self._invalid_banners.add(url)
                        return None
                    return url
        except Exception as e:
            if url:
                self._invalid_banners.add(url)
            return None

    def find_userbot(self, keys: Iterable[str]) -> str | None:
        scores = defaultdict(int)

        for key in keys:
            parts = key.split(".")

            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                suffix = ".".join(parts[i:])

                weight = WEIGHTS.get(suffix, DEFAULT_WEIGHT)

                scores[prefix] += weight

        if not scores:
            return None

        return max(scores, key=scores.get)

    @property
    def user_lang(self) -> str:

        userbot = self.find_userbot(self.db.keys())

        if not userbot:
            logger.warning(
                "Cannot determine userbot type. "
                "Probably not FTG-like Userbot? "
                "Defaulting language to English. "
                "If this is unexpected, please report to the module developer."
            )
            return "en"

        return self.db.get(f"{userbot}.translations", "lang")

    def generate_commands(self, module_info, lang: str = "en"):
        commands = []
        for i, cmd in enumerate(module_info.get("new_commands", []), 1):
            name = cmd.get("name", "")
            desc_map = cmd.get("description", {})
            if i <= 9:
                emoji = self.strings["emojis"].get(i, "")
            else:
                emoji = ""
                for digit in str(i):
                    emoji += self.strings["emojis"].get(int(digit), "")
            desc = _get_lang_value(desc_map, lang) or self.strings["no_info"]
            commands.append(
                self.strings["command_template"].format(
                    prefix=self.get_prefix(),
                    command=html.escape(name),
                    emoji=emoji,
                    description=html.escape(desc),
                )
            )
        for i, handler in enumerate(module_info.get("inline_handlers", []), 1):
            name = handler.get("name", "")
            desc_map = handler.get("description", {})
            desc = _get_lang_value(desc_map, lang) or self.strings["no_info"]
            commands.append(
                self.strings["inline_handler_template"].format(
                    inline_bot=self._userbot_bot_username,
                    command=html.escape(name),
                    description=html.escape(desc),
                )
            )
        return commands

    def _format_module_content(
        self,
        module_info: Dict[str, Any],
        query: str,
        filters: Dict[str, List[str]],
        include_categories: bool = True,
        module_path: Optional[str] = None,
        lang: str = "en",
    ) -> tuple:
        name = html.escape(module_info.get("name") or self.strings["no_info"])
        cls_doc = module_info.get("cls_doc", {})
        description = html.escape(
            _get_lang_value(cls_doc, lang)
            or _get_lang_value(module_info.get("description", ""), lang)
            or self.strings["no_info"]
        )
        dev_username = html.escape(module_info["meta"].get("developer") or "Unknown")
        raw_path = (
            module_path if module_path is not None else module_info.get("path", "")
        )
        clean_module_path = (raw_path or "").replace("\\", "/")
        commands = self.generate_commands(module_info, lang)
        categories_text = ""
        if include_categories:
            categories = filters.get("category", [])
            if categories:
                categories_text = "\n" + self.strings["selected_categories"].format(
                    categories=", ".join(html.escape(c) for c in categories)
                )
        if len(description) > 300:
            description = description[:297] + "…"
        repo_key = (
            "/".join(module_path.split("/")[:2]) if "/" in module_path else module_path
        )
        tags_list = []
        for x in self.repositories:
            if x.replace("https://github.com/", "") == repo_key:
                tags_list = self.repositories.get(x, {}).get("tags", [])
                break
        tags_text = ", ".join(self.strings["tags"].get(tag, tag) for tag in tags_list)
        header = self.strings["found_header"].format(
            query=html.escape(query),
            name=name,
            description=description,
            username=dev_username,
            tags=tags_text,
        )
        commands_text = "".join(commands)
        if len(commands_text) <= 500:
            body_pages = [commands_text] if commands_text else [""]
        else:
            body_pages = []
            current_page = []
            current_length = 0
            for cmd in commands:
                if current_length + len(cmd) > 500:
                    if current_page:
                        body_pages.append("".join(current_page))
                        current_page = []
                        current_length = 0
                current_page.append(cmd)
                current_length += len(cmd)
            if current_page:
                body_pages.append("".join(current_page))
            if not body_pages:
                body_pages = [""]
        footer = self.strings["found_footer"].format(
            url=html.escape(self.config["limokaurl"]),
            module_path=html.escape(clean_module_path),
            prefix=html.escape(self.get_prefix()),
        )
        return header, body_pages, footer, categories_text

    def _build_navigation_markup(self, session: Dict[str, Any]) -> list:
        result = session["results"]
        index = session["current_index"]
        query = session["query"]
        filters = session["filters"]

        page = index + 1
        markup = [
            [
                {
                    "text": "⏪" if index > 0 else "🚫",
                    "callback": self._previous_page if index > 0 else self._inline_void,
                    "args": (session,) if index > 0 else (),
                },
                {"text": f"{page}/{len(result)}", "callback": self._inline_void},
                {
                    "text": "⏩" if index + 1 < len(result) else "🚫",
                    "callback": (
                        self._next_page
                        if index + 1 < len(result)
                        else self._inline_void
                    ),
                    "args": (session,) if index + 1 < len(result) else (),
                },
            ],
            [
                {
                    "text": "🔍 " + self.strings["filter_menu"].split(":")[0],
                    "callback": self._display_filter_menu,
                    "args": (session,),
                },
                {
                    "text": "🔄 " + self.strings["change_query"],
                    "callback": self._enter_query,
                },
            ],
            [
                {
                    "text": self.strings["global_button"],
                    "callback": self._show_global_results,
                    "args": (session,),
                },
            ],
        ]
        markup.append(
            [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
        )
        return markup

    def _build_module_markup(
        self,
        session: Dict[str, Any],
        body_pages: List[str],
        page_body: int,
        module_path: str,
    ) -> list:
        result = session["results"]
        index = session["current_index"]
        query = session["query"]
        filters = session["filters"]

        markup = []
        if len(body_pages) > 1:
            markup.append(
                [
                    {
                        "text": "◀️" if page_body > 0 else "🚫",
                        "callback": (
                            self._previous_body_page
                            if page_body > 0
                            else self._inline_void
                        ),
                        "args": (
                            (session, module_path, page_body) if page_body > 0 else ()
                        ),
                    },
                    {
                        "text": f"{self.strings['body_page']} {page_body + 1}/{len(body_pages)}",
                        "callback": self._inline_void,
                    },
                    {
                        "text": "▶️" if page_body + 1 < len(body_pages) else "🚫",
                        "callback": (
                            self._next_body_page
                            if page_body + 1 < len(body_pages)
                            else self._inline_void
                        ),
                        "args": (
                            (session, module_path, page_body)
                            if page_body + 1 < len(body_pages)
                            else ()
                        ),
                    },
                ]
            )
        page = index + 1
        markup.append(
            [
                {
                    "text": "⏪" if index > 0 else "🚫",
                    "callback": self._previous_page if index > 0 else self._inline_void,
                    "args": (session,) if index > 0 else (),
                },
                {"text": f"{page}/{len(result)}", "callback": self._inline_void},
                {
                    "text": "⏩" if index + 1 < len(result) else "🚫",
                    "callback": (
                        self._next_page
                        if index + 1 < len(result)
                        else self._inline_void
                    ),
                    "args": (session,) if index + 1 < len(result) else (),
                },
            ]
        )
        markup.append(
            [
                {
                    "text": "🔍 " + self.strings["filter_menu"].split(":")[0],
                    "callback": self._display_filter_menu,
                    "args": (session,),
                },
                {
                    "text": "🔄 " + self.strings["change_query"],
                    "callback": self._enter_query,
                },
            ]
        )
        markup.append(
            [
                {
                    "text": self.strings["global_button"],
                    "callback": self._show_global_results,
                    "args": (session,),
                },
            ]
        )
        markup.append(
            [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
        )
        return markup

    async def _safe_display(
        self,
        message_or_call: Union[Message, InlineCall],
        text: str,
        markup: list,
        photo: Optional[Any] = None,
    ):
        try:
            if message_or_call is None:
                logger.error("message_or_call is None in _safe_display")
                return
            if isinstance(message_or_call, Message):
                if photo is not None:
                    await self.inline.form(
                        text=text,
                        message=message_or_call,
                        reply_markup=markup,
                        photo=photo,
                    )
                else:
                    await self.inline.form(
                        text=text, message=message_or_call, reply_markup=markup
                    )
            else:
                if photo is not None:
                    await message_or_call.edit(
                        text=text, reply_markup=markup, photo=photo
                    )
                else:
                    await message_or_call.edit(text=text, reply_markup=markup)
        except (BadRequest, WebpageMediaEmptyError) as e:
            logger.exception(f"Error in _safe_display: {e}")
            if isinstance(message_or_call, Message):
                await utils.answer(message_or_call, self.strings["display_error"])
            elif hasattr(message_or_call, "edit"):
                await message_or_call.edit(self.strings["display_error"])

    async def _display_module(
        self,
        message_or_call: Union[Message, InlineCall],
        module_info: Dict[str, Any],
        module_path: str,
        session: Dict[str, Any],
        page_body: int = 0,
    ):
        try:
            query = session["query"]
            filters = session["filters"]

            lang = self.user_lang
            module_banner_raw = module_info.get("meta", {}).get("banner")
            photo = await self._validate_url(module_banner_raw)

            if not photo:
                state_banner_raw = self._get_banner_for_state("no_banner")
                photo = await self._validate_url(state_banner_raw)

            header, body_pages, footer, categories_text = self._format_module_content(
                module_info,
                query,
                filters,
                include_categories=True,
                module_path=module_path,
                lang=lang,
            )
            current_body = body_pages[min(page_body, len(body_pages) - 1)]
            full_message = header + current_body + footer + categories_text

            markup = self._build_module_markup(
                session, body_pages, page_body, module_path
            )

            await self._safe_display(message_or_call, full_message, markup, photo)
        except Exception as e:
            logger.exception(f"Error in _display_module: {e}")
            if isinstance(message_or_call, Message):
                await utils.answer(message_or_call, self.strings["error_occurred"])
            elif hasattr(message_or_call, "edit"):
                await message_or_call.edit(self.strings["error_occurred"])

    async def _previous_body_page(
        self,
        call: InlineCall,
        session: Dict[str, Any],
        module_path: str,
        page_body: int,
    ):
        module_info = self.modules[module_path]
        new_page_body = max(page_body - 1, 0)
        await self._display_module(
            call, module_info, module_path, session, page_body=new_page_body
        )

    async def _next_body_page(
        self,
        call: InlineCall,
        session: Dict[str, Any],
        module_path: str,
        page_body: int,
    ):
        module_info = self.modules[module_path]
        query = session["query"]
        filters = session["filters"]
        header, body_pages, footer, categories_text = self._format_module_content(
            module_info,
            query,
            filters,
            include_categories=True,
            module_path=module_path,
            lang=self.user_lang,
        )
        new_page_body = min(page_body + 1, len(body_pages) - 1)
        await self._display_module(
            call, module_info, module_path, session, page_body=new_page_body
        )

    async def _display_filter_menu(self, call: InlineCall, session: Dict[str, Any]):
        query = session["query"]
        current_filters = session["filters"]

        categories = current_filters.get("category", [])
        filters_text = self.strings["selected_categories"].format(
            categories=(
                ", ".join(categories) if categories else self.strings["no_category"]
            )
        )
        markup = [
            [
                {
                    "text": self.strings["filter_cat"],
                    "callback": self._select_category,
                    "args": (session,),
                },
            ],
            [
                {
                    "text": self.strings["apply_filters"],
                    "callback": self._apply_filters,
                    "args": (session,),
                },
                {
                    "text": self.strings["clear_filters"],
                    "callback": self._clear_filters,
                    "args": (session,),
                },
            ],
            [
                {
                    "text": self.strings["back_to_results"],
                    "callback": self._show_results,
                    "args": (session, True),
                },
            ],
            [{"text": self.strings.get("close", "❌ Close"), "action": "close"}],
        ]
        text = self.strings["filter_menu"].format(query=query) + f"\n{filters_text}"
        await call.edit(
            text, reply_markup=markup, photo=self._get_banner_for_state("filter_select")
        )

    async def _select_category(self, call: InlineCall, session: Dict[str, Any]):
        query = session["query"]
        current_filters = session["filters"]

        all_categories = set()
        for module_data in self.modules.values():
            all_categories.update(module_data.get("category", ["No category"]))
        categories = sorted(all_categories)
        if not categories:
            await call.edit(
                self.strings["no_categories"],
                reply_markup=[
                    [
                        {
                            "text": self.strings["back"],
                            "callback": self._display_filter_menu,
                            "args": (session,),
                        }
                    ]
                ],
            )
            return
        selected_categories = current_filters.get("category", [])
        buttons = []
        row = []
        for i, cat in enumerate(categories):
            button_text = (
                self.strings["category"].format(category=cat)
                if "category" in self.strings
                else f"📁 {cat}"
            )
            if cat in selected_categories:
                button_text = "✅ " + button_text

            # Create new session with updated filters
            new_session = session.copy()
            row.append(
                {
                    "text": button_text,
                    "callback": self._toggle_category,
                    "args": (session, cat),
                }
            )
            if (i + 1) % 3 == 0 or i == len(categories) - 1:
                buttons.append(row)
                row = []
        buttons.append(
            [
                {
                    "text": self.strings["back"],
                    "callback": self._display_filter_menu,
                    "args": (session,),
                }
            ]
        )
        buttons.append(
            [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
        )
        text = self.strings["select_category"].format(query=query)
        await call.edit(text, reply_markup=buttons)

    async def _toggle_category(
        self, call: InlineCall, session: Dict[str, Any], category: str
    ):
        query = session["query"]
        current_filters = session["filters"]

        new_filters = current_filters.copy()
        selected_categories = new_filters.get("category", [])
        if category in selected_categories:
            selected_categories.remove(category)
        else:
            selected_categories.append(category)
        if selected_categories:
            new_filters["category"] = selected_categories
        else:
            new_filters.pop("category", None)
        new_session = session.copy()
        new_session["filters"] = new_filters
        await self._select_category(call, new_session)

    async def _apply_filters(self, call: InlineCall, session: Dict[str, Any]):
        await self._show_results(call, session, from_filters=True)

    async def _clear_filters(self, call: InlineCall, session: Dict[str, Any]):
        new_session = session.copy()
        new_session["filters"] = {}
        await self._show_results(call, new_session, from_filters=True)

    async def _show_results(
        self, call: InlineCall, session: Dict[str, Any], from_filters: bool = False
    ):
        query = session["query"]
        filters = session["filters"]

        searcher = Search(query.lower(), self.ix)
        try:
            result = searcher.search_module()
        except Exception:
            await call.edit(self.strings["?"], reply_markup=[])
            return
        if not result:
            markup = (
                [
                    [
                        {
                            "text": self.strings["back"],
                            "callback": self._display_filter_menu,
                            "args": (session,),
                        }
                    ]
                ]
                if from_filters
                else []
            )
            markup.append(
                [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
            )
            await call.edit(
                self.strings["404"].format(query=query), reply_markup=markup
            )
            return
        if filters.get("category"):
            filtered_result = [
                path
                for path in result
                if any(
                    cat in self.modules.get(path, {}).get("category", ["No category"])
                    for cat in filters["category"]
                )
            ]
        else:
            filtered_result = result
        if not filtered_result:
            markup = (
                [
                    [
                        {
                            "text": self.strings["back"],
                            "callback": self._display_filter_menu,
                            "args": (session,),
                        }
                    ]
                ]
                if from_filters
                else []
            )
            markup.append(
                [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
            )
            await call.edit(
                self.strings["404"].format(query=query), reply_markup=markup
            )
            return
        module_path = filtered_result[0]
        module_info = self.modules[module_path]

        # Create session for displaying module
        display_session = self._create_search_session(
            state=self.SEARCH_STATES["global_search"],
            query=query,
            filters=filters,
            results=filtered_result,
            current_index=0,
        )
        await self._display_module(call, module_info, module_path, display_session, 0)

    async def _enter_query_handler(
        self, call_or_query, query: Optional[str] = None, *args, **kwargs
    ):
        call = None
        if query is None and isinstance(call_or_query, str):
            query = call_or_query
            for a in args:
                if hasattr(a, "edit") or isinstance(a, Message):
                    call = a
                    break
        else:
            call = call_or_query
        if call is None:
            logger.error("_enter_query_handler: missing call/context")
            return
        if not query:
            await call.edit(
                self.strings["?"],
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": self._enter_query,
                        }
                    ]
                ],
            )
            return
        if len(query) <= 1:
            await call.edit(
                self.strings["?"],
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": self._enter_query,
                        }
                    ]
                ],
            )
            return
        searcher = Search(query.lower(), self.ix)
        try:
            result = searcher.search_module()
        except Exception:
            await call.edit(
                self.strings["?"],
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": self._enter_query,
                        }
                    ]
                ],
            )
            return
        if not result:
            await call.edit(
                self.strings["404"].format(query=query),
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": self._enter_query,
                        }
                    ],
                    [
                        {
                            "text": self.strings.get("close", "❌ Close"),
                            "action": "close",
                        }
                    ],
                ],
            )
            return
        module_path = result[0]
        module_info = self.modules[module_path]

        # Create session for displaying module
        display_session = self._create_search_session(
            state=self.SEARCH_STATES["global_search"],
            query=query,
            filters={},
            results=result,
            current_index=0,
        )
        await self._display_module(call, module_info, module_path, display_session, 0)

    async def _enter_query(self, call: InlineCall, query: Optional[str] = None):
        markup = [
            [
                {
                    "text": "✍️ " + self.strings["enter_query"],
                    "input": self.strings["enter_query"],
                    "handler": self._enter_query_handler,
                }
            ],
            [
                {
                    "text": self.strings["back_to_results"],
                    "callback": self._show_results,
                    "args": (
                        self._create_search_session(
                            state=self.SEARCH_STATES["global_search"],
                            query=query or "",
                            filters={},
                        ),
                    ),
                }
            ],
            [
                {
                    "text": self.strings.get("close", "❌ Close"),
                    "action": "close",
                }
            ],
        ]
        await call.edit(self.strings["enter_query"], reply_markup=markup)

    async def _show_global_results(self, call: InlineCall, session: Dict[str, Any]):
        query = session["query"]

        searcher = Search(query.lower(), self.ix)
        try:
            result = searcher.search_module()
        except Exception:
            await call.edit(self.strings["?"], reply_markup=[])
            return
        if not result:
            await call.edit(
                self.strings["404"].format(query=query),
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": self._enter_query,
                        }
                    ]
                ],
            )
            return
        text = self.strings["global_search"].format(
            query=html.escape(query), count=len(result)
        )
        buttons = []
        for i, path in enumerate(result[:15]):
            info = self.modules.get(path)
            if not info:
                continue
            name = info.get("name", "Unknown")

            global_session = self._create_search_session(
                state=self.SEARCH_STATES["global_search"],
                query=query,
                filters={},
                results=result,
                current_index=i,
            )
            buttons.append(
                [
                    {
                        "text": f"{i + 1}. {name}",
                        "callback": self._display_module_from_global,
                        "args": (path, global_session),
                    }
                ]
            )
        buttons.append(
            [{"text": self.strings["change_query"], "callback": self._enter_query}]
        )
        await call.edit(text=text[:4096], reply_markup=buttons)

    async def _display_module_from_global(
        self, call: InlineCall, module_path: str, session: Dict[str, Any]
    ):
        module_info = self.modules[module_path]
        await self._display_module(call, module_info, module_path, session, 0)

    async def _next_page(self, call: InlineCall, session: Dict[str, Any]):
        result = session["results"]
        index = session["current_index"]

        if index + 1 >= len(result):
            await call.answer(self.strings["last_page"])
            return
        index += 1
        module_path = result[index]
        module_info = self.modules[module_path]

        new_session = session.copy()
        new_session["current_index"] = index
        await self._display_module(call, module_info, module_path, new_session, 0)

    async def _previous_page(self, call: InlineCall, session: Dict[str, Any]):
        result = session["results"]
        index = session["current_index"]

        if index - 1 < 0:
            await call.answer(self.strings["first_page"])
            return
        index -= 1
        module_path = result[index]
        module_info = self.modules[module_path]

        new_session = session.copy()
        new_session["current_index"] = index
        await self._display_module(call, module_info, module_path, new_session, 0)

    async def _inline_void(self, call: InlineCall):
        await call.answer()

    @loader.command(ru_doc="[запрос / ничего] — Поиск модулей")
    async def limokacmd(self, message: Message):
        """[query / nothing] - Search modules"""
        args = utils.get_args_raw(message)
        lock_path = os.path.join(BASE_DIR, "limoka_search", "index.lock")

        if os.path.exists(lock_path):
            await utils.answer(message, self.strings["indexing_in_progress"])
            return
        if not args:
            markup = [
                [
                    {
                        "text": "✍️ " + self.strings["enter_query"],
                        "input": self.strings["enter_query"],
                        "handler": self._enter_query_handler,
                    }
                ],
                [
                    {
                        "text": self.strings["global_button"],
                        "callback": self._show_global_form,
                        "args": (message,),
                    }
                ],
            ]
            markup.append(
                [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
            )
            await self.inline.form(
                text=self.strings["start_search_form"],
                message=message,
                reply_markup=markup,
                photo=self._get_banner_for_state("global_search"),
            )
            return
        history = self.get("history", [])
        if len(history) >= 10:
            history = history[-9:]
        history.append(args)
        self.set("history", history)
        await utils.answer(
            message,
            self.strings["wait"].format(
                count=len(self.modules),
                fact=random.choice(self.strings["facts"]),
                query=args,
            ),
        )
        searcher = Search(args.lower(), self.ix)
        try:
            result = searcher.search_module()
        except Exception:
            return await utils.answer(message, self.strings["?"])
        if not result:
            return await utils.answer(message, self.strings["404"].format(query=args))
        module_path = result[0]
        module_info = self.modules[module_path]

        # Create session for displaying module
        display_session = self._create_search_session(
            state=self.SEARCH_STATES["global_search"],
            query=args,
            filters={},
            results=result,
            current_index=0,
        )
        await self._display_module(
            message, module_info, module_path, display_session, 0
        )

    async def _show_global_form(self, call: InlineCall, message: Message):
        markup = [
            [
                {
                    "text": "✍️ " + self.strings["enter_query"],
                    "input": self.strings["enter_query"],
                    "handler": self._global_search_handler,
                    "args": (message,),
                }
            ],
            [
                {
                    "text": "🔙 " + self.strings["back"],
                    "callback": self._inline_void,
                }
            ],
            [
                {
                    "text": self.strings.get("close", "❌ Close"),
                    "action": "close",
                }
            ],
        ]
        await call.edit(self.strings["global_search_form"], reply_markup=markup)

    async def _global_search_handler(
        self, call: InlineCall, query: str, message: Message, *args, **kwargs
    ):
        global_session = self._create_search_session(
            state=self.SEARCH_STATES["global_search"],
            query=query,
            filters={},
            results=[],
            current_index=0,
        )  # idk what is that crap but it works lol
        if len(query) <= 1:
            await call.edit(
                self.strings["?"],
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": lambda c: self._show_global_form(c, message),
                        }
                    ],
                    [
                        {
                            "text": self.strings.get("close", "❌ Close"),
                            "action": "close",
                        }
                    ],
                ],
            )
            return
        searcher = Search(query.lower(), self.ix)
        try:
            result = searcher.search_module()
        except Exception:
            await call.edit(
                self.strings["?"],
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": lambda c: self._show_global_form(c, message),
                        }
                    ],
                    [
                        {
                            "text": self.strings.get("close", "❌ Close"),
                            "action": "close",
                        }
                    ],
                ],
            )
            return
        if not result:
            await call.edit(
                self.strings["404"].format(query=query),
                reply_markup=[
                    [
                        {
                            "text": "🔄 " + self.strings["change_query"],
                            "callback": lambda c: self._show_global_form(c, message),
                        }
                    ],
                    [
                        {
                            "text": self.strings.get("close", "❌ Close"),
                            "action": "close",
                        }
                    ],
                ],
            )
            return
        text = self.strings["global_search"].format(
            query=html.escape(query), count=len(result)
        )
        buttons = []
        for i, path in enumerate(result[:15]):
            info = self.modules.get(path)
            if not info:
                continue
            name = info.get("name", "Unknown")
            buttons.append(
                [
                    {
                        "text": f"{i + 1}. {name}",
                        "callback": self._display_module_from_global,
                        "args": (path, global_session),
                    }
                ]
            )
        buttons.append(
            [
                {
                    "text": "🔄 " + self.strings["change_query"],
                    "callback": lambda c: self._show_global_form(c, message),
                }
            ]
        )
        buttons.append(
            [{"text": self.strings.get("close", "❌ Close"), "action": "close"}]
        )
        await call.edit(text=text[:4096], reply_markup=buttons)

    @loader.command(ru_doc="[clear] — Показать или очистить историю поиска")
    async def lshistorycmd(self, message: Message):
        """[clear] - Show or clear search history"""
        args = utils.get_args_raw(message).strip().lower()
        if args == "clear":
            self.set("history", [])
            await utils.answer(message, self.strings["history_cleared"])
            return
        if args:
            await utils.answer(message, self.strings["invalid_history_arg"])
            return
        history = self.get("history", [])
        if not history:
            await utils.answer(message, self.strings["empty_history"])
            return
        formatted_history = [
            f"{i + 1}. <code>{utils.escape_html(h)}</code>"
            for i, h in enumerate(history[-10:])
        ]
        await utils.answer(
            message,
            self.strings["history"].format(history="\n".join(formatted_history)),
        )

    @loader.watcher(from_dl=False)
    async def secure_install_watcher(self, message: Message):
        if not message.text:
            return
        if not hasattr(message, "from_id") or not message.from_id:
            return
        sender_id = None
        if hasattr(message.from_id, "user_id"):
            sender_id = message.from_id.user_id
        elif hasattr(message.from_id, "channel_id"):
            sender_id = message.from_id.channel_id
        if sender_id != self._service_bot_id:
            # logger.debug("Message not from official bot, ignoring")
            return
        if not self.config["external_install_allowed"]:
            return
        try:
            clean_text = (
                getattr(message, "raw_text", None)
                or getattr(message, "message", None)
                or message.text
                or ""
            )
            if message.entities:
                from html import unescape

                clean_text = unescape(clean_text)
            clean_text = re.sub(r"<[^>]+>", "", clean_text)
            match = re.search(r"#limoka:([^\s\"'<>]+)", clean_text)
            if not match:
                logger.debug(
                    "No #limoka tag found in cleaned text; leaving original message intact"
                )
                return
            tag_content = match.group(1)
            parts = tag_content.split(":", 1)
            if len(parts) != 2:
                logger.error("Invalid tag format after cleaning")
                await utils.answer(message, self.strings["watcher_invalid_format"])
                return
            module_path, signature_hex = parts
            module_path = re.sub(r"[<>\"']", "", module_path).strip()
            if module_path.startswith("href="):
                module_path = module_path[5:].strip('"').strip("'")
            if module_path not in self.modules:
                found = False
                for db_path in self.modules.keys():
                    if module_path in db_path or db_path in module_path:
                        module_path = db_path
                        found = True
                        break
                if not found:
                    logger.warning(f"Module not found after cleanup: {module_path}")
                    await utils.answer(
                        message,
                        self.strings["watcher_module_not_found"].format(
                            path=html.escape(module_path)
                        ),
                    )
                    return
            try:
                import base64
                from cryptography.hazmat.primitives.asymmetric import ed25519

                PUB_KEY_B64 = (
                    "MCowBQYDK2VwAyEA1ltSnqtf3pGBuctuAYqHivCXsaRtKOVxavai7yin7ZE="
                )
                der_bytes = base64.b64decode(PUB_KEY_B64)
                raw_pubkey = der_bytes[-32:]
                module_url = self.config["limokaurl"] + module_path
                async with aiohttp.ClientSession() as session:
                    async with session.get(module_url, timeout=10) as resp:
                        if resp.status != 200:
                            logger.error(
                                f"Failed to fetch module for verification: {module_url} (HTTP {resp.status})"
                            )
                            await utils.answer(
                                message, self.strings["watcher_loader_missing"]
                            )
                            return
                        module_bytes = await resp.read()
                        sha256 = hashlib.sha256(module_bytes).hexdigest()
                        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                            raw_pubkey
                        )
                        signature = bytes.fromhex(signature_hex)
                        signed_payload = f"{module_path}|{sha256}".encode()
                        public_key.verify(signature, signed_payload)
            except Exception as e:
                logger.error(f"Signature verification failed for {module_path}: {e}")
                await utils.answer(message, self.strings["watcher_signature_invalid"])
                return
            loader_mod = self.lookup("loader")
            if not loader_mod:
                logger.error("Loader module not found")
                await utils.answer(message, self.strings["watcher_loader_missing"])
                return
            module_url = self.config["limokaurl"] + module_path
            status = await loader_mod.download_and_install(module_url, None)
            if getattr(loader_mod, "fully_loaded", False):
                loader_mod.update_modules_in_db()
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            if status:
                try:
                    bot_peer = await self.client.get_entity(self._service_bot_id)
                    await self.client.send_message(
                        bot_peer, f"#limoka:sucsess:{message.id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send success confirmation: {e}")
            else:
                logger.error(f"Installation failed with status: {status}")
                try:
                    bot_peer = await self.client.get_entity(self._service_bot_id)
                    await self.client.send_message(
                        bot_peer, f"#limoka:failed:{message.id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send failure notification: {e}")
        except Exception as e:
            logger.exception(f"CRITICAL ERROR in secure_install_watcher: {e}")
            try:
                await utils.answer(
                    message, self.strings["watcher_critical"].format(error=str(e)[:100])
                )
                await asyncio.sleep(5)
                await message.delete()
            except Exception:
                pass

