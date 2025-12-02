"""
Conversation Service - Xử lý hội thoại với AI (OhMyGPT)

=== CHỨC NĂNG ===
1. Generate opening message cho conversation
2. Generate AI reply dựa vào context và history
3. Analyze user message (grammar, vocabulary)
4. Generate conversation summary và feedback

=== OHMYGPT API ===
- Base URL: https://api.ohmygpt.com/v1 (hoặc custom)
- Model: gpt-3.5-turbo / gpt-4
- Compatible với OpenAI API format

=== CONVERSATION FLOW ===
1. User bắt đầu → AI gửi opening message
2. User reply → AI analyze + response
3. Lặp lại đến khi đủ turns
4. End → Generate summary + scores
"""
import json
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from openai import OpenAI, AsyncOpenAI

from app.config import settings


@dataclass
class GrammarError:
    """Lỗi grammar trong câu"""
    original: str
    corrected: str
    error_type: str  # spelling, grammar, punctuation, word_choice
    explanation: str
    position: Optional[int] = None


@dataclass
class MessageAnalysis:
    """Kết quả phân tích tin nhắn user"""
    grammar_errors: List[GrammarError]
    vocabulary_used: List[str]
    sentiment: str  # positive, negative, neutral
    complexity_level: str  # basic, intermediate, advanced
    suggestions: List[str]


@dataclass
class ConversationContext:
    """Context cho conversation"""
    ai_role: str
    scenario_context: str
    user_level: str = "intermediate"
    suggested_topics: List[str] = field(default_factory=list)
    vocabulary_focus: List[str] = field(default_factory=list)


class ConversationService:
    """Service xử lý hội thoại với AI"""
    
    def __init__(self):
        self.api_key = settings.OHMYGPT_API_KEY
        self.base_url = settings.OHMYGPT_BASE_URL
        self.model = settings.OHMYGPT_MODEL
        self.temperature = settings.OHMYGPT_TEMPERATURE
        self.max_tokens = settings.OHMYGPT_MAX_TOKENS
        
        # Initialize OpenAI client (compatible with OhMyGPT)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def generate_opening_message(self, context: ConversationContext) -> str:
        """
        Generate tin nhắn mở đầu từ AI
        
        Args:
            context: ConversationContext với role và scenario
            
        Returns:
            Opening message từ AI
        """
        system_prompt = self._build_system_prompt(context)
        
        user_prompt = """Start the conversation with a friendly greeting. 
Keep it simple, 1-2 sentences, appropriate for English learners.
Do not explain that you're an AI. Stay in character."""
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            # Fallback opening
            return f"Hello! I'm your {context.ai_role}. How can I help you today?"
    
    async def generate_reply(
        self,
        context: ConversationContext,
        history: List[Dict[str, str]],
        user_message: str
    ) -> str:
        """
        Generate AI reply dựa vào context và history
        
        Args:
            context: ConversationContext
            history: List of {"role": "user"|"assistant", "content": "..."}
            user_message: Tin nhắn mới từ user
            
        Returns:
            AI reply message
        """
        system_prompt = self._build_system_prompt(context)
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return "That's interesting! Could you tell me more?"
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build system prompt cho AI"""
        
        prompt = f"""You are playing the role of: {context.ai_role}
Scenario: {context.scenario_context}

Guidelines for your responses:
1. Keep responses simple and clear (1-3 sentences)
2. Use vocabulary appropriate for {context.user_level} English learners
3. Be encouraging, friendly, and helpful
4. Stay completely in character - never break character
5. Ask follow-up questions to keep the conversation going
6. If the user makes mistakes, gently model correct usage
7. Respond ONLY in English

