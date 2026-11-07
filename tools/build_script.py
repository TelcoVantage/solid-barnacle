#!/usr/bin/env python3
"""Build the Chat Ticket Script as a Genesys Cloud .script import file.

The JSON shapes used here are copied from real Script Editor exports (component
property names, variable records, custom action blocks, bridge.bridge data action
steps, if/else conditions). Run with --check to verify every reference resolves.

    python3 tools/build_script.py \
        --create-ticket-action-id  <data action GUID> \
        --chat-logs-action-id      <data action GUID> \
        --name "Chat Ticket Script v2" \
        -o scripts/chat-ticket-script.script

Without the two --*-action-id flags the file is written with placeholder IDs that
you can find-and-replace before importing.
"""
import argparse
import json
import re
import sys
import uuid

NS = uuid.UUID("7d1c2f4e-5b6a-4c3d-9e8f-0a1b2c3d4e5f")  # stable ids across rebuilds
FONT = 'Arial, "Helvetica Neue", Helvetica, sans-serif'

PLACEHOLDER_CREATE = "REPLACE_WITH_CREATE_TICKET_DATA_ACTION_ID"
PLACEHOLDER_LOGS = "REPLACE_WITH_CHAT_LOGS_DATA_ACTION_ID"


def gid(name):
    u = uuid.uuid5(NS, name).hex
    return str(uuid.UUID(u[:12] + "4" + u[13:]))  # stable, and version-4 shaped like editor ids


# ---------- property helpers (shapes copied from exports) ----------
def t_bool(v): return {"typeName": "boolean", "value": v}
def t_int(v): return {"typeName": "integer", "value": v}
def t_text(v): return {"typeName": "text", "value": v}
def t_itext(v): return {"typeName": "interpolatedText", "value": v}
def t_null(): return {"typeName": "null"}
def t_color(hexv): return {"typeName": "color", "value": hexv}
def t_spacing(v): return {"typeName": "spacing", "value": v}
def t_var(vid=None): return {"typeName": "variable", "value": vid} if vid else {"typeName": "variable"}
def t_action(action_id=None):
    return {"typeName": "action", "value": {"actionName": action_id, "actionArgumentValues": []} if action_id else {}}
def size_auto(): return {"typeName": "sizing", "value": {"sizeType": "auto"}}
def size_stretch(pct=100): return {"typeName": "sizing", "value": {"sizeType": "stretch", "size": pct}}
def size_px(px): return {"typeName": "sizing", "value": {"sizeType": "pixels", "size": px}}
def border(width=0, color="000000"):
    return {"typeName": "border", "value": {"width": width, "style": "solid", "color": color}}


def base_layout(width=None, height=None, margin=None, visible=None):
    return {
        "margin": t_spacing(margin if margin is not None else [5, 5, 5, 5]),
        "alignment": {"typeName": "alignment", "value": "start"},
        "width": width or size_auto(),
        "height": height or size_auto(),
        "visible": t_var(visible),
        "preserveLayoutLocation": t_bool(False),
    }


def container(kind, children, *, width=None, height=None, margin=None, padding=10,
              visible=None, bg=None, border_w=0, border_c="000000"):
    props = base_layout(width or size_stretch(), height, margin, visible)
    props.update({
        "backgroundColor": t_color(bg) if bg else t_null(),
        "padding": t_spacing(padding),
        "childArrangement": {"typeName": "childArrangement", "value": "start"},
        "border": border(border_w, border_c),
    })
    return {"type": kind, "properties": props, "children": children}


def vstack(children, **kw): return container("verticalStackContainer", children, **kw)
def hstack(children, **kw): return container("horizontalStackContainer", children, **kw)


def text(value, *, size=12, bold=False, color=None, width=None, margin=None, visible=None,
         justification="left", bg=None):
    props = base_layout(width, None, margin, visible)
    props.update({
        "text": t_itext(value),
        "bold": t_bool(bold), "italic": t_bool(False), "underline": t_bool(False),
        "font": {"typeName": "font", "value": FONT},
        "fontSize": t_int(size),
        "justification": t_text(justification),
        "backgroundColor": t_color(bg) if bg else t_null(),
        "textColor": t_color(color) if color else t_null(),
        "padding": t_spacing(0),
    })
    return {"type": "text", "properties": props}


