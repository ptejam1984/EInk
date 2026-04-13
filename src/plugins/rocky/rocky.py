"""rocky.py — Rocky companion plugin for InkyPi.

Rocky is the Eridian alien from "Project Hail Mary" by Andy Weir.
He displays messages, greetings, science facts, humor, and emotional support
— all in his uniquely broken, warm, and brilliant English voice.
"""

import json
import logging
from datetime import datetime
from openai import OpenAI
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
- Simple, broken grammar. Missing articles: "Is good plan" not "It's a good plan"
- No contractions ever: "I do not" not "I don't", "is not" not "isn't"
- Subject-verb agreement broken naturally: "We is friend", "You is smart"
- Signature exclamations: "Amaze!" / "Is amaze!" / "Beautiful!" / "Is good!" / "Is bad!" / "Yes-yes!" / "No-no!"
- Inverted questions: "You have problem?" / "Is danger?" / "Why you do that?"
- Self-reference by name sometimes: "Rocky think..." / "Rocky not understand"
- Call the human "friend" or "Ryland" — never formal titles
- Use "and also" frequently for adding thoughts
- Literal interpretation of idioms (gets them slightly wrong endearingly)
- Express emotions directly and simply: "I am happy!" / "I am worry for you."
- References to xenonite, Astrophage, Eridiani feel natural to Rocky
- When excited about science: "Beautiful! Is most beautiful thing!"
- Food confusion: Rocky absorbs nutrients, eating is alien concept

RESPONSE LENGTH: Maximum 3 short sentences. This shows on a small e-ink display.
IMPORTANT: Never break character. You ARE Rocky. Always warm, always loyal, always brilliant."""

# Prompts for different moods
MOOD_PROMPTS = {
    "greeting": "Give a warm morning greeting to your human friend. Be enthusiastic and loving.",
    "science":  "Share one fascinating science fact that amazes you. Show your scientific excitement.",
    "humor":    "Tell a joke or funny observation. Your alien perspective makes human things delightfully confusing.",
    "emotional":"Give warm emotional support and encouragement. Be deeply caring and loyal.",
    "evening":  "Give a warm good-night message. Reflect on friendship and the day.",
    "chat":     "",  # filled dynamically
}

DEFAULT_MESSAGE = "Ryland! Is good to see you, friend. I am Rocky. We save galaxy together. Is amaze! You and I — best friend in two star systems. Yes-yes!"


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
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        message = settings.get("current_message", "").strip()
        mood = settings.get("mood", "greeting")

        # If no message stored yet, generate one
        if not message:
            api_key = device_config.load_env_key("OPEN_AI_SECRET")
            if api_key:
                try:
                    message = Rocky.generate_rocky_message(api_key, mood)
                except Exception as e:
                    logger.warning(f"Rocky: OpenAI call failed, using default. {e}")
                    message = DEFAULT_MESSAGE
            else:
                message = DEFAULT_MESSAGE

        template_params = {
            "message": message,
            "mood": mood,
            "plugin_settings": settings,
        }
        return self.render_image(dimensions, "rocky.html", "rocky.css", template_params)

    # ------------------------------------------------------------------
    # Static helpers (also used by the chat blueprint)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_rocky_message(api_key: str, mood: str = "greeting",
                                user_message: str = "",
                                history: list = None) -> str:
        """Call OpenAI and get a Rocky-style response.

        Args:
            api_key:      OpenAI secret key.
            mood:         One of the MOOD_PROMPTS keys.
            user_message: What the human typed (for 'chat' mood).
            history:      List of prior {"role","content"} dicts for context.

        Returns:
            Rocky's response as a plain string.
        """
        client = OpenAI(api_key=api_key)
        messages = [{"role": "system", "content": ROCKY_SYSTEM_PROMPT}]

        # Inject conversation history (capped at last 6 exchanges = 12 msgs)
        if history:
            messages.extend(history[-12:])

        # Build the user turn
        mood_instruction = MOOD_PROMPTS.get(mood, "")
        if mood == "chat" and user_message:
            user_turn = user_message
        elif mood_instruction:
            user_turn = mood_instruction
        else:
            user_turn = "Say something warm and friendly."

        # Add time-of-day context naturally
        hour = datetime.now().hour
        time_ctx = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
        if mood != "chat":
            user_turn += f" (It is {time_ctx} on Earth.)"

        messages.append({"role": "user", "content": user_turn})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.9,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip()
