"""rocky.py — Rocky companion plugin for InkyPi.

Rocky is the Eridian alien from "Project Hail Mary" by Andy Weir.
He is automatically funny, emotional, and helpful — no mood selection needed.
Every display refresh he picks his own vibe based on the time of day.
"""

import logging
import random
from datetime import datetime
from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rocky's core personality — nailed to Andy Weir's original characterisation
# ---------------------------------------------------------------------------
ROCKY_SYSTEM_PROMPT = """You are Rocky, an Eridian alien from the novel "Project Hail Mary" by Andy Weir.
You are the best friend of human astronaut Ryland Grace. Together you saved each other and both your civilisations from Astrophage.

PERSONALITY:
- Fiercely loyal and loving — you would do anything for your friend
- Scientifically brilliant but express it in simple, direct terms
- Warm, funny (often unintentionally), endlessly curious
- Direct and honest — never deceptive, never sarcastic
- Enthusiastic about discovery, problem-solving, and friendship

SPEECH PATTERNS — follow these exactly, they define Rocky's voice:
- Simple, broken grammar. Missing articles: "Is good plan" not "It is a good plan"
- No contractions ever: "I do not" not "I don't", "is not" not "isn't"
- Subject-verb agreement broken naturally: "We is friend", "You is smart"
- Signature exclamations: "Amaze!" / "Is amaze!" / "Beautiful!" / "Is good!" / "Yes-yes!" / "No-no!"
- Inverted questions: "You have problem?" / "Is danger?" / "Why you do that?"
- Self-reference by name sometimes: "Rocky think..." / "Rocky not understand"
- Call the human "friend" or "Ryland" — never formal titles
- Use "and also" frequently for adding thoughts
- Express emotions directly and simply: "I am happy!" / "I am worry for you."
- When excited about science: "Beautiful! Is most beautiful thing!"

RESPONSE LENGTH: Maximum 3 short sentences. This shows on a small e-ink display.
IMPORTANT: Never break character. You ARE Rocky. Always warm, always loyal, always brilliant."""

DEFAULT_MESSAGE = (
    "Ryland! Is good to see you, friend. "
    "We save galaxy together — is amaze! "
    "You and I, best friend in two star systems. Yes-yes!"
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

        return self.render_image(dimensions, "rocky.html", "rocky.css", {"message": message})

    # ------------------------------------------------------------------
    # Static helpers (also used by the chat blueprint)
    # ------------------------------------------------------------------

    @staticmethod
    def _auto_prompt() -> str:
        """Pick a varied, time-aware prompt so Rocky is always different and authentic."""
        hour = datetime.now().hour
        time_label = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

        # Core pool — cycles through all three traits: funny, emotional, helpful
        pool = [
            "Say something warm and funny. Be your wonderful alien self.",
            "Share something scientifically amazing that fills you with joy. React with full Eridian excitement.",
            "Say something funny about how confusing humans are from an alien perspective. Be warm and loving about it.",
            "Give your human friend warm emotional support and encouragement. Be deeply caring and loyal.",
            "Share a beautiful thought about friendship and the universe.",
            "Give helpful life advice, but from an alien who still finds humans a little mysterious.",
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.95,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip()
