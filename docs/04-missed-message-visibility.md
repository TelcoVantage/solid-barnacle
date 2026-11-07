# Making unanswered customer messages visible (native only)

Problem: a customer sends a message mid-conversation, the agent is on another
interaction or looking elsewhere, and nothing escalates. Genesys Cloud has no trigger
topic for "customer message received" and the script has no message events, so there
is no single switch. Three native layers, cheapest first.

## Layer 1: agent desktop settings (no build, do this first)

| Setting | Where | Effect |
|---|---|---|
| Desktop notifications on | Agent: Preferences > Notifications (web app) or the Genesys Cloud desktop app / browser extension | OS-level pop-up with the customer's name when a message interaction alerts or receives a message while the tab is not focused |
| Sounds on, volume up | Preferences > Notifications > Interaction Notification Volume | Audible cue. Note: Genesys does not play the sound when that conversation is already the focused tab |
| Auto-answer messages | Admin > Contact Center > Queues > (queue) > Media settings, or per-user auto-answer | Removes the alerting phase where a message can time out unseen |
| Lower message utilization | Admin > Contact Center > Utilization (org or per agent): Message max 2 to 3 for a mixed-skill team | Fewer concurrent conversations is the single biggest reducer of missed replies |
| Interrupt rules | Same Utilization page | Decide whether a new message may interrupt a call; if it may, agents must be trained on the roster indicator |

The interaction roster already highlights a conversation with an unread customer
message and shows the count. Agents who park Genesys in a background tab lose that
cue, which is why the desktop app or browser extension matters.

## Layer 2: supervisor visibility (no build)

* **Performance > Queues Activity > (queue) > Interacting list**, sort by Duration.
  Long interacting durations on message media are the first sign of stalled chats.
  More > View Details opens the conversation to read it live.
* **Channel Insights dashboard > Response Times** and the analytics metrics
  `tAgentResponseTime` / `tAverageAgentResponseTime` show who is slow to reply, by
  agent and queue, for coaching and for setting the threshold in Layer 3.
* **Alert rule (Performance > Alerting > Add rule)**: Definition type User, presence
  metric *Interacting*, threshold for example 1200 seconds, in-app notification to the
  agent and the team lead, re-notify every 10 minutes. Coarse (it fires on any long
  interaction, not specifically on an unanswered message) but it is native, takes five
  minutes to set up, and the toast appears inside the agent's own Genesys window.

## Layer 3: unanswered-message watchdog (native build: Trigger + Workflow + data actions)

This is the precise version: "customer's last message is older than N minutes and the
agent has not replied since". Everything below is Genesys-native; nothing runs outside
the org.

### Components

1. **Trigger** (Admin > Architect > Triggers): topic
   `v2.detail.events.conversation.{id}.user.start`, match criteria `mediaType` equals
   `message`. Target: the workflow below. Pass `conversationId`, `participantId`,
   `userId`, `queueId` as flow inputs.
2. **Data action A: Get Message Conversation** (Genesys Cloud Data Actions integration):
   `GET /api/v2/conversations/messages/${input.conversationId}`. Success template
   returns flat fields the flow can use: `state` of the agent participant,
   `lastCustomerMessageTime`, `lastAgentMessageTime` (latest `messageTime` of inbound
   and outbound messages respectively), and `customerParticipantId`.
3. **Workflow** (Architect > Workflows) "Message Response Watchdog":

   ```
   Loop  (max 60 iterations)
   ├─ Wait  60 seconds
   ├─ Call Data Action A
   ├─ Decision  agent participant state != connected        → Exit loop (conversation ended or transferred)
   ├─ Decision  lastCustomerMessageTime > lastAgentMessageTime
   │            AND DiffSeconds(Now, lastCustomerMessageTime) >= Flow.thresholdSeconds
   │            AND Flow.alreadyEscalated == false
   │   └─ then  run the escalation of choice (below), set Flow.alreadyEscalated = true
   └─ Decision  lastAgentMessageTime > lastCustomerMessageTime → set Flow.alreadyEscalated = false
   ```

   `thresholdSeconds` starts at 180 for web messaging; tune it from the Channel Insights
   response-time data.
4. **Escalation, pick one or stack them** (all native Genesys Cloud APIs, each is one
   more data action):

   | Escalation | Data action | Who sees it |
   |---|---|---|
   | Agentless email to the team lead or a shared mailbox | `POST /api/v2/conversations/emails/agentless` | Supervisors |
   | Agentless SMS to the agent's mobile | `POST /api/v2/conversations/messages/agentless` | The agent, even away from the desk |
   | Move the conversation to an "Escalations" queue staffed by team leads | `POST /api/v2/conversations/${conversationId}/participants/${participantId}/replace` with `queueId` | Re-alerts with sound and screen pop; strongest signal |
   | Create a Workitem in a supervisor workbin | Workflow *Create Task* action | Supervisors, with an audit trail |

   Recommended stack: at threshold send the agentless email (silent, cheap); at 2x
   threshold move the conversation to the Escalations queue so a human picks it up.

### Caveats

* The data action success template needs the latest inbound and outbound message
  times. Genesys data actions cannot index "last element" reliably in every org, so
  the usual approach is to return the message time arrays joined as strings and take
  the last item in Architect with `GetAt(Split(...), Count-1)`. Test this in the
  action's Test tab against a real conversation before wiring the flow.
* The trigger fires per agent connect, so a transferred conversation starts a second
  watchdog. The state check in the loop makes the old one exit on its next tick.
* A workflow running for the life of a long async conversation costs flow minutes; the
  60-iteration cap bounds it at one hour. Raise the Wait to 120 seconds if conversations
  are long-lived.
* Messaging inactivity handling (Admin > Message > Inactivity) is for the *customer*
  going silent, not the agent. It will not help here; do not spend time on it.

### What the script can and cannot do

The Script Editor has no message events and no timers, so the ticket script cannot
show a "customer waiting" cue on its own. If you want the agent-facing cue inside the
script page, the watchdog can `Set Participant Data` `unansweredSince=<time>` and the
agent can press a *Refresh* button bound to the `Scripter.Refresh Input Variables`
action, but that still needs the agent to act. The in-app alert toast from Layer 2 or
the queue move from Layer 3 is the reliable agent-facing signal.
