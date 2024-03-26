import sys
sys.path.append('./components')
sys.path.append('./assets')
import json
# import csv2json

# csv2json.convert_csv_to_json('data.csv')

# import speech_to_text
import part2_new
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts
prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

def chat_with_user():
    chat_history = []
    while True:
        # query = speech_to_text.transcribe_stream()  # Captures spoken input from the user.
        query = input('user: ')
        if query:
            print('query:', query)
            
            category_filler = llama_get_category(query, chat_history, prompt1, prompt2)  # Processes the query to categorize and determine the filler response.
            print('category_filler:', category_filler)
            
            filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)


            print('category_filler:', category_filler)
            print('filler_no:', filler_no)
            print('Category:', Category)
            print('Sub_Category:', Sub_Category)
            print('QuestionType:', QuestionType)

            ContextGiven = ''
            for item in category_filler:
            
                category_dict = json.loads(item[0].replace('\n', ''))
                
                # Check if the dictionary has 'Category' or 'FillerNo' and update the variables accordingly
                if 'Context Given' in category_dict:
                    ContextGiven = category_dict['Context Given']

            # Assembling the category information into a dictionary for further processing.
            category = {
                'Category': Category,
                'Sub Category': Sub_Category,
                'QuestionType': QuestionType,
                'ContextGiven': ContextGiven
            }

            # Processes the user query and updates chat history accordingly.
            chat_history = part2_new.response_type(query, category, chat_history)
            print(chat_history)

            if len(chat_history) > 6:
                chat_history = chat_history[-6:]
                print('New chat history:', chat_history)

chat_with_user()
