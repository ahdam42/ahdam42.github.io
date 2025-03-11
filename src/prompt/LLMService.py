import logging
import httpx


LLM_URL = "http://localhost:1234/v1/chat/completions"

class LLMService:
    @staticmethod
    def get_llm_response(prompt, temperature=0.8):
        try:
            data = {
                "model": "mistral-nemo-instruct-2407",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 10000
            }
            response = httpx.post(LLM_URL, json=data, timeout=None)
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"].strip()
            
            logging.error(f"Unexpected response structure: {response_data}")
            return ""
        except Exception as e:
            logging.error(f"LLM request failed: {str(e)}")
            return ""