import os
import socket
from aiohttp import web
from platform import uname
from abc import ABC


class BaseHost(ABC):
    name: str = ""
    display_name: str = ""
    emoji: str = ""
    emoji_document_id: int = 0
    multiple_sessions_per_acc: bool = True

    def __init__(self):
        if (
            not self.name
            or not self.display_name
            or not self.emoji
            or not self.emoji_document_id
        ):
            raise ValueError(
                "Host class must define name, display_name, emoji, and emoji_document_id."
            )

    def is_eula_forbidden(self):
        if not self.multiple_sessions_per_acc:
            return True
        return False

    def get_forbidden_response(self):
        return web.Response(status=403, body=f"Forbidden by {self.display_name} EULA")


class VDS(BaseHost):
    name = "VDS"
    display_name = "VDS"
    emoji = "💎"
    emoji_document_id = 5467541303938019154


class Railway(BaseHost):
    name = "RAILWAY"
    display_name = "Railway"
    emoji = "🚂"
    emoji_document_id = 5456525163795344370


class Userland(BaseHost):
    name = "USERLAND"
    display_name = "Userland"
    emoji = "🐧"
    emoji_document_id = 5458508523858062696


class Oracle(BaseHost):
    name = "ORACLE"
    display_name = "Oracle"
    emoji = "🧨"
    emoji_document_id = 5380110961090788815


class Aeza(BaseHost):
    name = "AEZA"
    display_name = "Aeza"
    emoji = "🛡"
    emoji_document_id = 5467637896789538823


class WSL(BaseHost):
    name = "WSL"
    display_name = "WSL"
    emoji = "🍀"
    emoji_document_id = 5467729112632330243


class Docker(BaseHost):
    name = "DOCKER"
    display_name = "Docker"
    emoji = "🐳"
    emoji_document_id = 5456574628933693253


class HikkaHost(BaseHost):
    name = "HIKKAHOST"
    display_name = "HikkaHost"
    emoji = "🌼"
    emoji_document_id = 5458807006905264299
    multiple_sessions_per_acc = False


class OrangePi(BaseHost):
    name = "ORANGE"
    display_name = "Orange Pi"
    emoji_document_id = 5467811234567890123
    emoji = "🍊"


class RaspberryPi(BaseHost):
    name = "RASPBERRY"
    display_name = "Raspberry Pi"
    emoji = "🍇"
    emoji_document_id = 5467892345678901234


class HostManager:
    supported_hosts = [
        RaspberryPi,
        HikkaHost,
        Userland,
        OrangePi,
        Railway,
        Docker,
        Oracle,
        Aeza,
        VDS,
        WSL,
    ]

    def __init__(self):
        self._hosts = {}
        self._register_supported_hosts()

    def _register_supported_hosts(self):

        for host in self.supported_hosts:
            try:
                host_class = host()
                self._hosts[host_class.name.lower()] = host_class
            except ValueError as e:
                print(str(e))

    def get_host(self, host_name):
        return self._hosts.get(host_name.lower())

    def _detect_by_uname(self):
        for host in self._hosts:
            if host.lower() in uname().release.lower():
                return self.get_host(host)
        return None

    def _detect_by_device_tree(self):
        if os.path.isfile("/proc/device-tree/model"):
            with open("/proc/device-tree/model") as f:
                model = f.read()
                for host in self._hosts:
                    if host.lower() in model.lower():
                        return self.get_host(host)
        return None

    def _detect_by_hostname(self):
        for host in self._hosts:
            if host.lower() in socket.gethostname().lower():
                return self.get_host(host)
        return None

    def _detect_by_env_vars(self):
        for host in self._hosts:
            if os.environ.get(host.upper()) or os.environ.get(host.lower()):
                return self.get_host(host)
        return None

    def _get_default_host(self):
        return self.get_host("vds")

    def get_current_hosting(self):
        detection_chain = [
            self._detect_by_uname,
            self._detect_by_device_tree,
            self._detect_by_hostname,
            self._detect_by_env_vars,
            self._get_default_host,
        ]
        for detect in detection_chain:
            host = detect()
            if host:
                return host


host_manager = HostManager()
