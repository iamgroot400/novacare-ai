"""Nepali fluency check against a running backend.

    python scripts/nepali_check.py [http://localhost:8000]

Sends Nepali / romanized-Nepali customer turns and flags replies that are not Devanagari,
contain Hindi words, or are too long to speak comfortably. A human should still read them:
the flags catch the common failures, not awkward phrasing.
"""
from __future__ import annotations

import re
import sys
import time

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
# One conversation per list, so follow-ups keep context.
SCENARIOS = [
    ["नमस्ते, मेरो अर्डर NS-1077 कहाँ पुग्यो?", "NS-1089 किन ढिलो भयो?"],
    ["mero order NS-1042 return garna milcha?", "हुँदैन, पर्दैन"],
    ["NS-1033 फिर्ता गर्न मिल्छ?"],
    ["मेरो NovaPods Pro बारम्बार डिस्कनेक्ट हुन्छ", "अर्डर NS-1042 हो", "मैले त्यो सबै गरिसकेँ"],
    ["सात हजार भित्रको noise cancelling हेडफोन सुझाव दिनुहोस्"],
    ["मलाई मान्छेसँग कुरा गर्नु छ"],
]
HINDI = {"है", "हैं", "आप", "आपका", "आपकी", "आपके", "नहीं", "मैं", "क्या", "रहा", "रही",
         "किया", "गया", "हूँ", "और", "लेकिन", "भी"}  # not कृपया: it is standard Nepali too
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
TOKEN = re.compile(r"[\s,।.!?;:()\"']+")


def flags(reply: str) -> list[str]:
    out = []
    if not DEVANAGARI.search(reply):
        out.append("not Nepali")
    hindi = sorted(HINDI & set(TOKEN.split(reply)))
    if hindi:
        out.append("Hindi words: " + " ".join(hindi))
    if len(re.findall(r"[।.!?]", reply)) > 4 or len(reply) > 400:
        out.append("long for a call")
    if re.search(r"[*#`]|^\s*([-•]|\d+\.)", reply, re.M):
        out.append("markdown/list")
    if "फिर्टा" in reply:
        out.append("misspelt फिर्ता")
    # a physical button on the device is fine; an on-screen confirm button/card is not
    if re.search(r"पुष्टि बटन|कार्ड|स्क्रिन|confirm button|card|screen", reply, re.I):
        out.append("mentions an on-screen button/card (not usable on a call)")
    return out


def main() -> int:
    bad = total = 0
    with httpx.Client(timeout=300) as c:  # free-tier 429 retries can take a while
        for turns in SCENARIOS:
            cid = c.post(f"{BASE}/api/conversations", json={"channel": "voice"}).json()["id"]
            for msg in turns:
                t = time.time()
                r = c.post(f"{BASE}/api/conversations/{cid}/message",
                           json={"content": msg, "channel": "voice"}).json()
                reply = r.get("reply", "")
                f = flags(reply)
                total += 1
                bad += bool(f)
                print(f"\nYOU  : {msg}\nAGENT: {reply}\n       {time.time() - t:.1f}s"
                      + (f"  !! {'; '.join(f)}" if f else "  ok")
                      + ("  [awaiting confirmation]" if r.get("pending_action") else ""))
    print(f"\n{total - bad}/{total} replies passed the automatic checks")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
