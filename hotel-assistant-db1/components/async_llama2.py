import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

model_name = "llama-2-70b-chat"


def get_category(query, system_message):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"user query: {query}"},
    ]

    # Chat completion with streaming
    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    content = ""
    for response in response_stream:
        if "choices" in response:
            content = response["choices"][0]["message"]["content"]
            # break  # Assuming we need just the first response that contains 'choices'

    if content.strip():
        pattern = r"\{.*?\}"

        matches = re.findall(pattern, content, re.DOTALL)

        return matches

    return [], content


# prompt1 = """You are Jacob, a Hotel receptionist who provides responses to customer queries. Please keep your response short and use real talk sentences.
#     Respond with a Question category in JSON format {"category":"<>", "Sub Category": "<>", "QuestionType": "<FAQ/DB>"}. 
#     Values for "category" can be Account Specific or General Inquiry.
#     General Inquiry questions include "What is your name?", "Is this the Grand Holiday Hotel?", "Do you have room service?", "Do you have Wi-Fi?", "What's the checkout time?" and are typically FAQ type.
#     Account Specific questions include subcategories: Room Booking, Billing, Refunds, Feedback, Booking, Services and may vary between FAQ and DB type depending on the specificity of the query.
#     FAQ type questions do not require database access and are general. DB type questions require specific information from the database, such as room availability or pricing.
#     Always respond with the following JSON format {"Category": "<category>", "Sub Category": "<subCategory>", "QuestionType": "<FAQ/DB>"}"""

prompt1 = """You are Jacob, a Hotel receptionist who provides responses to customer queries.
    Your task is to match the User query with the most suitable category, sub category from the given table.
      
    Respond with the Question category in JSON format {"Category":"<>", "Sub Category": "<>"}. 
    Do not leave any field empty.
    The following is the table of categories, sub categories and sub sub categories in respective rows:
    Room Types	FAQs
    Room Types	Confirmations
    Room Types	FAQs
    Room Types	FAQs
    Room Types	FAQs
    Room Types	Confirmations

    Checkout/check in	FAQs
    Checkout/check in	FAQs
    Checkout/check in	Confirmations

    Payments	Requests
    Payments	Recommendations 
    Payments	FAQs
    Payments	Confirmations
    Payments	Confirmations
    Policies	Confirmations
    Policies	FAQs
    Policies	FAQs
    Policies	FAQs
    Policies	Confirmations
    Policies	Confirmations
    Policies	Requests
    Customer Account	Confirmations
    Customer Account	Issues
    Feedback	Instructions
    Reservations	Instructions
    Reservations	Confirmations
    Reservations	Confirmations
    Reservations	Confirmations
    Reservations	FAQs
    Reservations	Instructions
    Reservations	Confirmations
    Reservations	FAQs
    Reservations	FAQs
    Reservations	Instructions
    Reservations	FAQs
    Amenities	Instructions
    Amenities	FAQs
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Recommendations 
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	Confirmations
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Confirmations
    Amenities	FAQs
    Amenities	Confirmations
    
    Services	FAQs
    Services	FAQs
    Services	FAQs
    Services	Confirmations
    Services	FAQs
    Services	Confirmations
    Services	Confirmations
    Services	FAQs
    Services	Confirmations
    Services	FAQs
    Services	Confirmations
    Services	FAQs
    Services	FAQs
    Services	Confirmations
    Services	FAQs
    Services	FAQs
    Services	Confirmations
    Services	Confirmations
    Services	FAQs
    Services	FAQs
    Services	Requests
    Services	FAQs
    Services	Confirmations
    Local Attractions/Event	Recommendations 
    Local Attractions/Event	Recommendations 
    Local Attractions/Event	Requests
    Local Attractions/Event	Confirmations
    Local Attractions/Event	Recommendations 
    Local Attractions/Event	Recommendations 
    Local Attractions/Event	Confirmations
    Transportation	FAQs
    Transportation	Recommendations 
    Transportation	Confirmations
    Transportation	Confirmations
    Transportation	Requests
    Transportation	Recommendations 
    Transportation	Confirmations
    Restaurants	FAQs
    Restaurants	FAQs
    Restaurants	Recommendations 


    Respond in JSON format {"Category":"<>", "Sub Category": "<>"}. 
    Do not leave any field empty, respond with the most suitable only from the given table.
    """

