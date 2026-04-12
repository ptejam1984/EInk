"""quotes.py — Daily Quotes plugin for InkyPi.

Displays a daily rotating quote from a curated built-in list.
No external API required.
"""

import logging
from datetime import datetime

from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated quote list — no API needed
# ---------------------------------------------------------------------------
QUOTES = [
    {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"text": "In the middle of every difficulty lies opportunity.", "author": "Albert Einstein"},
    {"text": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius"},
    {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
    {"text": "Spread love everywhere you go. Let no one ever come to you without leaving happier.", "author": "Mother Teresa"},
    {"text": "When you reach the end of your rope, tie a knot in it and hang on.", "author": "Franklin D. Roosevelt"},
    {"text": "Always remember that you are absolutely unique. Just like everyone else.", "author": "Margaret Mead"},
    {"text": "Don't judge each day by the harvest you reap but by the seeds that you plant.", "author": "Robert Louis Stevenson"},
    {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
    {"text": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "author": "Benjamin Franklin"},
    {"text": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb"},
    {"text": "An unexamined life is not worth living.", "author": "Socrates"},
    {"text": "Spread the love. Spread the joy.", "author": "Unknown"},
    {"text": "You miss 100% of the shots you don't take.", "author": "Wayne Gretzky"},
    {"text": "Whether you think you can or you think you can't, you're right.", "author": "Henry Ford"},
    {"text": "The two most important days in your life are the day you are born and the day you find out why.", "author": "Mark Twain"},
    {"text": "Whatever you are, be a good one.", "author": "Abraham Lincoln"},
    {"text": "Be yourself; everyone else is already taken.", "author": "Oscar Wilde"},
    {"text": "Two roads diverged in a wood, and I — I took the one less traveled by.", "author": "Robert Frost"},
    {"text": "I am not a product of my circumstances. I am a product of my decisions.", "author": "Stephen Covey"},
    {"text": "Eighty percent of success is showing up.", "author": "Woody Allen"},
    {"text": "Your time is limited, so don't waste it living someone else's life.", "author": "Steve Jobs"},
    {"text": "Strive not to be a success, but rather to be of value.", "author": "Albert Einstein"},
    {"text": "I attribute my success to this: I never gave or took any excuse.", "author": "Florence Nightingale"},
    {"text": "The mind is everything. What you think you become.", "author": "Buddha"},
    {"text": "The most common way people give up their power is by thinking they don't have any.", "author": "Alice Walker"},
    {"text": "The person who says it cannot be done should not interrupt the person who is doing it.", "author": "Chinese Proverb"},
    {"text": "There is only one way to avoid criticism: do nothing, say nothing, and be nothing.", "author": "Aristotle"},
    {"text": "Ask and it will be given to you; search and you will find.", "author": "Jesus of Nazareth"},
    {"text": "The only person you are destined to become is the person you decide to be.", "author": "Ralph Waldo Emerson"},
    {"text": "Go confidently in the direction of your dreams. Live the life you have imagined.", "author": "Henry David Thoreau"},
    {"text": "When I stand before God at the end of my life, I would hope that I would not have a single bit of talent left.", "author": "Erma Bombeck"},
    {"text": "Few things can help an individual more than to place responsibility on him.", "author": "Booker T. Washington"},
    {"text": "Certain things catch your eye, but pursue only those that capture the heart.", "author": "Ancient Indian Proverb"},
    {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    {"text": "Everything you've ever wanted is on the other side of fear.", "author": "George Addair"},
    {"text": "We can easily forgive a child who is afraid of the dark; the real tragedy is when men are afraid of the light.", "author": "Plato"},
    {"text": "Teach thy tongue to say, 'I do not know,' and thou shalt progress.", "author": "Maimonides"},
    {"text": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
    {"text": "When I was 5 years old, my mother always told me that happiness was the key to life.", "author": "John Lennon"},
    {"text": "Fall seven times and stand up eight.", "author": "Japanese Proverb"},
    {"text": "When one door of happiness closes, another opens.", "author": "Helen Keller"},
    {"text": "Life is not measured by the number of breaths we take, but by the moments that take our breath away.", "author": "Maya Angelou"},
    {"text": "If you look at what you have in life, you'll always have more.", "author": "Oprah Winfrey"},
    {"text": "If you want to lift yourself up, lift up someone else.", "author": "Booker T. Washington"},
    {"text": "I have been impressed with the urgency of doing. Knowing is not enough; we must apply.", "author": "Leonardo da Vinci"},
    {"text": "Limitations live only in our minds. But if we use our imaginations, our possibilities become limitless.", "author": "Jamie Paolinetti"},
    {"text": "You take your life in your own hands, and what happens? A terrible thing: no one to blame.", "author": "Erica Jong"},
    {"text": "What's money? A man is a success if he gets up in the morning and goes to bed at night and in between does what he wants to do.", "author": "Bob Dylan"},
    {"text": "I didn't fail the test. I just found 100 ways to do it wrong.", "author": "Benjamin Franklin"},
    {"text": "In order to succeed, your desire for success should be greater than your fear of failure.", "author": "Bill Cosby"},
    {"text": "A person who never made a mistake never tried anything new.", "author": "Albert Einstein"},
    {"text": "The secret of success is to do the common thing uncommonly well.", "author": "John D. Rockefeller Jr."},
    {"text": "I find that the harder I work, the more luck I seem to have.", "author": "Thomas Jefferson"},
    {"text": "The successful warrior is the average man, with laser-like focus.", "author": "Bruce Lee"},
    {"text": "Success usually comes to those who are too busy to be looking for it.", "author": "Henry David Thoreau"},
    {"text": "Don't be afraid to give up the good to go for the great.", "author": "John D. Rockefeller"},
    {"text": "I wake up every morning and think to myself, 'How far can I push this company in the next 24 hours.'", "author": "Leah Busque"},
    {"text": "If you genuinely want something, don't wait for it — teach yourself to be impatient.", "author": "Gurbaksh Chahal"},
    {"text": "Stop chasing the money and start chasing the passion.", "author": "Tony Hsieh"},
    {"text": "Success is walking from failure to failure with no loss of enthusiasm.", "author": "Winston Churchill"},
    {"text": "Just when the caterpillar thought the world was ending, it turned into a butterfly.", "author": "Unknown"},
    {"text": "An entrepreneur is someone who has a vision for something and a want to create it.", "author": "David Karp"},
    {"text": "Try not to become a man of success, but rather try to become a man of value.", "author": "Albert Einstein"},
    {"text": "Great minds discuss ideas; average minds discuss events; small minds discuss people.", "author": "Eleanor Roosevelt"},
    {"text": "I have not failed. I've just found 10,000 ways that won't work.", "author": "Thomas Edison"},
    {"text": "If you are not willing to risk the usual, you will have to settle for the ordinary.", "author": "Jim Rohn"},
    {"text": "Trust because you are willing to accept the risk, not because it's safe or certain.", "author": "Anonymous"},
    {"text": "Take up one idea. Make that one idea your life — think of it, dream of it, live on that idea.", "author": "Swami Vivekananda"},
    {"text": "All our dreams can come true — if we have the courage to pursue them.", "author": "Walt Disney"},
    {"text": "Good things come to people who wait, but better things come to those who go out and get them.", "author": "Anonymous"},
    {"text": "If you do what you always did, you will get what you always got.", "author": "Anonymous"},
    {"text": "Success is not final; failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
    {"text": "Definiteness of purpose is the starting point of all achievement.", "author": "W. Clement Stone"},
    {"text": "Life isn't about getting and having, it's about giving and being.", "author": "Kevin Kruse"},
    {"text": "Whatever the mind of man can conceive and believe, it can achieve.", "author": "Napoleon Hill"},
    {"text": "I've learned that people will forget what you said, people will forget what you did, but people will never forget how you made them feel.", "author": "Maya Angelou"},
    {"text": "Either you run the day, or the day runs you.", "author": "Jim Rohn"},
    {"text": "Happiness is not something readymade. It comes from your own actions.", "author": "Dalai Lama"},
    {"text": "If the wind will not serve, take to the oars.", "author": "Latin Proverb"},
    {"text": "You can't use up creativity. The more you use, the more you have.", "author": "Maya Angelou"},
    {"text": "Dream big and dare to fail.", "author": "Norman Vaughan"},
    {"text": "You may be disappointed if you fail, but you are doomed if you don't try.", "author": "Beverly Sills"},
    {"text": "Remember that not getting what you want is sometimes a wonderful stroke of luck.", "author": "Dalai Lama"},
    {"text": "You can't build a reputation on what you are going to do.", "author": "Henry Ford"},
    {"text": "It's not what you look at that matters, it's what you see.", "author": "Henry David Thoreau"},
    {"text": "The only real mistake is the one from which we learn nothing.", "author": "Henry Ford"},
    {"text": "Life is 10% what happens to me and 90% of how I react to it.", "author": "Charles Swindoll"},
    {"text": "No act of kindness, no matter how small, is ever wasted.", "author": "Aesop"},
    {"text": "Twenty years from now you will be more disappointed by the things that you didn't do.", "author": "Mark Twain"},
    {"text": "I am not afraid of storms, for I am learning how to sail my ship.", "author": "Louisa May Alcott"},
    {"text": "Do one thing every day that scares you.", "author": "Eleanor Roosevelt"},
    {"text": "Well done is better than well said.", "author": "Benjamin Franklin"},
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"text": "It's always too early to quit.", "author": "Norman Vincent Peale"},
    {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
    {"text": "In the end, it's not the years in your life that count. It's the life in your years.", "author": "Abraham Lincoln"},
    {"text": "Change your thoughts and you change your world.", "author": "Norman Vincent Peale"},
]


class DailyQuotes(BasePlugin):
    """Displays a daily rotating quote from a built-in curated list."""

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["settings_template"] = "quotes/settings.html"
        params["style_settings"] = True
        return params

    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        quote = self._pick_quote(settings)

        template_params = {
            "quote_text": quote["text"],
            "quote_author": quote["author"],
            "plugin_settings": settings,
        }

        return self.render_image(dimensions, "quotes.html", "quotes.css", template_params)

    # ------------------------------------------------------------------

    def _pick_quote(self, settings: dict) -> dict:
        """Select a quote for today.  Rotates daily through the list."""
        day_of_year = datetime.now().timetuple().tm_yday
        return QUOTES[day_of_year % len(QUOTES)]
