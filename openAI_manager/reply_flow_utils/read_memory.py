def read_memory(chat_history_manager, include_tool_outputs=False):
    # print("Reading memory from chat history...")
    return chat_history_manager.read_chat_history(include_tool_outputs=include_tool_outputs)