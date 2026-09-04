from groq import Groq
import os, json

client = Groq(api_key=os.environ["GROQ_API_KEY_2"])


SEARCH_ROUTER_PROMPT = """
You classify a search query into one of four categories and extract the
needed parameters. Output ONLY this JSON shape:

{"action":"...", "parameters":{}}

CATEGORIES:

weather -> query is about current/forecast weather conditions
  parameters: {"location": "<city/place name>"} — omit "location" entirely
  if no place was mentioned (assistant will default to home location)
  "what's the weather" -> {"action":"weather","parameters":{}}
  "what's the weather in Toronto" -> {"action":"weather","parameters":{"location":"Toronto"}}

news -> query is asking for current events, headlines, or news on a subject
  parameters: {"topic":"<subject>", "count":<number>} — omit "topic" if asking
  for general headlines. Omit "count" unless the speaker specifies how many
  stories/headlines they want (default is 3).
  "what's in the news today" -> {"action":"news","parameters":{}}
  "any news on the AI regulation bill" -> {"action":"news","parameters":{"topic":"AI regulation bill"}}
  "give me one headline" -> {"action":"news","parameters":{"count":1}}
  "top 5 stories about the election" -> {"action":"news","parameters":{"topic":"election","count":5}}

general_search -> anything else requiring outside knowledge: facts, definitions,
  "what is"/"who is"/"how much does X cost", trivia, general information
  parameters: {"query":"<verbatim original question>"}
  "how much does a tesla model 3 cost" -> {"action":"general_search","parameters":{"query":"how much does a tesla model 3 cost"}}
  "who is the ceo of openai" -> {"action":"general_search","parameters":{"query":"who is the ceo of openai"}}

Output ONLY the JSON object. No markdown, no explanation.
"""


def classify_query(query: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": SEARCH_ROUTER_PROMPT
            },
            {"role": "user", "content": query}
        ],
        temperature=0.7,
        max_completion_tokens=512,
        reasoning_effort="low",
        stream=False,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "general_search", "parameters": {"query": query}}