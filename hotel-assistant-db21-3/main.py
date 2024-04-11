import asyncio
import json
import pyaudio
import websockets
from dotenv import load_dotenv
import pyautogui as pg
import os
import sys
import sounddevice as sd
import soundfile as sf
from datetime import datetime


load_dotenv()

sys.path.append('./components')
sys.path.append('./assets')
import prompts
prompt3 = prompts.prompt3
prompt4 = prompts.prompt4
#from pplx_playht1 import ask_question, final_answer, rooms_availability_final_answer

from gpt_response import gpt_get_user_info, gpt_final_sub_sub_category
# from gpt_streaming import final_booking

get_user_info_prompt = prompts.get_user_info_prompt
final_sub_sub_category_prompt = prompts.final_sub_sub_category_prompt
ask_question_prompt = prompts.ask_question_prompt
create_db_query_prompt = prompts.create_db_query_prompt


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
import uuid
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
global current_query 
global previous_query
global task_status
global chat_history
global stop_playing 
task_status = []  #'name' : 'Task-64', 'status': 'done'}
current_query = ''
previous_query = ''
chat_history = []
stop_playing = False


################################################################################################


import openai
from dotenv import load_dotenv
import os
import numpy as np
import sounddevice as sd
from pyht import Client
from pyht.client import TTSOptions
import time
import re 
import grpc
from log import print_and_save
from datetime import datetime
import asyncio

load_dotenv()  # Load environment variables

PPLX_API_KEY = os.getenv("PPLX_API_KEY")

PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
client = Client(user_id=PLAYHT_USER_ID, api_key=PLAYHT_API_KEY)
# options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
options = TTSOptions(voice="s3://voice-cloning-zero-shot/2bc098a7-c1fc-4b32-9452-556c5ab4814e/jason/manifest.json")
sample_rate = 24000 

def play_audio_from_text(text):
    global stop_playing 
    success = False
    attempts = 0

    # if 'ending the call' in text.lower():
        
    #     d, fs = sf.read('assets/outro.wav')
    #     sd.play(d, fs)
    #     sd.wait()
    #     pg.click('assets/buttons/end_call.png')
    #     print('Call ended from our side.')
    #     return

    while not success and attempts < 3:  # Try up to 3 times
        try:
            stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
            stream.start()

            # if stop_playing:
            #     stream.stop()
            #     stream.close()
            #     return
            #     # break
            # else:
            #     for chunk in client.tts(text, options):
            #         audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / np.iinfo(np.int16).max
            #         stream.write(audio_data)
            #     print('audio Played:', text)

            #     stream.stop()
            #     stream.close()
            #     success = True  # If we reach this line, it means no error was raised

            for chunk in client.tts(text, options):
                if stop_playing:
                    stream.stop()
                    stream.close()
                    return
                else:
                    audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / np.iinfo(np.int16).max
                    stream.write(audio_data)
            print('audio Played:', text)

            stream.stop()
            stream.close()
            success = True  # If we reach this line, it means no error was raised


        except grpc._channel._MultiThreadedRendezvous as e:
            if e._state.code == grpc.StatusCode.RESOURCE_EXHAUSTED:
                attempts += 1
                print(f"Resource exhausted, retrying... Attempt {attempts}")
                time.sleep(0.5)  # Wait for 1 second before retrying
            else:
                raise  

processed_sentences = set()
sentence_end_pattern = re.compile(r'(?<=[.?!])\s')

async def handle_gpt_response(full_content):
    await asyncio.sleep(0)
    sentences = re.split(r'[.!?]', full_content)
    # print('1',sentences)
    sentences = [s.strip() for s in sentences if s]
    # print('2',sentences)

    for sentence in sentences:
        # print('3',sentence)
        if sentence not in processed_sentences:
            # print('4',sentence)

            if 'have a great day' in sentence.lower():
                play_audio_from_text(sentence)
                
                print('Call ended from our side.')
                self_end_call = pg.locateOnScreen('assets/buttons/self_end_call.png', confidence = 0.98)
                if self_end_call:
                    pg.click(self_end_call)
                    pg.mouseDown()
                    time.sleep(0.1)  # Short delay to simulate a real click
                    pg.mouseUp()
                else:
                    print('self_end_call button not found')
                
                return
            else:
                play_audio_from_text(sentence)
                print('sentence sent to playht: ', sentence)
                processed_sentences.add(sentence)

