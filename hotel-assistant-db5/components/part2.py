import json
import soundfile as sf
import sounddevice as sd
import pplx_playht_final
import re
import openai
from dotenv import load_dotenv
import os
import requests
import sys
sys.path.append('./assets')
import prompts
prompt3 = prompts.prompt3
prompt4 = prompts.prompt4

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
    # # Display or process the results
    # for result in results:
    #     print(result)


def final_sub_sub_category(sub_category, query):
    messages = [
        {
            "role": "system",
            "content": (
                """
                Which category, sub category and sub sub category does this user query belong to from the given options and 
                what type of question is asked is it FAQ or DB related question. only 2 possible response for this. FAQ/DB in type key?
                Always respond in json format {"QuestionType": "<questionType>", "Category": "<category>", "Sub Category": "<subCategory>", "Sub Sub Category": "<subSubCategory>"}. Please keep your response short and use real talk sentences.
                Options: 
                """
                + str(sub_category)
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


def response_type(query, category, type_value, chat_history):
    # Assuming category now includes 'QuestionType'
    question_type = category.get("QuestionType")
    general_talk = category.get('GeneralTalk')
    if question_type == "FAQ":
        print("General Inquiry - FAQ")

        if general_talk == "Yes":
            chat_history = pplx_playht_final.final_answer('', chat_history, query, prompt3)
        else:
            info = find_information(data, category)  
            print('info: ', info)
            chat_history = pplx_playht_final.final_answer(info, chat_history, query, prompt3)

    elif question_type == "DB":
        print("DB Inquiry")

        
        chat_history = pplx_playht_final.rooms_availability_final_answer(rooms_data, chat_history, query, prompt4)

    return chat_history
