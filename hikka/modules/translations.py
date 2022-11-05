#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from telethon.tl.types import Message

from .. import loader, translations, utils

logger = logging.getLogger(__name__)


@loader.tds
class Translations(loader.Module):
    """Processes internal translations"""

    strings = {
        "name": "Translations",
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translate pack"
            " saved!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Incorrect language"
            " specified</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translations reset"
            " to default ones</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Invalid pack format"
            " in url</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You need to specify"
            " valid url containing a langpack</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Command output seems"
            " to be too long, so it's sent in file.</b>"
        ),
        "opening_form": " <b>Opening form...</b>",
        "opening_gallery": " <b>Opening gallery...</b>",
        "opening_list": " <b>Opening list...</b>",
        "inline403": "🚫 <b>You can't send inline units in this chat</b>",
        "invoke_failed": "<b>🚫 Unit invoke failed! More info in logs</b>",
        "show_inline_cmds": "📄 Show all available inline commands",
        "no_inline_cmds": "You have no available commands",
        "no_inline_cmds_msg": (
            "<b>😔 There are no available inline commands or you lack access to them</b>"
        ),
        "inline_cmds": "ℹ️ You have {} available command(-s)",
        "inline_cmds_msg": "<b>ℹ️ Available inline commands:</b>\n\n{}",
        "run_command": "🏌️ Run command",
        "command_msg": "<b>🌘 Command «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Command «{}»",
        "button403": "You are not allowed to press this button!",
        "keep_id": "⚠️ Do not remove ID! {}",
    }

    strings_ru = {
        "lang_saved": "{} <b>Язык сохранён!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Пакет переводов"
            " сохранён!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Указан неверный"
            " язык</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Переводы сброшены"
            " на стандартные</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Неверный формат"
            " пакета переводов в ссылке</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Вы должны указать"
            " ссылку, содержащую пакет переводов</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Вывод команды слишком"
            " длинный, поэтому он отправлен в файле.</b>"
        ),
        "opening_form": " <b>Открываю форму...</b>",
        "opening_gallery": " <b>Открываю галерею...</b>",
        "opening_list": " <b>Открываю список...</b>",
        "inline403": "🚫 <b>Вы не можете отправлять встроенные элементы в этом чате</b>",
        "invoke_failed": "<b>🚫 Вызов модуля не удался! Подробнее в логах</b>",
        "show_inline_cmds": "📄 Показать все доступные встроенные команды",
        "no_inline_cmds": "У вас нет доступных inline команд",
        "no_inline_cmds_msg": (
            "<b>😔 Нет доступных inline команд или у вас нет доступа к ним</b>"
        ),
        "inline_cmds": "ℹ️ У вас {} доступная(-ых) команда(-ы)",
        "inline_cmds_msg": "<b>ℹ️ Доступные inline команды:</b>\n\n{}",
        "run_command": "🏌️ Выполнить команду",
        "command_msg": "<b>🌘 Команда «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Команда «{}»",
        "button403": "Вы не можете нажать на эту кнопку!",
        "keep_id": "⚠️ Не удаляйте ID! {}",
    }

    strings_de = {
        "lang_saved": "{} <b>Sprache gespeichert!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungs"
            " Paket gespeichert!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Falsche Sprache"
            " angegeben</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungen"
            " auf Standard zurückgesetzt</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Ungültiges"
            " Übersetzungs Paket in der URL</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Sie müssen eine"
            " gültige URL angeben, die ein Übersetzungs Paket enthält</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Befehlsausgabe scheint"
            " zu lang zu sein, daher wird sie in einer Datei gesendet.</b>"
        ),
        "opening_form": " <b>Formular wird geöffnet...</b>",
        "opening_gallery": " <b>Galerie wird geöffnet...</b>",
        "opening_list": " <b>Liste wird geöffnet...</b>",
        "inline403": "🚫 <b>Sie können Inline-Einheiten in diesem Chat nicht senden</b>",
        "invoke_failed": (
            "<b>🚫 Modulaufruf fehlgeschlagen! Weitere Informationen in den"
            " Protokollen</b>"
        ),
        "show_inline_cmds": "📄 Zeige alle verfügbaren Inline-Befehle",
        "no_inline_cmds": "Sie haben keine verfügbaren Inline-Befehle",
        "no_inline_cmds_msg": (
            "<b>😔 Keine verfügbaren Inline-Befehle oder Sie haben keinen Zugriff"
            " auf sie</b>"
        ),
        "inline_cmds": "ℹ️ Sie haben {} verfügbare(n) Befehl(e)",
        "inline_cmds_msg": "<b>ℹ️ Verfügbare Inline-Befehle:</b>\n\n{}",
        "run_command": "🏌️ Befehl ausführen",
        "command_msg": "<b>🌘 Befehl «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Befehl «{}»",
        "button403": "Sie können auf diese Schaltfläche nicht klicken!",
        "keep_id": "⚠️ Löschen sie das ID nicht! {}",
    }

    strings_tr = {
        "lang_saved": "{} <b>Dil kaydedildi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviri paketi"
            " kaydedildi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Yanlış dil"
            " belirtildi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviriler varsayılan"
            " hale getirildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'deki çeviri"
            " paketi geçersiz</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Geçerli bir URL"
            " belirtmelisiniz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Komut çıktısı çok uzun"
            " görünüyor, bu yüzden dosya olarak gönderildi.</b>"
        ),
        "opening_form": " <b>Form açılıyor...</b>",
        "opening_gallery": " <b>Galeri açılıyor...</b>",
        "opening_list": " <b>Liste açılıyor...</b>",
        "inline403": "🚫 <b>Bu sohbete satır içi birimler gönderemezsin</b>",
        "invoke_failed": (
            "<b>🚫 Modül çağrısı başarısız! Kayıtlardan daha fazla bilgiye"
            " erişebilirsin</b>"
        ),
        "show_inline_cmds": "📄 Tüm kullanılabilir inline komutlarını göster",
        "no_inline_cmds": "Kullanılabilir inline komutunuz yok",
        "no_inline_cmds_msg": (
            "<b>😔 Kullanılabilir inline komutunuz yok veya erişiminiz yok</b>"
        ),
        "inline_cmds": "ℹ️ {} kullanılabilir komutunuz var",
        "inline_cmds_msg": "<b>ℹ️ Kullanılabilir inline komutlar:</b>\n\n{}",
        "run_command": "🏌️ Komutu çalıştır",
        "command_msg": "<b>🌘 Komut «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Komut «{}»",
        "button403": "Bu düğmeye basamazsınız!",
        "keep_id": "⚠️ ID'yi silmeyin! {}",
    }

    strings_uz = {
        "lang_saved": "{} <b>Til saqlandi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjima paketi"
            " saqlandi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Noto'g'ri til"
            " belgilandi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjimalar"
            " standart holatga qaytarildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'dagi tarjima"
            " paketi noto'g'ri</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Siz noto'g'ri URL"
            " belirtdingiz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Bajarilgan buyruq"
            " natijasi juda uzun, shuning uchun fayl sifatida yuborildi.</b>"
        ),
        "opening_form": " <b>Formani ochish...</b>",
        "opening_gallery": " <b>Galeriyani ochish...</b>",
        "opening_list": " <b>Ro'yxatni ochish...</b>",
        "inline403": (
            "🚫 <b>Siz bu guruhda inline obyektlarni yuborishingiz mumkin emas</b>"
        ),
        "invoke_failed": (
            "<b>🚫 Modulni chaqirish muvaffaqiyatsiz! Batafsil ma'lumotlar"
            " jurnallarda</b>"
        ),
        "show_inline_cmds": "📄 Barcha mavjud inline buyruqlarini ko'rsatish",
        "no_inline_cmds": "Sizda mavjud inline buyruqlar yo'q",
        "no_inline_cmds_msg": (
            "<b>😔 Sizda mavjud inline buyruqlar yo'q yoki ularga kirish huquqingiz"
            " yo'q</b>"
        ),
        "inline_cmds": "ℹ️ Sizda {} mavjud buyruq bor",
        "inline_cmds_msg": "<b>ℹ️ Mavjud inline buyruqlar:</b>\n\n{}",
        "run_command": "🏌️ Buyruqni bajarish",
        "command_msg": "<b>🌘 Buyruq «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Buyruq «{}»",
        "button403": "Siz ushbu tugmani bosib bo'lmaysiz!",
        "keep_id": "⚠️ ID-ni o'chirmang! {}",
    }

    strings_es = {
        "lang_saved": "{} <b>¡Idioma guardado!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>¡Paquete de"
            " traducción guardado!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Idioma"
            " incorrecto seleccionado</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Restablecer la"
            " traducción a los valores predeterminados</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Paquete de"
            " traducción seleccionado incorrecto</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL incorrecta"
            " seleccionada</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>El resultado del"
            " comando excede el límite. Enviado como archivo.</b>"
        ),
        "opening_form": " <b>Abriendo formulario...</b>",
        "opening_gallery": " <b>Abriendo galería...</b>",
        "opening_list": " <b>Abriendo lista...</b>",
        "inline403": (
            "🚫 <b>No se permiten elementos de interfaz de usuario en este grupo</b>"
        ),
        "invoke_failed": (
            "<b>🚫 ¡Error al invocar la unidad! Consulte el registro"
            " para obtener más detalles</b>"
        ),
        "show_inline_cmds": "📄 Mostrar todos los comandos disponibles",
        "no_inline_cmds": "No hay comandos disponibles",
        "no_inline_cmds_msg": (
            "<b>😔 No hay comandos disponibles o no tienes permiso para acceder a"
            " los comandos</b>"
        ),
        "inline_cmds": "ℹ️ {} comandos disponibles",
        "inline_cmds_msg": "<b>ℹ️ Comandos disponibles:</b>\n\n{}",
        "run_command": "🏌️ Ejecutar comando",
        "command_msg": "<b>🌘 Comando '{}'</b>\n\n<i>{}</i>",
        "command": "🌘 Comando '{}'",
        "button403": "¡No puedes presionar este botón!",
        "button404": "¡No puedes presionar este botón ahora!",
    }

    strings_tt = {
        "lang_saved": "{} <b>Тел сакланган!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Тәрҗемә пакеты"
            " сакланган!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Дөрес булмаган тел"
            " күрсәтелгән</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Тәрҗемәләр стандартка"
            " ташланган</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Сылтамада тәрҗемә"
            " пакетларының дөрес булмаган форматы</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Сез тәрҗемә пакеты"
            " булган сылтаманы кертергә тиеш/b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Команда чыгышы бик"
            " озын, шуңа күрә ул файлда җибәрелә.</b>"
        ),
        "opening_form": " <b>Мин форманы ачам...</b>",
        "opening_gallery": " <b>Мин галереяны ачам...</b>",
        "opening_list": " <b>Исемлекне ачу...</b>",
        "inline403": "🚫 <b>Сез бу чатта урнаштырылган элементларны җибәрә алмыйсыз</b>",
        "invoke_failed": "<b>🚫 Модуль проблемасы уңышлы булмады! Логларда тулырак</b>",
        "show_inline_cmds": "📄 Барлык урнаштырылган командаларны күрсәтегез",
        "no_inline_cmds": "Сезнең inline командаларыгыз юк",
        "no_inline_cmds_msg": (
            "<b>😔 Inline командалар юк яисә аларга керү мөмкинлеге юк</b>"
        ),
        "inline_cmds": "ℹ️ Сездә {} уңайлы командалар бар",
        "inline_cmds_msg": "<b>ℹ️ Inline командалар:</b>\n\n{}",
        "run_command": "🏌️ Команданы үтәгез",
        "command_msg": "<b>🌘 Команда «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Команда «{}»",
        "button403": "Сез төймәгә баса алмыйсыз!",
        "keep_id": "⚠️ ID'ны бетеремэгез {}",
    }

    @loader.command(
        ru_doc="[языки] - Изменить стандартный язык",
        de_doc="[Sprachen] - Ändere die Standard-Sprache",
        tr_doc="[Diller] - Varsayılan dili değiştir",
        uz_doc="[til] - Standart tili o'zgartirish",
        es_doc="[Idiomas] - Cambiar el idioma predeterminado",
    )
    async def setlang(self, message: Message):
        """[languages in the order of priority] - Change default language"""
        args = utils.get_args_raw(message)
        if not args or any(len(i) != 2 for i in args.split(" ")):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        self._db.set(translations.__name__, "lang", args.lower())
        await self.allmodules.reload_translations()

        emoji_flags = {
            "🇬🇧": "<emoji document_id=6323589145717376403>🇬🇧</emoji>",
            "🇺🇿": " <emoji document_id=6323430017179059570>🇺🇿</emoji>",
            "🇷🇺": " <emoji document_id=6323139226418284334>🇷🇺</emoji>",
            "🇩🇪": " <emoji document_id=6320817337033295141>🇩🇪</emoji>",
            "🇪🇸": " <emoji document_id=6323315062379382237>🇪🇸</emoji>",
            "🇹🇷": " <emoji document_id=6321003171678259486>🇹🇷</emoji>",
            "🥟": "<emoji document_id=5382337996123020810>🥟</emoji>",
        }

        lang2country = {"en": "🇬🇧", "tt": "🥟"}

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join(
                    [
                        emoji_flags.get(flag, flag)
                        for flag in [
                            lang2country.get(lang) or utils.get_lang_flag(lang)
                            for lang in args.lower().split(" ")
                        ]
                    ]
                )
            ),
        )

    @loader.command(
        ru_doc="[ссылка на пак | пустое чтобы удалить] - Изменить внешний пак перевода",
        de_doc=(
            "[Link zum Paket | leer um zu entfernen] - Ändere das externe Übersetzungs"
            " Paket"
        ),
        tr_doc=(
            "[Çeviri paketi bağlantısı | boş bırakmak varsayılan hale getirir] - Harici"
            " çeviri paketini değiştir"
        ),
        uz_doc=(
            "[tarjima paketi havolasini | bo'sh qoldirish standart holatga qaytaradi] -"
            " Tashqi tarjima paketini o'zgartirish"
        ),
        es_doc="[Enlace al paquete | vacío para eliminar] - Cambiar el paquete de",
    )
    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change Hikka translate pack (external)
        """
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        await utils.answer(
            message,
            self.strings(
                "pack_saved"
                if await self.allmodules.reload_translations()
                else "check_pack"
            ),
        )