# Function to handle chat with user and then play response as audio
async def pplx_streaming(messages, chat_history, query, output_filename):

    global processed_sentences
    processed_sentences.clear()
    if query is None:
        print("Query is None. Skipping the request.")
        return chat_history
    chat_history_str = str(chat_history)
    model_name = "llama-2-70b-chat"
    previous_content = ""  # Keep track of what content has already been processed

    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    processed_content = ""
    await asyncio.sleep(0)
    for response in response_stream:
        if 'choices' in response:
            content = response['choices'][0]['message']['content']
            new_content = content.replace(processed_content, "", 1).strip()  # Remove already processed content
            # print(new_content)

            # Split the content by sentence-ending punctuations
            parts = sentence_end_pattern.split(new_content)

            # Process each part that ends with a sentence-ending punctuation
            for part in parts[:-1]:  # Exclude the last part for now
                part = part.strip()
                # if part:
                if part and len(part.split()) > 1:
                    # print('part', part)
                    await handle_gpt_response(part + '.')  # Re-add the punctuation for processing
                    processed_content += part + ' '  # Add the processed part to processed_content

            # Now handle the last part separately
            last_part = parts[-1].strip()
            if last_part:
                # If the last part ends with a punctuation, process it directly
                if sentence_end_pattern.search(last_part):
                    await handle_gpt_response(last_part)
                    processed_content += last_part + ' '
                else:
                    # Otherwise, add it to the sentence buffer to process it later
                    processed_content += last_part + ' '
    if last_part:
        # print(f"Processed part sent to FAISS: '{last_part}'")
        await handle_gpt_response(last_part)
        processed_content += last_part + ' '

    # Append only the complete assistant's response to messages
    if content.strip():        
        # missing_part = content.replace(processed_content, "").strip()
        # if missing_part:
        #     await handle_gpt_response(missing_part)
        #     print('missing part sent to playht', missing_part)

        #     processed_content += missing_part + ' '

        messages.append({"role": "assistant", "content": content.strip()})
        chat_history.append({"role": "user", "content": query})
        chat_history.append({"role": "assistant", "content": content})
        print_and_save('LlamaPerplexity', output_filename)
        print_and_save(f'|Bot| {content} | ', output_filename)
        print_and_save(str(datetime.now()), output_filename)
        print_and_save('\n', output_filename)
        print(content)

        base, extension = output_filename.rsplit('.', 1)
        detailed_filename = f"{base}_detailed.{extension}"

        print_and_save('LlamaPerplexity', detailed_filename)
        print_and_save(f'|Bot| {content} | ', detailed_filename)
        print_and_save(str(datetime.now()), detailed_filename)
        print_and_save('\n', detailed_filename)
        

    return chat_history

# Function to handle chat with user and then play response as audio
async def ask_question(chat_user_info, chat_history, query, ask_question_prompt, output_filename):

    # query = input("User: ")
    messages = [
        {
            "role": "system",
            "content": (
                ask_question_prompt +  
                f'Chat History: {str(chat_history)}'
                
                
            )
        },
        {"role": "user", "content": f'chat_user_info: {str(chat_user_info)}' + ', \n User query: '+ query }
    ]

    print('ask_question_input' + str(messages))
    chat_history = await pplx_streaming(messages, chat_history, query, output_filename)

    return chat_history


async def rooms_availability_final_answer(rooms_data, info, chat_user_info, chat_history, query, prompt4, output_filename):
    
    messages = [
        {
            "role": "system",
            "content": (
                prompt4 +  
                f'Chat History: {str(chat_history)}' + 
                f'Info: {str(info)}'
                f'Rooms data: {str(rooms_data)}'
                f'The user has provided the following information: {str(chat_user_info)}'
            )
        },
        {"role": "user", "content": 'User query: ' + query }
    ]

    chat_history = await pplx_streaming(messages, chat_history, query, output_filename)
    return chat_history

