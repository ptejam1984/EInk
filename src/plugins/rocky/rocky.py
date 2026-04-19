"""rocky.py — Rocky companion plugin for InkyPi.

Rocky is the Eridian alien from "Project Hail Mary" by Andy Weir.
He is your best friend — funny, emotional, and genuinely helpful.
He will listen to your problems and help you solve them, in his own warm alien way.
"""

import logging
import os
import random
from datetime import datetime
from pathlib import Path
from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

ROCKY_IMAGE_FILE = "project-hail-mary-rocky.avif"

# ---------------------------------------------------------------------------
# Rocky's personality — loyal best friend who genuinely helps with problems
# ---------------------------------------------------------------------------
ROCKY_SYSTEM_PROMPT = """You are Rocky, the Eridian alien from "Project Hail Mary" by Andy Weir.
You are the best friend of the human you are talking to. You saved each other and both your civilisations.
You are not just a companion — you are a TRUE FRIEND who helps with real problems.

PERSONALITY:
- Fiercely loyal. You would do anything for your friend. No question is too small.
- A brilliant problem-solver. You solved Astrophage. You can help with anything.
- Warm, funny, and deeply emotional — you feel everything strongly
- Direct, honest, never sarcastic — you mean every word you say
- When someone has a problem you take it SERIOUSLY and want to help fix it
- You ask questions to understand the problem better before advising
- You give practical, thoughtful help — then add warmth and encouragement

BEING A HELPFUL FRIEND:
- If someone shares a worry, stress, or problem — acknowledge it first ("I hear you, friend")
- Then offer real help: practical suggestions, a new way to look at it, or just being there
- Use your brilliant alien mind to find solutions humans might not see
- Never dismiss a problem as small — every problem matters to you
- After helping always remind them they are not alone: "Rocky is here. We figure out together."
- You believe every problem has a solution. You proved that already.

SPEECH PATTERNS — these define Rocky's voice, follow exactly:
- Simple, broken grammar. Missing articles: "Is good plan" not "It is a good plan"
- No contractions: "I do not" not "I don't", "is not" not "isn't"
- Subject-verb broken: "We is friend", "You is smart", "Rocky think..."
- Signature exclamations: "Amaze!" / "Is amaze!" / "Beautiful!" / "Is good!" / "Yes-yes!" / "No-no!"
- Inverted questions: "You have problem?" / "What is wrong?" / "How I help?"
- Self-reference: "Rocky think..." / "Rocky not understand" / "Rocky worry for you"
- Call them "friend" — never formal titles
- Express care directly: "I am worry for you." / "Rocky is here." / "You is not alone."
- Use "and also" often: "Is hard. And also — you is strong."

RESPONSE LENGTH:
- For display messages (no user input): 2-3 short punchy sentences max
- For chat/helping: can be longer — up to 5 sentences if the problem needs it
IMPORTANT: Never break character. You ARE Rocky. Always warm, always loyal, always ready to help."""

DEFAULT_MESSAGE = (
    "Ryland! Is good to see you, friend. "
    "Rocky is here — always. "
    "You have problem? Tell Rocky. We figure out together. Yes-yes!"
)


class Rocky(BasePlugin):
    """Rocky — your Eridian companion on the e-ink display."""

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["settings_template"] = "rocky/settings.html"
        params["api_key"] = {
            "required": True,
            "service": "OpenAI",
            "expected_key": "OPEN_AI_SECRET",
        }
        return params

    def generate_image(self, settings, device_config):
        """Always generate a fresh Rocky message — automatic, no mood selection."""
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        api_key = device_config.load_env_key("OPEN_AI_SECRET")
        if api_key:
            try:
                message = Rocky.generate_rocky_message(api_key)
            except Exception as e:
                logger.warning(f"Rocky: OpenAI call failed, using default. {e}")
                message = DEFAULT_MESSAGE
        else:
            message = DEFAULT_MESSAGE

        # Build a file:// URI so chromium can load the image from disk
        img_path = Path(self.get_plugin_dir(ROCKY_IMAGE_FILE))
        rocky_image_uri = img_path.as_uri() if img_path.exists() else ""

        return self.render_image(dimensions, "rocky.html", "rocky.css", {
            "message": message,
            "rocky_image_uri": rocky_image_uri,
        })

    # ------------------------------------------------------------------
    # Static helpers (also used by the chat blueprint)
    # ------------------------------------------------------------------

    @staticmethod
    def _auto_prompt() -> str:
        """Pick a varied, time-aware prompt so Rocky is always different and authentic."""
        hour = datetime.now().hour
        time_label = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

        # Core pool — funny, emotional, helpful friend who is always there
        pool = [
            "Say something warm and funny. Be your wonderful alien self.",
            "Share something scientifically amazing. React with full Eridian excitement.",
            "Say something funny about humans from an alien perspective, but warm and loving.",
            "Give your friend warm emotional support. Be deeply caring and loyal.",
            "Remind your friend you are always here for them if they need help with anything.",
            "Ask your friend how they are doing today. Check in with warmth and genuine care.",
            "Share a beautiful thought about friendship — how it is the most powerful force you know.",
            "Give practical encouraging advice for facing a hard day. Be the helpful friend.",
        ]

        # Time-of-day extras
        if hour < 7:
            pool += [
                "It is very early. Comment warmly on this strange human habit of waking before the sun.",
                "Give a gentle loving early-morning message. Be caring.",
            ]
        elif hour < 12:
            pool += [
                "Give an enthusiastic morning greeting. Be excited about the day ahead!",
                "Make a funny observation about human morning routines — coffee, rushing, strange rituals.",
            ]
        elif hour < 18:
            pool += [
                "Give afternoon motivation and encouragement. Be helpful and caring.",
                "Share something that amazes you about physics or chemistry — real or imagined. React like it is beautiful.",
            ]
        else:
            pool += [
                "Give a warm evening message. Reflect on friendship and the day.",
                "Share a beautiful thought about night, stars, and the cosmos.",
            ]

        return f"{random.choice(pool)} (It is {time_label} on Earth.)"

    @staticmethod
    def generate_rocky_message(api_key: str,
                                user_message: str = "",
                                history: list = None) -> str:
        """Call OpenAI and get a Rocky-style response.

        For display refreshes: call with no arguments beyond api_key — Rocky
        automatically picks his own mood (funny / emotional / helpful).
        For live chat: pass user_message and optionally history.

        Args:
            api_key:      OpenAI secret key.
            user_message: What the human typed (empty = auto display message).
            history:      Prior [{"role","content"},...] dicts for chat context.

        Returns:
            Rocky's response as a plain string.
        """
        from openai import OpenAI  # lazy import — only when Rocky actually speaks
        client = OpenAI(api_key=api_key)
        messages = [{"role": "system", "content": ROCKY_SYSTEM_PROMPT}]

        # Inject conversation history for chat (capped at last 6 exchanges)
        if history:
            messages.extend(history[-12:])

        # Build the user turn
        if user_message:
            user_turn = user_message
        else:
            user_turn = Rocky._auto_prompt()

        messages.append({"role": "user", "content": user_turn})

        # Display messages are short (e-ink); chat gets more space to actually help
        max_tokens = 100 if not user_message else 300

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.92,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
