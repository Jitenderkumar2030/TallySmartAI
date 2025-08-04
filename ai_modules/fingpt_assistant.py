import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_fingpt(question):
    # Specialized financial AI model
    # Business and tax query handling
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst assistant."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Error: {e}"
