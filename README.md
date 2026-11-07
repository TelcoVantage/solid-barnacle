# Chat Ticket Script (Genesys Cloud)

Modernisation of the agent script used on the chat / web messaging channel: the
"User's inputs" page with the Create Ticket form, and the custom action behind the
Submit button. The deliverable is a `.script` file that imports through the admin GUI.

| Path | What it holds |
|---|---|
| `scripts/chat-ticket-script.script` | The importable script. Replace the two data action ID placeholders first (see below). |
| `tools/build_script.py` | Generator that produces the `.script` file and validates every reference in it. |
| `mockup/agent-ticket-page.html` | Visual mockup of the page with build notes. Open it in a browser. |
| `docs/01-page-build.md` | What is on the page and how each component is bound. Use it when editing the script in the editor. |
| `docs/02-create-ticket-action.md` | The three custom actions step by step. |
| `docs/03-flow-and-queue-wiring.md` | Architect inbound message flow, participant data keys, queue assignment, Messenger. |
| `docs/04-missed-message-visibility.md` | Native options for surfacing customer messages the agent has not answered: desktop settings, alert rules, and a Trigger + Workflow watchdog. |
| `data-actions/` | Input/output contracts and response template for the two data actions. |

## Import in three steps

1. **Create the two data actions** in the target org and copy their IDs. In Admin >
   Integrations > Actions, open the action; the ID is the last segment of the browser
   URL. You need:
   * `Create Ticket (v9)`: see `data-actions/create-ticket-v9.md` for its contracts.
   * `Insert Data Table Row (Chat Logs)`: generated from the data table in
     `data-actions/chat-logs-table.md`.
2. **Put the IDs into the file.** Either run the generator:

   ```bash
   python3 tools/build_script.py \
     --create-ticket-action-id 00000000-0000-0000-0000-000000000000 \
     --chat-logs-action-id    00000000-0000-0000-0000-000000000000 \
     -o scripts/chat-ticket-script.script
   ```

   or open `scripts/chat-ticket-script.script` in a text editor and replace
   `REPLACE_WITH_CREATE_TICKET_DATA_ACTION_ID` and `REPLACE_WITH_CHAT_LOGS_DATA_ACTION_ID`.
   The generator prints `OK: all references resolve` when nothing is left unresolved.
3. **Import.** Admin > Digital and Telephony > Interaction Assets > Scripts > **Import**
   (older menus: Admin > Contact Center > Scripts). Pick a division, select the file,
   click Import. To overwrite the existing script instead, select it and click
   **Replace**. Open the script, check the two Execute Data Action steps show the
   actions and their mappings, then **Publish**.

Permissions needed: all permissions under *Scripter > Script*, plus *Scripter >
Published Script > Add* and *View*, with user-level (not group-inherited) access to
the org.

## How the file was built

The Genesys script format is not documented, so every JSON shape in the generator was
copied from real exports published by Genesys and its partners (the Genesys Cloud
blueprints, the Terraform provider test data, and partner integration repos). The
generator checks that each component's property set matches those exports and that
every variable, custom action and data action reference resolves. It has not been
imported into a live org from this repository; if the importer rejects it, the error
message names the path in the file, and `tools/build_script.py` is where to fix it.

After the first successful import, export the published script from the GUI and commit
that export over `scripts/chat-ticket-script.script`, so the file in git is always the
editor's own output.
