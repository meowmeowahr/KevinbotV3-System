import os
import subprocess

import serial
from command_queue.commands import BaseCommand as _BaseCommand
from command_queue.commands import MultiprocessingCommand as _MpCmd

import pyttsx3
import playsound

import remote_interface

from loguru import logger

from settings import SettingsManager
from utils import split_string

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')
settings = SettingsManager(SETTINGS_PATH)


class SpeechCommand(_MpCmd):
    def __init__(self, content: str, engine: str):
        super().__init__()
        self.content = content
        self.engine = engine
        self.command = self._speak

    def _speak(self):
        import festival
        _espeak_engine = pyttsx3.init("espeak")
        if self.engine == "festival":
            festival.sayText(self.content.replace("Kevinbot", "Kevinbought"))
        elif self.engine == "espeak":
            _espeak_engine.say(self.content)
            _espeak_engine.runAndWait()


class RemoteHandshakeCommand(_BaseCommand):
    def __init__(self, interface: remote_interface.RemoteInterface, uid: str, version: str, current_state):
        super().__init__()
        self.interface = interface
        self.uid = uid
        self.version = version
        self.current_state = current_state
        self.command = self._handshake

    def _handshake(self):
        logger.info(f"Remote ({self.uid}) handshake started")
        self.interface.send(f"connection.handshake.start={self.uid}")
        self.interface.send(f"kevinbot.enabled={self.current_state.enabled}")
        self.interface.send(f"system.speechEngine={self.current_state.speech_engine}")
        self.interface.send(f"lighting.head.update={self.current_state.lighting_head_update}")
        self.interface.send(f"lighting.head.bright={self.current_state.lighting_head_brightness}")
        self.interface.send(f"lighting.body.update={self.current_state.lighting_body_update}")
        self.interface.send(f"lighting.body.bright={self.current_state.lighting_body_brightness}")
        self.interface.send(f"lighting.base.update={self.current_state.lighting_base_update}")
        self.interface.send(f"lighting.base.bright={self.current_state.lighting_base_brightness}")

        mesh = [f"KEVINBOTV3|{self.version}|kevinbot.kevinbot"] + self.current_state.connected_remotes
        data = split_string(",".join(mesh), settings.services.com.data_max)

        for count, part in enumerate(data):
            self.interface.send(f"system.remotes.list:{count}:"
                                f"{len(data) - 1}={data[count]}")

        self.interface.send(f"connection.handshake.end={self.uid}")
        logger.success(f"Remote ({self.uid}) handshake ended")


class RobotRequestEnableCommand(_BaseCommand):
    def __init__(self, ena: bool, core_interface: serial.Serial, remote: remote_interface.RemoteInterface,
                 current_state, sound: bool = True):
        super().__init__()
        self.ena = ena
        self.core = core_interface
        self.remote = remote
        self.sound = sound
        self.current_state = current_state
        self._command = self._request

    def _request(self):
        if self.current_state.error:
            self.remote.send(f"kevinbot.enableFailed={int(self.ena)}")
            return

        if not self.ena == self.current_state.enabled:
            logger.info(f"Enabled: {self.ena}")
            self.core.write(f"kevinbot.enabled={int(self.ena)}\n".encode("utf-8"))

            if not self.ena:
                # On disable
                self.core.write("head_effect=color1\n".encode("utf-8"))
                self.core.write("body_effect=color1\n".encode("utf-8"))
                self.core.write("base_effect=color1\n".encode("utf-8"))
                self.core.write("head_color1=000000\n".encode("utf-8"))
                self.core.write("body_color1=000000\n".encode("utf-8"))
                self.core.write("base_color1=000000\n".encode("utf-8"))

            self.remote.send(f"kevinbot.enabled={self.ena}")
            if self.sound:
                playsound.playsound(os.path.join(os.curdir,
                                                 "sounds/enable.wav"), False)


class RobotRequestEstopCommand(_BaseCommand):
    def __init__(self, core_interface: serial.Serial, remote: remote_interface.RemoteInterface,
                 current_state, power_off: bool = False):
        super().__init__()
        self.core = core_interface
        self.remote = remote
        self.power_off = power_off
        self.current_state = current_state
        self._command = self._request

    def _request(self):
        self.core.write("system.estop\n".encode("utf-8"))
        self.remote.send("system.estop")

        self.core.write("kevinbot.enabled=0\n".encode("utf-8"))
        self.remote.send("kevinbot.enabled=False")
        self.core.write("head_effect=color1\n".encode("utf-8"))
        self.core.write("body_effect=color1\n".encode("utf-8"))
        self.core.write("base_effect=color1\n".encode("utf-8"))
        self.core.write("head_color1=000000\n".encode("utf-8"))
        self.core.write("body_color1=000000\n".encode("utf-8"))
        self.core.write("base_color1=000000\n".encode("utf-8"))

        if self.power_off:
            self.core.flush()
            self.remote.serial.flush()
            subprocess.run(["systemctl", "poweroff"])


class RobotArmCommand(_BaseCommand):
    def __init__(self, core: serial.Serial, positions: list[int], arm_ports: list[int]):
        super().__init__()
        self.core = core
        self.positions = positions
        self.ports = arm_ports
        self._command = self._run

    def _run(self):
        for port, position in (zip(self.ports, self.positions)):
            self.core.write(f"s={port},{position}\n".encode("utf-8"))


class CoreSerialCommand(_BaseCommand):
    def __init__(self, core: serial.Serial, command: str):
        super().__init__()
        self._command = lambda: core.write(command.encode("utf-8"))