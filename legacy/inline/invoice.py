# ©️ Undefined & XDesai, 2025
# This file is a part of Legacy Userbot
# 🌐 https://github.com/Crayz310/Legacy
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Based on Dan Gazizullin's work
# 🌐 https://github.com/hikariatama/Hikka

import logging
import typing

from aiogram.types import (InlineQuery, InlineQueryResultArticle,
                           InputInvoiceMessageContent, LabeledPrice)
from legacytl.tl.types import Message

from .. import utils
from .types import InlineMessage, InlineUnit

logger = logging.getLogger(__name__)


class Invoice(InlineUnit):
    async def invoice(
        self,
        message: typing.Union[Message, int],
        title: str,
        description: str,
        id: str,
        payload: str,
        label: str,
        amount: int,
        currency: str,
        *,
        photo_url: typing.Optional[str] = None,
        max_tip_amount: typing.Optional[int] = None,
        suggested_tip_amounts: typing.Optional[typing.List[int]] = None
    ) -> typing.Union[InlineMessage, bool]:
        if not isinstance(message, Message):
            logger.error(
                "Invalid type for `message`. Expected Message, got %s",
                type(message),
            )
            return False

        if not isinstance(title, str):
            logger.error("Invalid type for `title`. Expected str, got %s", type(title))
            return False

        if not isinstance(description, str):
            logger.error(
                "Invalid type for `description`. Expected str, got %s",
                type(description),
            )
            return False

        if not isinstance(id, str):
            logger.error("Invalid type for `id`. Expected str, got %s", type(id))
            return False

        if not isinstance(payload, str):
            logger.error(
                "Invalid type for `payload`. Expected str, got %s", type(payload)
            )
            return False

        if not isinstance(currency, str):
            logger.error(
                "Invalid type for `currency`. Expected str, got %s", type(currency)
            )
            return False

        if not isinstance(amount, int):
            logger.error(
                "Invalid type for `amount`. Expected int, got %s",
                type(prices),
            )
            return False

        if not isinstance(label, str):
            logger.error(
                "Invalid type for `label`. Expected str, got %s",
                type(prices),
            )
            return False
        if isinstance(message, Message) and message.out:
            await message.delete()
        unit_id = utils.rand(16)
        self._units[unit_id] = {
            "type": "invoice",
            "title": title,
            "id": id,
            "payload": payload,
            "currency": currency,
            "prices": {"label": label, "amount": amount},
            "description": description,
            "photo_url": photo_url,
            "max_tip_amount": max_tip_amount,
            "suggested_tip_amounts": suggested_tip_amounts,
            "uid": unit_id,
        }

        m = await self._invoke_unit(unit_id, message)
        del self._units[unit_id]

    async def _invoice_inline_handler(self, inline_query: InlineQuery):
        form = self._units[inline_query.query]
        results = [
            InlineQueryResultArticle(
                title=form["title"],
                description=form["description"],
                id=form["id"],
                input_message_content=InputInvoiceMessageContent(
                    title=form["title"],
                    description=form["description"],
                    payload=form["payload"],
                    photo_url=form["photo_url"],
                    suggested_tip_amounts=form["suggested_tip_amounts"],
                    max_tip_amount=form["max_tip_amount"],
                    currency=form["currency"],
                    prices=[
                        LabeledPrice(
                            label=form["prices"]["label"],
                            amount=form["prices"]["amount"],
                        )
                    ],
                ),
            )
        ]
        await inline_query.answer(results, cache_time=0)
        return
