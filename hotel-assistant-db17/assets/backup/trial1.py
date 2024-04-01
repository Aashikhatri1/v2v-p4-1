import re

from dotenv import load_dotenv
import os
import requests
import sys
sys.path.append('./assets')
sys.path.append('./components')
import prompts
prompt3 = prompts.prompt3
prompt4 = prompts.prompt4
from log import print_and_save
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import openai
import json
# from gpt_response import gpt_get_user_info
# from gpt_streaming import final_booking


get_user_info_prompt = prompts.get_user_info_prompt
final_sub_sub_category_prompt = prompts.final_sub_sub_category_prompt
ask_question_prompt = prompts.ask_question_prompt
create_db_query_prompt = prompts.create_db_query_prompt

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY,
)


# def get_user_info(info, chat_history, query, get_user_info_prompt):
#     model_name ="mixtral-8x7b-32768"
#     messages = [
#         {
#             "role": "system",
#             "content": (
                
                
#                 f'Info: {str(info)}' +
#                 get_user_info_prompt +
#                 f'Chat History: {str(chat_history)}'
#             ),
#         }
#     ]

#     messages.append({"role": "user", "content": f"user query: {query}"})

#     chat_completion = client.chat.completions.create(
#         messages=messages,
#         model= model_name,
#         temperature=0.5,
#         max_tokens=32768,
#         top_p=1,
#         stop=None,
#     )

#     content = chat_completion.choices[0].message.content
#     print('content' , content)

#     pattern = r"\{.*?\}"
#     matches = re.findall(pattern, content, re.DOTALL)
#     # if content.strip():
#     # if content.strip(): 
#     if content.strip  and re.findall(pattern, content, re.DOTALL):
#         matches = re.findall(pattern, content, re.DOTALL)
#         matches = json.loads(matches[0])
#         for i in matches:
#             if not 'Information Required From Client' in i:
#                 return matches
#     else:
#         return 'didnt work'
    

# chat_history = []
# info = {}
# system_message = "HI, how are you"
# query = 'hi hello'
# messages = [
#     {"role": "system", "content": system_message},
#     {"role": "user", "content": f"user query: {query}"},
# ]
# a = get_user_info(info, chat_history, query, get_user_info_prompt)
# print(a)


###########
# content = '''{
#   "number of guests": "N/A",
#   "check in date": "N/A",
#   "check out date": "N/A"
# }'''

# pattern = r"\{.*?\}"
# if content.strip()  and re.findall(pattern, content, re.DOTALL):
#     matches = re.findall(pattern, content, re.DOTALL)
#     matches = json.loads(matches[0])
#     for i in matches:
#         if not 'Information Required From Client' in i:
#             print(matches) 
# else:
#     print('didnt work')

################################3
# def gpt_get_user_info(info, chat_history, query, get_user_info_prompt):
#     print('--> Sending query to GPT')
#     filename = 'assets/fillers/cat1fillerno3.wav'
#     d, fs = sf.read(filename)
#     sd.play(d, fs)

#     openai_api_key = os.getenv("OPENAI_API_KEY_GPT")
#     if openai_api_key is None:
#         raise ValueError("The OPENAI_API_KEY is not set in the environment.")
#     model = "gpt-3.5-turbo"

#     # Format the prompt as a conversation, if necessary
#     messages = [
#         {
#             "role": "system",
#             "content": (
                
                
#                 f'Info: {str(info)}' +
#                 get_user_info_prompt +
#                 f'Chat History: {str(chat_history)}'
#             ),
#         }
#     ]

#     messages.append({"role": "user", "content": f"user query: {query}"})

#     # Call to OpenAI chat API
#     response = openai.ChatCompletion.create(
#         model=model,
#         messages=messages,
#         api_key=openai_api_key,  # Use the API key from the environment variable
#     )

#     # Get the answer from OpenAI
#     content = (
#         response.get("choices", [{}])[0]
#         .get("message", {})
#         .get("content", "No answer found.")
#         .strip()
#     )
#     if content.strip():
#         print(content)
            
#         pattern = r"\{.*?\}"
#         matches = re.findall(pattern, content, re.DOTALL)
#         matches = json.loads(matches[0])
#         return matches

#     return content

# chat_history = []
# info = {}
# system_message = "HI, how are you"
# query = 'hi hello'
# messages = [
#     {"role": "system", "content": system_message},
#     {"role": "user", "content": f"user query: {query}"},
# ]
# a = gpt_get_user_info(info, chat_history, query, get_user_info_prompt)
# print(a)



#######################3
content = '''{
  "number of guests': 'N/A",
  "check in date": "N/A",
  "check out date": "N/A"
}'''

pattern = r"\{.*?\}"
if content.strip()  and re.findall(pattern, content, re.DOTALL):
    matches = re.findall(pattern, content, re.DOTALL)
    matches = matches[0].replace("'", '"')
    matches = json.loads(matches)
    for i in matches:
        if not 'Information Required From Client' in i:
            print(matches) 
else:
    print('didnt work')
