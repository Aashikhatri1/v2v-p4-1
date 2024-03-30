
import json
import os
import openai
from dotenv import load_dotenv
import time
import re


# Load the environment variables from .env file
load_dotenv()

def gpt_get_category(query, system_message):

    openai_api_key = os.getenv("OPENAI_API_KEY_GPT")
    if openai_api_key is None:
        raise ValueError("The OPENAI_API_KEY is not set in the environment.")
    model = "gpt-3.5-turbo"

    # Format the prompt as a conversation, if necessary
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"user query: {query}"},
    ]

    # Call to OpenAI chat API
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        api_key=openai_api_key,  # Use the API key from the environment variable
    )

    # Get the answer from OpenAI
    content = (
        response.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "No answer found.")
        .strip()
    )
    if content.strip():
            
        pattern = r"\{.*?\}"
        matches = re.findall(pattern, content, re.DOTALL)
        return matches

    return content


def gpt_get_user_info(info, chat_history, query, get_user_info_prompt):

    openai_api_key = os.getenv("OPENAI_API_KEY_GPT")
    if openai_api_key is None:
        raise ValueError("The OPENAI_API_KEY is not set in the environment.")
    model = "gpt-3.5-turbo"

    # Format the prompt as a conversation, if necessary
    messages = [
        {
            "role": "system",
            "content": (
                
                
                f'Info: {str(info)}' +
                get_user_info_prompt +
                f'Chat History: {str(chat_history)}'
            ),
        }
    ]

    messages.append({"role": "user", "content": f"user query: {query}"})

    # Call to OpenAI chat API
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        api_key=openai_api_key,  # Use the API key from the environment variable
    )

    # Get the answer from OpenAI
    content = (
        response.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "No answer found.")
        .strip()
    )
    if content.strip():
            
        pattern = r"\{.*?\}"
        matches = re.findall(pattern, content, re.DOTALL)
        matches = json.loads(matches[0])
        return matches

    return content

# gpt_get_category("hello", "system message")