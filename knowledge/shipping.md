---
title: Shipping Policy
document_type: policy
---

# Shipping Policy

NovaStore ships across Nepal. Delivery times are estimates and depend on weather and
road conditions. **Never promise an exact delivery time** unless the order record
contains an explicit estimated delivery date.

## Delivery estimates

| Zone | Typical time |
| --- | --- |
| Kathmandu Valley | 1–3 business days |
| Other major cities (Pokhara, Biratnagar, Butwal, Dharan, Nepalgunj, Birgunj) | 2–5 business days |
| Remote and hill areas | 3–8 business days |

## Delays

Monsoon rain, landslides, festival periods and highway closures can extend delivery.
When an order is marked `delayed`, the order record carries a `delay_reason` and an
updated `estimated_delivery`. Share those exact values with the customer.

## Order statuses

- `processing` – payment confirmed, item being prepared, not yet shipped
- `shipped` – handed to courier, has left the origin hub
- `in_transit` – moving between hubs, `current_location` is set
- `delayed` – in transit but behind schedule, `delay_reason` explains why
- `delivered` – handed to the customer, `delivered_at` is set
- `cancelled` – order cancelled, nothing shipped
- `return_requested` – delivered, and the customer has opened a return

## Tracking

Customers can track any order on the `/orders` page by entering the order ID
(for example `NS-1077`), or ask NovaCare "where is NS-1077".
