# utils/moderation.py
from utils.gemini_helper import check_profanity_llm
import asyncio

# In a real application, this list would be much more extensive and possibly managed elsewhere.
# Consider using a library for more robust profanity filtering.
SIMPLE_PROFANITY_LIST = [
    "badword1",
    "badword2",
    "curseword",
    # Add more words as needed
]


async def contains_profanity(text: str, language: str = "en") -> bool:
    """Check if the given text contains any profanity using the LLM service."""
    if not text:  # Handle empty or None text
        return False
    # LLM-based check
    return await check_profanity_llm(text, language)

    # Fallback or alternative: simple list check (currently commented out)
    # lower_text = text.lower()
    # for word in SIMPLE_PROFANITY_LIST:
    #     if word in lower_text:
    #         return True
    # return False


async def moderate_content(text: str, language: str = "en") -> str:
    """
    Simple content moderation. For now, it just checks for profanity using the LLM.
    In the future, this could be expanded to use more advanced techniques,
    like AI-based content moderation services or masking profanity.
    """
    if await contains_profanity(text, language):
        # Action is typically taken in the router (e.g., raising HTTPException).
        # If masking or other modification were needed, it would happen here.
        # For now, this function primarily serves as a wrapper if we wanted to add masking later.
        # The boolean check from contains_profanity is what routers will use to decide to raise an error.
        pass  # Indicates profanity was found; router handles the exception.

    return text  # Returns original text; router decides action based on contains_profanity output.
