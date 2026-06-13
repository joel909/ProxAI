def request_reply(prompt, client, model):
    if not model:
            raise ValueError("Model is not set. Please set the model before requesting a reply.")
    response = client.responses.create(
        model=model,
        input=[
            {"role": "developer", "content": "You are a helpful and accurate assistant. Before answering, identify the user's core objective and define the key requirements for a successful response. Then internally evaluate whether your planned answer satisfies those requirements, is factually correct, and directly addresses the user's goal. Optimize for usefulness, clarity, and correctness while keeping responses concise and avoiding unnecessary verbosity."},
            {"role": "user", "content": prompt}
            ],
    )
    return response.output_text