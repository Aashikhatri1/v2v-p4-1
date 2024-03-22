import sys
sys.path.append('./components')
sys.path.append('./assets')
import json
# import csv2json

# csv2json.convert_csv_to_json('data.csv')

import speech_to_text
import part2
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts
prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

def chat_with_user():
    chat_history = []
    while True:
        query = speech_to_text.transcribe_stream()  # Captures spoken input from the user.
        print('query:', query)
        
        category_filler = llama_get_category(query, chat_history, prompt1, prompt2)  # Processes the query to categorize and determine the filler response.
        print('category_filler:', category_filler)
        
        type_value, filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)


        print('category_filler:', category_filler)
        print('type_value:', type_value)
        print('filler_no:', filler_no)
        print('Category:', Category)
        print('Sub_Category:', Sub_Category)
        print('QuestionType:', QuestionType)

        general_talk = ''
        for item in category_filler:
        
            category_dict = json.loads(item[0].replace('\n', ''))
            
            # Check if the dictionary has 'Category' or 'FillerNo' and update the variables accordingly
            if 'General Talk' in category_dict:
                general_talk = category_dict['General Talk']

        # Assembling the category information into a dictionary for further processing.
        category = {
            'Category': Category,
            'Sub Category': Sub_Category,
            'QuestionType': QuestionType,
            'GeneralTalk': general_talk
        }

        # Processes the user query and updates chat history accordingly.
        chat_history = part2.response_type(query, category, type_value, chat_history)
        print(chat_history)

        # words = chat_history.split()  # Split the text into words

        # # Check if the number of words is more than 200
        # if len(words) > 200:
        #     # Keep only the last 200 words
        #     chat_history = words[-200:]
        #     print('New chat history:', chat_history)

        if len(chat_history) > 5:
            chat_history = chat_history[-5:]
            print('New chat history:', chat_history)

chat_with_user()
