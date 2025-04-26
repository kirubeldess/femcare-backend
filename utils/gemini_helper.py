import os
from dotenv import load_dotenv
from google import genai
import asyncio
from fastapi import HTTPException

# Load environment variables
load_dotenv()

# Configure the Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Create the client exactly as in the example
client = genai.Client(api_key=GOOGLE_API_KEY)

async def get_health_consultation_response(symptoms: str) -> str:
    """
    Generate a health consultation response using Google's Gemini AI model based on user-reported symptoms.
    
    Args:
        symptoms (str): The user's reported symptoms.
        
    Returns:
        str: The AI-generated health consultation response.
        
    Raises:
        HTTPException: If there's an error with the Gemini API request or response.
    """
    try:
        # Create the prompt
        prompt = f"""
        Act as a healthcare consultation assistant. A user has reported the following symptoms:
        
        {symptoms}
        
        Provide a helpful response that includes:
        1. Possible causes for these symptoms
        2. General advice on managing these symptoms
        3. Clear guidance on when to seek professional medical care
        
        IMPORTANT: Make it clear that this is AI-generated advice and not a substitute for professional medical care.
        """
        
        # Use the example pattern exactly with gemini-2.0-flash model
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash", 
            contents=prompt
        )
        
        return response.text
        
    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error generating Gemini response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}") 