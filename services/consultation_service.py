import uuid
from google import genai
from sqlalchemy.orm import Session
from models.ai_consultation import AIConsultation, ConsultationStatus, Language
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import os
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API with your API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

client = genai.Client(api_key=GOOGLE_API_KEY)


class ConsultationService:
    """
    Service for handling AI-powered consultations on women's health and mental wellbeing.

    This service provides:
    - Women's physical health information (menstrual cycles, pregnancy, etc.)
    - Mental health guidance and emotional support
    - Stress reduction and mindfulness techniques
    - Self-care recommendations
    - Support for multiple languages (English and Amharic)
    - Conversation context for follow-up questions
    - Detection of complex/sensitive health issues with professional healthcare referrals
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_consultation(
        self,
        user_id: str,
        symptoms: str,
        language: str = "english",
        conversation_id: Optional[str] = None,
        previous_consultation_id: Optional[str] = None,
    ) -> AIConsultation:
        """
        Create a new AI consultation for women's health questions or mental wellbeing concerns.

        This method records the user's query, processes it with the Gemini AI model,
        and provides guidance on physical health, mental health, stress reduction,
        and mindfulness practices. It maintains conversation context for follow-up questions.

        Args:
            user_id: ID of the user requesting the consultation
            symptoms: The user's health concern, question, or mental health topic
            language: Preferred language for the response (english or amharic)
            conversation_id: Optional ID to group related consultations
            previous_consultation_id: Optional ID of the previous consultation message

        Returns:
            The completed consultation with AI response
        """
        try:
            # Generate a new conversation_id if none was provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # Create consultation record with pending status
            consultation = AIConsultation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                symptoms=symptoms,
                language=language,
                conversation_id=conversation_id,
                previous_consultation_id=previous_consultation_id,
                status=ConsultationStatus.pending.value,
            )

            self.db.add(consultation)
            self.db.commit()
            self.db.refresh(consultation)

            # Process the consultation immediately
            consultation = await self.process_consultation(consultation.id)

            return consultation
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def process_consultation(self, consultation_id: str) -> AIConsultation:
        """Process a pending consultation using Gemini AI with conversation history"""
        try:
            # Get the consultation from DB
            consultation = (
                self.db.query(AIConsultation)
                .filter(AIConsultation.id == consultation_id)
                .first()
            )

            if not consultation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Consultation with ID {consultation_id} not found",
                )

            if consultation.status == ConsultationStatus.completed.value:
                return consultation

            # Retrieve conversation history if this is a follow-up question
            conversation_history = []
            if consultation.previous_consultation_id:
                conversation_history = self._get_conversation_history(consultation)

            # Get AI response with conversation context
            response = await self._get_womens_health_response(
                consultation.symptoms, consultation.language, conversation_history
            )

            # Update consultation with AI response
            consultation.ai_response = response["text"]
            consultation.contains_sensitive_issue = response["contains_sensitive_issue"]
            consultation.status = ConsultationStatus.completed.value

            self.db.commit()
            self.db.refresh(consultation)

            return consultation
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"AI processing error: {str(e)}"
            )

    def _get_conversation_history(
        self, consultation: AIConsultation
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a consultation"""
        history = []
        current = consultation

        # Limit to the last 5 messages to avoid context window limits
        for _ in range(5):
            if not current.previous_consultation_id:
                break

            # Get the previous consultation
            previous = (
                self.db.query(AIConsultation)
                .filter(AIConsultation.id == current.previous_consultation_id)
                .first()
            )

            if not previous:
                break

            # Add to history (oldest first)
            history.insert(
                0,
                {"user_query": previous.symptoms, "ai_response": previous.ai_response},
            )

            # Move to the previous message
            current = previous

        return history

    async def _get_womens_health_response(
        self,
        symptoms: str,
        language: str,
        conversation_history: List[Dict[str, Any]] = [],
    ) -> Dict[str, Any]:
        """Generate a women's health consultation response using Gemini in the specified language with conversation context"""
        try:
            # Format conversation history for the prompt
            history_text = ""
            if conversation_history:
                history_text = "Previous messages in this conversation:\n\n"
                for i, exchange in enumerate(conversation_history, 1):
                    history_text += f"Message {i}:\n"
                    history_text += f"User: {exchange['user_query']}\n"
                    history_text += f"Assistant: {exchange['ai_response']}\n\n"

            # Create the base prompt
            base_prompt = self._create_base_prompt(symptoms, history_text)

            # Add language instructions
            if language.lower() == "amharic":
                prompt = (
                    base_prompt
                    + """
                
                IMPORTANT: Respond in Amharic (አማርኛ) language. Make sure your entire response is in Amharic script 
                and is culturally appropriate for Ethiopian women, while maintaining medical accuracy.
                
                Also, add a line at the end of your response with "SENSITIVE_ISSUE: YES" if you detected a complex or sensitive health issue that requires professional medical attention, or "SENSITIVE_ISSUE: NO" if not. This line will be used for internal processing only and will be removed before showing the response to the user.
                """
                )
            else:  # Default to English
                prompt = (
                    base_prompt
                    + """
                
                Respond in clear, easy to understand English.
                
                Also, add a line at the end of your response with "SENSITIVE_ISSUE: YES" if you detected a complex or sensitive health issue that requires professional medical attention, or "SENSITIVE_ISSUE: NO" if not. This line will be used for internal processing only and will be removed before showing the response to the user.
                """
                )

            # Use the model
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.0-flash",
                contents=prompt,
            )

            response_text = response.text

            # Check for sensitive issue flag
            contains_sensitive_issue = False

            if "SENSITIVE_ISSUE: YES" in response_text:
                contains_sensitive_issue = True
                # Remove the flag from the response
                response_text = response_text.replace(
                    "SENSITIVE_ISSUE: YES", ""
                ).strip()
            else:
                # Remove the flag from the response if present
                response_text = response_text.replace("SENSITIVE_ISSUE: NO", "").strip()

            return {
                "text": response_text,
                "contains_sensitive_issue": contains_sensitive_issue,
            }

        except Exception as e:
            print(f"Error generating women's health consultation: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate AI response: {str(e)}"
            )

    def _create_base_prompt(self, symptoms: str, conversation_history: str = "") -> str:
        """Create the base prompt for the AI with conversation history"""
        context_instruction = ""
        if conversation_history:
            context_instruction = f"""
            This is a follow-up question in an ongoing conversation. Here is the conversation history:
            
            {conversation_history}
            
            Take into account the conversation context above when answering the current question. 
            If the user is asking a follow-up question, use the context from previous exchanges to 
            provide a more helpful and personalized response. Ensure continuity in your responses
            and don't repeat information already provided unless clarification is needed.
            
            """

        # List of terms/symptoms that might indicate complex or sensitive health issues
        sensitive_issue_detection = f"""
        ALERT - MEDICAL TRIAGE PROTOCOL:
        
        Carefully analyze the user's question for signs of ANY of the following urgent or sensitive health conditions:
        
        1. URGENT MEDICAL CONCERNS:
           - Severe pain (especially sudden, intense chest, abdominal, or head pain)
           - Bleeding (especially abnormal vaginal bleeding, heavy menstrual bleeding)
           - Shortness of breath or breathing difficulties
           - Dizziness, fainting, or loss of consciousness
           - Severe headaches, especially with other symptoms
           - Severe abdominal pain
           - Sudden vision changes
           - Sudden numbness or weakness
           - High fever (especially during pregnancy)
           - Pregnancy complications (cramping, bleeding, reduced movement)
        
        2. COMPLEX REPRODUCTIVE HEALTH ISSUES:
           - Abnormal Pap results or HPV
           - Reproductive organ masses, cysts or fibroids
           - Endometriosis symptoms
           - PCOS symptoms
           - Infertility concerns
           - Pregnancy complications
           - Menopause complications
           - Recurrent infections
        
        3. MENTAL HEALTH RED FLAGS:
           - Suicidal thoughts or self-harm
           - Severe depression symptoms
           - Panic attacks
           - Symptoms of post-partum depression
           - Severe anxiety interfering with daily life
           - Traumatic experiences
           - Eating disorders
        
        4. MEDICATION AND TREATMENT CONCERNS:
           - Questions about changing prescription medications
           - Reactions to medications
           - Questions about specific dosages
           - Requests for prescription recommendations
           - Treatment plan inquiries
        
        If ANY of these issues are detected in the user's question:
        
        1. BEGIN your response with a CLEAR and DIRECT statement about consulting a healthcare professional, using phrases like:
           "This situation requires professional medical attention. I strongly recommend consulting a healthcare provider without delay."
        
        2. EXPLICITLY state why professional consultation is necessary:
           "The symptoms/issues you've described could indicate a condition that needs proper medical diagnosis and treatment."
        
        3. EMPHASIZE the limitations of AI advice:
           "As an AI assistant, I cannot diagnose conditions or provide medical treatment. A healthcare professional can provide proper evaluation, testing, and treatment options for your specific situation."
        
        4. PROVIDE guidance on appropriate type of care (emergency, urgent, routine):
           - For potentially life-threatening issues: "Please seek emergency medical care immediately by calling emergency services or going to your nearest emergency room."
           - For urgent but non-emergency issues: "You should schedule an appointment with your healthcare provider as soon as possible, ideally within the next few days."
           - For routine concerns: "I recommend scheduling a consultation with your primary care provider or gynecologist to discuss these concerns thoroughly."
        
        5. AFTER these warnings, you may provide general educational information, but repeatedly emphasize the importance of professional medical advice.
        """

        return f"""
        Act as a women's health information assistant. A user has the following question or concern about women's health:
        
        {symptoms}
        
        {context_instruction}
        
        {sensitive_issue_detection}
        
        Provide a helpful, accurate, and compassionate response that includes:
        1. Information about this women's health topic (menstrual cycles, pregnancy, reproductive health, mental health, etc.)
        2. Relevant facts or explanations that could help the user understand their situation
        3. General guidance or suggestions that might be helpful
        4. If relevant, include stress reduction techniques, mindfulness practices, or emotional support strategies
        5. Clear indications of when professional medical or mental health care should be sought
        
        Keep in mind topics important to women such as:
        - Menstrual health and menstrual cycles
        - Pregnancy and fertility
        - Reproductive health
        - Hormonal changes and conditions
        - Contraception
        - Menopause
        - Mental health and emotional wellbeing
        - Stress reduction and mindfulness techniques
        - Self-care practices
        - Work-life balance
        - Preventive care and screenings
        
        For mental health concerns, offer:
        - Evidence-based stress reduction techniques
        - Mindfulness and meditation guidance appropriate for beginners
        - Emotional support and validation
        - Healthy coping mechanisms
        - Information on how mental health connects to physical health for women
        
        IMPORTANT: Make it clear that this is AI-generated information and not a substitute for professional medical or mental healthcare.
        Be empathetic, accurate, and focus on providing evidence-based information rather than specific diagnoses or treatment plans.
        """

    def get_consultation(self, consultation_id: str) -> Optional[AIConsultation]:
        """Get a consultation by ID"""
        consultation = (
            self.db.query(AIConsultation)
            .filter(AIConsultation.id == consultation_id)
            .first()
        )

        if not consultation:
            raise HTTPException(
                status_code=404,
                detail=f"Consultation with ID {consultation_id} not found",
            )

        return consultation

    def get_conversation_consultations(
        self, conversation_id: str
    ) -> List[AIConsultation]:
        """Get all consultations in a conversation"""
        return (
            self.db.query(AIConsultation)
            .filter(AIConsultation.conversation_id == conversation_id)
            .order_by(AIConsultation.created_at.asc())
            .all()
        )

    def get_user_consultations(self, user_id: str) -> List[AIConsultation]:
        """Get all consultations for a specific user"""
        return (
            self.db.query(AIConsultation)
            .filter(AIConsultation.user_id == user_id)
            .order_by(AIConsultation.created_at.desc())
            .all()
        )

    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a specific user, grouped by conversation_id"""
        # Get all consultations for the user
        consultations = (
            self.db.query(AIConsultation)
            .filter(AIConsultation.user_id == user_id)
            .order_by(AIConsultation.created_at.asc())
            .all()
        )

        # Group by conversation_id
        conversations = {}
        for consultation in consultations:
            if consultation.conversation_id not in conversations:
                conversations[consultation.conversation_id] = {
                    "conversation_id": consultation.conversation_id,
                    "started_at": consultation.created_at,
                    "last_updated": consultation.created_at,
                    "language": consultation.language,
                    "messages": [],
                }

            # Add message to conversation
            conversations[consultation.conversation_id]["messages"].append(
                {
                    "id": consultation.id,
                    "symptoms": consultation.symptoms,
                    "ai_response": consultation.ai_response,
                    "created_at": consultation.created_at,
                }
            )

            # Update last_updated time
            if (
                consultation.created_at
                > conversations[consultation.conversation_id]["last_updated"]
            ):
                conversations[consultation.conversation_id][
                    "last_updated"
                ] = consultation.created_at

        # Convert to list and sort by last_updated (most recent first)
        result = list(conversations.values())
        result.sort(key=lambda x: x["last_updated"], reverse=True)

        return result

    def get_sensitive_issue_consultations(
        self, limit: int = 20
    ) -> List[AIConsultation]:
        """Get consultations that were flagged as containing sensitive health issues"""
        return (
            self.db.query(AIConsultation)
            .filter(AIConsultation.contains_sensitive_issue == True)
            .order_by(AIConsultation.created_at.desc())
            .limit(limit)
            .all()
        )
