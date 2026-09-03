"""Deterministic demo dataset for NovaStore.

Everything here is fictional. Prices are integer NPR. Dates are ISO strings
anchored around DEMO_DATE = 2026-09-03.
"""
from __future__ import annotations

PRODUCTS: list[dict] = [
    dict(id="P001", name="NovaPods Pro", category="Audio", price_npr=8499, stock=17,
         warranty_months=12, rating=4.6,
         features=["ANC", "Bluetooth 5.4", "38-hour battery", "USB-C", "Wireless charging"],
         description="Flagship wireless earbuds with adaptive active noise cancellation, "
                     "spatial audio and a 38-hour total battery life with the case."),
    dict(id="P002", name="NovaPods Lite", category="Audio", price_npr=5999, stock=12,
         warranty_months=12, rating=4.4,
         features=["ANC", "Bluetooth 5.3", "35-hour battery", "USB-C"],
         description="Affordable wireless earbuds with active noise cancellation and a "
                     "comfortable all-day fit."),
    dict(id="P003", name="NovaWatch S2", category="Wearables", price_npr=11999, stock=8,
         warranty_months=12, rating=4.5,
         features=["AMOLED display", "GPS", "Heart-rate monitor", "SpO2", "5-day battery", "5ATM water resistance"],
         description="A premium smartwatch with a bright AMOLED display, built-in GPS and "
                     "comprehensive health tracking."),
    dict(id="P004", name="NovaSound Mini", category="Audio", price_npr=4499, stock=21,
         warranty_months=12, rating=4.3,
         features=["Bluetooth 5.2", "IPX6", "12-hour battery", "Built-in mic"],
         description="Pocket-sized waterproof Bluetooth speaker with a surprisingly full sound."),
    dict(id="P005", name="NovaCharge 65W", category="Accessories", price_npr=2999, stock=34,
         warranty_months=6, rating=4.7,
         features=["65W GaN", "USB-C PD", "Dual port", "Foldable pins"],
         description="Compact 65W GaN charger that powers laptops, tablets and phones from a "
                     "dual-port design."),
    dict(id="P006", name="NovaKeys Mechanical", category="Computing", price_npr=7499, stock=6,
         warranty_months=12, rating=4.6,
         features=["Hot-swappable switches", "RGB backlight", "Wireless", "Bluetooth", "USB-C", "75% layout"],
         description="A 75% hot-swappable mechanical keyboard with wireless and wired modes, "
                     "great for work and gaming."),
    dict(id="P007", name="NovaMouse Air", category="Computing", price_npr=3499, stock=19,
         warranty_months=12, rating=4.3,
         features=["Wireless", "Bluetooth", "Silent switches", "4000 DPI", "Rechargeable"],
         description="Lightweight silent wireless mouse for quiet offices and long work sessions."),
    dict(id="P008", name="NovaCam 2K", category="Computing", price_npr=6799, stock=11,
         warranty_months=12, rating=4.5,
         features=["2K video", "Autofocus", "Dual microphones", "Privacy shutter", "USB-C"],
         description="A sharp 2K webcam with autofocus and dual noise-cancelling microphones "
                     "for calls and streaming."),
    # ---- additional Nova-branded catalogue (12+) ----
    dict(id="P009", name="NovaBook 14 Sleeve", category="Accessories", price_npr=1499, stock=40,
         warranty_months=6, rating=4.2,
         features=["Water-resistant", "Fits 14-inch laptops", "Felt lining", "Magnetic flap"],
         description="A slim protective sleeve for 14-inch laptops with a soft felt lining."),
    dict(id="P010", name="NovaHub 7-in-1", category="Accessories", price_npr=3999, stock=23,
         warranty_months=12, rating=4.4,
         features=["HDMI 4K", "USB-C PD 100W", "2x USB-A", "SD/microSD", "Gigabit Ethernet"],
         description="A 7-in-1 USB-C hub that adds HDMI, Ethernet, card readers and power "
                     "pass-through to any modern laptop."),
    dict(id="P011", name="NovaBuds Sport", category="Audio", price_npr=4999, stock=18,
         warranty_months=12, rating=4.3,
         features=["IPX7", "Ear hooks", "Bluetooth 5.3", "28-hour battery", "Low-latency mode"],
         description="Secure-fit sport earbuds with ear hooks, sweat resistance and a "
                     "low-latency gaming mode."),
    dict(id="P012", name="NovaWatch Active", category="Wearables", price_npr=7499, stock=14,
         warranty_months=12, rating=4.2,
         features=["LCD display", "Heart-rate monitor", "10-day battery", "5ATM water resistance", "Sleep tracking"],
         description="A lightweight fitness watch with a 10-day battery and everyday health tracking."),
    dict(id="P013", name="NovaBand Fit", category="Wearables", price_npr=3299, stock=27,
         warranty_months=12, rating=4.1,
         features=["AMOLED band", "SpO2", "14-day battery", "Step & sleep tracking", "IP68"],
         description="A slim fitness band with a colour AMOLED strip and a two-week battery."),
    dict(id="P014", name="NovaDesk Stand", category="Accessories", price_npr=2299, stock=31,
         warranty_months=6, rating=4.5,
         features=["Aluminium", "Adjustable height", "Cable channel", "Anti-slip pads"],
         description="An adjustable aluminium laptop stand that raises your screen to eye level."),
    dict(id="P015", name="NovaPad Wireless Charger", category="Accessories", price_npr=1999, stock=29,
         warranty_months=6, rating=4.3,
         features=["15W Qi", "USB-C input", "Case-friendly", "LED indicator"],
         description="A 15W Qi wireless charging pad with a case-friendly coil and subtle LED."),
    dict(id="P016", name="NovaMic Studio", category="Computing", price_npr=8999, stock=9,
         warranty_months=12, rating=4.6,
         features=["USB-C", "Cardioid + omni", "Zero-latency monitoring", "Mute touch button", "Tripod included"],
         description="A USB condenser microphone with selectable pickup patterns for "
                     "podcasts, streaming and calls."),
    dict(id="P017", name="NovaDock Pro", category="Computing", price_npr=13999, stock=5,
         warranty_months=12, rating=4.5,
         features=["Dual 4K output", "USB-C 100W", "5x USB-A", "Ethernet", "Audio jack"],
         description="A full desktop docking station that drives two 4K monitors and charges "
                     "your laptop over a single cable."),
    dict(id="P018", name="NovaGlow Desk Lamp", category="Accessories", price_npr=2799, stock=22,
         warranty_months=12, rating=4.4,
         features=["Adjustable colour temperature", "Touch dimmer", "USB-C powered", "Flicker-free"],
         description="A flicker-free LED desk lamp with tunable warmth and a touch dimmer."),
    dict(id="P019", name="NovaKeys Compact", category="Computing", price_npr=4999, stock=13,
         warranty_months=12, rating=4.3,
         features=["60% layout", "Wireless", "Bluetooth", "Low-profile switches", "USB-C"],
         description="A 60% low-profile wireless keyboard built for small desks and travel."),
    dict(id="P020", name="NovaSound Bar 2.0", category="Audio", price_npr=9499, stock=7,
         warranty_months=12, rating=4.4,
         features=["Bluetooth 5.3", "HDMI ARC", "Optical in", "80W output", "Wall-mountable"],
         description="A compact 2.0 soundbar that upgrades TV and desktop audio over HDMI ARC "
                     "or Bluetooth."),
    dict(id="P021", name="NovaPower 20K", category="Accessories", price_npr=3499, stock=25,
         warranty_months=12, rating=4.6,
         features=["20000mAh", "45W USB-C PD", "Dual output", "Pass-through charging", "Digital display"],
         description="A 20,000mAh power bank with 45W fast charging and a clear digital "
                     "battery readout."),
    dict(id="P022", name="NovaTrack Tag", category="Accessories", price_npr=1299, stock=50,
         warranty_months=12, rating=4.2,
         features=["Bluetooth tracker", "Replaceable battery", "IP67", "Loud finder ring"],
         description="A small Bluetooth item tracker for keys, bags and luggage."),
]

