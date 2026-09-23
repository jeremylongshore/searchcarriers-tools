---
name: sc-alerts
description: Explain SearchCarriers alert-feed availability or format a caller-supplied carrier event for delivery.
argument-hint: "[event JSON] [--route slack|telegram|email|webhook] [--destination value]"
---

# /sc-alerts — Carrier Event Compatibility and Formatting

The published SearchCarriers API does not expose an alert-feed route. Do not
query or retry the former assumed endpoint.

When invoked without an event, call `get_alerts` and present its structured
`endpoint_unavailable` result with these supported alternatives:

1. Use SearchCarriers' configured notification channel.
2. Run `monitor_compliance` for a point-in-time DOT review.
3. Pass a validated external event to this command for formatting.

When the user supplies an event and a route, validate that the object includes a
DOT number or carrier name plus a summary/message. Then call `route_alert` with
the event, channel, and destination. Return the formatted payload for the user's
external delivery system. Never claim the plugin sent the message.
