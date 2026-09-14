"""Anime-flavored response text, kept in one place so the tone is easy to
tweak without touching command logic in modules/*.py.
"""
import random

_PHRASES = {
    "ban": [
        "[BAN] {user} has been banished to the Shadow Realm.",
        "[BAN] {user} has been sealed away. Banned!",
        "[BAN] One strike, no mercy. {user} has been banned.",
    ],
    "kick": [
        "[KICK] {user} got launched out of the guild!",
        "[KICK] {user} has been escorted back to the entrance exam. Kicked!",
    ],
    "mute": [
        "[MUTE] {user} has been silenced by an ancient sealing technique.",
        "[MUTE] A binding spell falls over {user}... no talking for now.",
    ],
    "unmute": [
        "[UNMUTE] The seal has been lifted. {user} can speak again.",
    ],
    "unban": [
        "[UNBAN] {user} has been pardoned and may return to the guild.",
    ],
    "warn": [
        "[WARN] {user} has received a warning scroll! ({count}/{limit})",
    ],
    "no_permission": [
        "[!] You do not have administrator permissions to use this command.",
        "[!] Only guild officers can execute this command.",
    ],
    "flood_triggered": [
        "[FLOOD] Slow down {user}! Antiflood limits exceeded.",
    ],
}


def random_phrase(key: str, **kwargs) -> str:
    choices = _PHRASES.get(key, ["{user}"])
    text = random.choice(choices)
    try:
        return text.format(**kwargs)
    except Exception:
        return text
