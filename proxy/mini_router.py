"""
RouteAudit - a tiny router of our own, for testing.

When the app asks for the model "routeaudit/auto", the proxy calls choose_model()
to decide which real model to use. This copies what routers like Tokenless and
Conifer do: send easy questions to a cheap model, harder ones to a stronger one.

Because the choice is made per turn, a conversation can switch models halfway
through - and that is exactly what causes cache breaks.
"""

AUTO_MODEL_NAME = "routeaudit/auto"

# Two free models you've already used.
CHEAP_MODEL = "dots-studio/dots-3-note-preview:free"
STRONG_MODEL = "nvidia/nemotron-3.5-lightning:free"

# Words that suggest a harder task.
HARD_WORDS = ["summarise", "summarize", "explain", "compare", "why"]


def choose_model(messages: list) -> str:
    """
    Look at the LATEST user question and return CHEAP_MODEL or STRONG_MODEL.
    """
    last_question = messages[-1]["content"].lower()   # the newest message, in lowercase

    # Routing rule: long questions or "hard" words go to the strong model.
    is_long = len(last_question) > 40
    has_hard_word = any(word in last_question for word in HARD_WORDS)

    if is_long or has_hard_word:
        return STRONG_MODEL
    return CHEAP_MODEL