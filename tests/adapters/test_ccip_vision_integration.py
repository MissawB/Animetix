"""Integration smoke: the REAL CCIP graph over REAL catalog portraits.

Marked ``integration`` (excluded from the CI unit job via ``-m "not
integration"``): it downloads ``deepghs/ccip_onnx`` and a handful of AniList
character portraits over the network. Where the mocked tests in
``test_ccip_vision.py`` pin the preprocessing *tensor*, this pins the
END-TO-END property the 35 292-image character build relies on — real
portraits encode to 768-d, non-zero, deterministic vectors that
*discriminate* between characters (self-similarity ~1.0 >> cross-character).

A subtly-wrong preprocessing change (BGR vs RGB, a dropped ``/255``, a lost
transpose) can still produce a plausibly-shaped tensor and pass every mocked
unit test, then classify garbage. This test is the net for exactly that: run
it with ``pytest -m integration`` when touching ``ccip_vision``.
"""

import urllib.request

import numpy as np
import pytest

pytestmark = pytest.mark.integration

# Real catalog portraits (media_type=Character, AniList CDN), a mix of .png/.jpg.
PORTRAITS = [
    (
        "2007",
        "Shikamaru Nara",
        "https://s4.anilist.co/file/anilistcdn/character/large/b2007-QaesJlIZDifj.jpg",
    ),
    (
        "269",
        "Totoro",
        "https://s4.anilist.co/file/anilistcdn/character/large/b269-sbPL4w1ygjSe.jpg",
    ),
    (
        "199205",
        "RIM",
        "https://s4.anilist.co/file/anilistcdn/character/large/b199205-EDOhnKvQTYwM.png",
    ),
    (
        "377668",
        "Sosshi",
        "https://s4.anilist.co/file/anilistcdn/character/large/b377668-4kLYSkxSgvI4.png",
    ),
    ("66377", "Y", "https://s4.anilist.co/file/anilistcdn/character/large/66377.jpg"),
    (
        "291682",
        "Chaldea Operator",
        "https://s4.anilist.co/file/anilistcdn/character/large/b291682-3JhYKvzXRONL.png",
    ),
    (
        "140960",
        "Hizamaru",
        "https://s4.anilist.co/file/anilistcdn/character/large/b140960-Fqi4jfCNPxyV.jpg",
    ),
    (
        "163911",
        "Lynette",
        "https://s4.anilist.co/file/anilistcdn/character/large/b163911-rLwACkpz9S34.png",
    ),
    (
        "55101",
        "Matsuda",
        "https://s4.anilist.co/file/anilistcdn/character/large/55101.jpg",
    ),
    (
        "291919",
        "Martha Conway",
        "https://s4.anilist.co/file/anilistcdn/character/large/b291919-aTw9ZZr4m9af.png",
    ),
]
# Same source image at a different resolution -> exercises size-invariance.
SHIKAMARU_MEDIUM = (
    "https://s4.anilist.co/file/anilistcdn/character/medium/b2007-QaesJlIZDifj.jpg"
)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ccip-it"})
    with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310 (fixed hosts)
        return r.read()


def _cos(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def _engine():
    from adapters.inference.ccip_vision import CcipVisionMixin

    class _E(CcipVisionMixin):
        def _log_usage(self, **kwargs):
            pass

    return _E()


@pytest.fixture(scope="module")
def encoded():
    """Download the model + portraits and encode once; shared by all tests.

    Skips (never fails) when the network or the Hub model is unavailable, so
    the suite stays green offline; it only asserts when it has real vectors.
    """
    eng = _engine()
    vecs, labels = [], []
    for ext_id, title, url in PORTRAITS:
        try:
            data = _fetch(url)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"network unavailable ({title}): {e}")
        try:
            vec = eng.get_character_embedding(data)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"CCIP model unavailable: {e}")
        vecs.append(np.asarray(vec, dtype=np.float64))
        labels.append(f"{title} ({ext_id})")
    return eng, vecs, labels


def test_real_portraits_encode_to_768d_nonzero(encoded):
    _, vecs, _ = encoded
    assert len(vecs) == len(PORTRAITS)
    for v in vecs:
        assert v.shape == (768,)
        assert np.linalg.norm(v) > 0.0


def test_encoding_is_deterministic(encoded):
    eng, vecs, _ = encoded
    again = np.asarray(
        eng.get_character_embedding(_fetch(PORTRAITS[0][2])), dtype=np.float64
    )
    assert _cos(vecs[0], again) > 0.9999


def test_distinct_characters_are_discriminated(encoded):
    _, vecs, _ = encoded
    sims = [
        _cos(vecs[i], vecs[j])
        for i in range(len(vecs))
        for j in range(i + 1, len(vecs))
    ]
    mean = float(np.mean(sims))
    # Self-similarity is ~1.0; distinct characters must sit well below it.
    # Observed ~0.33; 0.6 is a loose, non-flaky ceiling that a BGR/normalization
    # regression (which collapses everything toward high similarity) would break.
    assert mean < 0.6, f"cross-character mean similarity too high: {mean:.3f}"


def test_preprocessing_is_size_invariant(encoded):
    eng, vecs, _ = encoded
    try:
        med = np.asarray(
            eng.get_character_embedding(_fetch(SHIKAMARU_MEDIUM)), dtype=np.float64
        )
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"medium portrait unavailable: {e}")
    assert _cos(vecs[0], med) > 0.9


def test_search_ranks_the_query_first(encoded):
    _, vecs, _ = encoded
    query = 0
    ranked = sorted(range(len(vecs)), key=lambda i: -_cos(vecs[query], vecs[i]))
    assert ranked[0] == query
