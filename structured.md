# Anime Mod Bot — Rose-Style Feature Roadmap

> Reference: [Miss Rose Docs](https://missrose.org/docs/)
> Pattern: Each module follows a **5-step loop** → DB Schema → CRUD → Handler → Register → Test

---

## Status Matrix

| Feature | Rose Has | You Have | Gap |
|---|---|---|---|
| Ban/Kick/Mute/Unmute | ✅ | ✅ | tban/tmute (timed) |
| Warns | ✅ | ✅ | warn buttons, warn filters |
| Purge/Del | ✅ | ✅ | /purgefrom, /purgeuser |
| Welcome/Goodbye | ✅ | ✅ | media welcome, captcha verify |
| Blacklist | ✅ | ✅ (basic) | blocklist modes (delete/warn/mute/kick/ban), sticker blocklist |
| Antiflood | ✅ | ✅ | per-type flood (text/sticker/photo) |
| Rules | ✅ | ✅ | rules button, /privaterules |
| Pin | ✅ | ✅ (basic) | /unpin, /unpinall, /permapin, anti-channel-pin |
| Notes | ✅ | ❌ | **NEW** — save/get/clear per-chat notes |
| Filters | ✅ | ❌ | **NEW** — keyword auto-reply |
| Locks | ✅ | ❌ | **NEW** — lock message types |
| Approvals | ✅ | ❌ | **NEW** — whitelist users from restrictions |
| Admin Log Channel | ✅ | ❌ | **NEW** — log admin actions |
| Reports | ✅ | ❌ | **NEW** — /report, @admin tag |
| Connections | ✅ | ❌ | **NEW** — manage group from PM |
| Disabling | ✅ | ❌ | **NEW** — disable specific commands |
| Federations | ✅ | ❌ | **NEW** — cross-group ban network |
| CAPTCHA | ✅ | ❌ | **NEW** — verify new joins |
| AntiRaid | ✅ | ❌ | **NEW** — temporary lockdown |
| Timed Actions | ✅ | ❌ | **NEW** — /tban /tmute with duration |
| User Info | ✅ | ❌ | **NEW** — /info command |
| Languages/i18n | ✅ | ❌ | Low priority |

---

## 5-Step Loop (repeat per module)

```
LOOP {
  1. DB    → add collection/fields in crud.py
  2. CRUD  → add async helpers (get/set/delete)
  3. HANDLER → write command handlers in modules/<name>.py
  4. REGISTER → wire handlers in register(application)
  5. TEST  → /command in test group, verify DB state
}
```

---

## Priority Execution Order

### 🔴 Phase 1 — Core Missing (High Impact)

#### 1. Notes Module
```
File: modules/notes.py
DB: notes collection {chat_id, note_name, content, media_type, file_id}
Commands:
  /save <name> <text>     — save note (reply for media)
  /get <name> or #name    — retrieve note
  /notes                  — list all notes
  /clear <name>           — delete note
  /clearall               — wipe all (owner only)
Loop: DB→CRUD→Handler→Register→Test
```

#### 2. Filters Module
```
File: modules/cust_filters.py
DB: filters collection {chat_id, keyword, reply_text, media_type, file_id}
Commands:
  /filter <keyword> <reply>  — add auto-reply trigger
  /filters                   — list active filters
  /stop <keyword>            — remove filter
  /stopall                   — wipe all
Handler: MessageHandler checks every message for keyword match
Loop: DB→CRUD→Handler→Register→Test
```

#### 3. Locks Module
```
File: modules/locks.py
DB: chat_settings add locks field {text, sticker, photo, video, audio, voice, gif, url, forward, bot}
Commands:
  /lock <type>       — lock a message type
  /unlock <type>     — unlock it
  /locks             — show lock status
  /locktypes         — list available lock types
Handler: MessageHandler deletes locked content from non-admins
Loop: DB→CRUD→Handler→Register→Test
```

#### 4. Approvals Module
```
File: modules/approvals.py
DB: approvals collection {chat_id, user_id}
Commands:
  /approve <user>      — exempt from restrictions/locks/blocklist
  /unapprove <user>    — remove exemption
  /approved            — list approved users
Check: antispam/antiflood/locks handlers skip approved users
Loop: DB→CRUD→Handler→Register→Test
```

#### 5. Timed Actions (tban/tmute)
```
File: modify modules/moderation.py
Add:
  /tban <user> <time> [reason]   — temp ban (e.g. 1h, 2d)
  /tmute <user> <time> [reason]  — temp mute
  Parse duration: 30m, 1h, 2d, 1w
  Use until_date param in restrict/ban API
Loop: Handler→Register→Test (no new DB needed)
```

---

### 🟡 Phase 2 — Admin Quality of Life

#### 6. Admin Log Channel
```
File: modules/log_channel.py
DB: chat_settings add log_channel field
Commands:
  /logchannel          — show current log channel
  /setlog              — set current channel as log target
  /unsetlog            — remove logging
Emit: hook into ban/mute/warn/kick to send log messages
Loop: DB→CRUD→Handler→Register→Test
```

#### 7. Reports
```
File: modules/reports.py
DB: chat_settings add reports_enabled field
Commands:
  /report (reply)      — report message to admins
  /reports on|off      — toggle
Handler: also trigger on @admin in message text
Loop: DB→CRUD→Handler→Register→Test
```

#### 8. Enhanced Pins
```
File: modify modules/admin_tools.py
Add:
  /unpin               — unpin current pinned
  /unpinall            — unpin all messages
  /permapin <text>     — pin a new message with text
  /antichannelpin on|off — auto-unpin channel-auto-pins
Loop: Handler→Register→Test
```

#### 9. Disable Commands
```
File: modules/disabling.py
DB: chat_settings add disabled_commands list
Commands:
  /disable <cmd>       — disable a command in this chat
  /enable <cmd>        — re-enable
  /disabled            — list disabled commands
  /enableall           — reset
Check: wrap command dispatch to skip disabled
Loop: DB→CRUD→Handler→Register→Test
```

#### 10. User Info
```
File: modules/info.py
Commands:
  /info [user]         — show user id, name, username, DC, profile pic count
  /id                  — quick id lookup
Loop: Handler→Register→Test
```

---

### 🟢 Phase 3 — Advanced

#### 11. Connections
```
File: modules/connections.py
DB: connections collection {user_id, chat_id}
Commands:
  /connect <chat_id>   — manage a group from PM
  /disconnect           — disconnect
  /connection           — show connected chat
Route: admin commands check connection context
```

#### 12. CAPTCHA
```
File: modules/captcha.py
DB: chat_settings add captcha_enabled, captcha_mode (button/text/math)
Flow: new member → restrict → send challenge → verify → unrestrict / kick on timeout
Commands:
  /captcha on|off
  /captchamode button|text|math
  /setcaptchatime <seconds>
```

#### 13. AntiRaid
```
File: modules/antiraid.py
DB: chat_settings add antiraid_enabled
Commands:
  /antiraid on|off     — emergency lockdown
  /raidtime <duration> — auto-disable after time
Action: auto-kick/mute all new joins during raid mode
```

#### 14. Federations
```
File: modules/federations.py
DB: federations collection {fed_id, fed_name, owner_id, admins[], banned_users[]}
    fed_chats collection {chat_id, fed_id}
Commands:
  /newfed <name>        — create federation
  /delfed               — delete
  /joinfed <fed_id>     — join chat to fed
  /leavefed             — leave fed
  /fban <user> [reason] — federation ban
  /unfban <user>        — unban
  /fedinfo              — info
  /fedadmins            — list fed admins
  /fedpromote/demote    — manage fed admins
```

#### 15. Blocklist Modes
```
File: modify modules/antispam.py
Add blocklist_mode to chat_settings: delete|warn|mute|kick|ban
Commands:
  /blocklistmode <mode> — set punishment
  /addblacklist supports regex via {re:pattern}
  /blacklistdelete on|off — toggle delete on match
```

---

## Utility Checklist

- [ ] `utils/time_parser.py` — parse "1h30m", "2d" into seconds/datetime
- [ ] `utils/permissions.py` — add `is_approved()` check
- [ ] `utils/decorators.py` — add `@owner_only`, `@sudo_only`
- [ ] `utils/callback.py` — inline keyboard callback router
- [ ] Update `help_module.py` — dynamic help per module with inline buttons

---

## DB Collections Summary

| Collection | Key Fields |
|---|---|
| `chat_settings` | _id=chat_id, all per-chat config |
| `warns` | chat_id, user_id, reason, admin_id |
| `blacklist_words` | chat_id, word |
| `notes` | chat_id, note_name, content, media |
| `filters` | chat_id, keyword, reply |
| `approvals` | chat_id, user_id |
| `federations` | fed_id, name, owner, admins, bans |
| `fed_chats` | chat_id, fed_id |
| `connections` | user_id, chat_id |