async def final_answer(info, chat_history, query, prompt3, output_filename):
    
    messages = [
        {
            "role": "system",
            "content": (
                prompt3 +  
                f'Chat History: {str(chat_history) if chat_history else "No history available."}' + 
                f'Info: {str(info) if info else "No additional info."}'
            )
        },
        {"role": "user", "content": query if query else "Default query text."}
    ]

    chat_history = await pplx_streaming(messages, chat_history, query, output_filename)

    return chat_history


################################################################################################
async def handle_transcript(transcript):
    global stop_playing
    global previous_query
    print('handle transcript called')
    global current_processing_task, transcription_buffer, new_transcript_received
    if transcript and not transcript.isspace():
        transcription_buffer.append(transcript)
        
        # Signal that a new transcript has been received.
        new_transcript_received = True
        print('handle_transcript')
        
        if current_processing_task:
            print('current processing task  ', current_processing_task)
            print(get_value_by_name(current_processing_task.get_name()))
            if get_value_by_name(current_processing_task.get_name()) !='done':
                print('process stopped --handle transcript 1')
                print('previous_query:', previous_query)
                print('current_query:', current_query)
                previous_query = current_query
                

            else:
                previous_query = ''
                
        if current_processing_task and not current_processing_task.done():

            print('process stopped --handle transcript 2')
            print('previous_query:', previous_query)
            print('current_query:', current_query)
            previous_query = current_query
            
            current_processing_task.cancel()
            stop_playing = True
            print('task cancelled in handle transcript')
        else:
            previous_query = ''
            
        
        new_data_event.set()

def get_value_by_name(name):
    for task in task_status:
        if task["name"] == name:
            return task["value"]
    return None  

def add_task(name, value):
    task_status.append({"name": name, "value": value})

def set_or_add_value_by_name(name, new_value):
    for task in task_status:
        if task["name"] == name:
            task["value"] = new_value
            return "Updated"
    # If the task is not found, add a new one
    add_task(name, new_value)
    return "Added"
async def process_transcriptions():
    # global previous_query
    global stop_playing
    global current_query
    print('process_transcription called')
    global transcription_buffer, current_processing_task, new_transcript_received
    while True:
        await new_data_event.wait()
        
        # Clear the event early to ensure it's ready for next signaling.
        new_data_event.clear()
        
        if transcription_buffer:
            print('transcription buffer')
            data_to_process = " ".join(transcription_buffer)
            transcription_buffer = []  # Clear buffer after copying
            
            print('current processing task ', current_processing_task )
            
            # Cancel any ongoing processing task before starting a new one.
            if current_processing_task and not current_processing_task.done():
                print('process stopped --process_transcriptions 1')
                print('previous_query 2:', previous_query)
                print('current_query 2 :', current_query)
                previous_query = current_query
                print('previous_query 3:', previous_query)

                print('current_processing_task 2: ' , current_processing_task)
                current_processing_task.cancel()
                stop_playing = True
                print('task cancelled in process_transcriptions')
                await current_processing_task  # Wait for the task to be cancelled


            print('current query ', current_query)
            current_query = data_to_process
            print('current query ', current_query)
            
            unique_value = uuid.uuid4()
            current_processing_task = asyncio.create_task(process_transcription_data(unique_value))
            current_processing_task.set_name(unique_value)
            set_or_add_value_by_name(current_processing_task.get_name(), 'in progress')
            stop_playing = False
            # print(current_processing_task.done)
            print('current_processing_task: ' , current_processing_task)
            try:
                await current_processing_task
            except asyncio.CancelledError:
                print("Processing was cancelled due to new transcript.")



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

