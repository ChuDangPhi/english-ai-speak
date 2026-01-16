"""
Text-to-Speech Service - Chuyển đổi văn bản thành giọng nói

Sử dụng Deepgram TTS API (chất lượng cao, giọng tự nhiên)
Fallback về gTTS nếu Deepgram không khả dụng
"""
import os
import uuid
from datetime import datetime
from typing import Optional
import asyncio
import httpx

from app.config import settings

# Directory lưu audio TTS
TTS_AUDIO_DIR = "uploads/audio/tts"


class TTSService:
    """Service chuyển văn bản thành audio"""
    
    # Deepgram TTS voices (English)
    # https://developers.deepgram.com/docs/tts-models
    VOICES = {
        "female_us": "aura-asteria-en",    # Female, US accent
        "female_uk": "aura-luna-en",       # Female, UK accent  
        "male_us": "aura-orion-en",        # Male, US accent
        "male_uk": "aura-arcas-en",        # Male, UK accent
        "female_soft": "aura-stella-en",   # Female, soft voice
        "male_deep": "aura-zeus-en",       # Male, deep voice
    }
    
    def __init__(self):
        # Tạo thư mục nếu chưa có
        os.makedirs(TTS_AUDIO_DIR, exist_ok=True)
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "female_us",
        language: str = "en"
    ) -> Optional[str]:
        """
        Chuyển text thành audio file sử dụng Deepgram TTS
        
        Args:
            text: Văn bản cần chuyển
            voice: Giọng đọc (female_us, male_us, female_uk, male_uk, etc.)
            language: Ngôn ngữ (en)
            
        Returns:
            URL của audio file hoặc None nếu lỗi
        """
        # Thử Deepgram TTS trước
        if settings.DEEPGRAM_API_KEY:
            result = await self._deepgram_tts(text, voice)
            if result:
                return result
        
        # Fallback về gTTS nếu Deepgram không khả dụng
        print("⚠️ Falling back to gTTS...")
        return await self._gtts_fallback(text, language)
    
    async def _deepgram_tts(self, text: str, voice: str = "female_us") -> Optional[str]:
        """
        Deepgram TTS API
        
        Models: aura-asteria-en, aura-luna-en, aura-stella-en, aura-orion-en, etc.
        Docs: https://developers.deepgram.com/docs/tts-models
        """
        try:
            # Get model name from voice key
            model = self.VOICES.get(voice, self.VOICES["female_us"])
            
            url = f"https://api.deepgram.com/v1/speak?model={model}"
            headers = {
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            print(f"🔊 Deepgram TTS: '{text[:50]}...' with voice={model}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"text": text}
                )
            
            if response.status_code == 200:
                # Save audio file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                filename = f"tts_{timestamp}_{unique_id}.mp3"
                filepath = os.path.join(TTS_AUDIO_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                audio_url = f"/uploads/audio/tts/{filename}"
                print(f"✅ Deepgram TTS saved: {audio_url}")
                return audio_url
            else:
                print(f"❌ Deepgram TTS error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Deepgram TTS error: {type(e).__name__}: {e}")
            return None
    
    async def _gtts_fallback(self, text: str, language: str = "en") -> Optional[str]:
        """Fallback to gTTS (Google Text-to-Speech)"""
        try:
            from gtts import gTTS
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"tts_{timestamp}_{unique_id}.mp3"
            filepath = os.path.join(TTS_AUDIO_DIR, filename)
            
            print(f"🔊 gTTS fallback: '{text[:50]}...'")
            
            # Run gTTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._generate_gtts(text, language, filepath)
            )
            
            audio_url = f"/uploads/audio/tts/{filename}"
            print(f"✅ gTTS saved: {audio_url}")
            return audio_url
            
        except ImportError:
            print("❌ gTTS not installed. Run: pip install gTTS")
            return None
        except Exception as e:
            print(f"❌ gTTS error: {type(e).__name__}: {e}")
            return None
    
    def _generate_gtts(self, text: str, language: str, filepath: str):
        """Synchronous gTTS audio generation"""
        from gtts import gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(filepath)


# Singleton instance
tts_service = TTSService()

