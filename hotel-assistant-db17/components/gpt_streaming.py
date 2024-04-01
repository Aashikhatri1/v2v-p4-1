

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

load_dotenv()  # Load environment variables

PPLX_API_KEY = os.getenv("PPLX_API_KEY")

PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
client = Client(user_id=PLAYHT_USER_ID, api_key=PLAYHT_API_KEY)
# options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
options = TTSOptions(voice="s3://voice-cloning-zero-shot/2bc098a7-c1fc-4b32-9452-556c5ab4814e/jason/manifest.json")
sample_rate = 24000 

def play_audio_from_text(text):
    success = False
    attempts = 0

    while not success and attempts < 3:  # Try up to 3 times
        try:
            stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
            stream.start()

            for chunk in client.tts(text, options):
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

def handle_gpt_response(full_content):
    sentences = re.split(r'[.!?]', full_content)
    sentences = [s.strip() for s in sentences if s]

    for sentence in sentences:
        if sentence not in processed_sentences:
            play_audio_from_text(sentence)
            print('sentence sent to playht: ', sentence)
            processed_sentences.add(sentence)

# Function to handle chat with user and then play response as audio
# def gpt_streaming(messages, chat_history, query, output_filename):

#     last_part = ''
#     openai_api_key = os.getenv("OPENAI_API_KEY_GPT")
#     if openai_api_key is None:
#         raise ValueError("The OPENAI_API_KEY is not set in the environment.")
    
#     if query is None:
#         print("Query is None. Skipping the request.")
#         return chat_history
#     chat_history_str = str(chat_history)
#     model_name = "gpt-3.5-turbo"
#     previous_content = ""  # Keep track of what content has already been processed

#     response_stream = openai.ChatCompletion.create(
#         model=model_name,
#         messages=messages,
#         api_key=openai_api_key,
#         # api_base="https://api.perplexity.ai",
#         # api_key=PPLX_API_KEY,
#         stream=True,
#     )

#     processed_content = ""
#     accumulated_content = ""

#     for response in response_stream:
        

#         if 'choices' in response and len(response['choices']) > 0:
#             choice = response['choices'][0]
#             if 'delta' in choice and 'content' in choice['delta']:
#                 content = choice['delta']['content']
        
#                 if content:
#                     accumulated_content += content
#                     print("Content fetched:", content)
#                     new_content = accumulated_content.replace(processed_content, "", 1).strip()  # Remove already processed content
#                 # print(new_content)
        
#         # content = response.choices[0].delta.content or ""
#         # if content:
#         #     # print('content: ', content)
#         #     accumulated_content += content
#             # new_content = accumulated_content.replace(processed_content, "", 1).strip()  # R
#                 # Split the content by sentence-ending punctuations
#                     parts = sentence_end_pattern.split(new_content)

#                     # Process each part that ends with a sentence-ending punctuation
#                     for part in parts[:-1]:  # Exclude the last part for now
#                         part = part.strip()
#                         # if part:
#                         if part and len(part.split()) > 1:
#                             # print('part', part)
#                             handle_gpt_response(part + '.')  # Re-add the punctuation for processing
#                             processed_content += part + ' '  # Add the processed part to processed_content

#                     # Now handle the last part separately
#                     last_part = parts[-1].strip()
#                     if last_part:
#                         # If the last part ends with a punctuation, process it directly
#                         if sentence_end_pattern.search(last_part):
#                             handle_gpt_response(last_part)
#                             processed_content += last_part + ' '
#                         else:
#                             # Otherwise, add it to the sentence buffer to process it later
#                             processed_content += last_part + ' '
#             if last_part:
#                 # print(f"Processed part sent to FAISS: '{last_part}'")
#                 handle_gpt_response(last_part)
#                 processed_content += last_part + ' '

#             # Append only the complete assistant's response to messages
#             if content.strip():
#                 messages.append({"role": "assistant", "content": content.strip()})
#                 chat_history.append({"role": "user", "content": query})
#                 chat_history.append({"role": "assistant", "content": content})
#                 print_and_save('LlamaPerplexity', output_filename)
#                 print_and_save(f'|Bot| {content} | ', output_filename)
#                 print_and_save(str(datetime.now()), output_filename)
#                 print_and_save('\n', output_filename)
#                 print(content)

#                 base, extension = output_filename.rsplit('.', 1)
#                 detailed_filename = f"{base}_detailed.{extension}"

#                 print_and_save('LlamaPerplexity', detailed_filename)
#                 print_and_save(f'|Bot| {content} | ', detailed_filename)
#                 print_and_save(str(datetime.now()), detailed_filename)
#                 print_and_save('\n', detailed_filename)
                

#     return chat_history

import re
import os

# Assuming openai and other necessary modules are imported correctly

# A pattern that matches sentence-ending punctuation
sentence_end_pattern = re.compile(r'[.!?]')

# def handle_gpt_response(sentence):
#     # Your existing logic to handle a complete sentence
#     print("Audio Played:", sentence)
    # Imagine here you would call the method to play audio or further process the sentence

