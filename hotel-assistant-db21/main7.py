import asyncio
import json
import pyaudio
import websockets
from dotenv import load_dotenv
import pyautogui as pg
import os
import sys

from datetime import datetime

load_dotenv()

sys.path.append('./components')
sys.path.append('./assets')
from log import print_and_save
import sounddevice as sd
import soundfile as sf
# import csv2json

# csv2json.convert_csv_to_json('data.csv')
# import csv2json
# csv2json.convert_csv_to_json('assets/roomav.csv', 'roomav.json')


# from speech_to_text_new import transcribe_stream
import part2_new
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts

prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

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

    async def sender(self, ws, timeout=10):
        silent_data = self.generate_silent_data()
        try:
            while not self.stop_pushing:
                try:
                    mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
                except asyncio.TimeoutError:
                    mic_data = silent_data  # Send silent data if there's no real data to send
                await ws.send(mic_data)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly in sender: {e}")
        finally:
            self.stop_pushing = True

    def generate_silent_data(self, duration=0.1):
        """Generate silent audio data to keep the connection alive."""
        # Number of frames per buffer
        num_frames = int(RATE * duration)
        silent_data = (b'\x00\x00' * num_frames)
        return silent_data


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

#####################################################
class Transcriber:
    def __init__(self, on_transcript=None):
        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.stop_pushing = False
        self.on_transcript = on_transcript
        self.reconnect_delay = 0.3  # seconds to wait before attempting to reconnect

    def mic_callback(self, input_data, frame_count, time_info, status_flag):
        if not self.stop_pushing:
            self.audio_queue.put_nowait(input_data)
        return (input_data, pyaudio.paContinue)

    async def connect_and_transcribe(self, key):
        deepgram_url = "wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        try:
            async with websockets.connect(deepgram_url, extra_headers={"Authorization": f"Token {key}"}) as ws:
                sender_coroutine = self.sender(ws)
                receiver_coroutine = self.receiver(ws)
                await asyncio.gather(sender_coroutine, receiver_coroutine)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed. Attempting to reconnect...")
            await asyncio.sleep(self.reconnect_delay)  # Wait before attempting to reconnect
            self.stop_pushing = False  # Reset the flag to allow pushing data
            await self.connect_and_transcribe(key)  # Attempt to reconnect
            
    async def sender(self, ws, timeout=1):
        try:
            while not self.stop_pushing:
                mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
                await ws.send(mic_data)
        except asyncio.TimeoutError:
            print("Timeout in sender coroutine. Stopping the push.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly in sender: {e}")
            # await self.connect_and_transcribe(key)
        finally:
            self.stop_pushing = True

    async def receiver(self, ws):
        try:
            async for msg in ws:
                res = json.loads(msg)
                transcript = (
                    res.get("channel", {})
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                if transcript.strip() and self.on_transcript:
                    await self.on_transcript(transcript.strip())
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly in receiver: {e}")
            # await self.connect_and_transcribe(key)

    

    async def run(self, key):
        p = pyaudio.PyAudio()
        self.stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=1024, stream_callback=self.mic_callback)
        self.stream.start_stream()

        await self.connect_and_transcribe(key)  # Start the connection and transcription process

        # Cleanup
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        p.terminate()


class Transcriber1:
    def __init__(self, on_transcript=None):
        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.on_transcript = on_transcript
        self.reconnect_delay = 0.3  # seconds

    def mic_callback(self, input_data, frame_count, time_info, status_flag):
        self.audio_queue.put_nowait(input_data)
        return (input_data, pyaudio.paContinue)

    async def sender(self, ws):
        while True:
            mic_data = await self.audio_queue.get()
            await ws.send(mic_data)

    async def receiver(self, ws):
        async for msg in ws:
            res = json.loads(msg)
            transcript = (
                res.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
            )
            if transcript.strip() and self.on_transcript:
                await self.on_transcript(transcript.strip())

    async def transcribe(self, key):
        deepgram_url = "wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        async with websockets.connect(deepgram_url, extra_headers={"Authorization": f"Token {key}"}) as ws:
            sender_task = asyncio.create_task(self.sender(ws))
            receiver_task = asyncio.create_task(self.receiver(ws))
            await asyncio.gather(sender_task, receiver_task)

    async def manage_connection(self, key):
        while True:
            try:
                await self.transcribe(key)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed unexpectedly: {e}, attempting to reconnect...")
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                print(f"Unexpected error: {e}, attempting to reconnect...")
                await asyncio.sleep(self.reconnect_delay)

    async def run(self, key):
        p = pyaudio.PyAudio()
        self.stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=1024, stream_callback=self.mic_callback)
        self.stream.start_stream()
        
        await self.manage_connection(key)
        
        # Cleanup
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

    output_filename = 'assets/log/'+ datetime.now().strftime('%d-%m-%Y_%H-%M-%S') + '.txt'
    chat_history = []
    chat_user_info = {}
    filename = "assets/intro.wav"
    # data, fs = sf.read(filename)
    # sd.play(data, fs)
    # Placeholder for your processing logic - adjust as necessary
    print(f"Processing data: {data}")
    # await asyncio.sleep(1)
    # print('1')

    # await asyncio.sleep(1)
    # print('2')

    # await asyncio.sleep(1)
    # print('3')

    # await asyncio.sleep(1)
    # print('4')

    # await asyncio.sleep(1)
    # print('5')

    # await asyncio.sleep(1)
    # print('6')
    query = data
    print('\n query:', query)
    print_and_save('LlamaPerplexity', output_filename)
    print_and_save(f'|User| {query} | ', output_filename)
    print_and_save(str(datetime.now()), output_filename)
    print_and_save('\n', output_filename)

    base, extension = output_filename.rsplit('.', 1)
    detailed_filename = f"{base}_detailed.{extension}"

    print_and_save('LlamaPerplexity', detailed_filename)
    print_and_save(f'|User| {query} | ',detailed_filename)
    print_and_save(str(datetime.now()), detailed_filename)
    print_and_save('\n', detailed_filename)
    
    print('1')
    category_filler = await llama_get_category(query, chat_history, prompt1, prompt2, output_filename)  # Processes the query to categorize and determine the filler response.
    print('category_filler:', category_filler)
    print('2')
    filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)
    print('3')

    print('category_filler:', category_filler)
    print('filler_no:', filler_no)
    print('Category:', Category)
    print('Sub_Category:', Sub_Category)
    print('QuestionType:', QuestionType)

    ContextGiven = ''
    for item in category_filler:
        print('4')
        category_dict = json.loads(item[0].replace('\n', ''))
        
        # Check if the dictionary has 'Category' or 'FillerNo' and update the variables accordingly
        if 'Context Given' in category_dict:
            ContextGiven = category_dict['Context Given']

    # Assembling the category information into a dictionary for further processing.
    category = {
        'Category': Category,
        'Sub Category': Sub_Category,
        'QuestionType': QuestionType,
        'ContextGiven': ContextGiven
    }
    print('5')
    # Processes the user query and updates chat history accordingly.
    chat_history, chat_user_info = part2_new.response_type(query, category, chat_history, output_filename, chat_user_info)
    print(chat_history)
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
    print('Start Speaking...')
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