def text_input(var_id, *, placeholder="", multiline=False, required=False, width=None,
               height=None, disabled=None, visible=None):
    props = base_layout(width, height, None, visible)
    props.update({
        "placeholderText": t_itext(placeholder),
        "validation": {"typeName": "inputValidation"},
        "doesRequireValue": t_bool(required),
        "isMultilineInput": t_bool(multiline),
        "isPasswordInput": t_bool(False),
        "isPasswordToggleVisible": t_bool(False),
        "value": t_var(var_id),
        "changeAction": t_action(),
        "disabled": t_var(disabled),
    })
    return {"type": "input", "properties": props}


def dropdown(var_id, options, *, placeholder="", width=None, required=True, disabled=None, visible=None):
    props = base_layout(width or size_px(220), None, None, visible)
    props.update({
        "placeholderText": t_itext(placeholder),
        "options": {"typeName": "list", "value": [[t_itext(o), t_itext(o)] for o in options]},
        "doesRequireValue": t_bool(required),
        "value": t_var(var_id),
        "changeAction": t_action(),
        "disabled": t_var(disabled),
    })
    return {"type": "dropdown", "properties": props}


def button(label, action_id, *, primary=False, disabled=None, visible=None, width=None):
    props = base_layout(width, None, None, visible)
    props.update({
        "text": t_itext(label),
        "clickAction": t_action(action_id),
        "backgroundColor": t_color("#1f5fbf") if primary else t_null(),
        "textColor": t_color("#ffffff") if primary else t_null(),
        "bold": t_bool(primary), "italic": t_bool(False), "underline": t_bool(False),
        "font": {"typeName": "font", "value": FONT},
        "fontSize": t_int(12),
        "justification": t_text("center"),
        "disabled": t_var(disabled),
    })
    return {"type": "button", "properties": props}


# ---------- custom action step helpers ----------
def set_var(var, value_prop, var_type):
    return {"type": "action", "actionName": "scripter.setVariable", "actionArgumentValues": [{
        "typeName": "variableWithValue",
        "value": {"variable": t_var(var["id"]), "variableTypeName": var_type, "valueOfVariableProperty": value_prop},
    }]}


def set_bool(var, v): return set_var(var, t_bool(v), "boolean")
def set_str(var, v): return set_var(var, t_itext(v), "string")
def set_num(var, v): return set_var(var, t_int(v), "number")


def data_action(action_id, inputs, outputs):
    """inputs: {dataActionInputName: property}, outputs: {dataActionOutputName: scriptVariableId}"""
    return {"type": "action", "actionName": "bridge.bridge", "actionArgumentValues": [{
        "typeName": "bridgeActionArguments",
        "value": {
            "actionName": "custom_-_" + action_id,
            "inputProperty": {"typeName": "objectFields", "value": {"fieldProperties": inputs}},
            "successProperty": {"typeName": "objectFields", "value": {"fieldProperties": {k: t_var(v) for k, v in outputs.items()}}},
            "isHedwigAction": True,
        },
    }]}


def if_not_equal(var, rhs_text, if_block, else_block):
    return {
        "type": "if",
        "condition": {"type": "standard", "leftHandSide": t_var(var["id"]), "operator": "notEqual",
                      "rightHandSide": t_itext(rhs_text)},
        "ifBlock": if_block,
        "elseBlock": else_block,
    }


# ---------- the script ----------
def variable(name, vtype, default, *, input_=False, output=False, description=""):
    return {"id": gid("var:" + name), "name": name, "description": description,
            "type": {"isDynamic": False, "isList": False, "name": vtype},
            "value": default, "input": input_, "output": output}


