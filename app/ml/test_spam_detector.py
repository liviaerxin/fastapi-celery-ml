import joblib
import re
from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

model = joblib.load('spam_classifier.joblib')

def preprocessor(text):
    text = re.sub('<[^>]*>', '', text) # Effectively removes HTML markup tags
    emoticons = re.findall('(?::|;|=)(?:-)?(?:\)|\(|D|P)', text)
    text = re.sub('[\W]+', ' ', text.lower()) + ' '.join(emoticons).replace('-', '')
    return text

def classify_message(model, message):
	message = preprocessor(message)
	label = model.predict([message])[0]
	spam_prob = model.predict_proba([message])
	return {'label': label, 'spam_probability': spam_prob[0][1]}


classify_message(model=model, message="phishing emails from xxxx")
classify_message(model=model, message="To use your credit, click the WAP link in the next txt message or click he")