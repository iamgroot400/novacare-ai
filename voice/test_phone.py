import phone
from config import config


def test_twilio_signature_matches_twilio_docs_example():
    config.twilio_auth_token = "12345"
    params = {"CallSid": "CA1234567890ABCDE", "Caller": "+12349013030", "Digits": "1234",
              "From": "+12349013030", "To": "+18005551212"}
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    assert phone.twilio_signature_ok(url, params, "0/KCTR6DLpKmkAf8muzZqo1nDgQ=")
    assert not phone.twilio_signature_ok(url, params, "forged")
