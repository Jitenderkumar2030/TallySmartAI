import speech_recognition as sr
import pyttsx3
import threading
import queue
import streamlit as st
from ai_modules.fingpt_assistant import ask_fingpt
import json

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.is_listening = False
        self.command_queue = queue.Queue()
        
        # Configure TTS
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.8)
        
        # Voice commands mapping
        self.commands = {
            'show dashboard': self._show_dashboard,
            'upload file': self._upload_file,
            'generate forecast': self._generate_forecast,
            'ask advisor': self._ask_advisor,
            'show trends': self._show_trends,
            'export report': self._export_report
        }
    
    def start_listening(self):
        """Start voice recognition in background thread"""
        if not self.is_listening:
            self.is_listening = True
            thread = threading.Thread(target=self._listen_continuously)
            thread.daemon = True
            thread.start()
            return True
        return False
    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
    
    def _listen_continuously(self):
        """Continuous listening loop"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for wake word "TallySmartAI"
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                try:
                    command = self.recognizer.recognize_google(audio).lower()
                    if 'tallysmartai' in command or 'tally smart' in command:
                        self._process_command(command)
                except sr.UnknownValueError:
                    pass  # Ignore unrecognized speech
                except sr.RequestError:
                    pass  # Ignore network errors
                    
            except sr.WaitTimeoutError:
                pass  # Continue listening
    
    def _process_command(self, command):
        """Process recognized voice command"""
        self.speak("Yes, how can I help you?")
        
        # Listen for actual command
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            user_command = self.recognizer.recognize_google(audio).lower()
            
            # Find matching command
            for cmd_key, cmd_func in self.commands.items():
                if cmd_key in user_command:
                    response = cmd_func(user_command)
                    self.speak(response)
                    return
            
            # If no direct command match, ask FinGPT
            if any(word in user_command for word in ['what', 'how', 'why', 'when', 'explain']):
                response = ask_fingpt(user_command)
                # Limit response length for TTS
                response = response[:200] + "..." if len(response) > 200 else response
                self.speak(response)
            else:
                self.speak("I didn't understand that command. Please try again.")
                
        except sr.UnknownValueError:
            self.speak("I couldn't hear you clearly. Please try again.")
        except sr.RequestError:
            self.speak("Voice recognition service is unavailable.")
    
    def speak(self, text):
        """Convert text to speech"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except:
            pass  # Ignore TTS errors
    
    def _show_dashboard(self, command):
        """Navigate to dashboard"""
        st.session_state['voice_command'] = 'show_dashboard'
        return "Showing dashboard"
    
    def _upload_file(self, command):
        """Trigger file upload"""
        st.session_state['voice_command'] = 'upload_file'
        return "Please select a file to upload"
    
    def _generate_forecast(self, command):
        """Generate forecast"""
        st.session_state['voice_command'] = 'generate_forecast'
        return "Generating financial forecast"
    
    def _ask_advisor(self, command):
        """Ask financial advisor"""
        question = command.replace('ask advisor', '').strip()
        if question:
            response = ask_fingpt(question)
            return response[:100] + "..." if len(response) > 100 else response
        return "What would you like to ask the advisor?"
    
    def _show_trends(self, command):
        """Show trend analysis"""
        st.session_state['voice_command'] = 'show_trends'
        return "Showing trend analysis"
    
    def _export_report(self, command):
        """Export report"""
        st.session_state['voice_command'] = 'export_report'
        return "Preparing report for export"

# Global instance
voice_assistant = VoiceAssistant()
