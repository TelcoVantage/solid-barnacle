# Exported scripts

Place the `.script` export here, for example `chat-ticket-script.script`.

The file is JSON produced by **Scripts > Export** in the Genesys Cloud admin GUI. It
imports through **Scripts > Import** (new script) or **Replace** (overwrite the selected
script) in any org where the referenced data actions exist.

Before importing into another org:

1. Create the data actions `Create Ticket (v9)` and `Insert Data Table Row (Chat Logs)`
   and the `Chat Logs` data table.
2. Import the script.
3. Open the custom actions **Create Ticket** and **Reset Ticket Form**, re-select the two
   data actions and check the input/output mappings.
4. Publish the script and attach it to the queue's Message default script.

Commit a new export after every published change, with the script version in the
commit message, so this folder is the source of truth.
