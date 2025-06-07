from celery import shared_task
from .ai_processor import AIVideoProcessor
from playlist.models import LearningVideo
from quiz.models import Quiz
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_video_async(video_id, video_url):
    """動画を非同期で処理してクイズを生成"""
    try:
        processor = AIVideoProcessor()
        
        # 1. 音声抽出
        audio_file, video_info = processor.extract_audio_from_youtube(video_url)
        
        # 2. 音声認識
        transcript = processor.transcribe_audio(audio_file)
        
        # 3. テキスト要約
        summary = processor.summarize_text(transcript)
        
        # 4. クイズ生成
        quiz_questions = processor.generate_quiz_questions(summary)
        
        # 5. データベース保存
        learning_video = LearningVideo.objects.get(video_id=video_id)
        learning_video.transcript = transcript
        learning_video.summary = summary
        learning_video.is_processed = True
        learning_video.save()
        
        # クイズをデータベースに保存
        for quiz_data in quiz_questions:
            Quiz.objects.create(
                video=learning_video,
                question=quiz_data['question'],
                option_1=quiz_data['options'][0],
                option_2=quiz_data['options'][1], 
                option_3=quiz_data['options'][2],
                option_4=quiz_data['options'][3],
                correct_option=quiz_data['correct_answer'],
                explanation=quiz_data['explanation']
            )
        
        logger.info(f"Video {video_id} processed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        return False
