

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
def pplx_streaming(messages, chat_history, query, output_filename):
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
                    handle_gpt_response(part + '.')  # Re-add the punctuation for processing
                    processed_content += part + ' '  # Add the processed part to processed_content

            # Now handle the last part separately
            last_part = parts[-1].strip()
            if last_part:
                # If the last part ends with a punctuation, process it directly
                if sentence_end_pattern.search(last_part):
                    handle_gpt_response(last_part)
                    processed_content += last_part + ' '
                else:
                    # Otherwise, add it to the sentence buffer to process it later
                    processed_content += last_part + ' '
    if last_part:
        # print(f"Processed part sent to FAISS: '{last_part}'")
        handle_gpt_response(last_part)
        processed_content += last_part + ' '

    # Append only the complete assistant's response to messages
    if content.strip():
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
def ask_question(chat_user_info, chat_history, query, ask_question_prompt, output_filename):

    # query = input("User: ")
    messages = [
        {
            "role": "system",
            "content": (
                ask_question_prompt +  
                f'Chat History: {str(chat_history)}'
                
                
            )
        },
        {"role": "user", "content": f'chat_user_info: {str(chat_user_info)}' + ', User query: '+ query }
    ]

    chat_history = pplx_streaming(messages, chat_history, query, output_filename)

    return chat_history


def rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4, output_filename):
    
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

    chat_history = pplx_streaming(messages, chat_history, query, output_filename)
    return chat_history

def final_answer(info, chat_history, query, prompt3, output_filename):
    
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

    chat_history = pplx_streaming(messages, chat_history, query, output_filename)

    return chat_history