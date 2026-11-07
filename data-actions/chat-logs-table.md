# Data table: Chat Logs

Admin > Contact Center > Data Tables. Suggested columns (the data action **Insert Data
Table Row (Chat Logs)** is regenerated from the table definition, so add the columns
first, then re-save the data action to pick up the new inputs).

| Column | Type | Notes |
|---|---|---|
| `key` | String | Row key. Interaction ID for one ticket per chat; ticket number if several. |
| `userId` | String | `Scripter.Agent ID` |
| `conversationId` | String | `Scripter.Interaction ID` |
| `ticketNumber` | String | Empty on failure |
| `outcome` | String | `CREATED` or `FAILED` |
| `returnCode` | Number | Raw return code from the ticketing system |
| `message` | String | Human readable message from the ticketing system |
| `category` | String | |
| `priority` | String | |
| `customerEmail` | String | |

Keeping failures in the same table is what makes the log useful for supervisors:
filter on `outcome = FAILED` to spot a broken integration before agents report it.
