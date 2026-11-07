# Data action: Create Ticket (v9)

Clone **Create Ticket (v8)** and change only the contracts and the response handling.
The goal: every 2xx response from the ticketing system sets `ticketDone = true` and
tells the script whether it succeeded, so the script never has to interpret a raw
return code.

## Input contract

```json
{
  "type": "object",
  "properties": {
    "fullname":       { "type": "string" },
    "email":          { "type": "string" },
    "location":       { "type": "string" },
    "category":       { "type": "string" },
    "priority":       { "type": "string" },
    "description":    { "type": "string" },
    "conversationId": { "type": "string" },
    "agentId":        { "type": "string" }
  },
  "additionalProperties": true
}
```

## Output contract

```json
{
  "type": "object",
  "properties": {
    "ticketDone":       { "type": "boolean" },
    "ticketCreated":    { "type": "boolean" },
    "ticketFailed":     { "type": "boolean" },
    "ticketReturnCode": { "type": "integer" },
    "ticketNumber":     { "type": "string" },
    "ticketMessage":    { "type": "string" },
    "ticketOutcome":    { "type": "string" }
  },
  "additionalProperties": true
}
```

## Request

Keep the v8 request URL, method and headers. Request body template (adjust field names
to the ticketing API):

```
{
  "requester": { "name": "${input.fullname}", "email": "${input.email}", "location": "${input.location}" },
  "category": "${input.category}",
  "priority": "${input.priority}",
  "description": "${input.description}",
  "externalReference": "${input.conversationId}",
  "createdBy": "${input.agentId}",
  "source": "genesys-messaging"
}
```

## Response: translation map and success template

Translation map (JSONPath against the ticketing API response; adjust the right-hand
paths to the real payload):

| Key | JSONPath |
|---|---|
| `returnCode` | `$.returnCode` |
| `ticketNumber` | `$.ticketNumber` |
| `message` | `$.message` |

Success template (Velocity). This is where the booleans are derived:

```
#set($rc = $returnCode)
#if(!$rc || $rc == "")#set($rc = 1)#end
{
  "ticketDone": true,
  "ticketReturnCode": ${rc},
  "ticketNumber": "${ticketNumber}",
  "ticketMessage": "${message}",
  "ticketCreated": #if($rc == 0)true#{else}false#end,
  "ticketFailed":  #if($rc == 0)false#{else}true#end,
  "ticketOutcome": "#if($rc == 0)CREATED#{else}FAILED#end"
}
```

## Empty description guard

If the ticketing API accepts an empty description, reject it before the call. The
cleanest place is the API itself. If that is not possible, add a validation check in
whatever middleware fronts the ticketing system and return:

```json
{ "returnCode": 2, "ticketNumber": "", "message": "Description is required" }
```

with HTTP 200, so the script gets a red panel rather than a hung request.

## HTTP failures

A 4xx/5xx or a timeout fails the data action and sets no outputs. The script covers
that with the amber "Creating ticket…" panel and its Cancel button. If the ticketing API
returns 4xx for business errors, front it with a translation layer that returns 200 and
a non-zero `returnCode`, or the agent will see the timeout panel instead of the reason.
