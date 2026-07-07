def record_final_response(chat_history_manager,prompt,response_text,):
    chat_history_manager.store_chat_history("user",prompt)
    chat_history_manager.store_chat_history("assistant",response_text)
