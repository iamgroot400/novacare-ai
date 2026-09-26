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
    tts.synthesize("एकछिन पर्खनुहोला, म हेर्दैछु।")
    tts.synthesize("नयाँ वाक्य। अर्को वाक्य।")
    # warmed once, then served from cache; the new reply is one request for both sentences
    assert calls == ["एकछिन पर्खनुहोला, म हेर्दैछु।", "नयाँ वाक्य। अर्को वाक्य।"]


def test_phrases_group_by_language():
    from tts import phrases

    assert phrases("नमस्ते! के सहयोग चाहियो? You can speak English too. धन्यवाद।") == [
        "नमस्ते! के सहयोग चाहियो?", "You can speak English too.", "धन्यवाद।"]


def test_nepali_text_is_made_speakable():
    from tts import speakable_ne

    assert speakable_ne("अर्डर NS-1077 अहिले हबमा छ।") == "अर्डर एन एस १०७७ अहिले हबमा छ।"
    assert speakable_ne("“NovaPods Pro” लाई हटाएर (forget) पुन: जोड्नुहोस्।") == "नोभा पड्स प्रो लाई हटाएर फेरि जोड्नुहोस्।"
    assert speakable_ne("NovaPods Lite NPR 5,999 मा छ, ANC सहित।") == "नोभा पड्स लाइट ५,९९९ रुपैयाँ मा छ, ए एन सी सहित।"
    assert speakable_ne("ब्लुटुथ अन‑अफ गर्नुहोस्, १४‑दिन।") == "ब्लुटुथ अन अफ गर्नुहोस्, १४ दिन।"
    assert speakable_ne("NovaCharge 65W चार्जर") == "नोभा चार्ज ६५ डब्लु चार्जर"


def test_spoken_text_drops_lists_and_formal_words():
    from tts import speakable_ne

    reply = "१. केसमा राख्नुहोस्।\n२. बटन थिच्नुहोस्।\n- अनि पुन: जोड्नुहोस्।"
    assert speakable(reply) == "केसमा राख्नुहोस्।\nबटन थिच्नुहोस्।\nअनि पुन: जोड्नुहोस्।"
    assert speakable_ne("म तपाईंलाई मानव विशेषज्ञसँग जोड्दैछु, केही क्षण पर्खनुहोला।") == \
        "म तपाईंलाई हाम्रो टिमको मान्छेसँग जोड्दैछु, एकछिन पर्खनुहोला।"