prompt2 = """For detailed assistance on a wide range of topics, please categorize the query with the appropriate Type and QuestionType in JSON format {"Type": "<1/2>", "FillerNo": "<1/2/3>", "QuestionType": "<FAQ/DB>"}.
- Type 1: Covers general inquiries and FAQs that include questions about hotel amenities, policies, and services. These questions do not require accessing the hotel's database or specific account details. Examples include inquiries about check-in and check-out times, availability of Wi-Fi, pet policies, and breakfast options.
- Type 2: Designated for inquiries that necessitate access to external APIs or specific account details to provide a personalized response. This includes checking room availability for specific dates, requesting invoices, reviewing detailed billing information, inquiring about the status of a refund, and processing feedback or complaints.
FAQ questions are those that involve general knowledge about the hotel and its services, which can be answered without needing to look up specific guest information or accessing a database. Examples include "What time is breakfast served?", "Do you have a gym?", and "Can I bring my pet?"
DB questions involve specific data or actions that require accessing a database, like checking room availability, prices, or processing a specific guest's request. Examples include "What is the availability of the deluxe room on the 15th of this month?", "How much does it cost for an extra bed?", and "Can you send me the invoice for my last stay?"
Fillers for Type 1 and Type 2 responses should be chosen based on the question's complexity and nature. 
- Type 1 Fillers (General Inquiries and FAQs): "Let's see here...", "Good question...", "Just a moment..."
- Type 2 Fillers (Specific Inquiries Requiring Detailed Checks): "Let me check that for you...", "I'll need to verify...", "Allow me a second to confirm..."
Based on the query's content, respond with the appropriate filler and include the "QuestionType" (FAQ or DB) in your response. Ensure to categorize accurately to facilitate swift and precise assistance to the guest. 
provide answer in the following JSON format {"Type": "<1/2>", "FillerNo": "<1/2/3>", "QuestionType": "<FAQ/DB>"}"""

def run_get_category(query, system_message):
    result = get_category(query, system_message)
    return result


def llama_get_category(query):
    tasks = [(query, prompt1), (query, prompt2)]
    results = []

    start_time = datetime.now()  # Start timing
    # Using ThreadPoolExecutor to run functions concurrently
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [
            executor.submit(run_get_category, task[0], task[1]) for task in tasks
        ]

        for future in as_completed(futures):
            result = future.result()
            print(result)
            results.append(result)

    print((datetime.now() - start_time).total_seconds())

    # print(f"Total time taken: {total_time} seconds")

    return results


def get_subsubcategory(Category, Sub_Category, chat_history, query):
    #   def chat_with_user():
    messages = [
        {
            "role": "system",
            "content": (
                """You are a Hotel receptionist who provides responses to customer queries. Please keep your response short and use real talk sentences.
            Respond with suitable sub sub category that this user query belongs to and QuestionType either FAQ or DB only these 2 options are supported.
            FAQ questions include "What is your name?", "Is this the Grand Holiday Hotel?", "Do you have room service?", "Do you have Wi-Fi?", "What's the checkout time?"
            DB questions include "Which room is available on 12th march?" "what is the price of the Delux room?"
            Always respond with following json format {
                "subsubCategory": "<subsubcategory>"}"""
                + f"Category: {Category}"
                + f"Sub Category: {Sub_Category}"
                + f"User Query: {query}"
                + f"Chat History: {messages}"
            ),
        }
    ]

    query = input("user:")
    print(query)
    messages.append({"role": "user", "content": query})

    # Chat completion with streaming
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
            # new_content = content.replace(processed_content, "", 1).strip()  # Remove already processed content
            print(content)

    if content.strip():
        messages.append({"role": "assistant", "content": content.strip()})
        print("final answer:", content.strip())


# def get_category(query, system_message):
#     messages = [
#         {"role": "system", "content": system_message},
#         {"role": "user", "content": f"user query: {query}"},
#     ]

#     # Call to the API to get a response based on system_message and query
#     # Simulating response here; replace with actual API call
#     response = {
#         "Category": "General Inquiry",
#         "Sub Category": "Wi-Fi",
#         "QuestionType": "FAQ",
#     }  # Example response

#     # Extract and return the relevant parts of the response
#     category = response.get("Category", "")
#     sub_category = response.get("Sub Category", "")
#     question_type = response.get("QuestionType", "")
#     return {
#         "Category": category,
#         "Sub Category": sub_category,
#         "QuestionType": question_type,
#     }


# # chat_with_user()

def get_category(query, system_message):
    messages = [
        {
            "role": "system",
            "content": system_message
        },
        {"role": "user", "content": f'user query: {query}'}
    ]

    # Chat completion with streaming
    response_stream = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        api_base="https://api.perplexity.ai",
        api_key=PPLX_API_KEY,
        stream=True,
    )

    content = ""
    for response in response_stream:
        if 'choices' in response:
            content = response['choices'][0]['message']['content']
            # break  # Assuming we need just the first response that contains 'choices'

    if content.strip():
        pattern = r'\{.*?\}'
        
        matches = re.findall(pattern, content, re.DOTALL)
        
        return matches

    return [], content
