def check_for_tool_calling(llm_reply,chat_history_file=None):
    # Placeholder for tool calling logic
    # You can implement your tool calling criteria here
    if llm_reply == "read_memory":
        return True,chat_history_file
    else :
        return False,None
