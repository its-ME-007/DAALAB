"""
Mistral AI Complexity Analyzer
Analyzes code and extracts time/space complexity information
"""

import os
import re
import json
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

def sanitize_text(text: str) -> str:
    """Remove non-ASCII characters (including emojis) to prevent Windows charmap errors."""
    if not text:
        return text
    return text.encode('ascii', errors='replace').decode('ascii')

class ComplexityAnalyzer:
    def __init__(self):
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.model = "mistral-large-latest"
    
    def analyze_code(self, code: str, language: str = "python") -> dict:
        """
        Analyze code and return time/space complexity
        
        Returns:
        {
            "time_complexity": "O(n²)",
            "time_complexity_class": "quadratic",  # for plotting
            "space_complexity": "O(n)",
            "space_complexity_class": "linear",
            "explanation": "...",
            "best_case": "O(n)",
            "average_case": "O(n²)",
            "worst_case": "O(n²)",
            "algorithm_name": "detected algorithm name"
        }
        """
        
        # Language-specific context
        lang_context = {
            "python": "Python",
            "cpp": "C++"
        }
        
        language_name = lang_context.get(language, language)
        
        prompt = f"""You are a computer science expert analyzing algorithm complexity.

Analyze this {language_name} code and provide ONLY a JSON response with these exact fields:

{{
    "time_complexity": "O(...)",
    "time_complexity_class": "constant|logarithmic|linear|linearithmic|quadratic|cubic|quartic|exponential|factorial",
    "space_complexity": "O(...)",
    "space_complexity_class": "constant|logarithmic|linear|linearithmic|quadratic|cubic|quartic|exponential",
    "explanation": "Brief explanation of the complexity analysis",
    "best_case": "O(...)",
    "average_case": "O(...)",
    "worst_case": "O(...)",
    "algorithm_name": "detected algorithm name or 'Unknown'"
}}

Code to analyze:
```{language_name.lower()}
{code}
```

Rules:
1. Return ONLY valid JSON, no markdown formatting
2. Use standard Big-O notation (O(1), O(log n), O(n), O(n log n), O(n²), O(n³), O(n⁴), O(2^n), O(n!))
3. time_complexity_class must be one of: constant, logarithmic, linear, linearithmic, quadratic, cubic, quartic, exponential, factorial
4. space_complexity_class must be one of: constant, logarithmic, linear, linearithmic, quadratic, cubic, quartic, exponential
5. Provide realistic complexity analysis based on the actual code structure
6. For {language_name}, consider language-specific features and STL/standard library functions
7. Use 'quartic' for O(n⁴) complexity (4 nested loops)"""

        try:
            chat_response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = chat_response.choices[0].message.content
            
            # Clean response - remove markdown code blocks if present
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = [
                "time_complexity", "time_complexity_class",
                "space_complexity", "space_complexity_class",
                "explanation"
            ]
            
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Sanitize all text fields to remove emojis
            for key, value in result.items():
                if isinstance(value, str):
                    result[key] = sanitize_text(value)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response was: {response_text}")
            return self._fallback_response("JSON parsing failed")
        
        except Exception as e:
            print(f"Mistral API Error: {e}")
            return self._fallback_response(f"Analysis failed: {str(e)}")
    
    def _fallback_response(self, error_msg: str) -> dict:
        """Return a safe fallback response when analysis fails"""
        return {
            "error": sanitize_text(f"Unable to analyze complexity: {error_msg}"),
            "time_complexity": "O(n)",
            "time_complexity_class": "linear",
            "space_complexity": "O(1)",
            "space_complexity_class": "constant",
            "explanation": f"Unable to analyze complexity: {error_msg}",
            "best_case": "Unknown",
            "average_case": "Unknown",
            "worst_case": "Unknown",
            "algorithm_name": "Unknown"
        }
    
    @staticmethod
    def complexity_to_function(complexity_class: str, input_size: int) -> float:
        """
        Convert complexity class to actual value for plotting
        Used to generate theoretical complexity curves
        """
        n = input_size
        
        complexity_map = {
            "constant": 1,
            "logarithmic": max(1, n * 0.1) if n > 0 else 1,  # log base 10 approximation
            "linear": n,
            "linearithmic": n * max(1, n * 0.1) if n > 0 else n,  # n log n
            "quadratic": n * n,
            "cubic": n * n * n,
            "quartic": n * n * n * n,  # n^4
            "exponential": min(2 ** min(n, 20), 1e10),  # Cap exponential growth
            "factorial": min(1e10, 1)  # Factorial grows too fast
        }
        
        return complexity_map.get(complexity_class, n)


# Standalone test function
def test_analyzer():
    """Test the complexity analyzer"""
    
    test_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
    
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze_code(test_code, "python")
    
    print("=" * 60)
    print("Complexity Analysis Result:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    test_analyzer()