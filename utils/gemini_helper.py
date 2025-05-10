# utils/gemini_helper.py
import os
from dotenv import load_dotenv
from google import genai
import asyncio
from fastapi import HTTPException
from pydantic_schemas.ai_consultation import ConsultationType

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
    consultation_type: ConsultationType, query: str, language: str = "en"
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
    if consultation_type == ConsultationType.health:
        return await get_health_consultation_response(query, language)
    elif consultation_type == ConsultationType.legal:
        return await get_legal_consultation_response(query, language)
    elif consultation_type == ConsultationType.mental_health:
        return await get_mental_health_consultation_response(query, language)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported consultation type: {consultation_type}",
        )
