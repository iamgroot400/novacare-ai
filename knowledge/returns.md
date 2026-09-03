---
title: Return Policy
document_type: policy
---

# Return Policy

The demo return system uses a fixed reference date of **2026-09-03** (`DEMO_DATE`) so
eligibility never changes with the real calendar.

## Standard return window

1. The standard return period is **14 calendar days after the delivery date**.
2. The order must have been **delivered** (`status = delivered` with a `delivered_at`
   date). Orders that are `processing`, `shipped`, `in_transit`, `delayed` or
   `cancelled` cannot be returned.
3. If the item is **outside the 14-day window**, the standard return is denied.
   Warranty support may still apply — see `warranty.md`.
4. A return request never issues real money. The MVP only creates a return/RMA
   record (`RET-XXXX`).

## Worked examples

- **NS-1042** – NovaPods Pro, delivered 2026-08-26. On 2026-09-03 that is 8 days
  after delivery, so it **is eligible**.
- **NS-1033** – NovaSound Mini, delivered 2026-08-10. On 2026-09-03 that is 24 days
  after delivery, so it is **not eligible** for a standard return. Warranty support
  is still available.

## How a return is created

1. NovaCare checks eligibility with `check_return_eligibility`.
2. If eligible, NovaCare asks the customer to confirm the return and its reason.
3. Only after the customer confirms does `create_return_request` run and a
   `RET-XXXX` record get created with status `REQUESTED`.

## Refund lifecycle

See `refunds.md`. A created return does **not** mean a completed refund.
