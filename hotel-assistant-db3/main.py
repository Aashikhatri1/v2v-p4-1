import sys
sys.path.append('./components')
import json
# import csv2json

# csv2json.convert_csv_to_json('data1.csv')

import speech_to_text1
import part2
from async_llama2 import llama_get_category
from playFiles import playAudioFile

def chat_with_user():
    chat_history = []
    while True:
        query = speech_to_text1.transcribe_stream()  # Captures spoken input from the user.
        print('query:', query)
        
        category_filler = llama_get_category(query)  # Processes the query to categorize and determine the filler response.
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

chat_with_user()