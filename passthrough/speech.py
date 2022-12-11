import os


def SayText(text):
    os.system('echo "{}" | festival --tts'.format(text.replace("Kevinbot", "Kevinbought")))

def SayTextEspeak(text):
    os.system('espeak "{}" -v english-us -p 45'.format(text))