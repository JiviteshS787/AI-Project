from openai import OpenAI
import os

# ============================================================
# DeepSeek
# ============================================================

MODEL = "deepseek-v4-flash"
KEY_NAME = 'DEEPSEEK_API_KEY'

client = OpenAI(api_key=os.environ.get(KEY_NAME), base_url="https://api.deepseek.com")


GENERAL_SEARCH_PROMPT = """
You are answering a spoken question for a voice assistant. Give a direct,
conversational answer based on your knowledge — the kind of answer someone
would want read aloud, not a written reference article.

RULES:
- Answer in 1-3 sentences. Voice output should be short; the user is listening,
  not reading.
- Be direct — lead with the answer itself, not "That's a great question" or
  similar filler.
- If the question involves a fact that changes over time (prices, current
  events, who holds a position, sports scores, stock prices) and you're not
  confident your knowledge is current, say so briefly rather than guessing
  ("Last I knew it was around $X, but that may have changed").
- If you genuinely don't know or the question is ambiguous, say so plainly
  instead of fabricating an answer.
- No markdown, no bullet points, no headers — plain spoken text only.
- Do not repeat the question back before answering.

Output ONLY the answer text. No JSON, no preamble, no explanation of your
reasoning.
"""


def search(user_query):
    parameters = user_query.get("parameters") or {}
    search_query = parameters.get("search") or ""
    if search_query:
        print(f"Query: {search_query}")
        try:
            response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": GENERAL_SEARCH_PROMPT
                },
                {
                    "role": "user",
                    "content": search_query
                }
                ],
                temperature=0.3,
                max_tokens = 150,
                extra_body={"thinking": {"type": "disabled"}}
            )
        
        except Exception as e:
            return {
                "error": "DeepSeek request failed",
                "details": str(e)
            }
        
        return response.choices[0].message.content.strip()