def build(name, create_id, logs_id):
    V = {}
    for spec in [
        ("fullname", "string", "", True, "Participant data key: fullname"),
        ("email", "string", "", True, "Participant data key: email"),
        ("location", "string", "", True, "Participant data key: location"),
        ("ticketCategory", "string", "Technical fault", False, ""),
        ("ticketPriority", "string", "Normal", False, ""),
        ("ticketDescription", "string", "", False, ""),
        ("showForm", "boolean", True, False, "Create ticket card visible"),
        ("isSubmitting", "boolean", False, False, "Disables Submit while a request is in flight"),
        ("showPending", "boolean", False, False, ""),
        ("ticketCreated", "boolean", False, False, ""),
        ("ticketFailed", "boolean", False, False, ""),
        ("showTimeoutError", "boolean", False, False, ""),
        ("ticketReturnCode", "number", 99, False, "99 = not called yet"),
        ("ticketNumber", "string", "", False, "Output of Create Ticket"),
        ("ticketMessage", "string", "", False, "Output of Create Ticket"),
        ("ticketOutcome", "string", "", False, "CREATED or FAILED"),
    ]:
        n, ty, d, inp, desc = spec
        V[n] = variable(n, ty, d, input_=inp, description=desc)

    A_CREATE, A_RESET, A_CANCEL = gid("act:create"), gid("act:reset"), gid("act:cancel")

    def ref(n): return "{{" + V[n]["id"] + "}}"

    # ---- page ----
    muted, line, ok, bad, warn = "#5b6778", "#d9dfe7", "#1d7a4a", "#b3261e", "#8a5a00"

    def kv_row(label, value_text):
        return hstack([
            text(label, color=muted, width=size_px(120)),
            text(value_text, bold=True),
        ], padding=0, margin=0, border_w=0)

    banner = hstack([
        text(ref("fullname"), size=16, bold=True),
        text("Messaging  ·  {{scripter.queueName}}", size=11, color=muted),
    ], bg="#e8f0fc", padding=10)

    details = vstack([
        text("Customer details", size=13, bold=True),
        kv_row("Full name", ref("fullname")),
        kv_row("Email", ref("email")),
        kv_row("Location", ref("location")),
        kv_row("Interaction", "{{scripter.interactionId}}"),
    ], border_w=1, border_c=line, padding=10)

    form = vstack([
        text("Create ticket", size=13, bold=True),
        hstack([
            vstack([text("Category", size=11, color=muted),
                    dropdown(V["ticketCategory"]["id"], ["Billing", "Technical fault", "Account", "Other"],
                             disabled=V["isSubmitting"]["id"])], width=size_auto(), padding=0, margin=0),
            vstack([text("Priority", size=11, color=muted),
                    dropdown(V["ticketPriority"]["id"], ["Low", "Normal", "High"], width=size_px(160),
                             disabled=V["isSubmitting"]["id"])], width=size_auto(), padding=0, margin=0),
        ], padding=0, margin=0),
        text("Description", size=11, color=muted),
        text_input(V["ticketDescription"]["id"], multiline=True, required=True,
                   placeholder="What the customer reported, what you checked, what they need next.",
                   width=size_stretch(), height=size_px(120), disabled=V["isSubmitting"]["id"]),
        text("Required. Shown to the ticket owner as the opening note.", size=10, color=muted),
        button("Create ticket", A_CREATE, primary=True, disabled=V["isSubmitting"]["id"]),
    ], visible=V["showForm"]["id"], border_w=1, border_c=line, padding=10)

    pending = vstack([
        text("Creating ticket…", size=13, bold=True, color=warn),
        text("Sending to the ticketing system. This usually takes a few seconds.", color=warn),
        button("Cancel and try again", A_CANCEL),
    ], visible=V["showPending"]["id"], bg="#fff4d6", padding=10)

    created = vstack([
        text("Ticket created", size=13, bold=True, color=ok),
        text(ref("ticketNumber"), size=18, bold=True),
        text("Logged to Chat Logs. Give the customer the number and the expected response time.", color=ok),
        button("Create another ticket", A_RESET),
    ], visible=V["ticketCreated"]["id"], bg="#e4f4ea", padding=10)

    failed = vstack([
        text("Ticket not created", size=13, bold=True, color=bad),
        text(ref("ticketMessage"), color=bad),
        text("Fix the issue and submit again. The attempt has been logged.", color=bad),
        button("Back to form", A_RESET),
    ], visible=V["ticketFailed"]["id"], bg="#fbe9e7", padding=10)

    timed_out = vstack([
        text("No reply from the ticketing system", size=13, bold=True, color=bad),
        text("Try again. If it keeps happening, raise it with the service desk and create the ticket manually.", color=bad),
        button("Back to form", A_RESET),
    ], visible=V["showTimeoutError"]["id"], bg="#fbe9e7", padding=10)

    root = vstack([banner, details, form, pending, created, failed, timed_out],
                  height=size_stretch(), padding=5, margin=[5, 5, 5, 5])

    page_id = gid("page:chat")
    page = {
        "id": page_id,
        "name": "Chat Page",
        "properties": {"onLoadAction": t_action(A_RESET), "backgroundColor": t_null()},
        "dataVersion": 0,
        "rootContainer": root,
    }

    # ---- custom actions ----
    def reset_steps(timeout_flag):
        return [
            set_bool(V["isSubmitting"], False),
            set_bool(V["showPending"], False),
            set_bool(V["ticketCreated"], False),
            set_bool(V["ticketFailed"], False),
            set_bool(V["showTimeoutError"], timeout_flag),
            set_bool(V["showForm"], True),
            set_num(V["ticketReturnCode"], 99),
            set_str(V["ticketOutcome"], ""),
            set_str(V["ticketMessage"], ""),
            set_str(V["ticketNumber"], ""),
        ]

    create_ticket = data_action(create_id, inputs={
        "fullname": t_var(V["fullname"]["id"]),
        "email": t_var(V["email"]["id"]),
        "location": t_var(V["location"]["id"]),
        "category": t_var(V["ticketCategory"]["id"]),
        "priority": t_var(V["ticketPriority"]["id"]),
        "description": t_var(V["ticketDescription"]["id"]),
        "conversationId": t_var("scripter.interactionId"),
        "agentId": t_var("scripter.agentId"),
    }, outputs={
        "ticketOutcome": V["ticketOutcome"]["id"],
        "ticketReturnCode": V["ticketReturnCode"]["id"],
        "ticketNumber": V["ticketNumber"]["id"],
        "ticketMessage": V["ticketMessage"]["id"],
    })

    log_row = data_action(logs_id, inputs={
        "key": t_var("scripter.interactionId"),
        "userId": t_var("scripter.agentId"),
        "conversationId": t_var("scripter.interactionId"),
        "ticketNumber": t_var(V["ticketNumber"]["id"]),
        "outcome": t_var(V["ticketOutcome"]["id"]),
        "returnCode": t_var(V["ticketReturnCode"]["id"]),
        "message": t_var(V["ticketMessage"]["id"]),
        "category": t_var(V["ticketCategory"]["id"]),
        "priority": t_var(V["ticketPriority"]["id"]),
        "customerEmail": t_var(V["email"]["id"]),
    }, outputs={})

    create_block = [
        set_bool(V["isSubmitting"], True),
        set_bool(V["ticketCreated"], False),
        set_bool(V["ticketFailed"], False),
        set_bool(V["showTimeoutError"], False),
        set_str(V["ticketOutcome"], ""),
        set_bool(V["showForm"], False),
        set_bool(V["showPending"], True),
        create_ticket,
        if_not_equal(V["ticketOutcome"], "CREATED",
                     if_block=[set_bool(V["ticketFailed"], True)],
                     else_block=[set_bool(V["ticketCreated"], True)]),
        log_row,
        set_bool(V["showPending"], False),
        set_bool(V["isSubmitting"], False),
    ]
    empty_desc_block = [
        set_str(V["ticketMessage"], "Description is required."),
        set_bool(V["ticketCreated"], False),
        set_bool(V["ticketFailed"], True),
    ]

    custom_actions = [
        {"id": A_CREATE, "name": "Create Ticket",
         "action": {"block": [if_not_equal(V["ticketDescription"], "", create_block, empty_desc_block)]}},
        {"id": A_RESET, "name": "Reset Ticket Form", "action": {"block": reset_steps(False)}},
        {"id": A_CANCEL, "name": "Cancel Ticket", "action": {"block": reset_steps(True)}},
    ]

    def feat(enabled): return {"properties": {"enabled": t_bool(enabled)}}
    features = {
        "dialer": {"properties": {"enabled": t_bool(False), "contactListId": t_text(""),
                                  "onContactDataLoadAction": t_action()}},
        "scripter": feat(True),
        "screenPop": feat(False),
        "callback": feat(False),
        "chat": feat(True),
        "email": feat(False),
        "message": feat(True),
        "bridge": feat(True),          # Data Actions
        "uuiData": feat(False),
        "customerSecuredData": feat(False),
        "list": feat(False),
        "workItem": feat(False),
    }

    return {
        "name": name,
        "startPageId": page_id,
        "pages": [page],
        "features": features,
        "variables": list(V.values()),
        "customActions": custom_actions,
        "dataVersion": 0,
    }


