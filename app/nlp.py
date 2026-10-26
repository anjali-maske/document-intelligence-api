
import re
from sklearn.feature_extraction.text import TfidfVectorizer


def extract_keywords(content, top_n=5):
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", content)
        if sentence.strip()
    ]

    if not sentences:
        return []

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=100
        )

        matrix = vectorizer.fit_transform(sentences)
        scores = matrix.sum(axis=0).A1
        terms = vectorizer.get_feature_names_out()

        ranked = sorted(
            zip(terms, scores),
            key=lambda item: item[1],
            reverse=True
        )

        return [term for term, score in ranked[:top_n]]

    except ValueError:
        return []
