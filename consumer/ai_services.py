"""
Enhanced AI Services for SwasthCare Consumer App
Includes Azure Speech Services, AI Chatbot, and Nutritional AI Assistant
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Generator
from django.conf import settings
from django.core.cache import cache
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
# import azure.cognitiveservices.speech as speechsdk
from azure.core.exceptions import AzureError

# Configure logging
logger = logging.getLogger(__name__)

class SwasthCareAIService:
    """
    Comprehensive AI service for SwasthCare application
    Integrates Azure Speech Services with AI chatbot functionality
    """
    
    def __init__(self):
        self.ai_client = None
        # self.speech_config = None
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize Azure AI and Speech services"""
        try:
            # Initialize AI Inference client
            self.ai_client = ChatCompletionsClient(
                endpoint=settings.AZURE_AI_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_AI_API_KEY)
            )
            
            # # Initialize Speech services
            # self.speech_config = speechsdk.SpeechConfig(
            #     subscription=settings.AZURE_SPEECH_KEY,
            #     region=settings.AZURE_SPEECH_REGION
            # )
            
            # Configure speech settings
            # self.speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
            # self.speech_config.speech_recognition_language = "en-US"
            
            logger.info("Azure AI and Speech services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {str(e)}")
            raise
    
    def chat_about_product(self, product_json: Dict, user_question: str, 
                          stream: bool = False, user_profile: Optional[Dict] = None) -> str:
        """
        Enhanced product chatbot with personalized responses
        
        Args:
            product_json: Product data dictionary
            user_question: User's question
            stream: Whether to stream the response
            user_profile: User profile data for personalization
        
        Returns:
            AI response string or generator for streaming
        """
        try:
            # Generate personalized system prompt
            system_prompt = self._generate_system_prompt(user_profile)
            
            # Create comprehensive product context
            product_context = self._create_product_context(product_json)
            
            # Generate user prompt with context
            user_prompt = f"""
            Product Information:
            {product_context}
            
            User Question: {user_question}
            
            Please provide a helpful, accurate, and personalized response based on the product information.
            If the question is about health, nutrition, or dietary advice, consider the user's profile if provided.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt)
            ]
            
            if stream:
                return self._stream_response(messages)
            else:
                return self._get_response(messages)
                
        except Exception as e:
            logger.error(f"Error in chat_about_product: {str(e)}")
            return f"I apologize, but I'm having trouble processing your question right now. Please try again."
    
    def _generate_system_prompt(self, user_profile: Optional[Dict] = None) -> str:
        """Generate personalized system prompt based on user profile"""
        base_prompt = """
        You are SwasthCare AI, a knowledgeable and friendly assistant specializing in food products, nutrition, and health.
        
        Your capabilities include:
        - Analyzing food products and nutritional information
        - Providing health and dietary advice
        - Identifying allergens and dietary restrictions
        - Suggesting alternatives and recommendations
        - Explaining ingredients and their benefits/risks
        
        Guidelines:
        - Always base your answers on the provided product data
        - Be accurate and helpful in your responses
        - If information is not available, clearly state so
        - Provide actionable advice when appropriate
        - Use a friendly, professional tone
        """
        
        if user_profile:
            personalization = f"""
            
            User Profile Context:
            - Dietary preferences: {user_profile.get('dietary_preferences', 'Not specified')}
            - Health goals: {user_profile.get('health_goals', 'Not specified')}
            - Allergies: {user_profile.get('allergies', 'Not specified')}
            - Age group: {user_profile.get('age_group', 'Not specified')}
            
            Please personalize your responses based on this user profile information.
            """
            base_prompt += personalization
        
        return base_prompt
    
    def _create_product_context(self, product_json: Dict) -> str:
        """Create comprehensive product context for AI"""
        context_parts = []
        
        # Basic product info
        context_parts.append(f"Product Name: {product_json.get('prod_name', 'Unknown')}")
        context_parts.append(f"Product Type: {product_json.get('prod_type', 'Unknown')}")
        context_parts.append(f"Barcode: {product_json.get('barcode', 'Unknown')}")
        context_parts.append(f"Price: ₹{product_json.get('price', 'Unknown')}")
        
        # Dates and shelf life
        context_parts.append(f"Manufacturing Date: {product_json.get('manufacturing_date', 'Unknown')}")
        if 'expiry' in product_json:
            expiry = product_json['expiry']
            context_parts.append(f"Expiry Date: {expiry.get('expiry_date', 'Unknown')}")
            context_parts.append(f"Shelf Life: {expiry.get('tenure', 'Unknown')} months")
        
        # Ingredients
        ingredients = product_json.get('ingredients', product_json.get('Ingredients', 'Not specified'))
        context_parts.append(f"Ingredients: {ingredients}")
        
        # Nutritional information
        if 'nutritional_info' in product_json:
            nutrition = product_json['nutritional_info']
            context_parts.append("\nNutritional Information (per serving):")
            for key, value in nutrition.items():
                readable_key = key.replace('_', ' ').title()
                context_parts.append(f"- {readable_key}: {value}")
        
        # Special diet and allergen info
        if 'special_diet' in product_json:
            context_parts.append(f"Special Diet: {', '.join(product_json['special_diet'])}")
        
        if 'allergen_info' in product_json:
            context_parts.append(f"Allergen Information: {product_json['allergen_info']}")
        
        return "\n".join(context_parts)
    
    def _stream_response(self, messages: List) -> Generator[str, None, None]:
        """Stream AI response"""
        try:
            response = self.ai_client.complete(
                stream=True,
                messages=messages,
                model="gpt-4.1-mini",
                max_tokens=1024,
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            
            for update in response:
                if update.choices and update.choices[0].delta.content:
                    yield update.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def _get_response(self, messages: List) -> str:
        """Get complete AI response"""
        try:
            response = self.ai_client.complete(
                messages=messages,
                model="gpt-4.1-mini",
                max_tokens=1024,
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in getting response: {str(e)}")
            return f"I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def text_to_speech(self, text: str, voice_name: str = "en-US-AriaNeural") -> bytes:
        """
        Convert text to speech using Azure Speech Services
        
        Args:
            text: Text to convert to speech
            voice_name: Azure Neural Voice name
        
        Returns:
            Audio bytes data
        """
        try:
            # Configure voice
            self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Return audio data instead of playing
            )
            
            # Generate speech
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Error in text_to_speech: {str(e)}")
            return None
    
    def speech_to_text(self, audio_data: bytes) -> str:
        """
        Convert speech to text using Azure Speech Services
        
        Args:
            audio_data: Audio bytes data
        
        Returns:
            Transcribed text
        """
        try:
            # Create audio config from audio data
            audio_config = speechsdk.audio.AudioConfig(stream=speechsdk.audio.PushAudioInputStream())
            
            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Perform recognition
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            else:
                logger.error(f"Speech recognition failed: {result.reason}")
                return ""
                
        except Exception as e:
            logger.error(f"Error in speech_to_text: {str(e)}")
            return ""
    
    def analyze_product_healthiness(self, product_json: Dict, user_profile: Optional[Dict] = None) -> Dict:
        """
        Analyze product healthiness and provide recommendations
        
        Args:
            product_json: Product data
            user_profile: User profile for personalization
        
        Returns:
            Dictionary with health analysis and recommendations
        """
        try:
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze the healthiness of this product and provide a detailed assessment:
            
            {self._create_product_context(product_json)}
            
            Please provide:
            1. Overall health score (1-10)
            2. Key health benefits
            3. Potential health concerns
            4. Recommendations for consumption
            5. Suitable for which dietary preferences
            
            Format your response as a JSON object with these keys:
            - health_score
            - benefits
            - concerns
            - recommendations
            - dietary_suitability
            """
            
            messages = [
                SystemMessage(content="You are a nutrition expert. Provide accurate, evidence-based health analysis."),
                UserMessage(content=analysis_prompt)
            ]
            
            response = self._get_response(messages)
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured response
                return {
                    "health_score": "Analysis available",
                    "benefits": [],
                    "concerns": [],
                    "recommendations": [response],
                    "dietary_suitability": []
                }
                
        except Exception as e:
            logger.error(f"Error in analyze_product_healthiness: {str(e)}")
            return {
                "health_score": "Unable to analyze",
                "benefits": [],
                "concerns": ["Analysis temporarily unavailable"],
                "recommendations": ["Please try again later"],
                "dietary_suitability": []
            }
    
    def get_product_alternatives(self, product_json: Dict, user_profile: Optional[Dict] = None) -> List[str]:
        """
        Get healthier alternatives for a product
        
        Args:
            product_json: Product data
            user_profile: User profile for personalization
        
        Returns:
            List of alternative product suggestions
        """
        try:
            alternatives_prompt = f"""
            Based on this product information, suggest healthier alternatives:
            
            {self._create_product_context(product_json)}
            
            Please provide 5-7 specific alternative products or brands that would be healthier choices.
            Consider factors like:
            - Lower sugar/sodium content
            - Higher protein/fiber
            - Fewer artificial ingredients
            - Better nutritional profile
            
            Provide your response as a simple list of alternatives.
            """
            
            messages = [
                SystemMessage(content="You are a nutrition expert specializing in healthy food alternatives."),
                UserMessage(content=alternatives_prompt)
            ]
            
            response = self._get_response(messages)
            
            # Extract alternatives from response
            alternatives = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    # Clean up the line
                    clean_line = line.lstrip('-•0123456789. ').strip()
                    if clean_line:
                        alternatives.append(clean_line)
            
            return alternatives[:7]  # Return max 7 alternatives
            
        except Exception as e:
            logger.error(f"Error in get_product_alternatives: {str(e)}")
            return ["Unable to generate alternatives at this time"]
    
    def generate_meal_suggestions(self, product_json: Dict, meal_type: str = "any") -> List[str]:
        """
        Generate meal suggestions using the product
        
        Args:
            product_json: Product data
            meal_type: Type of meal (breakfast, lunch, dinner, snack, any)
        
        Returns:
            List of meal suggestions
        """
        try:
            meal_prompt = f"""
            Create meal suggestions using this product:
            
            Product: {product_json.get('prod_name', 'Unknown')}
            Type: {product_json.get('prod_type', 'Unknown')}
            Ingredients: {product_json.get('ingredients', product_json.get('Ingredients', 'Not specified'))}
            
            Meal type: {meal_type}
            
            Please provide 3-5 creative and healthy meal ideas that incorporate this product.
            Include brief preparation tips for each suggestion.
            """
            
            messages = [
                SystemMessage(content="You are a creative chef and nutritionist specializing in healthy meal planning."),
                UserMessage(content=meal_prompt)
            ]
            
            response = self._get_response(messages)
            
            # Extract meal suggestions from response
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    clean_line = line.lstrip('-•0123456789. ').strip()
                    if clean_line:
                        suggestions.append(clean_line)
            
            return suggestions[:5]  # Return max 5 suggestions
            
        except Exception as e:
            logger.error(f"Error in generate_meal_suggestions: {str(e)}")
            return ["Unable to generate meal suggestions at this time"]


# Global AI service instance
ai_service = SwasthCareAIService()

# Convenience functions for backward compatibility
def chat_about_product(product_json: Dict, user_question: str, stream: bool = False, user_profile: Optional[Dict] = None):
    """Backward compatible function for existing chatbot"""
    return ai_service.chat_about_product(product_json, user_question, stream, user_profile)

def text_to_speech(text: str, voice_name: str = "en-US-AriaNeural") -> bytes:
    """Convert text to speech"""
    return ai_service.text_to_speech(text, voice_name)

def speech_to_text(audio_data: bytes) -> str:
    """Convert speech to text"""
    return ai_service.speech_to_text(audio_data)

def analyze_product_healthiness(product_json: Dict, user_profile: Optional[Dict] = None) -> Dict:
    """Analyze product healthiness"""
    return ai_service.analyze_product_healthiness(product_json, user_profile)

def get_product_alternatives(product_json: Dict, user_profile: Optional[Dict] = None) -> List[str]:
    """Get healthier alternatives"""
    return ai_service.get_product_alternatives(product_json, user_profile)

def generate_meal_suggestions(product_json: Dict, meal_type: str = "any") -> List[str]:
    """Generate meal suggestions"""
    return ai_service.generate_meal_suggestions(product_json, meal_type)
