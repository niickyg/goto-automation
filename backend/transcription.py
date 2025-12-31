"""
OpenAI Whisper integration for audio transcription.

Downloads call recordings and transcribes them using OpenAI Whisper API.
"""

import os
import logging
import tempfile
from typing import Optional, Tuple
from pathlib import Path
import httpx
from pydub import AudioSegment
from openai import OpenAI, AsyncOpenAI

from config import get_settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using OpenAI Whisper."""

    def __init__(self):
        """Initialize transcription service."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.async_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.temp_dir = Path(self.settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download_audio(
        self,
        url: str,
        headers: Optional[dict] = None
    ) -> Tuple[str, int]:
        """
        Download audio file from URL.

        Args:
            url: URL to download from
            headers: Optional HTTP headers (e.g., for authentication)

        Returns:
            Tuple of (file_path, file_size_bytes)

        Raises:
            httpx.HTTPError: If download fails
            ValueError: If file is too large
        """
        logger.info(f"Downloading audio from: {url[:100]}...")

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url, headers=headers or {}) as response:
                response.raise_for_status()

                # Check file size
                content_length = response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > self.settings.max_audio_size_mb:
                        raise ValueError(
                            f"Audio file too large: {size_mb:.2f}MB "
                            f"(max: {self.settings.max_audio_size_mb}MB)"
                        )

                # Determine file extension from content-type or URL
                content_type = response.headers.get("content-type", "")
                extension = self._get_extension_from_content_type(content_type)
                if not extension:
                    extension = Path(url).suffix or ".mp3"

                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=extension,
                    dir=self.temp_dir
                )

                total_bytes = 0
                try:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        temp_file.write(chunk)
                        total_bytes += len(chunk)
                finally:
                    temp_file.close()

                logger.info(
                    f"Downloaded {total_bytes / (1024 * 1024):.2f}MB "
                    f"to {temp_file.name}"
                )

                return temp_file.name, total_bytes

    def _get_extension_from_content_type(self, content_type: str) -> Optional[str]:
        """Get file extension from content type."""
        mappings = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/wave": ".wav",
            "audio/mp4": ".m4a",
            "audio/x-m4a": ".m4a",
            "audio/ogg": ".ogg",
            "audio/flac": ".flac",
        }
        return mappings.get(content_type.lower())

    def convert_to_whisper_format(self, input_path: str) -> str:
        """
        Convert audio to Whisper-compatible format.

        Whisper accepts: mp3, mp4, mpeg, mpga, m4a, wav, webm
        This method ensures the audio is in a compatible format and
        optimizes it for transcription.

        Args:
            input_path: Path to input audio file

        Returns:
            Path to converted file (may be same as input if no conversion needed)

        Raises:
            Exception: If conversion fails
        """
        input_path_obj = Path(input_path)
        extension = input_path_obj.suffix.lower()

        # These formats are already compatible
        compatible_formats = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

        if extension in compatible_formats:
            logger.info(f"Audio format {extension} is already compatible")
            return input_path

        logger.info(f"Converting {extension} to mp3 for Whisper compatibility")

        try:
            # Load audio file
            audio = AudioSegment.from_file(input_path)

            # Export as mp3
            output_path = input_path_obj.with_suffix(".mp3")
            audio.export(
                output_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ac", "1"]  # Convert to mono
            )

            logger.info(f"Converted audio to: {output_path}")

            # Clean up original file if conversion successful
            if output_path != input_path:
                try:
                    os.remove(input_path)
                except Exception as e:
                    logger.warning(f"Failed to remove original file: {e}")

            return str(output_path)

        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise

    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio file using OpenAI Whisper.

        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'en', 'es')
            prompt: Optional prompt to guide transcription

        Returns:
            Dictionary containing:
                - text: Full transcript
                - language: Detected language
                - duration: Audio duration in seconds

        Raises:
            Exception: If transcription fails
        """
        logger.info(f"Transcribing audio: {audio_file_path}")

        try:
            # Ensure file is in compatible format
            compatible_path = self.convert_to_whisper_format(audio_file_path)

            # Open file and transcribe
            with open(compatible_path, "rb") as audio_file:
                # Build transcription parameters
                transcription_params = {
                    "model": self.settings.whisper_model,
                    "file": audio_file,
                    "response_format": "verbose_json",
                }

                if language:
                    transcription_params["language"] = language

                if prompt:
                    transcription_params["prompt"] = prompt

                # Call Whisper API
                response = await self.async_client.audio.transcriptions.create(
                    **transcription_params
                )

            transcript_text = response.text
            detected_language = getattr(response, "language", language or "unknown")
            duration = getattr(response, "duration", 0)

            logger.info(
                f"Transcription complete: {len(transcript_text)} chars, "
                f"{duration:.2f}s, language={detected_language}"
            )

            return {
                "text": transcript_text,
                "language": detected_language,
                "duration": duration
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise

        finally:
            # Clean up temp file
            try:
                if os.path.exists(compatible_path):
                    os.remove(compatible_path)
                    logger.debug(f"Cleaned up temp file: {compatible_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

    async def transcribe_from_url(
        self,
        url: str,
        headers: Optional[dict] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        """
        Download and transcribe audio from URL.

        Args:
            url: URL to download audio from
            headers: Optional HTTP headers for download
            language: Optional language code
            prompt: Optional transcription prompt

        Returns:
            Dictionary containing transcript and metadata

        Raises:
            Exception: If download or transcription fails
        """
        audio_path = None

        try:
            # Download audio
            audio_path, file_size = await self.download_audio(url, headers)

            # Transcribe
            result = await self.transcribe(audio_path, language, prompt)
            result["file_size_bytes"] = file_size

            return result

        finally:
            # Clean up downloaded file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.debug(f"Cleaned up downloaded file: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up downloaded file: {e}")

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up old temporary files.

        Args:
            older_than_hours: Remove files older than this many hours
        """
        import time

        logger.info(f"Cleaning up temp files older than {older_than_hours} hours")

        cutoff_time = time.time() - (older_than_hours * 3600)
        removed_count = 0
        removed_size = 0

        for file_path in self.temp_dir.glob("*"):
            if file_path.is_file():
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        removed_size += file_size
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

        logger.info(
            f"Cleaned up {removed_count} files "
            f"({removed_size / (1024 * 1024):.2f}MB)"
        )


# Global service instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get global transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


if __name__ == "__main__":
    # Test transcription
    import asyncio
    from config import configure_logging

    configure_logging()

    async def test():
        service = get_transcription_service()
        # Test with a sample audio URL
        # result = await service.transcribe_from_url("https://example.com/audio.mp3")
        # print(result)
        print("Transcription service initialized successfully!")

    asyncio.run(test())
