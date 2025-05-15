# utils/gemini_helper.py
import os
from dotenv import load_dotenv
from google import genai
import asyncio
from fastapi import HTTPException

# from pydantic_schemas.ai_consultation import ConsultationType

# Load environment variables
load_dotenv()

# Configure the Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Create the client exactly as in the example
client = genai.Client(api_key=GOOGLE_API_KEY)

# Supported languages and their codes
SUPPORTED_LANGUAGES = {"en": "English", "am": "Amharic", "or": "Oromo"}  # Afaan Oromo


async def get_health_consultation_response(symptoms: str, language: str = "en") -> str:
    """
    Generate a health consultation response using Google's Gemini AI model based on user-reported symptoms.
    Supports multiple languages.

    Args:
        symptoms (str): The user's reported symptoms.
        language (str): The language code ("en", "am", "or")

    Returns:
        str: The AI-generated health consultation response.

    Raises:
        HTTPException: If there's an error with the Gemini API request or response.
    """
    try:
        # Get the language name
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        # Create the prompt with language instruction
        prompt = f"""
        Act as a healthcare consultation assistant. A user has reported the following symptoms:
        
        {symptoms}
        
        Provide a helpful response that includes:
        1. Possible causes for these symptoms
        2. General advice on managing these symptoms
        3. Clear guidance on when to seek professional medical care
        
        IMPORTANT: Make it clear that this is AI-generated advice and not a substitute for professional medical care.
        
        LANGUAGE INSTRUCTION: Please respond in {lang_name}.
        """

        # Use the example pattern exactly with gemini-2.0-flash model
        response = await asyncio.to_thread(
            client.models.generate_content, model="gemini-2.0-flash", contents=prompt
        )

        return response.text

    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error generating Gemini response: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate AI response: {str(e)}"
        )


async def get_legal_consultation_response(
    issue_description: str, language: str = "en"
) -> str:
    """
    Generate a legal consultation response using Google's Gemini AI model based on user-described legal issues.
    Supports multiple languages.

    Args:
        issue_description (str): The user's described legal issue.
        language (str): The language code ("en", "am", "or")

    Returns:
        str: The AI-generated legal consultation response.

    Raises:
        HTTPException: If there's an error with the Gemini API request or response.
    """
    try:
        # Get the language name
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        # Create the prompt with language instruction
        prompt = f"""
        Act as a legal information assistant. A user has described the following legal issue:
        
        {issue_description}
        
        Provide a helpful response that includes:
        1. General information about this type of legal issue
        2. Potential legal considerations that might be relevant
        3. Suggestions for what types of documents or information might be useful to gather
        4. Types of legal professionals who typically handle such matters
        
        IMPORTANT: Make it clear that this is AI-generated information, not legal advice, and not a substitute for consultation with a qualified legal professional. Do not provide specific legal advice for their situation.
        
        LANGUAGE INSTRUCTION: Please respond in {lang_name}.
        """

        # Use the model
        response = await asyncio.to_thread(
            client.models.generate_content, model="gemini-2.0-flash", contents=prompt
        )

        return response.text

    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error generating legal consultation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate AI response: {str(e)}"
        )


async def get_mental_health_consultation_response(
    concern_description: str, language: str = "en"
) -> str:
    """
    Generate a mental health consultation response using Google's Gemini AI model based on user-described concerns.
    Supports multiple languages.

    Args:
        concern_description (str): The user's described mental health concern.
        language (str): The language code ("en", "am", "or")

    Returns:
        str: The AI-generated mental health consultation response.

    Raises:
        HTTPException: If there's an error with the Gemini API request or response.
    """
    try:
        # Get the language name
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        # Create the prompt with language instruction
        prompt = f"""
        Act as a mental health information assistant. A user has described the following mental health concern:
        
        {concern_description}
        
        Provide a compassionate and helpful response that includes:
        1. General information about this type of mental health concern
        2. Evidence-based coping strategies that may be helpful
        3. When and how to seek professional mental health support
        4. Resources they might consider (like support groups, helplines, etc.)
        
        IMPORTANT: Make it clear that this is AI-generated information and not a substitute for professional mental healthcare. Be empathetic, non-judgmental, and focus on providing general information rather than specific diagnoses or treatment plans.
        
        LANGUAGE INSTRUCTION: Please respond in {lang_name}.
        """

        # Use the model
        response = await asyncio.to_thread(
            client.models.generate_content, model="gemini-2.0-flash", contents=prompt
        )

        return response.text

    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error generating mental health consultation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate AI response: {str(e)}"
        )


