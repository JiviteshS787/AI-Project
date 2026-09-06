from assistant.brain.brain_deepseek import interpret, MODEL
from assistant.router import execute

import time

TESTS = [
    # --- NEWS: general headlines ---
    ("Sports questions", "Score to the barcelona game today"),
    ("F1", "Who won monza f1 race"),
    ("NBA", "When will the new NBA season start")
]

WAIT_TIME = 5


def main():
    total = len(TESTS)
    total_time = 0
    name = MODEL

    print("=" * 70)
    print(f"AI ASSISTANT — {name} — WEB SEARCH TEST")
    print("=" * 70)

    for i, (name, prompt) in enumerate(TESTS, start=1):
        print("-" * 70)
        print(f"TEST {i}/{total}: {name}")
        print(f"Input: {prompt}")
        print()

        start = time.time()

        try:
            raw = interpret(prompt)
            if isinstance(raw, list):
                for entry in raw:
                    answer = execute(entry)
                    print(answer)

            elapsed = time.time() - start
            total_time += elapsed

            print("LLM Output:")
            print(raw)

            print(f"Request time: {elapsed:.3f} seconds")

        except Exception as e:
            elapsed = time.time() - start
            total_time += elapsed

            print("ERROR:", str(e))
            print(f"Request time: {elapsed:.3f} seconds")

        print()

        if i < total:
            print(f"Waiting {WAIT_TIME}s...\n")
            time.sleep(WAIT_TIME)

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total:   {total}")
    print(f"Runtime: {total_time:.2f}s")
    print(f"Average: {total_time / total:.2f}s/test")
    print("=" * 70)


if __name__ == "__main__":
    main()