Communication style:
- Natural and conversational
- Avoid complex grammar structures
- Use common everyday vocabulary
- Add variety to your responses"""
        
        if context.suggested_topics:
            topics = ", ".join(context.suggested_topics)
            prompt += f"\n\nSuggested topics to discuss: {topics}"
        
        if context.vocabulary_focus:
            vocab = ", ".join(context.vocabulary_focus)
            prompt += f"\n\nTry to naturally incorporate these words: {vocab}"
        
        return prompt
    
    def analyze_message(self, message: str) -> MessageAnalysis:
        """
        Phân tích tin nhắn của user (không cần API call)
        
        Args:
            message: Tin nhắn từ user
            
        Returns:
            MessageAnalysis với grammar errors, vocabulary, etc.
        """
        grammar_errors = self._check_grammar(message)
        vocabulary = self._extract_vocabulary(message)
        sentiment = self._detect_sentiment(message)
        complexity = self._assess_complexity(message)
        suggestions = self._generate_suggestions(grammar_errors, vocabulary)
        
        return MessageAnalysis(
            grammar_errors=grammar_errors,
            vocabulary_used=vocabulary,
            sentiment=sentiment,
            complexity_level=complexity,
            suggestions=suggestions
        )
    
    def _check_grammar(self, message: str) -> List[GrammarError]:
        """
        Kiểm tra lỗi grammar cơ bản
        
        Note: Đây là simple checker. Production nên dùng LanguageTool API
        """
        errors = []
        words = message.split()
        
        # Check 1: Lowercase 'i' should be 'I'
        if ' i ' in message.lower() or message.lower().startswith('i '):
            original_pos = message.lower().find(' i ')
            if original_pos == -1:
                original_pos = 0
            errors.append(GrammarError(
                original=message,
                corrected=message.replace(' i ', ' I ').replace('i ', 'I ', 1) if message.lower().startswith('i ') else message.replace(' i ', ' I '),
                error_type="capitalization",
                explanation="The pronoun 'I' should always be capitalized",
                position=original_pos
            ))
        
        # Check 2: Double spaces
        if '  ' in message:
            errors.append(GrammarError(
                original=message,
                corrected=message.replace('  ', ' '),
                error_type="spacing",
                explanation="Remove extra spaces between words"
            ))
        
        # Check 3: Common mistakes
        common_mistakes = {
            "your welcome": ("you're welcome", "grammar", "'Your' is possessive, 'you're' means 'you are'"),
            "i'm want": ("I want", "grammar", "Remove 'am' - 'want' is already a verb"),
            "he don't": ("he doesn't", "grammar", "Use 'doesn't' with he/she/it"),
            "she don't": ("she doesn't", "grammar", "Use 'doesn't' with he/she/it"),
            "it don't": ("it doesn't", "grammar", "Use 'doesn't' with he/she/it"),
            "more better": ("better", "grammar", "Don't use 'more' with 'better'"),
            "more faster": ("faster", "grammar", "Don't use 'more' with 'faster'"),
        }
        
        message_lower = message.lower()
        for mistake, (correction, error_type, explanation) in common_mistakes.items():
            if mistake in message_lower:
                errors.append(GrammarError(
                    original=mistake,
                    corrected=correction,
                    error_type=error_type,
                    explanation=explanation
                ))
        
        return errors
    
    def _extract_vocabulary(self, message: str) -> List[str]:
        """Extract từ vựng có ý nghĩa từ message"""
        
        # Remove punctuation
        cleaned = message.lower()
        for char in '.,!?;:"\'-()[]{}':
            cleaned = cleaned.replace(char, ' ')
        
        words = cleaned.split()
        
        # Filter out common words (stop words)
        stop_words = {
            'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it',
            'they', 'them', 'this', 'that', 'these', 'those', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'a', 'an', 'the', 'and', 'but', 'or',
            'if', 'of', 'to', 'in', 'on', 'at', 'by', 'for', 'with', 'about',
            'as', 'into', 'like', 'through', 'after', 'over', 'between',
            'out', 'up', 'down', 'off', 'just', 'only', 'very', 'too',
            'also', 'not', 'no', 'yes', 'so', 'than', 'then', 'now', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
            'both', 'few', 'more', 'most', 'other', 'some', 'such', 'what',
            'which', 'who', 'whom', 'ok', 'okay', 'hi', 'hello', 'bye',
            'thanks', 'thank', 'please', 'sorry', 'want', 'need', 'get',
            'got', 'go', 'going', 'went', 'come', 'came', 'see', 'saw',
            'know', 'knew', 'think', 'thought', 'say', 'said', 'make', 'made',
            'take', 'took', 'give', 'gave', 'find', 'found', 'tell', 'told'
        }
        
        vocabulary = [w for w in words if w not in stop_words and len(w) > 2 and w.isalpha()]
        
        return list(set(vocabulary))
    
    def _detect_sentiment(self, message: str) -> str:
        """Detect sentiment của message"""
        
        message_lower = message.lower()
        
        positive_words = {
            'good', 'great', 'nice', 'love', 'like', 'happy', 'wonderful',
            'excellent', 'amazing', 'fantastic', 'awesome', 'beautiful',
            'thanks', 'thank', 'please', 'yes', 'sure', 'okay', 'ok',
            'perfect', 'best', 'better', 'enjoy', 'glad', 'excited'
        }
        
        negative_words = {
            'bad', 'hate', 'dislike', 'sad', 'angry', 'terrible', 'awful',
            'horrible', 'wrong', 'worst', 'worse', 'sorry', 'unfortunately',
            'problem', 'difficult', 'hard', 'confused', 'frustrated', 'no',
            'not', "don't", "doesn't", "didn't", "won't", "can't", "couldn't"
        }
        
        words = set(message_lower.split())
        
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def _assess_complexity(self, message: str) -> str:
        """Đánh giá độ phức tạp của message"""
        
        words = message.split()
        word_count = len(words)
        
        # Average word length
        if word_count == 0:
            return "basic"
        
        avg_word_length = sum(len(w) for w in words) / word_count
        
        # Sentence count
        sentence_endings = message.count('.') + message.count('!') + message.count('?')
        sentence_count = max(sentence_endings, 1)
        
        # Words per sentence
        words_per_sentence = word_count / sentence_count
        
        # Complexity assessment
        if avg_word_length > 6 and words_per_sentence > 15:
            return "advanced"
        elif avg_word_length > 5 or words_per_sentence > 10:
            return "intermediate"
        return "basic"
    
    def _generate_suggestions(self, errors: List[GrammarError], vocabulary: List[str]) -> List[str]:
        """Generate gợi ý cải thiện"""
        
        suggestions = []
        
        if errors:
            suggestions.append("Review the grammar errors and corrections")
        
        if len(vocabulary) < 3:
            suggestions.append("Try to use more varied vocabulary")
        
        if len(vocabulary) > 5:
            suggestions.append("Great vocabulary usage! Keep it up!")
        
        return suggestions
    
    async def generate_summary(
        self,
        context: ConversationContext,
        messages: List[Dict[str, str]],
        user_analysis: List[MessageAnalysis]
    ) -> Dict:
        """
        Generate conversation summary và scores
        
        Args:
            context: ConversationContext
            messages: All conversation messages
            user_analysis: Analysis of each user message
            
        Returns:
            Summary với scores và feedback
        """
        # Count user messages
        user_messages = [m for m in messages if m.get("role") == "user"]
        ai_messages = [m for m in messages if m.get("role") == "assistant"]
        
        # Aggregate errors
        all_errors = []
        all_vocabulary = set()
        
        for analysis in user_analysis:
            all_errors.extend(analysis.grammar_errors)
            all_vocabulary.update(analysis.vocabulary_used)
        
        # Calculate scores
        total_words = sum(len(m.get("content", "").split()) for m in user_messages)
        error_rate = len(all_errors) / max(total_words, 1)
        
        fluency_score = max(90 - (error_rate * 100), 0)
        grammar_score = max(100 - (len(all_errors) * 10), 0)
        vocabulary_score = min(len(all_vocabulary) * 5, 100)
        
        overall_score = (fluency_score * 0.4 + grammar_score * 0.3 + vocabulary_score * 0.3)
        
        # Generate AI feedback
        feedback = await self._generate_ai_feedback(
            context, messages, fluency_score, grammar_score, vocabulary_score
        )
        
        return {
            "total_turns": len(user_messages),
            "total_user_messages": len(user_messages),
            "total_ai_messages": len(ai_messages),
            "fluency_score": round(fluency_score, 1),
            "grammar_score": round(grammar_score, 1),
            "vocabulary_score": round(vocabulary_score, 1),
            "overall_score": round(overall_score, 1),
            "grammar_errors_count": len(all_errors),
            "vocabulary_used": list(all_vocabulary),
            "feedback": feedback
        }
    
    async def _generate_ai_feedback(
        self,
        context: ConversationContext,
        messages: List[Dict[str, str]],
        fluency: float,
        grammar: float,
        vocabulary: float
    ) -> str:
        """Generate AI feedback về conversation"""
        
        overall = (fluency + grammar + vocabulary) / 3
        
        if overall >= 85:
            return "🌟 Excellent conversation! Your English is very good. Keep practicing to maintain your level!"
        elif overall >= 70:
            return "✅ Good job! You communicated well. Focus on grammar accuracy to improve further."
        elif overall >= 50:
            return "💪 Nice effort! Practice more conversations to build your confidence and fluency."
        else:
            return "📚 Keep practicing! Try to use simpler sentences and focus on common phrases first."
    
    def generate_suggested_replies(self, ai_message: str, context: ConversationContext) -> List[str]:
        """Generate gợi ý câu trả lời cho user"""
        
        # Simple context-based suggestions
        ai_lower = ai_message.lower()
        
        suggestions = []
        
        # Question patterns
        if "how are you" in ai_lower or "how do you" in ai_lower:
            suggestions.extend(["I'm fine, thank you!", "I'm doing well.", "Pretty good, thanks!"])
        elif "would you like" in ai_lower:
            suggestions.extend(["Yes, please.", "No, thank you.", "That sounds good."])
        elif "what" in ai_lower and "?" in ai_message:
            suggestions.extend(["I think...", "I would like...", "I'm not sure."])
        elif "can i help" in ai_lower or "may i help" in ai_lower:
            suggestions.extend(["Yes, please.", "I'm looking for...", "Could you recommend..."])
        else:
            # Default suggestions
            suggestions = [
                "That sounds good.",
                "Could you tell me more?",
                "I'm not sure, what do you think?",
                "Yes, please."
            ]
        
        return suggestions[:4]


# Singleton instance
conversation_service = ConversationService()
