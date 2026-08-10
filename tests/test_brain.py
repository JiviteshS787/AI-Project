from assistant.brain import interpret


print("=== Gemini Brain Test ===")
print("Type 'exit' to quit.\n")


while True:
    user_input = input("You: ")

    if user_input.lower().strip() in ["exit", "quit"]:
        break

    result = interpret(user_input)

    print("\nBrain:")
    print(result)
    print()