from typing import Callable, Literal

from command_queue.commands import BaseCommand as _BaseCommand
from command_queue.commands import MultiprocessingCommand as _MpCmd

import pyttsx3


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
