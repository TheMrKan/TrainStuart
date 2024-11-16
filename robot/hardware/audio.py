import os.path
import wave
import sys
import threading
import pyaudio
from utils.cancelations import CancellationToken
from typing import Optional


class AudioOutput:

    FILES_DIR = None

    CHUNK = 1024

    _playing_thread: Optional[threading.Thread] = None
    _cancellation: Optional[CancellationToken] = None

    @classmethod
    def play(cls, filename: str, cancellation: CancellationToken = None):
        filename = os.path.join(cls.FILES_DIR or os.getcwd(), filename)
        with wave.open(filename, 'rb') as wf:
            p = pyaudio.PyAudio()
            try:

                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
                try:

                    while len(data := wf.readframes(cls.CHUNK)) and (not cancellation or not cancellation.cancellation_event.is_set()):
                        stream.write(data)
                finally:
                    stream.close()
            finally:
                p.terminate()

    @classmethod
    def interrupt(cls):
        if cls._playing_thread is not None and cls._playing_thread.is_alive():
            if cls._cancellation is not None:
                cls._cancellation.cancel()
                cls._playing_thread.join()

    @classmethod
    def _play_and_clear(cls, filename: str):
        try:
            cls.play(filename, cls._cancellation)
        finally:
            cls._playing_thread = None
            cls._cancellation = None

    @classmethod
    def play_async(cls, filename: str):
        #cls.interrupt()

        cls._cancellation = CancellationToken()
        cls._playing_thread = threading.Thread(target=cls._play_and_clear, args=(filename, ))
        cls._playing_thread.start()
