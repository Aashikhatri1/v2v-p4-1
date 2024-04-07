import asyncio
import json
import pyaudio
import websockets
from dotenv import load_dotenv
import pyautogui as pg
import os
import sys

load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000

class Transcriber:
    def __init__(self, on_transcript=None):
        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.stop_pushing = False
        self.on_transcript = on_transcript

    def mic_callback(self, input_data, frame_count, time_info, status_flag):
        if not self.stop_pushing:
            self.audio_queue.put_nowait(input_data)
        return (input_data, pyaudio.paContinue)

    async def sender(self, ws, timeout=1):
        try:
            while not self.stop_pushing:
                mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
                await ws.send(mic_data)
        except asyncio.TimeoutError:
            print("Timeout in sender coroutine. Stopping the push.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly in sender: {e}")
        finally:
            self.stop_pushing = True

    async def receiver(self, ws):
        full_transcript = ""
        try:
            async for msg in ws:
                res = json.loads(msg)
                transcript = (
                    res.get("channel", {})
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                if transcript.strip():
                    full_transcript += transcript + " "
                if res.get("speech_final"):
                    if self.on_transcript:
                        await self.on_transcript(full_transcript.strip())
                    full_transcript = ""
        except asyncio.TimeoutError:
            print("Timeout occurred in receiver coroutine.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly in receiver: {e}")

    async def run(self, key):
        deepgram_url = "wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        p = pyaudio.PyAudio()
        self.stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, stream_callback=self.mic_callback)
        self.stream.start_stream()

        try:
            async with websockets.connect(deepgram_url, extra_headers={"Authorization": f"Token {key}"}) as ws:
                sender_coroutine = self.sender(ws)
                receiver_coroutine = self.receiver(ws)
                await asyncio.gather(sender_coroutine, receiver_coroutine)
        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            p.terminate()

transcription_buffer = []
current_processing_task = None
new_data_event = asyncio.Event()

# async def handle_transcript(transcript):
#     global current_processing_task, transcription_buffer
#     transcription_buffer.append(transcript)
#     if current_processing_task and not current_processing_task.done():
#         current_processing_task.cancel()  # Cancel the currently running task
#     new_data_event.set()

async def handle_transcript(transcript):
    global current_processing_task, transcription_buffer
    # Check if the transcript is not None and not empty
    if transcript and not transcript.isspace():
        transcription_buffer.append(transcript)
        # Cancel the currently running processing task if it exists and is not already completed
        if current_processing_task and not current_processing_task.done():
            current_processing_task.cancel()  # Cancel the currently running task
        new_data_event.set()

async def process_transcription_data(data):
    # Placeholder for your processing logic - adjust as necessary
    print(f"Processing data: {data}")
    await asyncio.sleep(1)
    print('1')

    await asyncio.sleep(1)
    print('2')

    await asyncio.sleep(1)
    print('3')

    await asyncio.sleep(1)
    print('4')

    await asyncio.sleep(1)
    print('5')

    await asyncio.sleep(1)
    print('6')

async def process_transcriptions():
    global transcription_buffer, current_processing_task
    while True:
        await new_data_event.wait()
        if transcription_buffer:
            data_to_process = " ".join(transcription_buffer)
            transcription_buffer = []  # Clear buffer after copying
            current_processing_task = asyncio.create_task(process_transcription_data(data_to_process))
            try:
                await current_processing_task
            except asyncio.CancelledError:
                print("Processing was cancelled due to new transcript.")
            new_data_event.clear()  # Clear the event until new data arrives

async def main():
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    if DEEPGRAM_API_KEY is None:
        print("Please set the DEEPGRAM_API_KEY environment variable.")
        return
    transcriber = Transcriber(on_transcript=handle_transcript)
    transcription_task = asyncio.create_task(transcriber.run(DEEPGRAM_API_KEY))
    processing_task = asyncio.create_task(process_transcriptions())

    await asyncio.gather(transcription_task, processing_task)

# if __name__ == "__main__":
#     asyncio.run(main())

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        # Create a new event loop if the default one is closed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())