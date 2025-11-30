"""
AI Configuration and Client Management
Handles Gemini (free tier) and Claude (reasoning) API integrations
"""

import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from anthropic import Anthropic
from config import settings

logger = logging.getLogger(__name__)

class AIConfig:
    """Centralized AI API configuration and client management"""
    
    def __init__(self):
        self.gemini_client: Optional[genai.GenerativeModel] = None
        self.claude_client: Optional[Anthropic] = None
        self.gemini_available = False
        self.claude_available = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients with proper error handling"""
        
        # Initialize Gemini (free tier for text generation)
        try:
            gemini_api_key = settings.GOOGLE_GEMINI_API_KEY
            if gemini_api_key:
                # Clean and validate API key
                gemini_api_key = gemini_api_key.strip()
                logger.info(f"🔑 Gemini API key length: {len(gemini_api_key)}")
                logger.info(f"🔑 Gemini API key starts with: {gemini_api_key[:10]}...")
                
                genai.configure(api_key=gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-flash-latest')
                self.gemini_available = True
                logger.info("✅ Gemini API initialized with gemini-flash-latest")
            else:
                logger.warning("⚠️ GOOGLE_GEMINI_API_KEY not found - using demo mode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini API: {e}")
            self.gemini_available = False
        
        # Initialize Claude (for reasoning tasks)
        try:
            claude_api_key = settings.ANTHROPIC_API_KEY
            if claude_api_key:
                # Clean and validate API key
                claude_api_key = claude_api_key.strip()
                logger.info(f"🔑 Claude API key length: {len(claude_api_key)}")
                logger.info(f"🔑 Claude API key starts with: {claude_api_key[:10]}...")
                
                self.claude_client = Anthropic(api_key=claude_api_key)
                self.claude_available = True
                logger.info("✅ Claude API initialized successfully")
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY not found - using demo mode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude API: {e}")
            self.claude_available = False
    
    async def generate_with_gemini(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate text using Gemini (for basic text generation tasks)"""
        
        if not self.gemini_available:
            logger.warning("Gemini API not available - returning None")
            return None
        
        try:
            # Log API key info for debugging
            current_key = settings.GOOGLE_GEMINI_API_KEY.strip() if settings.GOOGLE_GEMINI_API_KEY else ""
            logger.info(f"🔧 Making Gemini API call with key length: {len(current_key)}")
            
            response = await self.gemini_client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            logger.error(f"🔍 Gemini API key being used: {settings.GOOGLE_GEMINI_API_KEY[:10] if settings.GOOGLE_GEMINI_API_KEY else 'None'}...")
            return None
    
    async def generate_with_claude(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: str = "claude-sonnet-4-20250514"
    ) -> Optional[str]:
        """Generate text using Claude (for reasoning tasks)"""
        
        if not self.claude_available:
            logger.warning("Claude API not available - returning None")
            return None
        
        try:
            # Log API key info for debugging
            current_key = settings.ANTHROPIC_API_KEY.strip() if settings.ANTHROPIC_API_KEY else ""
            logger.info(f"🔧 Making Claude API call with key length: {len(current_key)}")
            
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.claude_client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating with Claude: {e}")
            logger.error(f"🔍 Claude API key being used: {settings.ANTHROPIC_API_KEY[:10] if settings.ANTHROPIC_API_KEY else 'None'}...")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of AI services"""
        return {
            "gemini_available": self.gemini_available,
            "claude_available": self.claude_available,
            "gemini_model": "gemini-flash-latest" if self.gemini_available else None,
            "claude_model": "claude-sonnet-4-20250514" if self.claude_available else None,
            "strategy": "Hybrid - Gemini for text generation, Claude for reasoning"
        }

# Global instance
ai_config = AIConfig() 