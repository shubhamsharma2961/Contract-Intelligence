import json
import requests
from difflib import SequenceMatcher

API_URL = "http://localhost:8000/api/ask/"
EVAL_FILE = "qa_eval_set.json"
THRESHOLD = 0.8  

def calculate_similarity(a, b):
    """Calculates the similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def run_evaluation():
    """Reads the evaluation set and tests the API."""
    try:
        with open(EVAL_FILE, 'r') as f:
            eval_set = json.load(f)
    except FileNotFoundError:
        print(f"Error: Evaluation file '{EVAL_FILE}' not found.")
        return

    total_tests = len(eval_set)
    correct_count = 0

    print(f"--- Running RAG Evaluation against {API_URL} ({total_tests} questions) ---")

    for i, item in enumerate(eval_set):
        doc_id = item['document_id']
        question = item['question']
        expected = item['expected_answer']

        try:
            response = requests.post(
                API_URL,
                json={"document_id": doc_id, "question": question}
            )
            response.raise_for_status()
            api_answer = response.json().get('answer', '')

        except requests.exceptions.RequestException as e:
            print(f"Test {i+1} (Doc {doc_id}) Failed: API Error: {e}")
            api_answer = "" 

        similarity = calculate_similarity(expected, api_answer)
        is_correct = similarity >= THRESHOLD

        if is_correct:
            correct_count += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"[{status}] Test {i+1} (Doc {doc_id}): Similarity={similarity:.2f}")
        print(f"  Q: {question}")
        print(f"  A: {api_answer}")
        if not is_correct:
            print(f"  E: {expected}")
        print("-" * 50)


    accuracy = (correct_count / total_tests) * 100 if total_tests > 0 else 0
    print("\n" + "=" * 50)
    print(f"FINAL RAG SCORE: {correct_count}/{total_tests} Correct (Accuracy: {accuracy:.2f}%)")
    print("=" * 50)
    
if __name__ == '__main__':
    run_evaluation()