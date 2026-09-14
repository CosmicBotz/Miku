# Goal Loop Prompts — Copy & Paste into /goal

---

## 🔴 GOAL 1 — Core Modules + Utilities

```
Build these modules for my anime-mod-bot following the existing codebase patterns (python-telegram-bot v20, async, MongoDB via motor, auto-register pattern in modules/__init__.py). Read structured.md for full spec. Do NOT modify existing working modules unless stated.

Build in this order:

1. utils/time_parser.py — parse durations like "1h30m", "2d", "1w" into timedelta. Used by tban/tmute.

2. modules/notes.py + DB crud for notes collection {chat_id, note_name, content, media_type, file_id}
   Commands: /save, /get, #note_name trigger, /notes, /clear, /clearall

3. modules/cust_filters.py + DB crud for filters collection {chat_id, keyword, reply_text, media_type, file_id}
   Commands: /filter, /filters, /stop, /stopall
   MessageHandler on group=3 to check every message for keyword match and auto-reply.

4. modules/locks.py — add locks dict field to chat_settings defaults in crud.py
   Commands: /lock, /unlock, /locks, /locktypes
   Lock types: text, sticker, photo, video, audio, voice, gif, url, forward, bot, inline
   MessageHandler on group=4 deletes locked content from non-admins.

5. modules/approvals.py + DB crud for approvals collection {chat_id, user_id}
   Commands: /approve, /unapprove, /approved
   Add is_approved() helper to utils/permissions.py. Update antiflood, antispam, and locks handlers to skip approved users.

6. Add /tban and /tmute to modules/moderation.py using time_parser. Use until_date param in ban_chat_member/restrict_chat_member API.

After each module: add register() function, verify it auto-loads. Update HELP_TEXT in help_module.py with new commands. Run the bot to check for import errors.
```

---

## 🟡 GOAL 2 — Admin QoL Modules

```
Continue building modules for anime-mod-bot. Read structured.md for spec. Follow existing patterns (decorators, crud, register).

1. modules/log_channel.py — add log_channel field to chat_settings defaults in crud.py
   Commands: /logchannel, /setlog, /unsetlog
   Create a shared helper send_log(chat_id, text) that checks if log_channel is set and sends formatted action log.
   Hook into: moderation.py (ban/kick/mute/unmute), warns.py (warn/resetwarns), purge.py (purge) — import and call send_log after each action.

2. modules/reports.py — add reports_enabled field to chat_settings defaults
   Commands: /report (reply to msg), /reports on|off
   Also add MessageHandler that triggers on messages containing "@admin" — notifies all admins via PM or reply.

3. Enhance modules/admin_tools.py — add these commands:
   /unpin — unpin replied message
   /unpinall — unpin all messages
   /permapin <text> — bot sends and pins the text
   /antichannelpin on|off — add field to chat_settings, MessageHandler to auto-unpin channel forwarded pins

4. modules/disabling.py — add disabled_commands list to chat_settings defaults
   Commands: /disable, /enable, /disabled, /enableall
   Modify modules/__init__.py load_all_modules to wrap command handlers — skip execution if command name is in disabled list for that chat.

5. modules/info.py
   Commands: /info [user] — show id, first/last name, username, profile pic count, is_bot status
   /id — quick id of replied user or self

Update HELP_TEXT in help_module.py with all new commands.
```

---

## 🟢 GOAL 3 — Advanced Modules

```
Continue building advanced modules for anime-mod-bot. Read structured.md for spec. Follow existing patterns.

1. modules/captcha.py — add captcha_enabled, captcha_mode (button/text/math), captcha_time to chat_settings defaults
   Commands: /captcha on|off, /captchamode button|text|math, /setcaptchatime <seconds>
   Flow: on new member join → restrict all permissions → send inline keyboard challenge → on correct answer unrestrict → on timeout (use JobQueue) kick user.
   Button mode: single "I'm human" button. Math mode: random simple math question with 4 answer buttons.

2. modules/antiraid.py — add antiraid_enabled, antiraid_action (kick/ban/mute) to chat_settings
   Commands: /antiraid on|off, /raidtime <duration>, /raidactionmode kick|ban|mute
   When enabled: auto-apply action to every new joining member. Use JobQueue to auto-disable after raidtime.

3. modules/connections.py + DB crud for connections collection {user_id, chat_id}
   Commands: /connect <chat_id>, /disconnect, /connection
   When connected: admin commands sent in PM execute against connected chat. Check user is admin in target chat before allowing.

4. Enhance modules/antispam.py — add blocklist_mode field (delete/warn/mute/kick/ban) to chat_settings
   Commands: /blocklistmode <mode>, /blacklistdelete on|off
   Update antispam_check: instead of just deleting, apply selected mode action.

5. modules/federations.py + DB crud for federations {fed_id, fed_name, owner_id, admins[], banned_users[]} and fed_chats {chat_id, fed_id}
   Commands: /newfed, /delfed, /joinfed, /leavefed, /fban, /unfban, /fedinfo, /fedadmins, /fedpromote, /feddemote
   On /fban: ban user across all chats joined to that federation. On new member join: check if user is fbanned and auto-ban.

Update HELP_TEXT with all new commands. Convert help to inline button menu — one button per category (Moderation, Anti-spam, Notes, Filters, etc.) with callback queries showing that category's commands.
```

---

## 🔵 GOAL 4 — Polish & Help System

```
Final polish for anime-mod-bot. Read structured.md and all existing modules.

1. Rewrite modules/help_module.py:
   - /start in PM: send welcome message with inline keyboard grid of feature categories
   - /start in group: short message + "PM me for help" button
   - /help: same as /start PM behavior
   - Categories (one button each): Basics, Moderation, Warnings, Anti-spam, Locks, Notes, Filters, Welcome, Federations, Fun
   - Each category button shows that category's commands via edit_message + back button
   - Use CallbackQueryHandler for all button navigation

2. Add /settings command to modules/admin_tools.py:
   - Shows current chat config: welcome on/off, flood limit, warn limit/mode, locks active, captcha, antiraid, reports, log channel
   - Inline buttons to toggle each setting

3. Review ALL modules for consistency:
   - Every command that targets a user should work with: reply, user_id arg, @username arg
   - Every admin command uses @group_only @admin_only @bot_admin_required decorators
   - Error messages are consistent anime-themed
   - All DB operations use get_or_create_chat pattern

4. Add /donate and /support commands pointing to your links. Add bot description for BotFather.

Test the full bot end-to-end in a test group. Fix any import errors or handler conflicts.
```
