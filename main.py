### 
import openai

#Set up OpenAI API key
openai.api_key = "YOUR_API_KEY"

# Generate text with OpenAI GPT-3
def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text


prompt = "Hello, I am ChatGPT. What can I help you with today?"

generated_text = generate_text(prompt)

print(generated_text)