# ©️ Undefined & XDesai, 2025
# This file is a part of Legacy Userbot
# 🌐 https://github.com/Crayz310/Legacy
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

from typing import Optional, Union, Any

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.client.default import DefaultBotProperties

from aiogram.types import InputFile, BufferedInputFile, FSInputFile, URLInputFile, InputFileUnion, Message

from urllib.parse import urlparse
import os
from io import BytesIO

def _is_url_valid(url: str) -> bool:
  """
  Checks whether the string passed is a syntactically correct URL

  Uses the built-in urlparse function to attempt to parse the string. Any error during parsing results in False being returned

  :param url: String to be checked
  :type url: str
  :returns: True if the string is a valid URL, otherwise False
  :rtype: bool
  """
  try:
    urlparse(url)

    return True
  except Exception:
    return False

class CustomBot(Bot):
  """
  Hybrid wrapper over `aiogram.Bot` for correct operation of modules that use aiogram 2.25

  Extends methods for automatic processing of various types of input data
  """

  def __init__(self, token: str, session: Optional[BaseSession] = None, default: Optional[DefaultBotProperties] = None, **kwargs: Any):
    super().__init__(token=token, session=session, default=default, **kwargs)
  
  async def send_document(self, chat_id: Union[int, str], document: Union[InputFile, str], thumb: Optional[Union[InputFile, str]] = None, filename: str = None, **kwargs: Any) -> Message:
    if isinstance(document, bytes):
      document = BufferedInputFile(document, filename=filename)
    elif isinstance(document, BytesIO):
      document = BufferedInputFile(document.getvalue(), filename=(getattr(document, "name") if hasattr(document, "name") else filename))
    elif isinstance(document, str):
      if os.path.exists(document):
        document = FSInputFile(document, filename=filename)
      elif _is_url_valid(document):
        document = URLInputFile(document, filename=filename)
      else:
        document = InputFileUnion(document)

    
    params = {
      "chat_id": chat_id,
      "document": document,
      "thumbnail": thumb
    }

    params.update(kwargs)

    return await super().send_document(**{k: v for k, v in params.items()})
  
  async def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile, str], **kwargs: Any) -> Message:
    if isinstance(photo, bytes):
      photo = BufferedInputFile(photo)
    elif isinstance(photo, BytesIO):
      photo = BufferedInputFile(photo.getvalue(), filename=(getattr(photo, "name") if hasattr(photo, "name") else None))
    elif isinstance(photo, str):
      if os.path.exists(photo):
        photo = FSInputFile(photo)
      elif _is_url_valid(photo):
        photo = URLInputFile(photo)
      else:
        photo = InputFileUnion(photo)

    
    params = {
      "chat_id": chat_id,
      "photo": photo
    }

    params.update(kwargs)

    return await super().send_photo(**{k: v for k, v in params.items()})
  
  async def send_video(self, chat_id: Union[int, str], video: Union[InputFile, str], thumb: Optional[Union[InputFile, str]] = None,  **kwargs: Any) -> Message:
    if isinstance(video, bytes):
      video = BufferedInputFile(video)
    elif isinstance(video, BytesIO):
      video = BufferedInputFile(video.getvalue(), filename=(getattr(video, "name") if hasattr(video, "name") else None))
    elif isinstance(video, str):
      if os.path.exists(video):
        video = FSInputFile(video)
      elif _is_url_valid(video):
        video = URLInputFile(video)
      else:
        video = InputFileUnion(video)

    
    params = {
      "chat_id": chat_id,
      "video": video,
      "thumbnail": thumb
    }

    params.update(kwargs)

    return await super().send_video(**{k: v for k, v in params.items()})
  