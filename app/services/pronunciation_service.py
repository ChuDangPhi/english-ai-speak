"""
Pronunciation Service - Xử lý phân tích phát âm với Deepgram API

=== CHỨC NĂNG ===
1. Nhận audio từ user (Base64 WebM)
2. Gửi đến Deepgram để speech-to-text
3. So sánh với reference text
4. Tính điểm: pronunciation, intonation, stress
5. Trả về feedback chi tiết từng từ

=== DEEPGRAM API ===
- Endpoint: https://api.deepgram.com/v1/listen
- Features: punctuate, diarize, utterances
- Model: nova-2 (best accuracy)

=== SCORING LOGIC ===
- Pronunciation Score: Độ chính xác phát âm từng từ
- Intonation Score: Ngữ điệu câu (lên/xuống giọng)
- Stress Score: Trọng âm từ và câu
"""
import base64
import httpx
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.config import settings


@dataclass
class WordAnalysis:
    """Phân tích từng từ"""
    word: str
    expected: str
    is_correct: bool
    confidence: float
    start_time: float
    end_time: float
    phonemes: Optional[List[str]] = None
    feedback: Optional[str] = None


@dataclass 
class PronunciationResult:
    """Kết quả phân tích phát âm"""
    transcript: str
    reference_text: str
    pronunciation_score: float
    intonation_score: float
    stress_score: float
    overall_score: float
    word_analysis: List[WordAnalysis]
    feedback: str
    areas_to_improve: List[str]
    audio_duration: float


