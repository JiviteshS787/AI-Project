from assistant.router import execute
import time

WAIT_TIME = 20

TESTS = {
    "Test 1":
    {
        "action": "mcp",
        "target": None,
        "parameters": {
            "check": "Can you start a draft to myself, titled Latest Resume"
        }
    },
    "Test 2":
     {
        "action": "mcp",
        "target": None,
        "parameters": {
             "check": "Draft an email to Cole regarding course selection and how we need to pick them soon"
         }
     }
}

for key, value in TESTS.items():
    print(key)
    print(execute(value))
    time.sleep(WAIT_TIME)

