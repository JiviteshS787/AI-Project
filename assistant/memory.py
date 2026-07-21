import json

memory = "data/memory.json"

#Load in anything in the memory, if unable to read return None for both entries.
def load_memory():
    try:
        with open(memory, "r") as file: #Open with intent to read JSON
            return json.load(file)
    except:
        return {
            "last_app": None,
            "last_project": None
        }

#Write to memory JSON
def save_memory(memory_data):
    with open(memory, "w") as file: #Open with intent to write to JSON
        json.dump(memory_data, file, indent=4) #4 lines of writing