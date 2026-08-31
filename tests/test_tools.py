from assistant.router import execute

TESTS = {
    "Test 1":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "Whats the weather in Markham, ON?"
        }
    },
    "Test 2":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "Whats the barca game score?"
        }
    },
    "Test 3":
    {
        "action": "search",
        "target": None,
        "parameters": {
            "query": "How far is Niagara Falls from 559 Caboto Trail?"
        }
    },
}

for key, value in TESTS.items():
    print(key)
    print(execute(value))

