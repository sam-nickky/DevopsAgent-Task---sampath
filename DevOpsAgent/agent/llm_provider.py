
import json
import logging
import requests
from typing import Dict, Any, Optional

class LLMProvider:
    def __init__(self, provider: str = "ollama", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Default models for each provider
        self.default_models = {
            "ollama": "llama2",  # Free local model
            "groq": "llama2-70b-4096",  # Free tier available
            "anthropic": "claude-3-haiku-20240307",  # Has free tier
            "openai": "gpt-3.5-turbo"  # Fallback
        }
        
        self.model = model or self.default_models.get(self.provider, "llama2")
        
    def analyze_logs(self, logs: str, alert_type: str) -> Dict[str, Any]:
        """Analyze logs using the configured LLM provider"""
        prompt = self._create_analysis_prompt(logs, alert_type)
        
        try:
            if self.provider == "ollama":
                return self._query_ollama(prompt)
            elif self.provider == "groq":
                return self._query_groq(prompt)
            elif self.provider == "anthropic":
                return self._query_anthropic(prompt)
            elif self.provider == "openai":
                return self._query_openai(prompt)
            else:
                return self._fallback_analysis(alert_type)
                
        except Exception as e:
            self.logger.error(f"Error with {self.provider} provider: {e}")
            return self._fallback_analysis(alert_type)
    
    def _create_analysis_prompt(self, logs: str, alert_type: str) -> str:
        return f"""
You are OpsBot, an AI DevOps assistant. Analyze the following logs to identify the possible cause of a {alert_type}.

Instructions:
1. Look for patterns that could cause high resource usage
2. Identify specific error messages or warnings
3. Provide a clear, actionable root cause analysis
4. Suggest remediation steps
5. Rate your confidence level (HIGH/MEDIUM/LOW)

Logs to analyze:
{logs[:4000]}

Respond in JSON format:
{{
    "root_cause": "Brief description of the identified cause",
    "confidence": "HIGH/MEDIUM/LOW",
    "evidence": ["List of specific log entries that support your analysis"],
    "recommended_actions": ["List of suggested remediation steps"],
    "requires_human_intervention": true/false
}}
"""
    
    def _query_ollama(self, prompt: str) -> Dict[str, Any]:
        """Query local Ollama instance (free)"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get("response", "{}"))
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Ollama query failed: {e}")
            raise
    
    def _query_groq(self, prompt: str) -> Dict[str, Any]:
        """Query Groq API (has free tier)"""
        if not self.api_key:
            raise Exception("Groq API key required")
            
        try:
            import groq
            client = groq.Groq(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are OpsBot, a reliable AI DevOps assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Groq query failed: {e}")
            raise
    
    def _query_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Query Anthropic Claude API (has free tier)"""
        if not self.api_key:
            raise Exception("Anthropic API key required")
            
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Anthropic query failed: {e}")
            raise
    
    def _query_openai(self, prompt: str) -> Dict[str, Any]:
        """Query OpenAI API (fallback)"""
        if not self.api_key:
            raise Exception("OpenAI API key required")
            
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are OpsBot, a reliable AI DevOps assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"OpenAI query failed: {e}")
            raise
    
    def _fallback_analysis(self, alert_type: str) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable"""
        return {
            "root_cause": f"Unable to analyze {alert_type} automatically - LLM provider unavailable",
            "confidence": "LOW",
            "evidence": ["LLM analysis failed"],
            "recommended_actions": [
                "Check system logs manually",
                "Restart affected services if needed",
                "Monitor system metrics"
            ],
            "requires_human_intervention": True
        }
