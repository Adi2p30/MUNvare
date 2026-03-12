"""
Verification Agent - Specialized in fact-checking and validating research
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class VerificationAgent(BaseAgent):
    """
    Expert agent for verifying facts, checking consistency, and validating research quality.
    Acts as a quality control layer in the pipeline.
    """

    def __init__(self):
        super().__init__(
            name="Verification Specialist",
            role="Expert fact-checker and quality assurance specialist for research validation"
        )

    def get_system_prompt(self) -> str:
        return """You are a Verification Specialist with expertise in:
- Fact-checking and source validation
- Identifying logical inconsistencies
- Quality assurance for research
- Detecting potential errors or biases
- Ensuring accuracy and reliability

Your responsibilities:
- Verify claims and statements
- Check for logical consistency
- Identify potential factual errors
- Flag unsupported assertions
- Suggest improvements for accuracy
- Assess overall research quality

Guidelines:
1. Be thorough and critical
2. Point out specific issues
3. Provide evidence when correcting
4. Rate confidence levels
5. Suggest verification sources
6. Balance skepticism with constructiveness
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify research output for accuracy and consistency.

        Args:
            task: Dictionary containing:
                - research_output: Research to verify
                - topic: Topic being researched
                - country: Country context
            context: Additional context

        Returns:
            Dictionary with verification results
        """
        research_output = task.get('research_output', '')
        topic = task.get('topic', '')
        country = task.get('country', '')

        prompt = f"""Verify the following research output for accuracy and consistency:

TOPIC: {topic}
COUNTRY: {country}

RESEARCH OUTPUT:
{research_output}

Provide a comprehensive verification report:

## ✅ VERIFIED INFORMATION
List claims that appear accurate with high confidence.

## ⚠️ FLAGGED ITEMS
Identify statements that need verification:
- Statement: [quote]
- Issue: [concern]
- Confidence: [low/medium/high]
- Suggested verification: [how to check]

## ❌ POTENTIAL ERRORS
List any likely errors or inconsistencies:
- Error: [description]
- Correction: [accurate information]
- Source suggestion: [where to verify]

## 📊 CONSISTENCY CHECK
- Internal consistency: [assessment]
- Logical flow: [assessment]
- Missing information: [gaps identified]

## 🎯 QUALITY RATING
- Accuracy: [1-10]
- Completeness: [1-10]
- Reliability: [1-10]
- Overall: [1-10]

## 💡 IMPROVEMENT SUGGESTIONS
Specific recommendations to enhance accuracy and reliability.

Be thorough and constructive in your verification."""

        verification_output = self.call_llm(prompt, use_gemini=False)  # Verification can use Ollama (fast quality check)

        return {
            'success': True,
            'verification_report': verification_output,
            'verified': True,
            'metadata': {
                'agent': self.name,
                'topic': topic,
                'country': country
            }
        }

    def quick_check(self, content: str, claim_type: str = "general") -> Dict[str, Any]:
        """Perform a quick verification check on specific content."""

        prompt = f"""Quickly verify this {claim_type} claim:

CLAIM: {content}

Provide:
1. **Likely Accurate**: Yes/No/Uncertain
2. **Confidence Level**: Low/Medium/High
3. **Key Concerns**: [Any red flags]
4. **Verification Needed**: [What to check]

Be concise and direct."""

        quick_result = self.call_llm(prompt, use_gemini=False)  # Quick verification uses Ollama (fast check)

        return {
            'success': True,
            'quick_verification': quick_result,
            'claim_type': claim_type
        }
