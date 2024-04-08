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

from part2 import process_db_query, fetch_sub_category, find_information_all, find_information, find_information_db, final_sub_sub_category, get_user_info, summarise_chat_history, check_room_availability, create_db_query, filter_by_dates

from stt import Transcriber
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

transcription_buffer = []
current_processing_task = None
new_data_event = asyncio.Event()

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
    try:
        chat_history, chat_user_info = await part2.response_type(query, category, chat_history, output_filename, chat_user_info)
        print(chat_history)
        print('6')
        return chat_history, chat_user_info

    except asyncio.CancelledError:
        # Perform cleanup here if necessary
        print("Task was cancelled....")
        # raise  # It's a good practice to re-raise the CancelledError after handling it
        return chat_history

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
    

# async def process_transcriptions():
#     global transcription_buffer, current_processing_task
#     while True:
#         await new_data_event.wait()
#         if transcription_buffer:
#             data_to_process = " ".join(transcription_buffer)
#             transcription_buffer = []  # Clear buffer after copying
#             current_processing_task = asyncio.create_task(process_transcription_data(data_to_process))
#             try:
#                 await current_processing_task
#             except asyncio.CancelledError:
#                 print("Processing was cancelled due to new transcript.")
#             new_data_event.clear()  # Clear the event until new data arrives

# async def process_transcriptions():
#     global transcription_buffer, current_processing_task
#     while True:
#         await new_data_event.wait()
#         if transcription_buffer:
#             data_to_process = " ".join(transcription_buffer)
#             transcription_buffer = []  # Clear buffer after copying

#             if current_processing_task and not current_processing_task.done():
#                 current_processing_task.cancel()  # Cancel the currently running task

#             current_processing_task = asyncio.create_task(process_transcription_data(data_to_process))
#             try:
#                 await current_processing_task
#             except asyncio.CancelledError:
#                 print("Processing was cancelled due to new transcript.")
#             new_data_event.clear()  # Clear the event until new data arrives

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