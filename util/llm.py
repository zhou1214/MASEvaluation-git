from openai import OpenAI
import os

def get_llm_evaluation(prompt, content):
    client = OpenAI(
        base_url=os.getenv('BASE_URL', ''),
        api_key=os.environ.get('OPENAI_API_KEY',""),
    )

    try:

        response = client.chat.completions.create(
            model="",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
            stream=False
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

