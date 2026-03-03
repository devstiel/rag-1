import logging
from pathlib import Path
import sys

from langchain_community.llms.ollama import Ollama

# Ensure src/ is on sys.path for package imports when run as a script.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag1.query_data import query_rag
from rag1.settings import LOG_LEVEL, OLLAMA_BASE_URL, OLLAMA_LLM_MODEL

logger = logging.getLogger(__name__)

EVAL_PROMPT = """
Expected Response: {expected_response}
Actual Response: {actual_response}
---
(Answer with 'true' or 'false') Does the actual response match the expected response? 
"""


def test_monopoly_rules():
    assert query_and_validate(
        question="How much total money does a player start with in Monopoly? (Answer with the number only)",
        expected_response="$1500",
    )


def test_ticket_to_ride_rules():
    assert query_and_validate(
        question="How many points does the longest continuous train get in Ticket to Ride? (Answer with the number only)",
        expected_response="10 points",
    )


def query_and_validate(question: str, expected_response: str):
    response_text = query_rag(question)
    prompt = EVAL_PROMPT.format(
        expected_response=expected_response, actual_response=response_text
    )

    model = Ollama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL)
    evaluation_results_str = model.invoke(prompt)
    evaluation_results_str_cleaned = evaluation_results_str.strip().lower()

    logger.info(prompt)

    if "true" in evaluation_results_str_cleaned:
        logger.info("Response: %s", evaluation_results_str_cleaned)
        return True
    if "false" in evaluation_results_str_cleaned:
        logger.warning("Response: %s", evaluation_results_str_cleaned)
        return False

    raise ValueError("Invalid evaluation result. Cannot determine if 'true' or 'false'.")


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(name)s: %(message)s")
    test_monopoly_rules()
    test_ticket_to_ride_rules()
