import whisper
import torch
from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
from yt_dlp import YoutubeDL
import os
import tempfile

class AIVideoProcessor:
    def __init__(self):
        # Whisper モデル (音声認識)
        self.whisper_model = whisper.load_model("base")
        
        # T5 モデル (要約)
        self.summarizer = pipeline("summarization", 
                                 model="t5-base", 
                                 tokenizer="t5-base")
        
        # Question Generation モデル
        self.qg_model = pipeline("text2text-generation",
                               model="valhalla/t5-base-qg-hl")
    
    def extract_audio_from_youtube(self, video_url):
        """YouTube動画から音声を抽出"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': 'temp_audio/%(id)s.%(ext)s',
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file = f"temp_audio/{info['id']}.wav"
            return audio_file, info
    
    def transcribe_audio(self, audio_file):
        """音声を日本語字幕に変換"""
        result = self.whisper_model.transcribe(audio_file, language="ja")
        return result["text"]
    
    def summarize_text(self, text, max_length=200):
        """テキストを要約"""
        # 長いテキストをチャンクに分割
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        summaries = []
        
        for chunk in chunks:
            summary = self.summarizer(chunk, max_length=max_length, min_length=50)
            summaries.append(summary[0]['summary_text'])
        
        return " ".join(summaries)
    
    def generate_quiz_questions(self, summary_text, num_questions=5):
        """要約から4択クイズを生成"""
        questions = []
        
        # 簡単な実装例（実際はより高度な処理が必要）
        sentences = summary_text.split('。')[:num_questions]
        
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                # Question Generation モデルで質問生成
                question_text = self.qg_model(f"generate question: {sentence}")
                
                # 4択選択肢を生成（実際はより高度な処理が必要）
                quiz_data = {
                    'question': question_text[0]['generated_text'],
                    'options': self._generate_options(sentence),
                    'correct_answer': 1,  # 仮の値
                    'explanation': sentence
                }
                questions.append(quiz_data)
        
        return questions
    
    def _generate_options(self, context):
        """4択選択肢を生成（簡易版）"""
        # 実際はより高度な選択肢生成が必要
        return [
            "正解の選択肢",
            "間違いの選択肢1", 
            "間違いの選択肢2",
            "間違いの選択肢3"
        ]