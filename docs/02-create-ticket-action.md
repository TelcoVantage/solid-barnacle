# Custom actions

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
* Failed attempts are never written to Chat Logs, so there is no audit trail of what
  the agent tried.

The fix is to make the data action always set a `ticketDone` flag and its own
`ticketCreated` / `ticketFailed` booleans (see `data-actions/create-ticket-v9.md`), wait
on `ticketDone`, and let the page panels show themselves from the booleans.

## Custom action: Create Ticket

| # | Step | Configuration |
|---|---|---|
| 1 | Set Variable | `isSubmitting` = True |
| 2 | Set Variable | `showPending` = True |
| 3 | Set Variable | `ticketDone` = False, `ticketCreated` = False, `ticketFailed` = False, `showTimeoutError` = False, `ticketReturnCode` = 99 (one Set Variable step per variable if the editor only allows one assignment per step) |
| 4 | Data Actions.Execute Data Action | Category: your integration. Action: **Create Ticket (v9)**. See input and output mapping below. |
| 5 | Wait Until | `ticketDone` Equals True |
| 5a | Data Actions.Execute Data Action (nested in 5) | **Insert Data Table Row (Chat Logs)**. Mapping below. |
| 5b | Set Variable (nested in 5) | `showForm` = False |
| 5c | Set Variable (nested in 5) | `showPending` = False |
| 5d | Set Variable (nested in 5) | `isSubmitting` = False |

### Step 4 input mapping

| Data action input | Script value |
|---|---|
| `fullname` | Variable `fullname` |
| `email` | Variable `email` |
| `location` | Variable `location` |
| `category` | Variable `ticketCategory` |
| `priority` | Variable `ticketPriority` |
| `description` | Variable `ticketDescription` |
| `conversationId` | Variable `Scripter.Interaction ID` |
| `agentId` | Variable `Scripter.Agent ID` |

### Step 4 output mapping

| Data action output | Script variable |
|---|---|
| `ticketDone` | `ticketDone` |
| `ticketReturnCode` | `ticketReturnCode` |
| `ticketNumber` | `ticketNumber` |
| `ticketMessage` | `ticketMessage` |
| `ticketCreated` | `ticketCreated` |
| `ticketFailed` | `ticketFailed` |
| `ticketOutcome` | `ticketOutcome` |

### Step 5a input mapping (Chat Logs row)

| Data table column | Script value |
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

If an interaction can create more than one ticket, the data table key must be unique
per row. Use the ticket number as the key, or `Scripter.Interaction ID` plus the ticket
number concatenated in the data action's request template.

## Custom action: Reset Ticket Form

Runs on page load and from every "Back to form" / "Cancel" / "Create another" button.

| # | Step | Configuration |
|---|---|---|
| 1 | Set Variable | `isSubmitting` = False |
| 2 | Set Variable | `showPending` = False |
| 3 | Set Variable | `ticketCreated` = False |
| 4 | Set Variable | `ticketFailed` = False |
| 5 | Set Variable | `showForm` = True |
| 6 | Set Variable | `ticketDone` = False |
| 7 | Set Variable | `ticketReturnCode` = 99 |

For the **Cancel and try again** button only, add a first step `showTimeoutError` = True
by giving it its own action "Cancel Ticket" that sets that flag and then runs the steps
above. Page load and the other buttons use the plain Reset action, which leaves
`showTimeoutError` False.

## Guarding against an empty description

The Script Editor does not offer an if/else step inside custom actions, so the empty
check lives in the data action instead: the request template returns return code 2 and
message "Description is required" when `description` is blank, without calling the
ticketing API (see `data-actions/create-ticket-v9.md`). The agent sees it in the red
panel like any other failure.

If your org's editor does expose a conditional step, move the check there and skip the
data action call.
