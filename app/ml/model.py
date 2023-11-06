import os

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "spam_classifier.joblib"
)


class SpamModel:
    """Wrapper for loading and serving pre-trained model"""

    def __init__(self):
        self.model = self._load_model_from_path(MODEL_PATH)

    @staticmethod
    def _load_model_from_path(path):
        import joblib

        model = joblib.load(path)
        return model

    @staticmethod
    def preprocessor(text):
        import re

        text = re.sub("<[^>]*>", "", text)  # Effectively removes HTML markup tags
        emoticons = re.findall("(?::|;|=)(?:-)?(?:\)|\(|D|P)", text)
        text = re.sub("[\W]+", " ", text.lower()) + " ".join(emoticons).replace("-", "")
        return text

    def predict(self, message):
        """
        Make batch prediction on list of preprocessed feature dicts.
        Returns class probabilities if 'return_options' is 'Prob', otherwise returns class membership predictions
        """
        message = self.preprocessor(message)
        label = self.model.predict([message])[0]
        spam_prob = self.model.predict_proba([message])

        return {"label": label, "spam_probability": spam_prob[0][1]}