CUSTOMERS: list[dict] = [
    dict(id="C001", name="Aarav Sharma", email="aarav@example.test", phone="+977-9800000001", city="Kathmandu"),
    dict(id="C002", name="Sita KC", email="sita@example.test", phone="+977-9800000002", city="Lalitpur"),
    dict(id="C003", name="Rohan Thapa", email="rohan@example.test", phone="+977-9800000003", city="Pokhara"),
    dict(id="C004", name="Anisha Rai", email="anisha@example.test", phone="+977-9800000004", city="Bhaktapur"),
    dict(id="C005", name="Bibek Gurung", email="bibek@example.test", phone="+977-9800000005", city="Butwal"),
    dict(id="C006", name="Prerana Adhikari", email="prerana@example.test", phone="+977-9800000006", city="Biratnagar"),
    dict(id="C007", name="Kiran Magar", email="kiran@example.test", phone="+977-9800000007", city="Dharan"),
    dict(id="C008", name="Sneha Shrestha", email="sneha@example.test", phone="+977-9800000008", city="Kathmandu"),
    dict(id="C009", name="Manish Karki", email="manish@example.test", phone="+977-9800000009", city="Hetauda"),
    dict(id="C010", name="Puja Bhattarai", email="puja@example.test", phone="+977-9800000010", city="Nepalgunj"),
    dict(id="C011", name="Sagar Lama", email="sagar@example.test", phone="+977-9800000011", city="Lalitpur"),
    dict(id="C012", name="Ritika Joshi", email="ritika@example.test", phone="+977-9800000012", city="Pokhara"),
    dict(id="C013", name="Nabin Bhandari", email="nabin@example.test", phone="+977-9800000013", city="Kathmandu"),
    dict(id="C014", name="Asmita Poudel", email="asmita@example.test", phone="+977-9800000014", city="Chitwan"),
    dict(id="C015", name="Dipesh Tamang", email="dipesh@example.test", phone="+977-9800000015", city="Dhangadhi"),
    dict(id="C016", name="Sushmita Khadka", email="sushmita@example.test", phone="+977-9800000016", city="Janakpur"),
    dict(id="C017", name="Arjun Basnet", email="arjun@example.test", phone="+977-9800000017", city="Kathmandu"),
    dict(id="C018", name="Melina Shah", email="melina@example.test", phone="+977-9800000018", city="Birgunj"),
    dict(id="C019", name="Prakash Oli", email="prakash@example.test", phone="+977-9800000019", city="Pokhara"),
    dict(id="C020", name="Bimala Dahal", email="bimala@example.test", phone="+977-9800000020", city="Lalitpur"),
]