async def process_transcription_data(name):

    global task_status    
    global chat_history
    print('chat_history:', chat_history)
    print('previous_query1:', previous_query)
    print('current_query1:', current_query)
    query = previous_query + '\n'+ current_query
    with open("data.json", "r") as file:
        data = json.load(file)
    output_filename = 'assets/log/'+ datetime.now().strftime('%d-%m-%Y_%H-%M-%S') + '.txt'
    
    chat_user_info = {}
    filename = "assets/intro.wav"
    global new_transcript_received
    try: 
        # end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence=0.90)
        # if end_call:
        #     print("Call ended")
            
        
        category_filler = await step1(query,chat_history, output_filename)
        await asyncio.sleep(0)
        filler_no, Category, Sub_Category, QuestionType = await step2(category_filler)
        await asyncio.sleep(0)
        category = await step3(category_filler,filler_no, Category, Sub_Category, QuestionType)
        print('category:', category)
        await asyncio.sleep(0)
        # chat_history, chat_user_info = await step4(data, category, output_filename, chat_history, chat_user_info)

        with open("room.json", "r") as file:
            rooms_data = json.load(file)
        # Assuming category now includes 'QuestionType'
        question_type = category.get("QuestionType")
        ContextGiven = category.get('ContextGiven')

        await asyncio.sleep(0)

        if question_type == "FAQ":
            print("General Inquiry - FAQ")

            if ContextGiven == "No":
                
                chat_history = await final_answer('', chat_history, query, prompt3, output_filename)
                
                set_or_add_value_by_name(name, 'done')
                await asyncio.sleep(0)
            else:
                print('ContextGiven 2', ContextGiven)
                info = find_information(data, category)  
                print('info: ', info)

                # print_and_save('LlamaPerplexity', detailed_filename)
                # print_and_save(f'|FAQ INFO| {info} | ', detailed_filename)
                # print_and_save(str(datetime.now()), detailed_filename)
                # print_and_save('\n', detailed_filename)

                chat_history = await final_answer(info, chat_history, query, prompt3, output_filename)
                set_or_add_value_by_name(name, 'done')
                await asyncio.sleep(0)
        # elif question_type == "DB":
        else:
            await asyncio.sleep(0)
            print("DB Inquiry")

            sub_sub_category_list = fetch_sub_category(category, question_type)
            # print('sub_sub_category_list:', sub_sub_category_list)
        
            sub_sub_category_list = json.loads(sub_sub_category_list)

            final_sub_sub_category_ = final_sub_sub_category(sub_sub_category_list, query, final_sub_sub_category_prompt, output_filename)
            await asyncio.sleep(0)
            # print_and_save('LlamaPerplexity', detailed_filename)
            # print_and_save(f'|output| {final_sub_sub_category_} | ', detailed_filename)
            # print_and_save(str(datetime.now()), detailed_filename)
            # print_and_save('\n', detailed_filename)

            print('final_sub_sub_category:', final_sub_sub_category_)
            
            info = find_information_db(data, final_sub_sub_category_)
            print('db info:',info)
            await asyncio.sleep(0)
            # print_and_save('LlamaPerplexity', detailed_filename)
            # print_and_save(f'|DB INFO| {info} | ', detailed_filename)
            # print_and_save(str(datetime.now()), detailed_filename)
            # print_and_save('\n', detailed_filename)
            
            if info != []:
                await asyncio.sleep(0)
                for info_item in info:
                    if 'Information Required From Client' in info_item:
                        value = info_item['Information Required From Client']
                        # if value is not None and value != 'N/A':
                        if value is not None and value != 'NA':
                            
                            

                            # print_and_save('LlamaPerplexity', detailed_filename)
                            # print_and_save(f'|GET USER INFO| {chat_user_info} | ', detailed_filename)
                            # print_and_save(str(datetime.now()), detailed_filename)
                            # print_and_save('\n', detailed_filename)

                            await asyncio.sleep(0)
                            if chat_user_info == {}:
                                user_info = get_user_info(info, chat_history, query, get_user_info_prompt)

                                chat_user_info = {**chat_user_info, **user_info}
                                print('chat_user_info: ', chat_user_info)
                                chat_history= await ask_question(chat_user_info, chat_history, query, ask_question_prompt, output_filename)
                                set_or_add_value_by_name(name, 'done')
                                await asyncio.sleep(0)
                            elif 'N/A' in chat_user_info.values():
                                print('Get missing info from user')
                                print('chat_user_info: ', chat_user_info)
                                missing_info = {k: v for k, v in chat_user_info.items() if v == 'N/A'}
                                print('missing_info: ', missing_info)
                                info = str(info) + "The following is the missing info from the user, If it is found in chat history or user query, fill it, otherwise write 'N/A' " +  str(missing_info)
                                user_info = get_user_info(info, chat_history, query, get_user_info_prompt)
                                user_info = {k: v for k, v in user_info.items() if v != 'N/A'}
                                chat_user_info = {**chat_user_info, **user_info}
                                print('chat_user_info: ', chat_user_info)

                                await asyncio.sleep(0)
                                
                                chat_history= await ask_question(chat_user_info, chat_history, query, ask_question_prompt, output_filename)
                                set_or_add_value_by_name(name, 'done')
                                await asyncio.sleep(0)
                            else:

                                await asyncio.sleep(0)
                                # play filler
                                print('No missing info')

                                filename = 'assets/fillers/cat2fillerno1.wav'
                                d, fs = sf.read(filename)
                                sd.play(d, fs)
                                
                                dates = create_db_query(info, chat_history, query, create_db_query_prompt, output_filename)
                                print(dates)
                                filtered_rooms_data = filter_by_dates(rooms_data, dates)
                                print('filtered_rooms_data: ',filtered_rooms_data)
                                
                                await asyncio.sleep(0)
                                # chat_history = final_booking(filtered_rooms_data, info, chat_history, query, prompt4, output_filename)
                                
                                chat_history = await rooms_availability_final_answer(filtered_rooms_data, info, chat_user_info, chat_history, query, prompt4, output_filename)
                                set_or_add_value_by_name(name, 'done')
                                await asyncio.sleep(0)
                        else:
                            await asyncio.sleep(0)
                            print('Information is not required from client.')
                            
                            chat_history = await rooms_availability_final_answer("", info, chat_user_info, chat_history, query, prompt4, output_filename)
                            set_or_add_value_by_name(name, 'done')
                            await asyncio.sleep(0)
                    else:
                        await asyncio.sleep(0)
                        print('Information is not required from client.')
                        
                        chat_history = await rooms_availability_final_answer("", info, chat_user_info, chat_history, query, prompt4, output_filename)
                        set_or_add_value_by_name(name, 'done')
                        await asyncio.sleep(0)
            else:
                await asyncio.sleep(0)
                
                chat_history = await rooms_availability_final_answer("", info, chat_user_info, chat_history, query, prompt4, output_filename)
                set_or_add_value_by_name(name, 'done')
                await asyncio.sleep(0)

        set_or_add_value_by_name(name, 'done')
        return chat_history


    except asyncio.CancelledError:
        # Perform cleanup here if necessary
        print("Task was cancelled....")
        
        # raise  # It's a good practice to re-raise the CancelledError after handling it
        return
    

