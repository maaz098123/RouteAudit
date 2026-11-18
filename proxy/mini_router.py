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

    # TODO (Maaz): write the routing rule.
    #   Send it to STRONG_MODEL if EITHER:
    #     - the question is long  (more than 40 characters), OR
    #     - it contains any word from HARD_WORDS
    #   Otherwise send it to CHEAP_MODEL.
    #
    #   Hints:
    #     len(last_question)                          -> number of characters
    #     any(word in last_question for word in HARD_WORDS)  -> True if any hard word appears
    #     join two conditions with "or"

    return CHEAP_MODEL   # placeholder: replace with your rule