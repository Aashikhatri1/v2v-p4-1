import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from gpt_response import gpt_get_category
# Load environment variables from .env file
load_dotenv()
import sounddevice as sd
import soundfile as sf


# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

model_name = "mixtral-8x7b-32768"

from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY,
)
def get_category(query, system_message):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"user query: {query}"},
    ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model= model_name,
    )

    content = chat_completion.choices[0].message.content
    print('content' , content)

    if content.strip(): 

        pattern = r"\{.*?\}"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            return matches
        else:
    
            chat_completion = client.chat.completions.create(
                messages=messages,
                model= model_name,
            )

            content = chat_completion.choices[0].message.content
            print('content' , content)

            if content.strip():
                
                pattern = r"\{.*?\}"
                matches = re.findall(pattern, content, re.DOTALL)

                if matches:
                    return matches
                else:
                    
                    filename = 'assets/fillers/cat1fillerno3.wav'
                    d, fs = sf.read(filename)
                    sd.play(d, fs)        
                    matches = gpt_get_category(query, system_message)
                    return matches

    # return [], content
    return content

def run_get_category(query, system_message):
    result = get_category(query, system_message)
    return result


def llama_get_category(query, chat_history, prompt1, prompt2):
    prompt1 = prompt1 + f'Ongoing conversation with the user is as follows: {chat_history}'
    prompt2 = prompt2 + f'Ongoing conversation with the user is as follows: {chat_history}'
    # prompt1 = list[prompt1]
    # prompt2 = list[prompt2]
    # a = f'Previous conversation with user: {chat_history}'
    # prompt1.append(a)
    tasks = [(query, prompt1), (query, prompt2)]
    results = []

    start_time = datetime.now()  # Start timing
    # Using ThreadPoolExecutor to run functions concurrently
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [
            executor.submit(run_get_category, task[0], task[1]) for task in tasks
        ]

        for future in as_completed(futures):
            result = future.result()
            print(result)
            results.append(result)

    print((datetime.now() - start_time).total_seconds())

    # print(f"Total time taken: {total_time} seconds")

    return results