global stop_pushing
stop_pushing = False  # This flag will control the running tasks.

async def check_call_end_periodically(check_interval=1):
    """Periodically check for the call end button and stop tasks if the end call button is found."""
    global stop_pushing
    # await asyncio.sleep(5)
    end_call = None
    while not stop_pushing:
        end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence=0.98)
        if end_call:
            print("Call ended")
            stop_pushing = True
        await asyncio.sleep(check_interval)

async def main():
    global chat_history
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    if DEEPGRAM_API_KEY is None:
        print("Please set the DEEPGRAM_API_KEY environment variable.")
        return
    print('Start Speaking...')
    transcriber = Transcriber(on_transcript=handle_transcript)
    transcription_task = asyncio.create_task(transcriber.run(DEEPGRAM_API_KEY))
    processing_task = asyncio.create_task(process_transcriptions())
    call_end_check_task = asyncio.create_task(check_call_end_periodically())

    # Wait for any task to complete. If call_end_check_task completes, it indicates the call ended.
    done, pending = await asyncio.wait(
        [transcription_task, processing_task, call_end_check_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # If the call_end_check_task is done, cancel other tasks.
    if call_end_check_task in done:
        transcription_task.cancel()
        processing_task.cancel()
        print("All tasks cancelled due to call end.")
        chat_history = []
        return

    # Optionally, you can await the cancellation to ensure the tasks are properly cleaned up.
    for task in pending:
        await task  # This ensures that any cleanup in the tasks is executed.


# if __name__ == "__main__":
def chat_with_user():
    global stop_pushing
    stop_pushing = False
    try:
        filename = "assets/intro.wav"
        data, fs = sf.read(filename)
        sd.play(data, fs)
        asyncio.get_event_loop().run_until_complete(main())
        print("Done!")
        
        return
    except RuntimeError as e:
        # Create a new event loop if the default one is closed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())


chat_with_user()
# print('End of the program')
