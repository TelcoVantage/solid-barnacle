# Custom actions

All three actions below are already in `scripts/chat-ticket-script.script`. This page
explains what they do so they can be reviewed or edited in the Script Editor.

## Why the current action misbehaves

The current action is:

1. Execute Data Action **Create Ticket (v8)**
2. Wait Until `ticketReturnCode` Equals 0
   * Execute Data Action **Insert Data Table Row (Chat Logs)**

Three consequences:

* A non-zero return code never satisfies the Wait Until. The action sits waiting, the
  page shows a blank `{{ticketStatus}}`, and the agent clicks Submit again.
* An HTTP failure or timeout of the data action never sets any output, which looks
  identical to "nothing happened".
* Failed attempts are never written to Chat Logs, so there is no audit trail.

Data action steps inside a custom action run in order and each one completes before
the next starts, so the Wait Until is not needed. The redesign uses an **If** step on
the outcome instead, which handles both results.

## Custom action: Create Ticket

```
If  ticketDescription  Not Equal  ""
├─ then
│   1. Set Variable  isSubmitting = True
│   2. Set Variable  ticketCreated = False
│   3. Set Variable  ticketFailed = False
│   4. Set Variable  showTimeoutError = False
│   5. Set Variable  ticketOutcome = ""
│   6. Set Variable  showForm = False
│   7. Set Variable  showPending = True
│   8. Execute Data Action  Create Ticket (v9)          (mappings below)
│   9. If  ticketOutcome  Not Equal  "CREATED"
│       ├─ then  Set Variable  ticketFailed = True
│       └─ else  Set Variable  ticketCreated = True
│  10. Execute Data Action  Insert Data Table Row (Chat Logs)   runs for both outcomes
│  11. Set Variable  showPending = False
│  12. Set Variable  isSubmitting = False
└─ else
    1. Set Variable  ticketMessage = "Description is required."
    2. Set Variable  ticketCreated = False
    3. Set Variable  ticketFailed = True
```

If the Create Ticket call fails at HTTP level (timeout, 5xx), its outputs are never
set. The page then stays on the amber "Creating ticket…" panel, and the agent's
**Cancel and try again** button runs *Cancel Ticket* below.

### Step 8 input mapping

| Data action input | Script value |
|---|---|
| `fullname` | Variable `fullname` |
| `email` | Variable `email` |
| `location` | Variable `location` |
| `category` | Variable `ticketCategory` |
| `priority` | Variable `ticketPriority` |
| `description` | Variable `ticketDescription` |
| `conversationId` | `Scripter.Interaction ID` |
| `agentId` | `Scripter.Agent ID` |

### Step 8 output mapping

| Data action output | Script variable |
|---|---|
| `ticketOutcome` | `ticketOutcome` (`CREATED` or `FAILED`) |
| `ticketReturnCode` | `ticketReturnCode` |
| `ticketNumber` | `ticketNumber` |
| `ticketMessage` | `ticketMessage` |

### Step 10 input mapping (Chat Logs row)

| Data action input | Script value |
|---|---|
| `key` | `Scripter.Interaction ID` |
| `userId` | `Scripter.Agent ID` |
| `conversationId` | `Scripter.Interaction ID` (the old `participantId` input was being fed the ticket number; stop that) |
| `ticketNumber` | `ticketNumber` |
| `outcome` | `ticketOutcome` |
| `returnCode` | `ticketReturnCode` |
| `message` | `ticketMessage` |
| `category` | `ticketCategory` |
| `priority` | `ticketPriority` |
| `customerEmail` | `email` |

The input names must match the data action's input contract exactly. If your Chat
Logs table keeps different column names, either rename the columns to these or change
the keys in `tools/build_script.py` (`log_row`) and rebuild.

If an interaction can create more than one ticket, the data table key must be unique
per row: use the ticket number as the key, or concatenate interaction ID and ticket
number in the data action's request template.

## Custom action: Reset Ticket Form

Runs on page load and from the "Back to form" and "Create another ticket" buttons.

| # | Set Variable |
|---|---|
| 1 | `isSubmitting` = False |
| 2 | `showPending` = False |
| 3 | `ticketCreated` = False |
| 4 | `ticketFailed` = False |
| 5 | `showTimeoutError` = False |
| 6 | `showForm` = True |
| 7 | `ticketReturnCode` = 99 |
| 8 | `ticketOutcome` = "" |
| 9 | `ticketMessage` = "" |
| 10 | `ticketNumber` = "" |

## Custom action: Cancel Ticket

Identical to Reset Ticket Form except step 5 sets `showTimeoutError` = True, which
shows the "No reply from the ticketing system" panel above the form.
