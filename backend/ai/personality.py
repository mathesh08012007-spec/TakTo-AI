"""Builds the system prompt and filters the follow-up chips out of streamed text."""
from ai.prompts import (BASE_PERSONA, MODE_PROMPTS, SUGGEST_MARKER,
                        SUGGESTION_INSTRUCTION, TONE_PROMPTS)


def build_system_prompt(user, prefs, mode, memories):
    parts = [BASE_PERSONA, MODE_PROMPTS.get(mode, MODE_PROMPTS["friend"]),
             TONE_PROMPTS.get(prefs.get("tone"), TONE_PROMPTS["auto"])]

    about = [f"The user's name is {user['name']}."]
    if prefs.get("learning_goals"):
        about.append(f"Their stated learning goals: {prefs['learning_goals']}")
    if prefs.get("interests"):
        about.append(f"Their interests: {prefs['interests']}")
    parts.append("About the user:\n" + "\n".join(about))

    if memories:
        lines = "\n".join(f"- {m['memory_text']}" for m in memories)
        parts.append("Things you remember about the user (use naturally and only when relevant; "
                     "never recite this list):\n" + lines)

    parts.append(SUGGESTION_INSTRUCTION)
    return "\n\n".join(parts)


class StreamFilter:
    """Passes text through while holding back the <<SUGGEST>> marker and everything after it."""

    def __init__(self):
        self.pending = ""
        self.tail = ""
        self.suppressing = False
        self.visible = ""

    def feed(self, chunk):
        if self.suppressing:
            self.tail += chunk
            return ""
        self.pending += chunk
        idx = self.pending.find(SUGGEST_MARKER)
        if idx != -1:
            out = self.pending[:idx]
            self.tail = self.pending[idx + len(SUGGEST_MARKER):]
            self.pending = ""
            self.suppressing = True
        else:
            # Hold back a trailing piece that could be the start of the marker.
            keep = 0
            for n in range(min(len(SUGGEST_MARKER) - 1, len(self.pending)), 0, -1):
                if SUGGEST_MARKER.startswith(self.pending[-n:]):
                    keep = n
                    break
            out = self.pending[:len(self.pending) - keep]
            self.pending = self.pending[len(self.pending) - keep:]
        self.visible += out
        return out

    def finish(self):
        """Flush held-back text. Returns (final_text_to_emit, suggestions)."""
        out = "" if self.suppressing else self.pending
        self.pending = ""
        self.visible += out
        return out, self.suggestions()

    def suggestions(self):
        items = []
        for part in self.tail.strip().split("\n")[0].split("|"):
            part = part.strip().strip("[]\"'").strip()
            if 0 < len(part) <= 40:
                items.append(part)
        return items[:3]