class PronunciationService:
    """Service xử lý phân tích phát âm"""
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1/listen"
        
    async def analyze_pronunciation(
        self,
        audio_base64: str,
        reference_text: str,
        audio_format: str = "webm"
    ) -> PronunciationResult:
        """
        Phân tích phát âm từ audio
        
        Args:
            audio_base64: Audio data dạng Base64
            reference_text: Text chuẩn để so sánh
            audio_format: Format audio (webm, mp3, wav)
            
        Returns:
            PronunciationResult với điểm số và feedback
        """
        # 1. Decode Base64 to bytes
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            raise ValueError(f"Invalid Base64 audio: {e}")
        
        # 2. Call Deepgram API
        deepgram_result = await self._call_deepgram(audio_bytes, audio_format)
        
        # 3. Extract transcript
        transcript = self._extract_transcript(deepgram_result)
        words_data = self._extract_words(deepgram_result)
        
        # 4. Compare with reference
        word_analysis = self._analyze_words(words_data, reference_text)
        
        # 5. Calculate scores
        pronunciation_score = self._calculate_pronunciation_score(word_analysis)
        intonation_score = self._calculate_intonation_score(deepgram_result)
        stress_score = self._calculate_stress_score(word_analysis, reference_text)
        
        overall_score = (
            pronunciation_score * 0.5 +
            intonation_score * 0.25 +
            stress_score * 0.25
        )
        
        # 6. Generate feedback
        feedback, areas_to_improve = self._generate_feedback(
            pronunciation_score, intonation_score, stress_score, word_analysis
        )
        
        # 7. Get audio duration
        audio_duration = self._get_audio_duration(deepgram_result)
        
        return PronunciationResult(
            transcript=transcript,
            reference_text=reference_text,
            pronunciation_score=round(pronunciation_score, 1),
            intonation_score=round(intonation_score, 1),
            stress_score=round(stress_score, 1),
            overall_score=round(overall_score, 1),
            word_analysis=word_analysis,
            feedback=feedback,
            areas_to_improve=areas_to_improve,
            audio_duration=audio_duration
        )
    
    async def _call_deepgram(self, audio_bytes: bytes, audio_format: str) -> dict:
        """Gọi Deepgram API để speech-to-text"""
        
        # Content type mapping
        content_types = {
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        content_type = content_types.get(audio_format, "audio/webm")
        
        # API parameters
        params = {
            "model": "nova-2",
            "language": "en",
            "punctuate": "true",
            "utterances": "true",
            "words": "true",           # Get word-level timestamps
            "smart_format": "true",
            "diarize": "false"
        }
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": content_type
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    params=params,
                    headers=headers,
                    content=audio_bytes
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                raise Exception(f"Deepgram API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Network error calling Deepgram: {e}")
    
    def _extract_transcript(self, result: dict) -> str:
        """Trích xuất transcript từ Deepgram response"""
        try:
            channels = result.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    return alternatives[0].get("transcript", "")
        except (KeyError, IndexError):
            pass
        return ""
    
    def _extract_words(self, result: dict) -> List[dict]:
        """Trích xuất thông tin từng từ từ Deepgram response"""
        try:
            channels = result.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    return alternatives[0].get("words", [])
        except (KeyError, IndexError):
            pass
        return []
    
    def _analyze_words(self, words_data: List[dict], reference_text: str) -> List[WordAnalysis]:
        """So sánh từng từ với reference text"""
        
        # Normalize reference text
        ref_words = reference_text.lower().replace(".", "").replace(",", "").replace("?", "").replace("!", "").split()
        
        analysis = []
        ref_index = 0
        
        for word_info in words_data:
            spoken_word = word_info.get("word", "").lower()
            confidence = word_info.get("confidence", 0)
            start_time = word_info.get("start", 0)
            end_time = word_info.get("end", 0)
            
            # Find matching reference word
            expected_word = ""
            is_correct = False
            
            if ref_index < len(ref_words):
                expected_word = ref_words[ref_index]
                
                # Check similarity
                similarity = SequenceMatcher(None, spoken_word, expected_word).ratio()
                is_correct = similarity >= 0.8  # 80% similarity threshold
                
                if is_correct:
                    ref_index += 1
            
            # Generate word feedback
            word_feedback = None
            if not is_correct and expected_word:
                word_feedback = f"Expected '{expected_word}', heard '{spoken_word}'"
            
            analysis.append(WordAnalysis(
                word=spoken_word,
                expected=expected_word,
                is_correct=is_correct,
                confidence=confidence,
                start_time=start_time,
                end_time=end_time,
                feedback=word_feedback
            ))
        
        return analysis
    
    def _calculate_pronunciation_score(self, word_analysis: List[WordAnalysis]) -> float:
        """Tính điểm phát âm dựa trên số từ đúng"""
        if not word_analysis:
            return 0.0
        
        correct_count = sum(1 for w in word_analysis if w.is_correct)
        total = len(word_analysis)
        
        # Base score from accuracy
        accuracy = correct_count / total
        
        # Bonus from confidence
        avg_confidence = sum(w.confidence for w in word_analysis) / total
        
        # Combined score (70% accuracy, 30% confidence)
        score = (accuracy * 70) + (avg_confidence * 30)
        
        return min(score, 100)
    
    def _calculate_intonation_score(self, result: dict) -> float:
        """
        Tính điểm ngữ điệu
        
        Logic đơn giản:
        - Kiểm tra có đủ utterances không
        - Kiểm tra độ dài phù hợp
        - Confidence cao = ngữ điệu tốt
        """
        try:
            channels = result.get("results", {}).get("channels", [])
            if not channels:
                return 70.0  # Default
            
            alternatives = channels[0].get("alternatives", [])
            if not alternatives:
                return 70.0
            
            # Get overall confidence as proxy for intonation
            confidence = alternatives[0].get("confidence", 0.7)
            
            # Scale to 0-100
            score = confidence * 100
            
            # Adjust based on utterance count (natural speech has pauses)
            utterances = result.get("results", {}).get("utterances", [])
            if utterances:
                # Having some pauses is good
                utterance_bonus = min(len(utterances) * 2, 10)
                score = min(score + utterance_bonus, 100)
            
            return score
            
        except Exception:
            return 70.0
    
    def _calculate_stress_score(self, word_analysis: List[WordAnalysis], reference_text: str) -> float:
        """
        Tính điểm trọng âm
        
        Logic:
        - Kiểm tra timing giữa các từ
        - Từ quan trọng nên được nhấn mạnh (duration longer)
        """
        if not word_analysis:
            return 70.0
        
        # Calculate average word duration
        durations = [w.end_time - w.start_time for w in word_analysis if w.end_time > w.start_time]
        
        if not durations:
            return 70.0
        
        avg_duration = sum(durations) / len(durations)
        
        # Check consistency (not too fast, not too slow)
        # Good speech has varied but consistent duration
        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        
        # Lower variance = more consistent = higher score
        # But some variance is good for stress
        if 0.1 <= std_dev <= 0.3:
            score = 90  # Good variation
        elif std_dev < 0.1:
            score = 75  # Too monotone
        else:
            score = 70  # Too inconsistent
        
        # Bonus for correct words
        correct_ratio = sum(1 for w in word_analysis if w.is_correct) / len(word_analysis)
        score = score * (0.7 + 0.3 * correct_ratio)
        
        return min(score, 100)
    
    def _generate_feedback(
        self,
        pronunciation_score: float,
        intonation_score: float,
        stress_score: float,
        word_analysis: List[WordAnalysis]
    ) -> Tuple[str, List[str]]:
        """Generate feedback và areas to improve"""
        
        areas_to_improve = []
        feedback_parts = []
        
        # Overall assessment
        overall = (pronunciation_score + intonation_score + stress_score) / 3
        
        if overall >= 85:
            feedback_parts.append("🌟 Excellent pronunciation!")
        elif overall >= 70:
            feedback_parts.append("✅ Good job! Keep practicing.")
        elif overall >= 50:
            feedback_parts.append("💪 Getting better! Focus on the areas below.")
        else:
            feedback_parts.append("📚 Need more practice. Don't give up!")
        
        # Pronunciation feedback
        if pronunciation_score < 70:
            areas_to_improve.append("Pronunciation accuracy")
            wrong_words = [w for w in word_analysis if not w.is_correct and w.expected]
            if wrong_words[:3]:  # Top 3 wrong words
                words_list = ", ".join([f"'{w.expected}'" for w in wrong_words[:3]])
                feedback_parts.append(f"Practice these words: {words_list}")
        
        # Intonation feedback
        if intonation_score < 70:
            areas_to_improve.append("Intonation (sentence melody)")
            feedback_parts.append("Try to vary your pitch more naturally.")
        
        # Stress feedback
        if stress_score < 70:
            areas_to_improve.append("Word stress")
            feedback_parts.append("Pay attention to stressed syllables.")
        
        feedback = " ".join(feedback_parts)
        
        if not areas_to_improve:
            areas_to_improve.append("Keep up the excellent work!")
        
        return feedback, areas_to_improve
    
    def _get_audio_duration(self, result: dict) -> float:
        """Lấy độ dài audio từ Deepgram response"""
        try:
            metadata = result.get("metadata", {})
            return metadata.get("duration", 0)
        except Exception:
            return 0
    
    async def generate_reference_audio(self, text: str) -> Optional[str]:
        """
        Generate reference audio từ text (TTS)
        
        TODO: Implement với Google TTS hoặc AWS Polly
        
        Returns:
            Base64 encoded audio hoặc None
        """
        # Placeholder - implement TTS later
        return None
    
    def compare_phonemes(self, spoken: str, expected: str) -> Dict:
        """
        So sánh phonemes giữa spoken và expected
        
        TODO: Implement phoneme-level comparison
        """
        return {
            "spoken_phonemes": [],
            "expected_phonemes": [],
            "differences": []
        }


# Singleton instance
pronunciation_service = PronunciationService()
