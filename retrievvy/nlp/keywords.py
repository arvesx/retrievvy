# Warning! Only English is supported as of right now for keyword extraction
import stanza
import yake


# Constants
# ---------

MAX_KEYWORDS = 7

# Stanza
# ------

stanza.download("en", processors="tokenize,pos", verbose=False)
nlp_stanza = stanza.Pipeline(
    lang="en", processors="tokenize,pos", tokenize_no_ssplit=True, verbose=False
)


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
    doc = nlp_stanza(sentence)
    for sentence in doc.sentences:
        for word in sentence.words:
            if word.upos in {"ADJ", "NUM"}:
                word_lower = word.text.lower()
                if word_lower not in keywords:
                    keywords.append(
                        word_lower
                    )  # add to the END to preserve YAKE! priority
    return keywords
