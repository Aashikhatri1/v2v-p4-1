import sys
sys.path.append('./components')
sys.path.append('./assets')
import json
# import csv2json

# csv2json.convert_csv_to_json('data.csv')

import speech_to_text
import part2_new
from part2_new import summarise_chat_history
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import prompts
prompt1 = prompts.prompt1
prompt2 = prompts.prompt2

from datetime import datetime
import threading
import asyncio

def chat_with_user():
    # chat_history = []
    chat_history = [{'role': 'user', 'content': 'Are there any amenities available?'}, {'role': 'assistant', 'content': 'Yes, we have a range of amenities available, including a fitness center, a business center, and a swimming pool. We also offer laundry services, a concierge service, and a tour desk. Additionally, we have a childcare service available, located just a short distance from our hotel. Would you like more information about any of these amenities?'}]
    while True:
        # query = speech_to_text.transcribe_stream()  # Captures spoken input from the user.
        # if len(chat_history) > 0:
        #     chat_history = summarise_chat_history(chat_history)
        #     print('Summarised chat history:', chat_history)
            
        # thread1 = threading.Thread(target=transcribe_stream)
        # thread2 = threading.Thread(target=lambda: summarise_chat_history(chat_history))

        # # Start the threads
        # thread1.start()
        # thread2.start()

        # # Wait for both threads to complete
        # thread1.join()
        # thread2.join()

        start_time = datetime.now()
        print(start_time)
        # A shared dictionary to store results from threads
        results = {}

        # Wrap the original functions to store their results
        def thread_transcribe_stream():
            # results['transcribe'] = speech_to_text.transcribe_stream()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Since transcribe_stream is an async function, we need to run it using loop.run_until_complete
            results['transcribe'] = loop.run_until_complete(speech_to_text.transcribe_stream())
            
            # Close the loop after completing the operation
            loop.close()

        def thread_summarise_chat_history(chat_history):
            results['summarise'] = summarise_chat_history(chat_history)
        

        # Simulated chat history for demonstration
        # chat_history = "Example chat history"

        # Create thread objects for each wrapped function
        thread1 = threading.Thread(target=thread_transcribe_stream)
        thread2 = threading.Thread(target=lambda: thread_summarise_chat_history(chat_history))

        # Start the threads
        thread1.start()
        thread2.start()

        # Wait for both threads to complete
        thread1.join()
        thread2.join()

        end_time = datetime.now()
        print(end_time - start_time)
        # Print the results
        print("Transcription Result:", results['transcribe'])
        print("Summary Result:", results['summarise'])


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

            # if len(chat_history) > 6:
            #     chat_history = chat_history[-6:]
            #     print('New chat history:', chat_history)

chat_with_user()
