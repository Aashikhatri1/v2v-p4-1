import sys
sys.path.append('./components')
import json
import speech_to_text
import part2
from async_llama2 import llama_get_category
from playFiles import playAudioFile
import webbrowser
import pyautogui as pg
import time
import threading
from queue import Queue

# import csv2json
# csv2json.convert_csv_to_json('data.csv')

audio_queue = Queue()
is_audio_playing = False

def audio_worker():
    global is_audio_playing
    while True:
        audio_data, samplerate = audio_queue.get()
        if audio_data is None:
            break  # This is the signal to stop the worker
        is_audio_playing = True
        sd.play(audio_data, samplerate)
        sd.wait()
        is_audio_playing = False
        audio_queue.task_done()


audio_thread = threading.Thread(target=audio_worker)
audio_thread.start()

def chat_with_user():
    chat_history = []
    global is_audio_playing
    while True:
        end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence = 0.98)  # path to your end call button image
        if end_call:
            print("Call ended")
            break
        # query = input('user: ')
        while is_audio_playing:
            time.sleep(0.1)
            
        query = speech_to_text.transcribe_stream()  # Captures spoken input from the user.
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


def open_website(url):
        webbrowser.open(url, new=2)  # new=2 opens in a new tab, if possible

# Opening call hipppo dialer
website = 'https://dialer.callhippo.com/dial'
open_website(website)

time.sleep(7)
            
while True:  # Main loop for handling incoming calls
    accept = pg.locateOnScreen("assets/buttons/accept.png", confidence=0.9)
    if accept:
        x, y, width, height = accept
        click_x, click_y = x + width // 2, y + height // 2  # Calculate the center of the button
        print("Call received at coordinates:", (click_x, click_y))
        pg.moveTo(click_x, click_y)  # Move to the center of the button
        time.sleep(0.5)  # Short delay
        #pg.mouseDown()
        time.sleep(0.1)  # Short delay to simulate a real click
        #pg.mouseUp()
        print("Call accepted")
        chat_with_user()  # Start chat with user

        print("Waiting for next call...")
        time.sleep(5)
    else:
        print("No call detected.")
        time.sleep(5) 
