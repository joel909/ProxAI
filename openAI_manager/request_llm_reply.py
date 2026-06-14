def request_reply(prompt, client, model):
    tools = [{
        "type": "function",
        "name": "read_memory",
        "description": """Call this tool if you need past conversation history to answer the user.
        Use it when:
        - user says 'remember', 'earlier', 'before', 'last time', 'we discussed'
        - the current message references something you have no context for
        - you feel like you're missing background to give a good answer
        Do NOT call it if the current conversation already has enough context.
        
        When you call this, the full conversation history will be injected and 
        your request will be automatically resent with that context. 
        You do not need to ask the user for anything — just call this tool and wait.""",
        "parameters": {
            "type": "object",
            "properties": {}   # no params needed, just a trigger
        }
    }]
    if not model:
            raise ValueError("Model is not set. Please set the model before requesting a reply.")
    print("prompt : ",prompt)
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": "You are a helpful assistant. If past context seems needed, call read_memory."},
            {"role": "developer", "content": "You are a helpful and accurate assistant. Before answering, identify the user's core objective and define the key requirements for a successful response. Then internally evaluate whether your planned answer satisfies those requirements, is factually correct, and directly addresses the user's goal. Optimize for usefulness, clarity, and correctness while keeping responses concise and avoiding unnecessary verbosity."},
            {"role": "user", "content": prompt}
            ],
        tools=tools
    )
    return response.output,response.output_text