# Required demo orders — IDs and fields must remain stable.
REQUIRED_ORDERS: list[dict] = [
    dict(id="NS-1042", customer_id="C001", product_id="P001", quantity=1, total_npr=8499,
         status="delivered", ordered_at="2026-08-20", delivered_at="2026-08-26",
         shipped_at="2026-08-22", payment_method="Khalti"),
    dict(id="NS-1077", customer_id="C002", product_id="P003", quantity=1, total_npr=11999,
         status="in_transit", ordered_at="2026-08-30", shipped_at="2026-09-01",
         current_location="Kathmandu Distribution Hub", estimated_delivery="2026-09-04",
         payment_method="eSewa"),
    dict(id="NS-1089", customer_id="C003", product_id="P006", quantity=1, total_npr=7499,
         status="delayed", ordered_at="2026-08-29", shipped_at="2026-08-31",
         current_location="Pokhara Sorting Center", estimated_delivery="2026-09-07",
         delay_reason="Weather-related transportation delay", payment_method="Cash on Delivery"),
    dict(id="NS-1033", customer_id="C004", product_id="P004", quantity=1, total_npr=4499,
         status="delivered", ordered_at="2026-08-04", delivered_at="2026-08-10",
         shipped_at="2026-08-06", payment_method="Khalti"),
    dict(id="NS-1091", customer_id="C001", product_id="P005", quantity=2, total_npr=5998,
         status="processing", ordered_at="2026-09-02", estimated_delivery="2026-09-06",
         payment_method="eSewa"),
]


def _price(pid: str) -> int:
    for p in PRODUCTS:
        if p["id"] == pid:
            return p["price_npr"]
    raise KeyError(pid)


