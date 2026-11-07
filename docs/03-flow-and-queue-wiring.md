# Flow and queue wiring

## Where the three input values come from

Script input variables are populated from participant data attributes with the same
name. The chain is:

```
Messenger (website)             Architect inbound message flow         Script
customAttributes  ─────────────▶ Get/Set Participant Data  ────────────▶ Input variables
  fullname, email, location       keys: fullname, email, location         fullname, email, location
```

### Option A: pre-chat form on the site

If the customer fills a form before chatting, the website sets the values before
opening Messenger:

```js
Genesys("command", "Database.set", {
  messaging: {
    customAttributes: {
      fullname: form.fullname,
      email: form.email,
      location: form.location
    }
  }
});
```

These arrive as participant data on the conversation. In the inbound message flow,
no extra step is required for the script to see them, but it is safer to normalise
them explicitly with **Set Participant Data** so a missing attribute becomes an empty
string rather than an unset variable.

### Option B: collected by a bot

If a digital bot flow asks for name, email and location, store the slot values with
**Set Participant Data** in the bot flow (keys `fullname`, `email`, `location`) before
the transfer to queue. The inbound message flow runs before the bot collects anything,
so do not try to read them in the inbound flow itself.

### Option C: authenticated customer

For authenticated Messenger sessions, call a data action in the inbound message flow
(customer lookup by the authenticated identity), then **Set Participant Data** with the
three keys.

In all three cases the key names are case-sensitive and must match the script
variable names exactly.

## Assigning the script

Either:

* **Queue default script**: Admin > Contact Center > Queues > (queue) > General >
  Default scripts, choose this script for the Message media type. Simplest and
  survives flow changes.
* **Set Screen Pop** in the inbound message flow, which also lets you map flow
  variables straight onto the script's input variables. Use this when the values are
  only available in the flow.

## Messenger settings that touch this page

* **Attachments / file upload** in the Messenger configuration lets the customer send
  files during the conversation. If the ticket needs the customer's screenshot, enable
  it there and have the agent reference the attachment in the description; the script
  itself does not handle files.
* Set the Messenger deployment's **Customer Attributes** (if used) with the same three
  key names.

## Test checklist

1. Start a messaging conversation from a test page that sets the three attributes.
2. Route to a test queue that has this script as its Message default script.
3. Confirm the banner and details card show the values, not empty text.
4. Submit with an empty description: red panel with "Description is required", row in
   Chat Logs with outcome FAILED.
5. Submit a valid ticket: amber panel, then green panel with the ticket number, row in
   Chat Logs with outcome CREATED.
6. Point the data action at an unreachable host temporarily: amber panel stays, Cancel
   returns to the form with the timeout message.
7. Transfer the interaction to another agent: page opens clean (Reset on page load).
