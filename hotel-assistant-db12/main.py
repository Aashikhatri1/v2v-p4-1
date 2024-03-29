import sys
from datetime import datetime
import json
import pyautogui as pg
sys.path.append('./components')
sys.path.append('./assets')
from log import print_and_save
# import csv2json

# csv2json.convert_csv_to_json('data.csv')

from speech_to_text_new import transcribe_stream
import part2_new
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts

prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

def chat_with_user():
    output_filename = 'assets/log/'+ datetime.now().strftime('%d-%m-%Y_%H-%M-%S') + '.txt'
    chat_history = []
    # chat_history = [{'role': 'user', 'content': 'Are there any amenities available?'}, {'role': 'assistant', 'content': 'Yes, we have a range of amenities available, including a fitness center, a business center, and a swimming pool. We also offer laundry services, a concierge service, and a tour desk. Additionally, we have a childcare service available, located just a short distance from our hotel. Would you like more information about any of these amenities?'}]
    while True:

        end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence = 0.98)  # path to your end call button image
        if end_call:
            print("Call ended")            
            break
        
        start_time = datetime.now()
        print(start_time)
        query, chat_history = transcribe_stream(chat_history)
        print(f"Summary: {chat_history}")
        print((datetime.now() - start_time).total_seconds())

        # query = input('user: ')
        if query:
            print('query:', query)
            print_and_save('LlamaPerplexity', output_filename)
            print_and_save(f'|User| {query} | ', output_filename)
            print_and_save(str(datetime.now()), output_filename)
            print_and_save('\n', output_filename)
            
            category_filler = llama_get_category(query, chat_history, prompt1, prompt2, output_filename)  # Processes the query to categorize and determine the filler response.
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
            chat_history = part2_new.response_type(query, category, chat_history, output_filename)
            print(chat_history)


chat_with_user()
