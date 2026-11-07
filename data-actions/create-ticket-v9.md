# Data action: Create Ticket (v9)

Clone **Create Ticket (v8)** and change only the contracts and the response handling.
The goal: every 2xx response from the ticketing system tells the script in one string
whether it succeeded, so the script's If step compares `ticketOutcome` to `CREATED`
and never has to interpret a raw return code.

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
    "ticketOutcome":    { "type": "string" },
    "ticketReturnCode": { "type": "integer" },
    "ticketNumber":     { "type": "string" },
    "ticketMessage":    { "type": "string" }
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

Success template (Velocity):

```
#set($rc = $returnCode)
#if(!$rc || $rc == "")#set($rc = 1)#end
{
  "ticketOutcome": "#if($rc == 0)CREATED#{else}FAILED#end",
  "ticketReturnCode": ${rc},
  "ticketNumber": "${ticketNumber}",
  "ticketMessage": "${message}"
}
```

## Business errors

If the ticketing API returns 4xx for business errors (account on hold, invalid
category), the data action fails and sets no outputs, so the agent sees the timeout
panel rather than the reason. Front such an API with a translation layer that returns
HTTP 200 and a non-zero `returnCode` with a readable `message`.

## Empty description

The script refuses an empty description before calling this action. Keep a server-side
check as well: return code 2, message "Description is required".
