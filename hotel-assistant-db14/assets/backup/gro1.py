from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# client = Groq()

client = Groq(
    api_key=GROQ_API_KEY,
)


prompt1 = """
"{\n  \"description\": \"As Jacob, a Hotel receptionist, your role involves matching user queries with the most appropriate category and subcategory from a specified table. This involves categorizing queries based on hotel aspects like services, policy, attractions, and more.\",\n  \"categoriesTable\": [\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Policy\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Services\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Attractions\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Check In/Check Out\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Accessible\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Fitness\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Restaurants/Club\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Parking\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"House Keeping\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Transportation\"},\n    {\"Category\": \"Hotel\", \"SubCategory\": \"Reservation\"},\n    {\"Category\": \"Hotel Services\", \"SubCategory\": \"Services\"},\n    {\"Category\": \"Room\", \"SubCategory\": \"Reservation\"},\n    {\"Category\": \"Room\", \"SubCategory\": \"Cancel/Refund\"},\n    {\"Category\": \"Room\", \"SubCategory\": \"Services\"},\n    {\"Category\": \"Room\", \"SubCategory\": \"Room type\"},\n    {\"Category\": \"Room\", \"SubCategory\": \"Payment/offer\"}\n  ],\n  \"responseFormat\": {\n    \"Category\": \"<Category from table>\",\n    \"Sub Category\": \"<SubCategory from table>\",\n    \"Context Given\": \"Yes/No\"\n  },\n  \"instructions\": \"Respond with the most suitable category and subcategory from the table for each user query. For queries without specific context ('yes', 'thank you', etc.), use 'No' for 'Context Given'. Otherwise, use 'Yes'. Ensure no fields are left empty.\"\n}\n"
"""
completion = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[
        {
            "role": "system",
            "content": prompt1
        },
        {
            "role": "user",
            "content": "chat history\n\nUser:Can you please check? Is there any rooms available on the 20 March? \nBot:Let me check that for you.\nSure, I can check that for you. According to our records, there are no available rooms on March 28.\nUser:Okay. Can you please check if there are any rooms available on the 19 March?\nBot:Let's see here.\nUnfortunately, there are no available rooms on March 19.\nUser:On which date there is any room available.\nBot:Let me check that for you.\nI apologize, but based on the provided data, there are no available rooms for the date of March 20. However, there are available rooms for other dates, such as March 11, 12th, 13th, 14th, 14th, 15th, 16th, 17th, 18th, 19th, 20th, 20th, 21st, 22nd, 23rd, 23rd, 25th.\nWould you like me to check for.\nAvailability on any of these dates?\nUser:Yeah. Uh, please check for the 23 March.\nBot:Let me check that for you.\nBot:Sure, I can assist you with that. Unfortunately, there are no available rooms for the date of March 20.\n\nUser Current Prompt\nPlease can you check for 11 March.\n\n\n"
        }
    ],
    temperature=0.5,
    max_tokens=32768,
    top_p=1,
    stream=True,
    stop=None,
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")