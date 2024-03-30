

# chat_user_info = {'number of guests': '5', 'check in date': 'N/A', 'check out date': '2023-04-18'}

# chat_user_info = {}
# if chat_user_info != {} :


# na_pairs = {k: v for k, v in chat_user_info.items() if v == 'N/A'}
# print(na_pairs)


# user_info = {}
# chat_user_info = {}
# chat_user_info = {**chat_user_info, **user_info}

# print(chat_user_info)


_+____________

na_pairs = {k: v for k, v in data.items() if v == 'N/A'}
{'number of guests': '5', 'check in date': 'N/A', 'check out date': '2023-04-18'}
______

if chat_user_info == {}:
    user_info = get_user_info()

    chat_user_info = {**chat_user_info, **user_info}

    # call llm

elif 'N/A' in chat_user_info.values():
    missing_info = {k: v for k, v in chat_user_info.items() if v == 'N/A'}

    user_info = get_user_info(missing_info)

    chat_user_info = {**chat_user_info, **user_info}

    # call llm