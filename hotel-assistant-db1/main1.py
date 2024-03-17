import asyncio
import os

import sys
sys.path.append('./components')
import speech_to_text1
import part2
from async_llama2 import llama_get_category
from playFiles import playAudioFile

from speech_to_text1 import Transcriber  # Assuming speech_to_text1.py is in the same directory

DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

async def process_transcription(transcript):
    """
    Asynchronously process the received transcript.
    This function should contain the logic that you want to run once a transcript is received.
    """
    print(f"Processing transcript: {transcript}")
    chat_history = []
    # Add your processing logic here
    await asyncio.sleep(10)  # Example delay to simulate processing time
    print('done')
    # query = transcript
    # category_filler = llama_get_category(query)  # Processes the query to categorize and determine the filler response.
    # print('category_filler:', category_filler)
    # # Assuming playAudioFile is adapted to handle the new structure and returns relevant information.
    # type_value, filler_no, Category, Sub_Category, QuestionType = playAudioFile(category_filler)
    # print('category_filler:', category_filler)
    # print('type_value:', type_value)
    # print('filler_no:', filler_no)
    # print('Category:', Category)
    # print('Sub_Category:', Sub_Category)
    # print('QuestionType:', QuestionType)

    # # Assembling the category information into a dictionary for further processing.
    # category = {
    #     'Category': Category,
    #     'Sub Category': Sub_Category,
    #     'QuestionType': QuestionType
    # }

    # # Processes the user query and updates chat history accordingly.
    # chat_history = part2.response_type(query, category, type_value, chat_history)

async def continuous_transcription():
    if DEEPGRAM_API_KEY is None:
        print("Please set the DEEPGRAM_API_KEY environment variable.")
        return

    transcriber = Transcriber()
    ongoing_task = None

    while True:
        print("Start speaking...")
        transcript = await transcriber.run(DEEPGRAM_API_KEY)
        

        if transcript:
            print(f"Received transcript: {transcript}")
            if ongoing_task and not ongoing_task.done():
                ongoing_task.cancel()
                try:
                    await ongoing_task
                except asyncio.CancelledError:
                    print("Ongoing processing was cancelled.")
                except Exception as e:
                    print(f"Error during processing: {e}")

            try:
                ongoing_task = asyncio.create_task(process_transcription(transcript))
            except Exception as e:
                print(f"Failed to start processing task: {e}")


if __name__ == "__main__":
    asyncio.run(continuous_transcription())
