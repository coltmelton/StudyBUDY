import requests

class GenerateFlashcards:
    def __init__(self, anki_url="http://localhost:8765"):
        self.anki_url = anki_url

    def _invoke(self, action, **params):
        """Send a request to the AnkiConnect API."""
        request_json = {"action": action, "version": 6, "params": params}
        response = requests.post(self.anki_url, json=request_json).json()
        if "error" in response and response["error"]:
            raise Exception(f"AnkiConnect error: {response['error']}")
        return response.get("result")

    def add_flashcards(self, flashcards_text, deck_name="StudyBuddy Deck", model_name="Basic"):
        lines = []
        for line in flashcards_text.strip().split("\n"):
            stripped_line = line.strip()
            if stripped_line:
                lines.append(stripped_line)
        notes = []
        errors = []

        #Iterate each question
        for i in range(0, len(lines), 2):
            #Each question should have a corresponding answer to it
            if i + 1 < len(lines) and lines[i].startswith("Q:") and lines[i+1].startswith("A:"):
                question = lines[i][2:].strip()
                answer = lines[i+1][2:].strip()


                if not question or not answer:
                    errors.append(f"Empty question/answer at pair starting line {i+1}")
                    continue

                #API names from anki
                note = {"deckName": deck_name,"modelName": model_name, "fields": {"Front": question, "Back": answer},"tags": ["StudyBuddy"]}
                notes.append(note)
            else:
                errors.append(f"Unmatched Q/A")

        # If any mismatches, block pushing to Anki
        if errors:
            return {"error": "Invalid flashcards", "details": errors}

        if not notes:
            return {"error": "No valid flashcards found."}

        return self._invoke("addNotes", notes=notes)


    #Create a new deck
    def create_deck(self, deck_name):
        return self._invoke("createDeck", deck=deck_name)


    #Grab deck names
    def get_deck_names(self):
        return self._invoke("deckNames")

    #List all type of note models provided by anki
    def get_model_names(self):
        return self._invoke("modelNames")
