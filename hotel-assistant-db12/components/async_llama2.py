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
from log import print_and_save


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
        temperature=0.5,
        max_tokens=32768,
        top_p=1,
        stop=None,
    )

    content = chat_completion.choices[0].message.content
    print('content' , content)

    if content.strip(): 

        pattern = r"\{.*?\}"
        matches = re.findall(pattern, content, re.DOTALL)

        # if matches and 'No' not in matches.values:
        if matches:
            return matches
        else:
            print('--> Sending query to Llama again')
            chat_completion = client.chat.completions.create(
                messages=messages,
                model= model_name,
                temperature=0.5,
                max_tokens=32768,
                top_p=1,
                stop=None,
            )

            content = chat_completion.choices[0].message.content
            print('content' , content)

            if content.strip():
                
                pattern = r"\{.*?\}"
                matches = re.findall(pattern, content, re.DOTALL)

                if matches:
                    return matches
                else:
                    print('--> Sending query to GPT')
                    filename = 'assets/fillers/cat1fillerno3.wav'
                    d, fs = sf.read(filename)
                    sd.play(d, fs)        
                    matches = gpt_get_category(query, system_message)
                    return matches

    # return [], content
    return content

def run_get_category(query, system_message):
    result = get_category(query, system_message)
    print('result', result)
    return result


def llama_get_category(query, chat_history, prompt1, prompt2, output_filename):
    prompt1 = prompt1 + f'Ongoing conversation with the user is as follows: {chat_history}'
    prompt2 = prompt2 + f'Ongoing conversation with the user is as follows: {chat_history}'
    
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

    base, extension = output_filename.rsplit('.', 1)
    detailed_filename = f"{base}_detailed.{extension}"
    # print(f"Total time taken: {total_time} seconds")

    print_and_save('LlamaPerplexity', detailed_filename)
    print_and_save(f'|prompt| {prompt1}{query} | ', detailed_filename)
    print_and_save(f'|prompt| {prompt1}{query} | ', detailed_filename)
    print_and_save(f'|output| {results} | ', detailed_filename)
    print_and_save(str(datetime.now()), detailed_filename)
    print_and_save('\n', detailed_filename)

    return results


