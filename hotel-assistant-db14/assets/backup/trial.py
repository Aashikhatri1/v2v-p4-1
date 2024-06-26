

import json
import soundfile as sf
import sounddevice as sd

import re
import openai
from dotenv import load_dotenv
import os
import requests
import sys
sys.path.append('./assets')
sys.path.append('./components')
import pplx_playht_final
import prompts
prompt3 = prompts.prompt3
prompt4 = prompts.prompt4
get_user_info_prompt = prompts.get_user_info_prompt
final_sub_sub_category_prompt = prompts.final_sub_sub_category_prompt
ask_question_prompt = prompts.ask_question_prompt
create_db_query_prompt = prompts.create_db_query_prompt

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

model_name = "llama-2-70b-chat"


# Path to your JSON file
filename = "data.json"

# Load JSON data from the file
with open(filename, "r") as file:
    data = json.load(file)

with open("room.json", "r") as file:
    rooms_data = json.load(file)

def process_db_query(question):
    url = f"http://localhost:8000/process-query/?question={question}"
    try:
        response = requests.get(url, timeout=30)  # 10-second timeout
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return "Response time exceeded. Please try again later."
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return {}


# Note: This function assumes your data.json structure includes 'Category', 'Sub Category', and optionally 'Sub Sub Category'.
def fetch_sub_category(category, question_type):
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("File not found. Ensure 'data.json' exists in the correct path.")
        return {}

    filtered_data = [
        entry
        for entry in data
        if entry["Category"] == category["Category"]
        and entry.get("Sub Category") == category.get("Sub Category")
    ]

    if not filtered_data:
        result_json = json.dumps(
            {
                "Category": category.get("Category", "N/A"),
                "Sub Category": category.get("Sub Category", "N/A"),
                "Sub Sub Category": "",  # Assuming you want an empty string if no sub-sub-category exists
                "QuestionType": question_type,  # Adding QuestionType
            },
            indent=4,
        )
    else:
        result = []
        for item in filtered_data:
            result.append(
                {
                    "Category": item["Category"],
                    "Sub Category": item.get("Sub Category", "N/A"),
                    "Sub Sub Category": item.get("Sub Sub Category", "N/A"),
                    "QuestionType": question_type,  # Adding QuestionType
                }
            )
        result_json = json.dumps(result, indent=4)

    print("Result JSON:", result_json)
    return result_json


def find_information_all(data, criteria_list):
    results = []
    for criteria in criteria_list:
        # Ensure criteria is a dictionary
        if isinstance(criteria, dict):
            match_found = False
            for item in data:
                if all(item.get(key) == value for key, value in criteria.items()):
                    results.append(item.get("Information Required From Client", "Information not found"))
                    match_found = True
                    break
            if not match_found:
                results.append("Information not found")
        else:
            print("Error: criteria is not a dictionary", criteria)
    return results


def find_information(data, criteria):
    print('criteria:', criteria)
    results = []

    # Iterate through each item in the JSON data
    for item in data:
        # Check if the item matches the Category and Sub Category in your criteria
        if item.get('Category') == criteria['Category'] and item.get('Sub Category') == criteria['Sub Category']:
            # Extract the required information
            # info_required = item.get('Information Required From Client', 'No information available')
            sample_answer = item.get('Sample Answer', 'No sample answer available')
            
            # Add the extracted information to the results list
            results.append({
                # 'Information Required From Client': info_required,
                'Sample Answer': sample_answer
            })

    return results
    
def find_information_db(data, criteria):
    print('criteria:', criteria)
    results = []

    # Iterate through each item in the JSON data
    for item in data:
        # Check if the item matches the Category and Sub Category in your criteria
        if item.get('Category') == criteria['Category'] and item.get('Sub Category') == criteria['Sub Category'] and item.get('Sub Sub Category') == criteria['Sub Sub Category']:
            # Extract the required information
            info_required = item.get('Information Required From Client')
            sample_answer = item.get('Sample Answer', 'No sample answer available')
            
            # Add the extracted information to the results list
            results.append({
                'Information Required From Client': info_required,
                'Sample Answer': sample_answer
            })

    return results

