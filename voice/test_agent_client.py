from agent_client import _NO, _YES, speakable


def test_yes_no():
    assert _YES.search("yeah, go ahead") and not _NO.search("yeah, go ahead")
    assert _NO.search("no thanks") and not _YES.search("no thanks")
    assert _YES.search("yes no") and _NO.search("yes no")  # ambiguous -> caller re-asks


def test_speakable():
    assert speakable("Done — return **RET-1** created") == "Done — return RET-1 created"


def test_nepali_yes_no():
    assert _YES.search("हो, गर्नुस्") and not _NO.search("हो, गर्नुस्")
    assert _NO.search("होइन, नगर्नुस्") and not _YES.search("होइन, नगर्नुस्")
    assert _YES.search("huncha") and _NO.search("chaina")


def test_nepali_phone_answers():
    # the confirm prompt asks for "हुन्छ" / "हुँदैन"
    assert _YES.search("हुन्छ") and not _NO.search("हुन्छ")
    assert _NO.search("हुँदैन") and not _YES.search("हुँदैन")


def test_warmed_phrases_are_not_resynthesized(monkeypatch):
    import numpy as np

    import tts

    calls = []
    monkeypatch.setattr(tts, "_speak", lambda t: calls.append(t) or np.ones(10, dtype="float32"))
    monkeypatch.setattr(tts, "_cache", {})
    tts.warm(["एकछिन पर्खनुहोला, म हेर्दैछु।"])
    tts.synthesize("एकछिन पर्खनुहोला, म हेर्दैछु। नयाँ वाक्य।")
    assert calls == ["एकछिन पर्खनुहोला, म हेर्दैछु।", "नयाँ वाक्य।"]  # warm once, then only the new one
