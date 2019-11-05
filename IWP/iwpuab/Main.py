from google.api_core.exceptions import InvalidArgument
from google.cloud import texttospeech
from PySide2 import QtGui
from PySide2.QtWidgets import (QApplication, QLabel, QPushButton,
                               QVBoxLayout, QWidget, QShortcut)
from PySide2.QtCore import Qt
from pydub import AudioSegment
from pydub.playback import play
import dialogflow
import os
import tempfile
import threading
import sys
import speech_recognition as rs

r = rs.Recognizer()

#Pointers
icon = './icon/uab.ico'
DIALOGFLOW_PROJECT_ID = "iwp-tnrykn"
DIALOGFLOW_LANGUAGE_CODE = 'en-US'
SESSION_ID = 'current-user-id' #For now Temporary
stringText = "Hello!\nPlease Start by saying \"Hello\""
import platform
if "Darwin" == platform.system():
    start = os.path.join(sys.argv[0].rsplit('/', 1)[0], "audio", "start.wav")
    end = os.path.join(sys.argv[0].rsplit('/', 1)[0], "audio", "end.wav")
    jsonCert = os.path.join(sys.argv[0].rsplit('/', 1)[0], "certs", "IWP-tnrykn-babf9d647c0b.json")
elif "Windows" == platform.system():
    #A tip. On some Windows machines, using Darwin's code works if you use \\ instead of /. Need to learn the Frozen dir if yes or no. To be Fixed.
    start = './audio/start.ogg'
    end = './audio/end.ogg'
    jsonCert = "./certs/IWP-tnrykn-babf9d647c0b.json"
else:
    start = './audio/start.wav'
    end = './audio/end.wav'
    jsonCert = "./certs/IWP-tnrykn-babf9d647c0b.json"
output = os.path.join(tempfile.gettempdir(), 'output.wav')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = jsonCert

def dialogflowMethod(textAsInput):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=textAsInput, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    responseNess = ""
    for obj in response.query_result.fulfillment_messages:
        for text in obj.text.text:
            responseNess += text
    return responseNess


def TTS(textAsInput):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.types.SynthesisInput(text=textAsInput)
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)
    response = client.synthesize_speech(synthesis_input, voice, audio_config)
    with open(output, 'wb') as out:
        out.write(response.audio_content)
    play(AudioSegment.from_mp3(output))
    os.remove(output)


def record():
    update_label("* recording")
    with rs.Microphone() as source:
        while recordStatus:
            audio = r.listen(source)
    update_label("* done recording")
    play(AudioSegment.from_ogg(end))
    try:
        text = r.recognize_google(audio)
    except:
        exceptMessage = "We didn't capture you quite well.\nCan you try again?"
        update_label(exceptMessage)
        TTS(exceptMessage)
        setButtonEnabled(True)
        return
    text2 = "You Said: "+str(text)
    update_label(text2)
    responseNess = dialogflowMethod(text)
    update_label(text2+"\nMr UAB Said: " + str(responseNess))
    TTS(responseNess)
    setButtonEnabled(True)


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setAutoRepeat(True)
        self.setAutoRepeatDelay(1000)
        self.setAutoRepeatInterval(1000)
        self.clicked.connect(self.handleClicked)
        self._state = 0

        # self.deleteShortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        # self.deleteShortcut.activated.connect(self.handleClicked)

    def handleClicked(self):
        global recordStatus
        if self.isDown():
            if self._state == 0:
                self._state = 1
                self.setAutoRepeatInterval(50)
                recordStatus = True
                x = threading.Thread(target=record)
                x.start()
                play(AudioSegment.from_ogg(start))
        elif self._state == 1:
            self._state = 0
            self.setAutoRepeatInterval(1000)
            recordStatus = False
            setButtonEnabled(False)


class MyWidget(QWidget):
    def __init__(self):
        global stringText
        QWidget.__init__(self)
        self.button = Button("Speak to Chatbot")
        self.text = QLabel(str(stringText))
        self.text.setAlignment(Qt.AlignCenter)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(icon))
    app.setApplicationName("IWP's Virtual Assistant")
    app.setApplicationDisplayName("IWP's Virtual Assistant")
    widget = MyWidget()
    widget.resize(500, 130)
    widget.show()

    def update_label(text):
        widget.text.setText(str(text))

    def setButtonEnabled(status):
        widget.button.setEnabled(status)
    sys.exit(app.exec_())

