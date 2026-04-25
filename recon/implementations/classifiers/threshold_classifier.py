from recon.domain.models import MatchClassification
from recon.ports import Classifier


class ThresholdClassifier(Classifier):
    def __init__(
        self,
        exact_threshold: float = 0.9,
        probable_threshold: float = 0.6
    ):
        self.exact_threshold = exact_threshold
        self.probable_threshold = probable_threshold
    
    def classify(self, score: float) -> MatchClassification:
        if score >= self.exact_threshold:
            return MatchClassification.EXACT_MATCH
        elif score >= self.probable_threshold:
            return MatchClassification.PROBABLE_MATCH
        else:
            return MatchClassification.LOW_CONFIDENCE
