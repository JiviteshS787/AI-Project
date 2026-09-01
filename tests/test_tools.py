from assistant.router import execute
import time

WAIT_TIME = 20

TESTS = {
    "Test 1":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "Whats the weather in Toronto, ON?"
        }
    },
    "Test 2":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "What is the weather in London, ON?"
        }
    },
    "Test 3":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "Whats the weather?"
        }
    },
    "Test 4":
     {
         "action": "search",
         "target": None,
         "parameters": {
             "query": "Whats in the news today?"
         }
     }
}

for key, value in TESTS.items():
    print(key)
    print(execute(value))
    time.sleep(WAIT_TIME)

