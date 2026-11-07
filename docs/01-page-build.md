# Page build: "Chat Page"

Build order matters a little: create the variables first, then containers, then
components, then bind Visible / Disabled / Click Action.

Where a property label below is marked *(verify)*, the name is from memory rather than
from the current Genesys documentation; the property exists, the label may differ slightly.

## 1. Script properties

Script > Script Properties:

| Property group | Setting |
|---|---|
| Message | Enabled. This is the web messaging (Messenger) channel. |
| Chat | Enable only if the legacy web chat widget is still in use. Otherwise leave off. |
| Data Actions | Enabled, or the Execute Data Action step will not appear. |
| Inbound / Outbound | Off for this script. |

## 2. Variables

Input variables must have **Input** switched on and must be named exactly like the
participant data keys written in the Architect flow (case-sensitive).

| Name | Type | Input | Default | Purpose |
|---|---|---|---|---|
| `fullname` | String | Yes | | From participant data |
| `email` | String | Yes | | From participant data |
| `location` | String | Yes | | From participant data |
| `ticketCategory` | String | No | `Technical fault` | Dropdown |
| `ticketPriority` | String | No | `Normal` | Dropdown |
| `ticketDescription` | String | No | | Multiline input |
| `showForm` | True/False | No | `True` | Form container visibility |
| `isSubmitting` | True/False | No | `False` | Disables Submit while in flight |
| `showPending` | True/False | No | `False` | "Creating ticket…" panel |
| `ticketDone` | True/False | No | `False` | Set by the data action on any 2xx response |
| `ticketCreated` | True/False | No | `False` | Set by the data action |
| `ticketFailed` | True/False | No | `False` | Set by the data action |
| `ticketReturnCode` | Number | No | `99` | 99 = not yet called |
| `ticketNumber` | String | No | | Data action output |
| `ticketMessage` | String | No | | Data action output, human readable |
| `ticketOutcome` | String | No | | `CREATED` or `FAILED`, for the log row |
| `showTimeoutError` | True/False | No | `False` | Set by the Reset action |

Drop the old `ticketStatus` and `InteractionId` variables once the new ones are wired.
`InteractionId` was holding the ticket number; `ticketNumber` replaces it.

## 3. Layout

One vertical stack container for the page, children as below. Use Width = Stretch on
the containers and Margin for breathing room instead of empty text rows.

```
Vertical stack (page)
├─ Horizontal stack  "Customer banner"           background colour: light accent
│   ├─ Read-only text  {{fullname}}               bold, larger
│   └─ Read-only text  {{Scripter.Media Type}} · {{Scripter.Queue Name}}   (verify built-in names in your org)
├─ Vertical stack  "Customer details"             border on
│   ├─ Read-only text  "Customer details"         label style
│   ├─ Horizontal stack: Read-only "Full name"  | Read-only {{fullname}}
│   ├─ Horizontal stack: Read-only "Email"      | Read-only {{email}}      | Button "Copy"  → Scripter.Copy to Clipboard (email)
│   ├─ Horizontal stack: Read-only "Location"   | Read-only {{location}}
│   └─ Horizontal stack: Read-only "Interaction"| Read-only {{Scripter.Interaction ID}} | Button "Copy" → Scripter.Copy to Clipboard
├─ Vertical stack  "Create ticket"                Visible = showForm
│   ├─ Read-only text  "Create ticket"
│   ├─ Horizontal stack
│   │   ├─ Dropdown  Label "Category"  Value = ticketCategory   Options: Billing | Technical fault | Account | Other
│   │   └─ Dropdown  Label "Priority"  Value = ticketPriority   Options: Low | Normal | High
│   ├─ Text input   Label "Description"  Value = ticketDescription  Multiline = Yes  Requires Value = True  Height ≈ 120px
│   │                Placeholder: "What the customer reported, what you checked, what they need next."
│   └─ Horizontal stack
│       └─ Button  "Create ticket"   Click Action = custom action "Create Ticket"   Disabled = isSubmitting
├─ Vertical stack  "Pending"                       Visible = showPending      background: amber tint
│   ├─ Markdown   **Creating ticket…**  Sending to the ticketing system. This usually takes a few seconds.
│   └─ Button  "Cancel and try again"   Click Action = custom action "Reset Ticket Form"
├─ Vertical stack  "Created"                       Visible = ticketCreated    background: green tint
│   ├─ Markdown   **Ticket created**
│   ├─ Read-only text  {{ticketNumber}}            large, monospace if available
│   ├─ Read-only text  "Logged to Chat Logs. Give the customer the number and the expected response time."
│   └─ Button  "Create another ticket"  Click Action = "Reset Ticket Form"
├─ Vertical stack  "Failed"                        Visible = ticketFailed     background: red tint
│   ├─ Markdown   **Ticket not created**
│   ├─ Read-only text  {{ticketMessage}}
│   ├─ Read-only text  "Fix the issue and submit again. The failed attempt has been logged."
│   └─ Button  "Back to form"   Click Action = "Reset Ticket Form"
└─ Vertical stack  "Timed out"                     Visible = showTimeoutError background: red tint
    └─ Markdown   **No reply from the ticketing system.** Try again. If it keeps happening, raise it with the service desk and create the ticket manually.
```

## 4. Property bindings, exactly

* **Visible** (Layout group): click *Select Variable* and pick the True/False variable.
  A True/False Expression is also allowed if you prefer to avoid the helper booleans.
* **Disabled** (Advanced group): bind the True/False variable `isSubmitting`. True disables.
* **Click Action** on buttons: *Custom actions > Create Ticket* / *Reset Ticket Form*.
* **Requires Value = True** on the description input shows the required marker. It does
  not block the button on its own, which is why the action also checks the value
  (see `02-create-ticket-action.md`).
* **Change Action** (Advanced group) on the description input is optional: point it at a
  tiny custom action that sets `showTimeoutError = False` and `ticketFailed = False`, so
  old error panels disappear as soon as the agent starts editing.

## 5. Page load

Page > Load Action: custom action "Reset Ticket Form". This guarantees a clean state when
the script opens on a new interaction, including after a transfer.

## 6. Limits to keep in mind

* Scripts cannot read a JSON array from a data action output. Return flat fields only.
* Data actions are not executed in Script Preview; output variables stay empty there.
  Test on a real interaction in a test queue.