# ---------- self check ----------
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def check(doc):
    problems = []
    var_ids = {v["id"] for v in doc["variables"]}
    names = [v["name"] for v in doc["variables"]]
    if len(names) != len(set(names)):
        problems.append("duplicate variable names")
    action_ids = {a["id"] for a in doc["customActions"]}
    page_ids = {p["id"] for p in doc["pages"]}
    if doc["startPageId"] not in page_ids:
        problems.append("startPageId does not match a page")

    def walk(o, path):
        if isinstance(o, dict):
            if o.get("typeName") == "variable" and "value" in o:
                v = o["value"]
                if not (v in var_ids or v.startswith("scripter.")):
                    problems.append(f"{path}: unknown variable {v}")
            if o.get("typeName") == "interpolatedText":
                for m in re.findall(r"\{\{([^}]+)\}\}", o.get("value") or ""):
                    if not (m in var_ids or m.startswith("scripter.")):
                        problems.append(f"{path}: unknown reference {{{{{m}}}}}")
            if o.get("typeName") == "action" and isinstance(o.get("value"), dict) and o["value"].get("actionName"):
                if o["value"]["actionName"] not in action_ids:
                    problems.append(f"{path}: unknown custom action {o['value']['actionName']}")
            if o.get("type") == "action" and GUID.match(o.get("actionName", "")) and o["actionName"] not in action_ids:
                problems.append(f"{path}: unknown custom action step {o['actionName']}")
            if o.get("typeName") == "bridgeActionArguments":
                an = o["value"]["actionName"]
                if "REPLACE_WITH" in an:
                    problems.append(f"{path}: data action id still a placeholder ({an})")
                elif not GUID.match(an.replace("custom_-_", "")):
                    problems.append(f"{path}: data action id is not a GUID ({an})")
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(doc, "$")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="Chat Ticket Script v2")
    ap.add_argument("--create-ticket-action-id", default=PLACEHOLDER_CREATE)
    ap.add_argument("--chat-logs-action-id", default=PLACEHOLDER_LOGS)
    ap.add_argument("-o", "--output", default="scripts/chat-ticket-script.script")
    ap.add_argument("--check", action="store_true", help="only validate an existing file given with -o")
    args = ap.parse_args()

    if args.check:
        doc = json.load(open(args.output, encoding="utf-8"))
    else:
        for flag, val in (("--create-ticket-action-id", args.create_ticket_action_id),
                          ("--chat-logs-action-id", args.chat_logs_action_id)):
            if val not in (PLACEHOLDER_CREATE, PLACEHOLDER_LOGS) and not GUID.match(val):
                sys.exit(f"{flag} must be a GUID, got {val}")
        doc = build(args.name, args.create_ticket_action_id, args.chat_logs_action_id)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"wrote {args.output}")

    problems = check(doc)
    for p in problems:
        print("  " + p)
    placeholders = [p for p in problems if "placeholder" in p]
    hard = [p for p in problems if "placeholder" not in p]
    if hard:
        sys.exit(f"{len(hard)} problem(s) found")
    if placeholders:
        print("OK apart from placeholders: pass --create-ticket-action-id and --chat-logs-action-id, "
              "or find-and-replace the two REPLACE_WITH_* tokens before importing.")
    else:
        print("OK: all references resolve; file is ready to import.")


if __name__ == "__main__":
    main()
