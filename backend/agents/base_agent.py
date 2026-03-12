"""
Base Agent Class - Foundation for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Each agent has a specific role and expertise.
    """

    def __init__(self, name: str, role: str, model: str = "gpt-4"):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            role: Role/purpose of the agent
            model: AI model to use (default: gpt-4)
        """
        self.name = name
        self.role = role
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'gemma3:1b')
        self.ollama_available = False

        # Check if Ollama is available
        try:
            import ollama
            ollama.list()
            self.ollama_available = True
        except:
            pass

    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the agent's primary task.

        Args:
            task: Task parameters
            context: Optional context from previous agents

        Returns:
            Result dictionary with output and metadata
        """
        pass

    def get_system_prompt(self) -> str:
        """
        Get the system prompt that defines this agent's personality and expertise.

        Returns:
            System prompt string
        """
        return f"""You are {self.name}, a specialized AI agent.

Your role: {self.role}

Guidelines:
- Focus on your specific expertise
- Provide accurate, professional information
- Use proper formatting and structure
- Be concise yet comprehensive
- Cite sources when applicable
"""

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False, use_gemini: bool = False):
        """
        Call the language model with a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt override
            stream: Whether to stream the response (returns generator if True)
            use_gemini: If False (DEFAULT), use Ollama/Gemma for fast orchestration; if True, use Gemini for complex core tasks

        Returns:
            LLM response (str) or generator for streaming
        """
        try:
            # DEFAULT: Use Ollama/Gemma for orchestration tasks (fast and cheap)
            if not use_gemini and self.ollama_available and not stream:
                import ollama
                sys_prompt = system_prompt or self.get_system_prompt()
                full_prompt = f"{sys_prompt}\n\n{prompt}"

                try:
                    response = ollama.generate(
                        model=self.ollama_model,
                        prompt=full_prompt
                    )
                    print(f"🚀 {self.name}: Using Ollama/{self.ollama_model} for orchestration")
                    return response['response']
                except Exception as e:
                    print(f"⚠ Ollama error in agent, falling back to Gemini: {e}")
                    # Fall through to Gemini

            # Try Gemini first (supports streaming) - for complex agent tasks
            if os.getenv('GEMINI_API_KEY'):
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
                model = genai.GenerativeModel('gemini-2.5-flash-lite')

                sys_prompt = system_prompt or self.get_system_prompt()
                full_prompt = f"{sys_prompt}\n\n{prompt}"

                if stream:
                    # Return streaming generator
                    response = model.generate_content(full_prompt, stream=True)
                    return self._gemini_stream_generator(response)
                else:
                    response = model.generate_content(full_prompt)
                    return response.text

            # Try OpenAI
            elif os.getenv('OPENAI_API_KEY'):
                import openai
                openai.api_key = os.getenv('OPENAI_API_KEY')

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                else:
                    messages.append({"role": "system", "content": self.get_system_prompt()})

                messages.append({"role": "user", "content": prompt})

                if stream:
                    # Return streaming generator
                    response = openai.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        stream=True
                    )
                    return self._openai_stream_generator(response)
                else:
                    response = openai.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7
                    )
                    return response.choices[0].message.content

            # Fallback to Anthropic
            elif os.getenv('ANTHROPIC_API_KEY'):
                import anthropic
                client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

                sys_prompt = system_prompt or self.get_system_prompt()

                if stream:
                    # Return streaming generator
                    with client.messages.stream(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4096,
                        system=sys_prompt,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        return self._anthropic_stream_generator(stream)
                else:
                    message = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4096,
                        system=sys_prompt,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return message.content[0].text

            else:
                raise ValueError("No API key found. Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY")

        except Exception as e:
            print(f"Error calling LLM: {e}")
            raise

    def _gemini_stream_generator(self, response):
        """Generator for Gemini streaming responses."""
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _openai_stream_generator(self, response):
        """Generator for OpenAI streaming responses."""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _anthropic_stream_generator(self, stream):
        """Generator for Anthropic streaming responses."""
        for text in stream.text_stream:
            yield text

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def __str__(self):
        return f"{self.name} ({self.role})"

    def __repr__(self):
        return f"<Agent: {self.name}>"
