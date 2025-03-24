# Warning! Only English is supported as of right now for keyword extraction
import nltk
import yake

# Required nltk resources
# -----------------------

nltk.download("punkt_tab")
nltk.download("averaged_perceptron_tagger_eng")

# Constants
# ---------

MAX_KEYWORDS = 7


# Keyword extractors
# ------------------

yake_extractor = yake.KeywordExtractor(
    lan="en",
    n=1,  # unigram for short queries
    top=MAX_KEYWORDS,
    dedupLim=0.9,
    features=None,
)


# Main get func
# -------------


def get(sentence: str) -> list[str]:
    keywords = _extract(sentence)

    return _boost_ordinals(keywords, sentence)


# Helpers
# -------


def _extract(sentence: str) -> list[str]:
    keywords = yake_extractor.extract_keywords(sentence)
    return [kw for kw, _ in keywords]


def _boost_ordinals(keywords: list[str], sentence: str) -> list[str]:
    tokens = nltk.word_tokenize(sentence)
    pos_tags = nltk.pos_tag(tokens)
    for word, tag in pos_tags:
        if tag in {"JJ", "CD"}:  # JJ = Adjective, CD = Cardinal Number
            word_lower = word.lower()
            if word_lower not in keywords:
                keywords.append(word_lower)  # maintain YAKE! priority
    return keywords
