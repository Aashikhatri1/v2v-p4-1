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

new_transcript_received = False

# import csv2json

# csv2json.convert_csv_to_json('data.csv')
# import csv2json
# csv2json.convert_csv_to_json('assets/roomav.csv', 'roomav.json')


# from speech_to_text_new import transcribe_stream
import part2
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts

prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000
key = os.getenv('DEEPGRAM_API_KEY')


class Transcriber:
    def __init__(self, on_transcript=None):
        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.stop_pushing = False
        self.on_transcript = on_transcript
        self.reconnect_delay = 0.3  # Time to wait before retrying connection
        self.max_reconnect_attempts = 5  # Max attempts to reconnect

    async def connect_and_transcribe(self, key):
        attempt_count = 0
        while attempt_count < self.max_reconnect_attempts:
            try:
                async with websockets.connect(
                        "wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000",
                        extra_headers={"Authorization": f"Token {key}"}) as ws:
                    self.stop_pushing = False
                    sender_coroutine = self.sender(ws)
                    receiver_coroutine = self.receiver(ws)
                    await asyncio.gather(sender_coroutine, receiver_coroutine)
                    break  # Exit loop if successfully connected and messages are processed
            except websockets.exceptions.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}. Attempting to reconnect...")
                attempt_count += 1
                await asyncio.sleep(self.reconnect_delay)
        
        if attempt_count >= self.max_reconnect_attempts:
            print("Maximum reconnect attempts reached. Stopping transcription.")

    def mic_callback(self, input_data, frame_count, time_info, status_flag):
        if not self.stop_pushing:
            self.audio_queue.put_nowait(input_data)
        return (input_data, pyaudio.paContinue)

    async def attempt_reconnect(self):
        self.stop_pushing = True  # Stop pushing data to ensure a clean state for reconnection
        
        # Check if the stream is open before trying to stop it
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
        if self.stream:
            self.stream.close()
        
        self.audio_queue = asyncio.Queue()  # Reset the audio queue
        
        # Ensure the audio stream is properly reset
        self.stream = None
        
        await asyncio.sleep(0.5)  # Wait for a few seconds before attempting to reconnect
        
        # Reset flag to start pushing data again
        self.stop_pushing = False
        
        # Reinitialize the stream as it was closed
        p = pyaudio.PyAudio()
        self.stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=1024, stream_callback=self.mic_callback)
        
        # Attempt to run the transcriber again with the current API key
        await self.connect_and_transcribe(key)


    async def sender(self, ws, timeout=10):
        while not self.stop_pushing:
            try:
                if self.audio_queue.empty():
                    await asyncio.sleep(0.1)  # Give some time to accumulate audio data
                    continue  # Skip this iteration if there's no data to send

                mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
                await ws.send(mic_data)
            except asyncio.TimeoutError:
                print("Timeout in sender coroutine. Stopping the push.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"WebSocket connection closed unexpectedly in sender: {e}")
                if "1011" in str(e):
                    self.stop_pushing = True  # Ensure to stop pushing data on specific error
                    await self.attempt_reconnect()  # Attempt to reconnect
                    break
                    # continue
                else:
                    raise  # Reraise the exception if it's not the specific error we're handling
            

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
            if "1011" in str(e):
                await self.attempt_reconnect()  # Attempt to reconnect
            else:
                raise  # Reraise the exception if it's not the specific error we're handling


    async def run(self, key):
        # Initialize and start the audio stream
        p = pyaudio.PyAudio()
        self.stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=1024, stream_callback=self.mic_callback)
        self.stream.start_stream()

        await self.connect_and_transcribe(key)  # Attempt to connect and transcribe

        # Cleanup
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        p.terminate()

transcription_buffer = []
current_processing_task = None
new_data_event = asyncio.Event()


# async def handle_transcript(transcript):
#     global current_processing_task, transcription_buffer
#     global new_transcript_received
#     # Check if the transcript is not None and not empty
#     if transcript and not transcript.isspace():
#         transcription_buffer.append(transcript)
#         # Cancel the currently running processing task if it exists and is not already completed
#         if current_processing_task and not current_processing_task.done():
#             current_processing_task.cancel()  # Cancel the currently running task
#             new_transcript_received = True
#         new_data_event.set()

# async def handle_transcript(transcript):
#     global current_processing_task, transcription_buffer, new_transcript_received
#     if transcript and not transcript.isspace():
#         transcription_buffer.append(transcript)
        
#         # Indicate a new transcript has been received
#         new_transcript_received = True

#         if current_processing_task and not current_processing_task.done():
#             current_processing_task.cancel()
        
#         new_data_event.set()

async def handle_transcript(transcript):
    global current_processing_task, transcription_buffer, new_transcript_received
    if transcript and not transcript.isspace():
        transcription_buffer.append(transcript)
        
        # Signal that a new transcript has been received.
        new_transcript_received = True

        if current_processing_task and not current_processing_task.done():
            current_processing_task.cancel()
        
        new_data_event.set()



async def step1(query, chat_history, output_filename ):
    print(query)
    print('1')
    category_filler = await llama_get_category(query, chat_history, prompt1, prompt2, output_filename)  # Processes the query to categorize and determine the filler response.
    print('category_filler:', category_filler)
    print('2')
    return category_filler

async def step2(category_filler):
    filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)
    print('3')
    return filler_no, Category, Sub_Category, QuestionType

async def step3(category_filler,filler_no, Category, Sub_Category, QuestionType):
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
    return category

async def step4(query, category, output_filename, chat_history, chat_user_info):
    chat_history, chat_user_info = await part2.response_type(query, category, chat_history, output_filename, chat_user_info)
    print(chat_history)
    print('6')
    return chat_history, chat_user_info

