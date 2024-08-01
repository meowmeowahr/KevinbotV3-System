"""
Interface for Kevinbot Remote over XBee
"""

import serial
import xbee
import enum

from loguru import logger


class RemoteCommand(enum.StrEnum):
    RemoteListAdd = "connection.remotes.add"
    RemoteListRemove = "connection.remotes.remove"
    RemoteListFetch = "connection.remotes.get"
    RemoteStatus = "connection.remote.status"
    Ping = "connection.ping"

    RequestEnable = "kevinbot.request.enable"
    RequestEstop = "kevinbot.request.estop"

    ArmPositions = "arms.positions"

    SpeechEngine = "system.speechEngine"
    SpeechSpeak = "system.speak"

    LightingHeadEffect = "lighting.head.effect"
    LightingBodyEffect = "lighting.body.effect"
    LightingBaseEffect = "lighting.base.effect"
    LightingHeadColor1 = "lighting.head.color1"
    LightingBodyColor1 = "lighting.body.color1"
    LightingBaseColor1 = "lighting.base.color1"
    LightingHeadColor2 = "lighting.head.color2"
    LightingBodyColor2 = "lighting.body.color2"
    LightingBaseColor2 = "lighting.base.color2"
    LightingHeadUpdateSpeed = "lighting.head.update"
    LightingBodyUpdateSpeed = "lighting.body.update"
    LightingBaseUpdateSpeed = "lighting.base.update"
    LightingCameraBrightness = "lighting.camera.brightness"

    EyeFetchSettings = "eyes.getSettings"
    EyeSetState = "eyes.setState"
    EyeSetSpeed = "eyes.setSpeed"
    EyeSetPosition = "eyes.setPosition"
    EyeSetMotion = "eyes.setMotion"
    EyeSetBacklight = "eyes.setBacklight"
    EyeSetSkinOption = "eyes.setSkinOption"

    HeadXPosition = "head.position.x"
    HeadYPosition = "head.position.y"

    DriveLeft = "drivebase.left"
    DriveRight = "drivebase.right"

    NoCommand = ""


class RemoteInterface:
    def __init__(self, port: str, baud: int, escaped: bool = False):
        self.port = port
        self.baud = baud

        self.serial = serial.Serial(self.port, baudrate=self.baud)
        self.xbee = xbee.XBee(self.serial, escaped=escaped)

    def get(self) -> dict:
        data = self.xbee.wait_read_frame()
        print("got data")

        logger.log("DATA", f"Got XBee frame {data}")

        if "rf_data" not in data.keys():
            return {"raw": "".encode("utf-8"), "status": "no_rf_data", "command": RemoteCommand.NoCommand, "value": ""}

        cv = data['rf_data'].decode().strip("\r\n").split('=', 1)

        if len(cv) == 1:
            value = ""
        else:
            value = cv[1]

        return {"raw": data['rf_data'], "status": "ok", "command": RemoteCommand(cv[0]), "value": value}

    def send(self, data: str):
        self.xbee.send("tx", dest_addr=b'\x00\x00',
                       data=bytes("{}".format(data), 'utf-8'))