def _generated_orders() -> list[dict]:
    """~28 additional deterministic orders covering every status."""
    rows: list[dict] = []
    plan = [
        # (num, customer, product, qty, status, ordered, delivered, shipped, eta, location, delay)
        (1050, "C005", "P002", 1, "delivered", "2026-07-15", "2026-07-20", "2026-07-16", None, None, None),
        (1051, "C006", "P007", 1, "delivered", "2026-07-18", "2026-07-24", "2026-07-20", None, None, None),
        (1052, "C007", "P005", 3, "delivered", "2026-07-22", "2026-07-27", "2026-07-23", None, None, None),
        (1053, "C008", "P010", 1, "delivered", "2026-08-01", "2026-08-05", "2026-08-02", None, None, None),
        (1054, "C009", "P016", 1, "delivered", "2026-08-02", "2026-08-09", "2026-08-04", None, None, None),
        (1055, "C010", "P021", 2, "delivered", "2026-08-10", "2026-08-15", "2026-08-11", None, None, None),
        (1056, "C011", "P001", 1, "delivered", "2026-08-12", "2026-08-18", "2026-08-13", None, None, None),
        (1057, "C012", "P013", 1, "delivered", "2026-08-14", "2026-08-19", "2026-08-15", None, None, None),
        (1058, "C013", "P020", 1, "delivered", "2026-08-21", "2026-08-27", "2026-08-23", None, None, None),
        (1059, "C014", "P008", 1, "delivered", "2026-08-24", "2026-08-30", "2026-08-25", None, None, None),
        (1060, "C002", "P011", 1, "delivered", "2026-08-18", "2026-08-23", "2026-08-19", None, None, None),
        (1061, "C015", "P017", 1, "cancelled", "2026-08-20", None, None, None, None, None),
        (1062, "C016", "P006", 1, "cancelled", "2026-08-25", None, None, None, None, None),
        (1063, "C017", "P003", 1, "cancelled", "2026-09-01", None, None, None, None, None),
        (1064, "C018", "P004", 2, "processing", "2026-09-02", None, None, "2026-09-06", None, None),
        (1065, "C019", "P007", 1, "processing", "2026-09-03", None, None, "2026-09-08", None, None),
        (1066, "C020", "P015", 1, "processing", "2026-09-03", None, None, "2026-09-07", None, None),
        (1067, "C005", "P012", 1, "shipped", "2026-08-31", None, "2026-09-02", "2026-09-05",
         "Kathmandu Distribution Hub", None),
        (1068, "C006", "P018", 1, "shipped", "2026-09-01", None, "2026-09-02", "2026-09-05",
         "Bhairahawa Hub", None),
        (1069, "C007", "P022", 4, "shipped", "2026-09-01", None, "2026-09-03", "2026-09-06",
         "Biratnagar Hub", None),
        (1070, "C008", "P002", 1, "in_transit", "2026-08-30", None, "2026-09-01", "2026-09-04",
         "Mugling Checkpoint", None),
        (1071, "C009", "P009", 2, "in_transit", "2026-08-31", None, "2026-09-01", "2026-09-04",
         "Kathmandu Distribution Hub", None),
        (1072, "C010", "P019", 1, "delayed", "2026-08-27", None, "2026-08-29", "2026-09-08",
         "Karnali Regional Hub", "Landslide on highway causing reroute"),
        (1073, "C011", "P020", 1, "delayed", "2026-08-28", None, "2026-08-30", "2026-09-09",
         "Surkhet Sorting Center", "Weather-related transportation delay"),
        (1074, "C012", "P001", 1, "delivered", "2026-08-05", "2026-08-09", "2026-08-06", None, None, None),
        (1075, "C013", "P011", 1, "delivered", "2026-08-06", "2026-08-11", "2026-08-07", None, None, None),
        (1076, "C014", "P005", 2, "return_requested", "2026-08-08", "2026-08-13", "2026-08-09", None, None, None),
        (1078, "C016", "P013", 1, "return_requested", "2026-08-15", "2026-08-21", "2026-08-16", None, None, None),
        (1079, "C017", "P002", 1, "delivered", "2026-08-16", "2026-08-22", "2026-08-17", None, None, None),
        (1080, "C018", "P008", 1, "delivered", "2026-08-19", "2026-08-24", "2026-08-20", None, None, None),
    ]
    payments = ["Khalti", "eSewa", "Cash on Delivery", "IME Pay", "ConnectIPS"]
    for i, (num, cust, prod, qty, status, ordered, delivered, shipped, eta, loc, delay) in enumerate(plan):
        rows.append(dict(
            id=f"NS-{num}", customer_id=cust, product_id=prod, quantity=qty,
            total_npr=_price(prod) * qty, status=status,
            ordered_at=ordered, delivered_at=delivered, shipped_at=shipped,
            estimated_delivery=eta, current_location=loc, delay_reason=delay,
            payment_method=payments[i % len(payments)],
        ))
    return rows


ORDERS: list[dict] = REQUIRED_ORDERS + _generated_orders()

# Historical returns (RET-XXXX). Tie to return_requested / delivered orders.
RETURNS: list[dict] = [
    dict(id="RET-4001", order_id="NS-1076", customer_id="C014", reason="Charger stopped delivering fast charge",
         status="APPROVED", created_at="2026-08-15"),
    dict(id="RET-4002", order_id="NS-1078", customer_id="C016", reason="Band strap broke within a week",
         status="ITEM_RECEIVED", created_at="2026-08-23"),
    dict(id="RET-4003", order_id="NS-1050", customer_id="C005", reason="Changed mind, prefer the Pro model",
         status="REFUNDED", created_at="2026-07-25"),
    dict(id="RET-4004", order_id="NS-1055", customer_id="C010", reason="One power bank arrived with a dented casing",
         status="REFUND_PROCESSING", created_at="2026-08-18"),
    dict(id="RET-4005", order_id="NS-1057", customer_id="C012", reason="Screen has a dead pixel line",
         status="REQUESTED", created_at="2026-08-20"),
]

