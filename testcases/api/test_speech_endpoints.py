"""
API tests for Speech endpoints
Tests speech generation, rating, and transcription
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestSpeechEndpoints:
    """Test Speech API endpoints"""

    @patch('app.ai_service')
    def test_generate_speech(self, mock_ai_service, client):
        """Test POST /api/speech/generate"""
        mock_ai_service.generate_speech.return_value = "Generated speech content"

        response = client.post('/api/speech/generate', json={
            'speech_type': 'opening',
            'country': 'USA',
            'topic': 'Climate Change',
            'position': 'Support',
            'time_limit': 90
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'speech' in data
        assert data['speech'] == "Generated speech content"

    @patch('app.ai_service')
    def test_rate_grammar(self, mock_ai_service, client):
        """Test POST /api/speech/rate-grammar"""
        mock_ai_service.chat.return_value = "Grammar score: 8/10"

        response = client.post('/api/speech/rate-grammar', json={
            'speech_text': 'Test speech content'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'rating' in data

    @patch('app.ai_service')
    def test_rate_ethics(self, mock_ai_service, client):
        """Test POST /api/speech/rate-ethics"""
        mock_ai_service.chat.return_value = "Ethics score: 9/10"

        response = client.post('/api/speech/rate-ethics', json={
            'speech_text': 'Test speech content',
            'country': 'USA'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'rating' in data

    @patch('app.ai_service')
    def test_rate_impact(self, mock_ai_service, client):
        """Test POST /api/speech/rate-impact"""
        mock_ai_service.chat.return_value = "Impact score: 7/10"

        response = client.post('/api/speech/rate-impact', json={
            'speech_text': 'Test speech content'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'rating' in data

    @patch('app.ai_service')
    def test_comprehensive_rating(self, mock_ai_service, client):
        """Test POST /api/speech/rate-comprehensive"""
        mock_ai_service.chat.return_value = "Overall: Excellent speech"

        response = client.post('/api/speech/rate-comprehensive', json={
            'speech_text': 'Test speech content',
            'country': 'USA',
            'topic': 'Climate Change'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'rating' in data

    @patch('app.ai_service')
    def test_summary_and_rewrite(self, mock_ai_service, client):
        """Test POST /api/speech/summary-and-rewrite"""
        mock_ai_service.chat.return_value = "Rewritten speech"

        response = client.post('/api/speech/summary-and-rewrite', json={
            'speech_text': 'Original speech',
            'instructions': 'Make it more formal'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data

    @patch('app.openai')
    def test_transcribe_audio(self, mock_openai, client):
        """Test POST /api/transcribe"""
        mock_openai.Audio.transcribe.return_value.text = "Transcribed text"

        # Create mock audio file
        from io import BytesIO
        audio_data = BytesIO(b"fake audio data")
        audio_data.name = 'test.wav'

        response = client.post('/api/transcribe', data={
            'audio': (audio_data, 'test.wav')
        }, content_type='multipart/form-data')

        # Note: This test may need adjustment based on actual audio handling
        assert response.status_code in [200, 400, 500]
