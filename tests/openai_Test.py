# imports not implemented

# USE THE .YAML FILE WHEN IMPORTING THE API KEY !!!

def test_new_openai_api(api_key: str):
    """
    Uses the new OpenAI interface.
    Expected usage (per your sample):
      - Instantiate client with API key.
      - Call client.chat.completions.create(...) with a model (e.g. "gpt-4o")
      - Print the response and the assistant's message.
    """
    # Instantiate the client with your API key
    client = OpenAI(api_key=api_key)

    # Call the new-style chat completions API
    response = client.chat.completions.create(
        model="gpt-4o",  # use your custom model name; change to "gpt-3.5-turbo" if needed
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please tell me a short joke."}
        ]
    )

    # Print the entire response for debugging
    print("Full response object:")
    print(response)

    # Extract and print the assistant's reply
    print("\nAssistant reply:")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    test_new_openai_api(open_ai_key)