def final_sub_sub_category(sub_category, query,final_sub_sub_category_prompt):
    messages = [
        {
            "role": "system",
            "content": (
                final_sub_sub_category_prompt 
                + f'Options: {str(sub_category)}'
            ),
        }
    ]

    messages.append({"role": "user", "content": f"user query: {query}"})

    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    for response in response_stream:
        if "choices" in response:
            content = response["choices"][0]["message"]["content"]

    if content.strip():
        pattern = r"\{.*?\}"
        matches = re.findall(pattern, content, re.DOTALL)
        matches = json.loads(matches[0])
        print("matches: ", matches)
        return matches

    return str(matches)

def get_user_info(info, chat_history, query, get_user_info_prompt):
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

    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    for response in response_stream:
        if "choices" in response:
            content = response["choices"][0]["message"]["content"]

    

    if content.strip():
        print("content: ", content)
        pattern = r"\{.*?\}"

        matches = re.findall(pattern, content, re.DOTALL)
        print("matches1: ", matches)
        print(type(matches))

        matches = matches[0]
        print("matches2: ", matches)
        print(type(matches))

        matches = json.loads(matches)
        print("matches: ", matches)
        print(type(matches))

        
        return matches

    return str(matches)

def summarise_chat_history(chat_history):

    if len(chat_history) > 3:
        messages = [
            {
                "role": "system",
                "content": (
                    'Summarise the given chat history in 150 words or less.'
                    
                ),
            }
        ]

        messages.append({"role": "user", "content": f'Chat History: {str(chat_history)}'})

        response_stream = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            api_base="https://api.perplexity.ai",
            api_key=PPLX_API_KEY,
            stream=True,
        )

        for response in response_stream:
            if "choices" in response:
                content = response["choices"][0]["message"]["content"]

        # if content.strip():
        content = [content]

        return content
    else:
        return chat_history

def check_room_availability(rooms_data, dates):
    
    # Function to find available rooms for given dates
    def find_available_rooms_for_dates(rooms_data, dates):
        available_rooms_by_date = {}
        for date in dates:
            available_rooms_by_date[date] = [room for room in rooms_data if room.get(date, 0) > 0]
        return available_rooms_by_date

    # Fetching available rooms for the specified dates
    available_rooms = find_available_rooms_for_dates(rooms_data, dates)
    
    return available_rooms

import ast

def extract_dates_from_content(content):
    try:
        # Attempt to directly evaluate the content as a Python literal.
        dates_list = ast.literal_eval(content)
        if isinstance(dates_list, list):
            print("Extracted list:", dates_list)
            return dates_list
        else:
            print("Content is not a list.")
            return None
    except (ValueError, SyntaxError) as e:
        print("Error evaluating content:", e)
        return None

def create_db_query(info, chat_history, query, create_db_query_prompt):
    messages = [
        {
            "role": "system",
            "content": (
                create_db_query_prompt +
                f'Info: {str(info)}' +
                f'Chat History: {str(chat_history)}' 
            
            ),
        }
    ]

    messages.append({"role": "user", "content": f"user query: {query}"})

    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    for response in response_stream:
        if "choices" in response:
            content = response["choices"][0]["message"]["content"]

    if content.strip():
        print('create_db_query content' , content)
        # pattern = r"\{.*?\}"
        # extracted_dates = extract_dates_from_content(content)
        # # matches = re.findall(pattern, content, re.DOTALL)
        # # print('create_db_query matches ' , matches)
        # # matches = json.loads(matches[0])
        # matches = extracted_dates
        # print("matches: ", matches)
        # return matches


        list_start = content.find('["')
        list_end = content.find('"]') + 2
        list_str = content[list_start:list_end]

        # Use a regular expression to find all dates in the format "dd-Mmm-yyyy" within the list
        dates = re.findall(r'\d{2}-[A-Za-z]{3}-\d{2}', list_str)

        print('dates:',dates)
    return dates


