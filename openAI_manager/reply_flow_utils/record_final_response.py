def record_final_response(
    storage_service,
    chat_history_file,
    prompt,
    response_text,
):
    storage_service.record_chat_history(
        chat_history_file,
        "user",
        prompt,
    )
    storage_service.record_chat_history(
        chat_history_file,
        "assistant",
        response_text,
    )
