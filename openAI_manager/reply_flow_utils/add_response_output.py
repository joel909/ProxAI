def add_response_output(input_messages, response_output):
    next_input_messages = list(input_messages)
    next_input_messages += response_output
    return next_input_messages
