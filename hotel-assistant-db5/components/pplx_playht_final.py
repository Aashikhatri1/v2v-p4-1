

import openai
from dotenv import load_dotenv
import os
import numpy as np
import sounddevice as sd
from pyht import Client
from pyht.client import TTSOptions
import time
import re

# Load environment variables
load_dotenv()

# Setup Perplexity AI
PPLX_API_KEY = os.getenv("PPLX_API_KEY")

# Setup PlayHT Client
PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
client = Client(user_id=PLAYHT_USER_ID, api_key=PLAYHT_API_KEY)
# options = TTSOptions(voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json")
# sample_rate = 20000
options = TTSOptions(voice="s3://voice-cloning-zero-shot/2bc098a7-c1fc-4b32-9452-556c5ab4814e/jason/manifest.json")
sample_rate = 24000 #20000

# Function to play audio from text
def play_audio_from_text(text):
    stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
    stream.start()

    for chunk in client.tts(text, options):
        audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / np.iinfo(np.int16).max
        stream.write(audio_data)

    stream.stop()
    stream.close()

processed_sentences = set()
sentence_end_pattern = re.compile(r'(?<=[.?!])\s')


def handle_gpt_response(full_content):
    sentences = re.split(r'[.!?]', full_content)
    sentences = [s.strip() for s in sentences if s]

    for sentence in sentences:
        if sentence not in processed_sentences:
            play_audio_from_text(sentence)
            processed_sentences.add(sentence)

# Function to handle chat with user and then play response as audio
def ask_question(chat_user_info, chat_history, query):
    if query is None:
        print("Query is None. Skipping the request.")
        return chat_history
    chat_history_str = str(chat_history)
    model_name = "llama-2-70b-chat"
    previous_content = ""  # Keep track of what content has already been processed
    
    # query = input("User: ")
    messages = [
        {
            "role": "system",
            "content": (
                '''You are a Hotel Receptionist, respond to the user according to the query and chat history, ask if any information is missing in chat user info  ''' +  
                f'Chat History: {str(chat_history)}'+
                f'Chat user info: {str(chat_user_info)}'
                
            )
        },
        {"role": "user", "content": query if query else "Default query text."}
    ]

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
                if part:
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
        print(content)

    return chat_history
# final_answer()

def rooms_availability_final_answer(info, chat_history, query, prompt4):
    if query is None:
        print("rooms Query is None. Skipping the request.")
        return chat_history
    chat_history_str = str(chat_history)
    model_name = "llama-2-70b-chat"
    previous_content = ""  # Keep track of what content has already been processed
    # query = input("User: ")
    messages = [
        {
            "role": "system",
            "content": (
                prompt4 +  
                f'Chat History: {str(chat_history) if chat_history else "No history available."}' + 
                f'Info: {str(info) if info else "No additional info."}'
            )
        },
        {"role": "user", "content": query if query else "Default query text."}
    ]

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
                if part:
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
        print(content)

    return chat_history

def final_answer(info, chat_history, query, prompt3):
    if query is None:
        print("rooms Query is None. Skipping the request.")
        return chat_history
    chat_history_str = str(chat_history)
    model_name = "llama-2-70b-chat"
    previous_content = ""  # Keep track of what content has already been processed
    # query = input("User: ")
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
                if part:
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
        print(content)

    return chat_history