TICKETS: list[dict] = [
    dict(id="SUP-8001", customer_id="C001", order_id="NS-1042", subject="NovaPods Pro left earbud quieter",
         description="Left earbud noticeably quieter than the right after two weeks of use.",
         priority="NORMAL", status="RESOLVED", created_at="2026-08-28",
         resolution="Guided customer through contact cleaning and reset; audio balance restored."),
    dict(id="SUP-8002", customer_id="C003", order_id="NS-1089", subject="Where is my keyboard order",
         description="Customer asking about delayed order NS-1089 to Pokhara.",
         priority="LOW", status="RESOLVED", created_at="2026-09-01",
         resolution="Explained weather delay; provided updated ETA of 2026-09-07."),
    dict(id="SUP-8003", customer_id="C005", order_id="NS-1050", subject="NovaPods Lite pairing issue",
         description="Earbuds not showing up in Bluetooth list on Android.",
         priority="NORMAL", status="RESOLVED", created_at="2026-07-21",
         resolution="Firmware update to 1.8 resolved the pairing problem."),
    dict(id="SUP-8004", customer_id="C009", order_id="NS-1054", subject="NovaMic Studio low input volume",
         description="Microphone input very low even at max gain.",
         priority="HIGH", status="IN_PROGRESS", created_at="2026-08-11",
         resolution=""),
    dict(id="SUP-8005", customer_id="C014", order_id="NS-1076", subject="NovaCharge 65W not fast charging",
         description="Charger only supplies 5W to laptop after a month.",
         priority="HIGH", status="ESCALATED", created_at="2026-08-14",
         resolution="Escalated to hardware team; return RET-4001 approved."),
    dict(id="SUP-8006", customer_id="C012", order_id="NS-1057", subject="NovaBand Fit dead pixels",
         description="Vertical line of dead pixels on the AMOLED strip.",
         priority="NORMAL", status="OPEN", created_at="2026-08-19",
         resolution=""),
    dict(id="SUP-8007", customer_id="C007", order_id="NS-1052", subject="Bulk charger order invoice",
         description="Needs a VAT invoice for 3x NovaCharge 65W.",
         priority="LOW", status="RESOLVED", created_at="2026-07-28",
         resolution="Invoice emailed to customer."),
    dict(id="SUP-8008", customer_id="C002", order_id="NS-1077", subject="Change delivery address for NS-1077",
         description="Wants delivery redirected within Lalitpur.",
         priority="NORMAL", status="IN_PROGRESS", created_at="2026-09-02",
         resolution=""),
    dict(id="SUP-8009", customer_id="C013", order_id="NS-1058", subject="NovaSound Bar 2.0 no HDMI ARC audio",
         description="Soundbar silent over HDMI ARC, works on Bluetooth.",
         priority="NORMAL", status="OPEN", created_at="2026-08-28",
         resolution=""),
    dict(id="SUP-8010", customer_id="C006", order_id="NS-1051", subject="NovaMouse Air double-clicking",
         description="Left button registers double clicks intermittently.",
         priority="NORMAL", status="RESOLVED", created_at="2026-07-26",
         resolution="Replaced under warranty; return not required."),
    dict(id="SUP-8011", customer_id="C016", order_id="NS-1078", subject="NovaBand Fit strap broke",
         description="Strap snapped at the lug after one week.",
         priority="NORMAL", status="RESOLVED", created_at="2026-08-22",
         resolution="Return RET-4002 created; replacement strap dispatched."),
    dict(id="SUP-8012", customer_id="C018", order_id="NS-1080", subject="NovaCam 2K autofocus hunting",
         description="Webcam autofocus keeps hunting in low light.",
         priority="LOW", status="OPEN", created_at="2026-08-25",
         resolution=""),
    dict(id="SUP-8013", customer_id="C010", order_id="NS-1055", subject="Dented power bank casing",
         description="One of two power banks arrived dented.",
         priority="NORMAL", status="ESCALATED", created_at="2026-08-17",
         resolution="Escalated; return RET-4004 refund processing."),
    dict(id="SUP-8014", customer_id="C011", order_id="NS-1056", subject="NovaPods Pro ANC weak",
         description="Noise cancellation much weaker than expected.",
         priority="LOW", status="RESOLVED", created_at="2026-08-19",
         resolution="Advised on ear-tip sizing; customer satisfied after switching tips."),
    dict(id="SUP-8015", customer_id="C019", order_id="NS-1065", subject="Cancel processing order NS-1065",
         description="Customer wants to cancel before dispatch.",
         priority="URGENT", status="IN_PROGRESS", created_at="2026-09-03",
         resolution=""),
]
