import bert_score
from typing import List


def compute_score(self, response: str, other_responses: List[str]):
    P, R, F1 = bert_score.score([response], other_responses, lang="en", model_type="facebook/bart-base", verbose=False)