import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

model_name = "llama-2-70b-chat"


def get_category(query, system_message):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"user query: {query}"},
    ]

    # Chat completion with streaming
    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    content = ""
    for response in response_stream:
        if "choices" in response:
            content = response["choices"][0]["message"]["content"]
            # break  # Assuming we need just the first response that contains 'choices'

    if content.strip():
        pattern = r"\{.*?\}"

        matches = re.findall(pattern, content, re.DOTALL)

        return matches

    return [], content

def run_get_category(query, system_message):
    result = get_category(query, system_message)
    return result


def llama_get_category(query, chat_history, prompt1, prompt2):
    prompt1 = prompt1 + f'Previous conversation with user: {chat_history}'
    prompt2 = prompt2 + f'Previous conversation with user: {chat_history}'
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


