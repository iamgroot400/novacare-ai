---
title: Refund Policy
document_type: policy
---

# Refunds

NovaStore is fictional and all transactions in this demo are demonstrations. **No real
banking or payment transaction is ever performed.**

## Return acceptance is not refund completion

When a return request is created it does **not** immediately refund anything. The
return moves through a lifecycle:

```
REQUESTED  ->  APPROVED  ->  ITEM_RECEIVED  ->  REFUND_PROCESSING  ->  REFUNDED
```

A return can also end in `REJECTED` if the item is not eligible or arrives damaged
beyond policy.

| Status | Meaning |
| --- | --- |
| REQUESTED | Customer opened the return, awaiting review |
| APPROVED | Return accepted, customer should ship the item back |
| ITEM_RECEIVED | Warehouse has the item and is inspecting it |
| REFUND_PROCESSING | Refund is being prepared through the original payment method |
| REFUNDED | Demo refund marked complete (no real money moved) |

## Timeframes (demo)

Inspection typically takes 2–4 business days after the item is received. Refund
processing to the original payment method (Khalti, eSewa, IME Pay, ConnectIPS) is
shown as 3–5 business days in the demo. Cash on Delivery orders are refunded to a
wallet or bank account provided by the customer.

## What NovaCare can and cannot do

- Can: create a return record, explain where a refund is in the lifecycle.
- Cannot: issue money, change a refund status, or promise a refund date beyond the
  demo estimate.