def response_type(query, category, chat_history):

    with open("room.json", "r") as file:
        rooms_data = json.load(file)
    # Assuming category now includes 'QuestionType'
    question_type = category.get("QuestionType")
    ContextGiven = category.get('ContextGiven')
    if question_type == "FAQ":
        print("General Inquiry - FAQ")

        if ContextGiven == "No":
            chat_history = pplx_playht_final.final_answer('', chat_history, query, prompt3)
        else:
            info = find_information(data, category)  
            print('info: ', info)
            chat_history = pplx_playht_final.final_answer(info, chat_history, query, prompt3)

    elif question_type == "DB":
        print("DB Inquiry")

        sub_sub_category_list = fetch_sub_category(category, question_type)
        # print('sub_sub_category_list:', sub_sub_category_list)
       
        sub_sub_category_list = json.loads(sub_sub_category_list)

        final_sub_sub_category_ = final_sub_sub_category(sub_sub_category_list, query, final_sub_sub_category_prompt)

        print('final_sub_sub_category:', final_sub_sub_category_)
        
        info = find_information_db(data, final_sub_sub_category_)
        print('db info:',info)
        
        if info != []:
            for info_item in info:
                if 'Information Required From Client' in info_item:
                    value = info_item['Information Required From Client']
                    # if value is not None and value != 'N/A':
                    if value is not None and value != 'NA':
                        chat_user_info = get_user_info(info, chat_history, query, get_user_info_prompt)
                        print('chat_user_info: ', chat_user_info)

                        if 'N/A' in chat_user_info.values():
                            # call llama
                            print('Get missing info from user')
                            chat_history= pplx_playht_final.ask_question(chat_user_info, chat_history, query, ask_question_prompt)
                            
                        else:
                            # play filler
                            # filename = 'assets/fillers/giveMeAFewSeconds.wav'
                            print('No missing info')
                            filename = 'assets/fillers/cat2fillerno1.wav'
                            d, fs = sf.read(filename)
                            sd.play(d, fs)
                            
                            dates_to_check = create_db_query(info, chat_history, query, create_db_query_prompt)
                            available_rooms_by_date = check_room_availability(rooms_data, dates_to_check)
                            rooms_data = json.dumps(available_rooms_by_date, indent=2)
                            print(rooms_data)
                            # rooms_data = 
                            chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4)
                            # pass
                    else:
                        print('Information is not required from client.')
                        chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4)
                
                else:
                        print('Information is not required from client.')
                        chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4)
    
        else:
            chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4)
        

    return chat_history



info = {'number of guests': '5', 'check-in date': '2023-03-19', 'check-out date': '2023-03-20'}
chat_history = [{'role': 'user', 'content': 'Hi. I want to book a room your on nineteenth March.'}, {'role': 'assistant', 'content': "Welcome to our hotel! I'm happy to help you with your booking. Can you please provide me with your check-out date?"}]
query = "A number of guests will be five and checkout out date will be twenty March."
dates = create_db_query(info, chat_history, query, create_db_query_prompt)
print(dates)
print(type(dates))

# available_rooms_by_date = check_room_availability(rooms_data, dates)
# rooms_data = json.dumps(available_rooms_by_date, indent=2)
# print(rooms_data)
# # rooms_data = 
# chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, info, chat_history, query, prompt4)


def filter_by_dates(rooms_data, dates):
    filtered_data = [entry for entry in rooms_data if entry["Date"] in dates]
    return filtered_data

# Use the function to get data for the dates of interest
filtered_rooms_data = filter_by_dates(rooms_data, dates)
print('filtered_rooms_data: ',filtered_rooms_data)
# Print or use the filtered data
# print(json.dumps(filtered_data, indent=4))

# chat_history = pplx_playht_final.rooms_availability_final_answer(filtered_rooms_data, info, chat_history, query, prompt4)