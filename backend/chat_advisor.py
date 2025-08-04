import openai

openai.api_key = "YOUR_OPENAI_KEY"

def get_financial_advice(question):
    # OpenAI GPT integration
    # Financial context prompting
    # Response generation
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "You are a financial advisor for business analytics."},
            {"role": "user", "content": question}
        ]
    )
    return response['choices'][0]['message']['content']