def gpt_streaming(messages, chat_history, query, output_filename):
    openai_api_key = os.getenv("OPENAI_API_KEY_GPT")
    if openai_api_key is None:
        raise ValueError("The OPENAI_API_KEY is not set in the environment.")
    
    if query is None:
        print("Query is None. Skipping the request.")
        return chat_history

    model_name = "gpt-3.5-turbo"

    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_key=openai_api_key,
        stream=True,
    )

    sentence_buffer = ""

    for response in response_stream:
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            if 'delta' in choice and 'content' in choice['delta']:
                content = choice['delta']['content']
                sentence_buffer += content  # Accumulate content
                
                # Split the accumulated content by sentence-ending punctuations
                parts = sentence_end_pattern.split(sentence_buffer)
                if sentence_end_pattern.search(sentence_buffer):  # Check if there's a sentence end
                    for part in parts[:-1]:  # Process all but the last part
                        handle_gpt_response(part.strip() + '.')  # Re-add the punctuation for processing
                    sentence_buffer = parts[-1]  # The last part is the start of a new sentence

    # If there's remaining content in the buffer after the loop, decide how to handle it
    if sentence_buffer.strip():
        # For example, you might want to process it as well, or log that it's incomplete
        handle_gpt_response(sentence_buffer.strip())
    
    content = (
        response.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "No answer found.")
        .strip()
    )
    if content.strip():
        chat_history.append({"role": "user", "content": query})
        chat_history.append({"role": "assistant", "content": content})

    return chat_history

# Make sure to define or adjust `handle_gpt_response` as per your requirements.


def final_booking(rooms_data, info, chat_history, query, prompt4, output_filename):

    print('final_booking_chathistory_input:', chat_history)
    messages = [
        {
            "role": "system",
            "content": (
                prompt4 +  
                f'Chat History: {str(chat_history)}' + 
                f'Info: {str(info)}'
                f'Rooms data: {str(rooms_data)}'
            )
        },
        {"role": "user", "content": query if query else "Default query text."}
    ]
    
    chat_history = gpt_streaming(messages, chat_history, query, output_filename)
    print('final_booking_chathistory_output:', chat_history)
    return chat_history

# rooms_data= '''[{'Date': '1-Apr-24', 'RoomType': 'Taj Club Suite', 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailable': '4'}, {'Date': '1-Apr-24', 'RoomType': 'Luxury Suite', 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailable': '5'}, {'Date': '2-Apr-24', 'RoomType': 'Luxury Suite', 'RoomAmenities': 'Garden view', 'NumberOfRoomsAvailable': '7'}, {'Date': '2-Apr-24', 'RoomType': 'Superior Room', 'RoomAmenities': 'Park view', 'NumberOfRoomsAvailable': '6'}, {'Date': '11-Apr-24', 'RoomType': 'Superior Room', 'RoomAmenities': 'Park view', 'NumberOfRoomsAvailable': '6'}, {'Date': '11-Apr-24', 'RoomType': 'Superior Room', 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailable': '5'}, {''}, {'Date': '11-Apr-24', 'RoomType': 'Taj Club Suite', 'RoomAmenities': 'Park view', 'NumberOfRoomsAvailable': '7'}, {'Date': '11-Apr-24', 'RoomType': 'Taj Club Suite',Amenit 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailable': '10'}, {'Date': '11-Apr-24', 'RoomType': 'Luxury Suite', 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailable':te': ' '20'}, {'Date': '11-Apr-24', 'RoomType': 'Luxury Suite', 'RoomAmenities': 'Garden view', 'NumberOfRoomsAvailable': '11'}, {'Date': '11-Apr-24', 'RoomType': 'Superior Ros': 'Pom', 'RoomAmenities': 'Park view', 'NumberOfRoomsAvailable': '3'}, {'Date': '11-Apr-24', 'RoomType': 'Superior Room', 'RoomAmenities': 'Pool view', 'NumberOfRoomsAvailabApr-24le': '2'}, {'Date': '12-Apr-24', 'RoomType': 'Taj Club Suite', 'RoomAmenities': 'Park view', 'NumberOfRoomsAvailable': '4'}]'''
# info = {'number of guests': '5', 'check in date': '2023-04-11', 'check out date': '2023-04-12'}
# output_filename = 'test.txt'

# chat_history = ['The user wants to book a room for April 11th, but has not provided any additional information such as the number of guests or preferred room type. '
# 'The assistant has asked the user to repeat their request for clarification.', {'role': 'user', 'content': 'Number of guests will be five and any room will be.'}, {'role': 'assistant', 'content': 'Great! Can you please provide the check-out date?'} ]
# query = 'Checkout date will be twelfth of April.'


# prompt4 = '''You are a receptionist of a hotel, Your goal is to assist customers by categorizing their rooms and booking queries if there are not suitable information provided by user ask user for date of booking and providing accurate responses based on the provided info data 
# and you will also be provided with chat history. Chat history is the summary of the ongoing conversation with the user till now. Please keep your response short and use real talk sentences. Do not repeat what assisstant has already said previously, do not ask many questions and do not ask for confirmation more than once. Do not inform about the rooms unless the user asks anything specifically.
# If the user has already provided check in and check out date, do not ask for it again, just inform that the room is available and ask for their name and contact number. When it is provided, tell them that you have booked a room.
# If you did not understand 'user query', ask them politely to repeat what they said. If they confirm booking, respond with 'Thank you for choosing our hotel, you will receive a confirmation email for your booking'.
# Please check chat history for check in/check out dates, name and contact number. If it is given in chat history, you don't have to ask.
# Your response should strictly be not more than 25 words, so create a consise answer. Your response will directly go to user, so answer accordingly. '''

# final_booking(rooms_data, info, chat_history, query, prompt4, output_filename)