async def get_consultation_response(
    consultation_type: str, query: str, language: str = "en"
) -> str:
    """
    Generate a consultation response based on the type of consultation requested.
    Supports multiple languages.

    Args:
        consultation_type (ConsultationType): The type of consultation (health, legal, mental_health)
        query (str): The user's query or description of symptoms/issues
        language (str): The language code ("en", "am", "or")

    Returns:
        str: The AI-generated consultation response

    Raises:
        HTTPException: If there's an error with the AI request or response
    """
    if consultation_type == "health":
        return await get_health_consultation_response(query, language)
    elif consultation_type == "legal":
        return await get_legal_consultation_response(query, language)
    elif consultation_type == "mental_health":
        return await get_mental_health_consultation_response(query, language)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported consultation type: {consultation_type}",
        )


async def check_profanity_llm(text_to_check: str, language: str = "en") -> bool:
    """
    Checks if the given text contains profanity using Google's Gemini AI model.

    Args:
        text_to_check (str): The text to be checked for profanity.
        language (str): The language of the text (e.g., "en", "am").

    Returns:
        bool: True if profanity is detected, False otherwise.

    Raises:
        HTTPException: If there's an error with the Gemini API request or if the response is not parsable.
    """
    try:
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        prompt = f"""
        Analyze the following text and determine if it contains any profanity, hate speech, or substantially offensive content.
        Text to analyze: "{text_to_check}"
        
        Respond with only "YES" if profanity/offensive content is detected, or "NO" if it is not.
        Do not provide any explanation or any other words.
        Language of the text is {lang_name}.
        """

        # Use a model that is good for classification tasks, like gemini-2.0-flash or a future classification model
        response = await asyncio.to_thread(
            client.models.generate_content, model="gemini-2.0-flash", contents=prompt
        )

        # Debug: print(f"Gemini raw response for profanity check: {response.text}")

        # Process the response
        # The model should ideally return a simple "YES" or "NO".
        # We should be robust to minor variations, like leading/trailing whitespace or case differences.
        processed_response = response.text.strip().upper()
        if processed_response == "YES":
            return True
        elif processed_response == "NO":
            return False
        else:
            # This case means the model didn't follow instructions perfectly.
            # Log this for monitoring. For safety, we might assume profanity if uncertain,
            # or try a fallback, or return False and flag for human review.
            # For now, let's log it and assume not profane to avoid false positives, but this is a design choice.
            print(
                f"Warning: Unexpected response from LLM for profanity check: '{response.text}'. Assuming not profane."
            )
            return False

    except Exception as e:
        print(f"Error during LLM profanity check: {str(e)}")
        # In case of an error with the LLM, we could fallback to a simpler check or deny by default.
        # For now, re-raising as an HTTPException might be too disruptive for content creation.
        # Let's return False and log the error. This means if the LLM fails, profanity check is bypassed.
        # A more robust solution would have a fallback (like the simple list) or a circuit breaker.
        # Consider what the safest default is: block content or allow it if the check fails.
        # For now, allowing it to prevent service disruption if LLM has issues.
        print(
            f"LLM Profanity check failed for text: '{text_to_check[:50]}...'. Error: {e}. Allowing content."
        )
        return False  # Fallback: assume not profane if LLM check fails