async def process_transcription_data(data):

    output_filename = 'assets/log/'+ datetime.now().strftime('%d-%m-%Y_%H-%M-%S') + '.txt'
    chat_history = []
    chat_user_info = {}
    filename = "assets/intro.wav"
    global new_transcript_received
    try: 
        category_filler = await step1(data,chat_history, output_filename)
        await asyncio.sleep(1)
        filler_no, Category, Sub_Category, QuestionType = await step2(category_filler)
        await asyncio.sleep(2)
        category = await step3(category_filler,filler_no, Category, Sub_Category, QuestionType)
        await asyncio.sleep(3)
        chat_history, chat_user_info = await step4(data, category, output_filename, chat_history, chat_user_info)
        return chat_history


    except asyncio.CancelledError:
        # Perform cleanup here if necessary
        print("Task was cancelled....")
        # raise  # It's a good practice to re-raise the CancelledError after handling it
        return
    
    # try:
    #     await asyncio.sleep(1)
    #     print('1')

    #     await asyncio.sleep(1)
    #     print('2')

    #     await asyncio.sleep(1)
    #     print('3')

    #     await asyncio.sleep(1)
    #     print('4')

    #     await asyncio.sleep(1)
    #     print('5')

    #     await asyncio.sleep(1)
    #     print('6')
    # except asyncio.CancelledError:
    #     # Perform cleanup here if necessary
    #     print("Task was cancelled....")
    #     # raise  # It's a good practice to re-raise the CancelledError after handling it
    #     return

############################################################
    # try: 
    #     print(f"Processing data: {data}")
    
    # # if new_transcript_received:
    # #     print('cancelling the task..')
    # #     return
    # # else:
    #     query = data
    #     print('\n query:', query)
    #     print_and_save('LlamaPerplexity', output_filename)
    #     print_and_save(f'|User| {query} | ', output_filename)
    #     print_and_save(str(datetime.now()), output_filename)
    #     print_and_save('\n', output_filename)

    #     base, extension = output_filename.rsplit('.', 1)
    #     detailed_filename = f"{base}_detailed.{extension}"

    #     print_and_save('LlamaPerplexity', detailed_filename)
    #     print_and_save(f'|User| {query} | ',detailed_filename)
    #     print_and_save(str(datetime.now()), detailed_filename)
    #     print_and_save('\n', detailed_filename)

    # # if new_transcript_received:
    # #     print('cancelling the task..')
    # #     return
    # # else:    
    #     print('1')
    #     category_filler = await llama_get_category(query, chat_history, prompt1, prompt2, output_filename)  # Processes the query to categorize and determine the filler response.
    #     print('category_filler:', category_filler)
    #     print('2')
    
    # # if new_transcript_received:
    # #     print('cancelling the task..')
    # #     return
    # # else:
    #     filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)
    #     print('3')

    # # if new_transcript_received:
    # #     print('cancelling the task..')
    # #     return
    # # else:
    #     print('category_filler:', category_filler)
    #     print('filler_no:', filler_no)
    #     print('Category:', Category)
    #     print('Sub_Category:', Sub_Category)
    #     print('QuestionType:', QuestionType)

    #     ContextGiven = ''
    #     for item in category_filler:
    #         print('4')
    #         category_dict = json.loads(item[0].replace('\n', ''))
            
    #         # Check if the dictionary has 'Category' or 'FillerNo' and update the variables accordingly
    #         if 'Context Given' in category_dict:
    #             ContextGiven = category_dict['Context Given']

    #     # Assembling the category information into a dictionary for further processing.
    #     category = {
    #         'Category': Category,
    #         'Sub Category': Sub_Category,
    #         'QuestionType': QuestionType,
    #         'ContextGiven': ContextGiven
    #     }
    #     print('5')

    # # if new_transcript_received:
    # #     print('cancelling the task..')
    # #     return
    # # else:
    #     # Processes the user query and updates chat history accordingly.
    #     chat_history, chat_user_info = await part2.response_type(query, category, chat_history, output_filename, chat_user_info)
    #     print(chat_history)
    #     print('6')

    # except asyncio.CancelledError:
    #     # Perform cleanup here if necessary
    #     print("Task was cancelled....")
    #     # raise  # It's a good practice to re-raise the CancelledError after handling it
    #     return

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

async def process_transcriptions():
    global transcription_buffer, current_processing_task
    while True:
        await new_data_event.wait()
        if transcription_buffer:
            data_to_process = " ".join(transcription_buffer)
            transcription_buffer = []  # Clear buffer after copying

            if current_processing_task and not current_processing_task.done():
                current_processing_task.cancel()  # Cancel the currently running task

            current_processing_task = asyncio.create_task(process_transcription_data(data_to_process))
            try:
                await current_processing_task
            except asyncio.CancelledError:
                print("Processing was cancelled due to new transcript.")
            new_data_event.clear()  # Clear the event until new data arrives

async def process_transcriptions():
    global transcription_buffer, current_processing_task, new_transcript_received
    while True:
        await new_data_event.wait()
        
        # Clear the event early to ensure it's ready for next signaling.
        new_data_event.clear()

        if transcription_buffer:
            data_to_process = " ".join(transcription_buffer)
            transcription_buffer = []  # Clear buffer after copying

            # Cancel any ongoing processing task before starting a new one.
            if current_processing_task and not current_processing_task.done():
                current_processing_task.cancel()
                await current_processing_task  # Wait for the task to be cancelled

            current_processing_task = asyncio.create_task(process_transcription_data(data_to_process))
            try:
                await current_processing_task
            except asyncio.CancelledError:
                print("Processing was cancelled due to new transcript.")


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


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        # Create a new event loop if the default one is closed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())