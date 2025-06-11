import openai
import json
import re
import requests
from django.conf import settings
from datetime import datetime, date
import yt_dlp
import tempfile
import os

class AIQuizGenerator:
    def __init__(self):
        # OpenAI API設定
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        print(f"🔍 デバッグ: OpenAI API Key = {api_key[:20] + '...' if api_key else 'None'}")
        
        if api_key and api_key.startswith('sk-'):
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=api_key)
                
                # APIキーの有効性をテスト
                try:
                    test_response = self.openai_client.models.list()
                    self.openai_available = True
                    print("✅ OpenAI API接続テスト成功")
                except Exception as test_error:
                    print(f"❌ OpenAI API接続テストエラー: {test_error}")
                    self.openai_available = False
                
            except Exception as e:
                print(f"❌ OpenAI API初期化エラー: {e}")
                self.openai_client = None
                self.openai_available = False
        else:
            self.openai_client = None
            self.openai_available = False
            print("⚠️ OpenAI API Key未設定または無効")
        
        # Hugging Face設定
        self.huggingface_api_key = getattr(settings, 'HUGGINGFACE_API_KEY', None)
        
        # YouTube API設定
        self.youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        
        print(f"🤖 AI生成オプション:")
        print(f"  - OpenAI: {'✅' if self.openai_available else '❌'}")
        print(f"  - Hugging Face API: {'✅' if self.huggingface_api_key else '❌'}")
        print(f"  - YouTube API: {'✅' if self.youtube_api_key else '❌'}")
        print(f"  - Whisper音声処理: {'✅' if self.openai_available else '❌'}")

        # Whisper設定
        self.whisper_settings = {
            'model': 'whisper-1',  # OpenAI Whisper API
            'language': 'ja',      # 日本語
            'response_format': 'text',
            'temperature': 0.0
        }
        
        # 要約設定
        self.summary_settings = {
            'max_transcript_length': 8000,  # トランスクリプト最大長
            'summary_max_tokens': 1000,     # 要約最大トークン数
            'chunk_size': 3000,             # チャンク分割サイズ
            'overlap_size': 200             # オーバーラップサイズ
        }
        
        # 簡素化されたタイムアウト設定
        self.timeout_settings = {
            'openai_timeout': 30,
            'huggingface_timeout': 20,
            'total_timeout': 60,
            'fallback_timeout': 5
        }
        
        print(f"⏱️ タイムアウト設定:")
        print(f"  - OpenAI: {self.timeout_settings['openai_timeout']}秒")
        print(f"  - Hugging Face: {self.timeout_settings['huggingface_timeout']}秒")

        # デバッグ設定
        self.debug_settings = {
            'force_fallback': False,
            'force_ai_failure': False,
            'show_generation_process': True,
            'test_mode': False
        }

    def detect_content_type(self, title):
        """タイトルからコンテンツタイプを判定"""
        title_lower = title.lower()
        
        content_patterns = {
            'math': ['算数', '数学', '計算', '方程式', '関数', '図形', '確率', '統計', 'まいにち算数'],
            'geography': ['地理', '都道府県', '県庁所在地', '地図', '国', '首都', '山', '川', '海', '日本地理'],
            'history': ['歴史', '戦国', '江戸', '明治', '昭和', '平成', '年号', '武将', '天皇', '時代'],
            'science': ['科学', '化学', '物理', '生物', '実験', '元素', '化合物', 'DNA'],
            'language': ['英語', '国語', '漢字', '文法', '単語', '発音', 'TOEIC', '英検'],
            'programming': ['プログラミング', 'Python', 'JavaScript', 'HTML', 'CSS', 'コード']
        }
        
        for content_type, keywords in content_patterns.items():
            if any(keyword in title_lower for keyword in keywords):
                return content_type
        
        return 'general'

    def calculate_age_from_birthdate(self, birth_date):
        """生年月日から年齢を計算"""
        try:
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            elif isinstance(birth_date, datetime):
                birth_date = birth_date.date()
            
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except Exception as e:
            print(f"❌ 年齢計算エラー: {e}")
            return None

    def determine_age_group_from_user(self, user):
        """ユーザー情報から年齢グループを判定（修正版）"""
        try:
            # UserProfileから生年月日を取得
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                age_group = profile.get_age_group()
                age = profile.get_age()
                
                if age_group and age:
                    print(f"👤 ユーザー実年齢: {age}歳 → グループ: {age_group}")
                    return age_group
            
            print("ℹ️ ユーザー年齢情報なし - タイトルから判定")
            return None
            
        except Exception as e:
            print(f"❌ ユーザー年齢判定エラー: {e}")
            return None

    def detect_age_group(self, video_title, user=None):
        """動画タイトルとユーザー情報から対象年齢を判定（強化版）"""
        
        # 1. まずユーザーの実年齢から判定
        user_age_group = self.determine_age_group_from_user(user) if user else None
        if user_age_group:
            print(f"👤 ユーザー実年齢による判定: {user_age_group}")
            return user_age_group
        
        # 2. 動画タイトルから判定（パターン強化）
        title_lower = video_title.lower()
        
        age_patterns = {
            'elementary_low': [  # 小学1-3年生
                '小学1年', '小学2年', '小学3年', '1年生', '2年生', '3年生',
                'ひらがな', 'かたかな', 'たしざん', 'ひきざん', 
                '時計', 'かず', '10まで', '１０まで', '100まで', '１００まで',
                '簡単', 'やさしい', 'はじめて', '基本',
                '小学校低学年', '小学生低学年', '小学生1-3年', 
                '小１', '小２', '小３', '低学年'
            ],
            'elementary_mid': [  # 小学4-6年生
                '小学4年', '小学5年', '小学6年', '4年生', '5年生', '6年生',
                '小４', '小５', '小６', '小学校高学年', '小学生高学年',
                '分数', 'わり算', '面積', '体積', '図形', '割り算',
                '高学年', '応用', '発展'
            ],
            'junior_high': [  # 中学生
                '中学', '中１', '中２', '中３', '中学生', 
                '中学1年', '中学2年', '中学3年',
                '方程式', '関数', '証明', '理科', '社会', '英語',
                '中学校', '証明問題', '連立方程式'
            ],
            'high_school': [  # 高校生
                '高校', '高１', '高２', '高３', '高校生', 
                '高校1年', '高校2年', '高校3年',
                '微分', '積分', '化学', '物理', '生物', 
                '世界史', '日本史', '高等学校', '大学受験'
            ]
        }
        
        # 優先度順で判定（より具体的なものから）
        for age_group, keywords in age_patterns.items():
            if any(keyword in title_lower for keyword in keywords):
                print(f"📋 タイトルによる年齢判定: {age_group}")
                return age_group
        
        print("📋 年齢判定: general")
        return 'general'

    def generate_quiz(self, video_id, user=None, force_fallback=False):
        """動画IDからクイズを自動生成（フォールバック確認対応版）"""
        try:
            # デバッグモード: フォールバック強制実行
            if force_fallback or self.debug_settings.get('force_fallback', False):
                print("🔧 デバッグモード: フォールバック生成を強制実行")
                return self.execute_fallback_generation(video_id, user)
            
            # 修正: 正しいモデルをインポート
            from django.apps import apps
            
            try:
                # LearningVideoモデルを取得
                LearningVideo = apps.get_model('playlist', 'LearningVideo')
                video = LearningVideo.objects.get(id=video_id)
                video_title = video.title
                youtube_video_id = getattr(video, 'youtube_video_id', None)
                
                print(f"🤖 AIクイズ生成開始: ID={video_id}, タイトル={video_title}")
                
            except LearningVideo.DoesNotExist:
                print(f"❌ 動画が見つかりません: ID={video_id}")
                return self.generate_fallback_quiz("動画が見つかりません")
            except Exception as model_error:
                print(f"❌ モデル取得エラー: {model_error}")
                return self.generate_fallback_quiz("モデル取得エラー")
            
            # コンテンツ分析
            content_type = self.detect_content_type(video_title)
            age_group = self.detect_age_group(video_title, user)
            
            print(f"📋 コンテンツタイプ: {content_type}")
            print(f"👶 対象年齢グループ: {age_group}")
            
            # デバッグモード: AI生成を強制失敗
            if self.debug_settings.get('force_ai_failure', False):
                print("🔧 デバッグモード: AI生成を強制失敗")
                return self.execute_fallback_generation(video_id, user)
            
            # 段階的AI生成（同期版）
            ai_result = self.try_ai_generation_sync(video_title, content_type, age_group)
            if ai_result and ai_result.get('questions'):
                print(f"✅ AI生成成功: {len(ai_result['questions'])}問")
                return ai_result
            
            # AI生成失敗時のフォールバック処理
            print("🔄 AI生成失敗 - フォールバック生成を実行")
            return self.execute_fallback_generation(video_id, user)
        
        except Exception as e:
            print(f"❌ クイズ生成エラー: {e}")
            return self.execute_fallback_generation(video_id, user, error_message=str(e))

    def execute_fallback_generation(self, video_id, user=None, error_message=None):
        """フォールバック生成の実行"""
        try:
            from django.apps import apps
            LearningVideo = apps.get_model('playlist', 'LearningVideo')
            video = LearningVideo.objects.get(id=video_id)
            
            content_type = self.detect_content_type(video.title)
            age_group = self.detect_age_group(video.title, user)
            
            print(f"🔄 フォールバック生成実行:")
            print(f"  - 動画: {video.title}")
            print(f"  - コンテンツタイプ: {content_type}")
            print(f"  - 年齢グループ: {age_group}")
            print(f"  - エラー理由: {error_message or '不明'}")
            
            # 年齢対応フォールバック生成
            fallback_result = self.generate_age_specific_quiz(
                video.title, content_type, age_group, None
            )
            
            # フォールバック情報を追加
            if fallback_result:
                fallback_result['generation_method'] = 'fallback'
                fallback_result['fallback_reason'] = error_message or 'AI生成失敗'
                fallback_result['content_analysis'] = {
                    'content_type': content_type,
                    'age_group': age_group,
                    'video_title': video.title
                }
                
                print(f"✅ フォールバック生成成功: {len(fallback_result.get('questions', []))}問")
                return fallback_result
            
            # 最後の手段: 緊急フォールバック
            return self.generate_emergency_fallback_quiz(video.title)
            
        except Exception as e:
            print(f"❌ フォールバック生成エラー: {e}")
            return self.generate_emergency_fallback_quiz(video.title)

    def generate_emergency_fallback_quiz(self, video_title):
        """緊急時のフォールバッククイズ（必ず成功する）"""
        print("🚨 緊急フォールバッククイズ生成")
        
        return {
            "quiz_type": "emergency_fallback",
            "generation_method": "emergency",
            "content_type": "general",
            "age_group": "general",
            "video_title": video_title,
            "questions": [
                {
                    "question": f"「{video_title}」のような動画を学習する際の基本的な心構えは？",
                    "options": [
                        "ながら見で気軽に視聴する",
                        "集中して内容を理解しようとする",
                        "速度を上げて短時間で終わらせる",
                        "音だけ聞いて他の作業をする"
                    ],
                    "correct": 2,
                    "explanation": "学習動画は集中して視聴し、内容をしっかり理解することが最も重要です。"
                },
                {
                    "question": "動画学習で重要な「アクティブラーニング」とは？",
                    "options": [
                        "受動的に動画を見ること",
                        "能動的に考えながら学習すること",
                        "動画を繰り返し見ること",
                        "ノートを取らずに見ること"
                    ],
                    "correct": 2,
                    "explanation": "アクティブラーニングとは、受け身ではなく能動的に考え、参加する学習方法です。"
                },
                {
                    "question": "学習効果を高めるために動画視聴後にすべきことは？",
                    "options": [
                        "すぐに次の動画を見る",
                        "内容を振り返り、まとめる",
                        "忘れるまで放置する",
                        "感想だけ書く"
                    ],
                    "correct": 2,
                    "explanation": "動画視聴後は内容を振り返り、要点をまとめることで学習効果が向上します。"
                },
                {
                    "question": "分からない部分があった時の対処法として最適なのは？",
                    "options": [
                        "そのまま進む",
                        "何度も同じ部分を見直す",
                        "諦めて他の動画を見る",
                        "関連情報を調べて理解を深める"
                    ],
                    "correct": 4,
                    "explanation": "分からない部分は関連情報を調べることで、より深い理解につながります。"
                },
                {
                    "question": "継続的な学習のために最も大切なことは？",
                    "options": [
                        "毎日長時間勉強する",
                        "短時間でも定期的に続ける",
                        "気が向いた時だけやる",
                        "完璧を目指して頑張る"
                    ],
                    "correct": 2,
                    "explanation": "学習は短時間でも定期的に続けることが、長期的な成果につながります。"
                }
            ]
        }

    def try_ai_generation_sync(self, video_title, content_type, age_group):
        """同期版AI生成試行（AI結果表示対応）"""
        print(f"⏳ AI生成試行開始: {video_title}")
        
        try:
            # OpenAI API試行（少し条件を緩和）
            if self.openai_available:
                print("🚀 OpenAI GPTでクイズ生成")
                try:
                    # まず軽量なテストクエリで確認
                    test_result = self.test_openai_connection()
                    if test_result:
                        ai_result = self.generate_quiz_with_gpt_enhanced(
                            video_title, content_type, age_group
                        )
                        if ai_result and ai_result.get('questions'):
                            print(f"✅ OpenAI生成成功: {len(ai_result['questions'])}問")
                            self.display_ai_generated_quiz(ai_result, "OpenAI GPT")
                            return ai_result
                except Exception as e:
                    print(f"❌ OpenAI生成失敗: {e}")
            
            # Hugging Face API試行（実際のAPI使用）
            if self.huggingface_api_key:
                print("🤗 Hugging Face API (強化版) でクイズ生成を試行")
                try:
                    # 接続テストを実行
                    if self.test_huggingface_connection():
                        hf_result = self.generate_quiz_with_huggingface_real(
                            video_title, content_type, age_group
                        )
                        if hf_result and hf_result.get('questions'):
                            print(f"✅ Hugging Face生成成功: {len(hf_result['questions'])}問")
                            self.display_ai_generated_quiz(hf_result, f"Hugging Face ({hf_result.get('model', 'Unknown')})")
                            return hf_result
                    else:
                        print("⚠️ Hugging Face接続テスト失敗 - シミュレーションに移行")
                except Exception as e:
                    print(f"❌ Hugging Face生成失敗: {e}")
            
            # ローカルAIシミュレーション（デモ用）
            print("🎭 AIクイズ生成シミュレーション（デモ用）")
            simulated_result = self.generate_ai_simulation_quiz(video_title, content_type, age_group)
            if simulated_result:
                self.display_ai_generated_quiz(simulated_result, "AI Simulation")
                return simulated_result
            
            print("❌ すべてのAI生成が失敗")
            return None
            
        except Exception as e:
            print(f"❌ AI生成試行エラー: {e}")
            return None

    def test_openai_connection(self):
        """OpenAI接続の軽量テスト"""
        try:
            # 非常に軽いテストクエリ
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=5,
                temperature=0
            )
            print("✅ OpenAI軽量テスト成功")
            return True
        except Exception as e:
            print(f"❌ OpenAI軽量テスト失敗: {e}")
            return False

    def generate_quiz_with_gpt_enhanced(self, video_title, content_type, age_group):
        """拡張版GPTクイズ生成（より確実）"""
        if not self.openai_available:
            return None
        
        print(f"🎯 GPT強化版生成: {age_group}向け - {content_type}")
        
        try:
            # より具体的で効果的なプロンプト
            enhanced_prompt = self.build_enhanced_prompt(video_title, content_type, age_group)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"あなたは{age_group}年齢層向けの教育クイズ作成の専門家です。必ずJSON形式で回答してください。"
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            quiz_json = response.choices[0].message.content
            quiz_data = json.loads(quiz_json)
            
            # 生成方法の情報を追加
            quiz_data['generation_method'] = 'openai_gpt'
            quiz_data['model'] = 'gpt-3.5-turbo'
            quiz_data['content_type'] = content_type
            quiz_data['age_group'] = age_group
            
            if self.validate_quiz_structure(quiz_data):
                return quiz_data
            else:
                print("❌ GPT生成結果が無効な構造")
                return None
                
        except Exception as e:
            print(f"❌ GPT強化版生成エラー: {e}")
            return None

    def generate_quiz_with_huggingface_real(self, video_title, content_type, age_group):
        """実際のHugging Face API使用（修正版）"""
        print(f"🤗 Hugging Face実API呼び出し: {video_title}")
        
        try:
            # より適切なモデルを使用（日本語対応）
            models_to_try = [
                "microsoft/DialoGPT-medium",
                "facebook/blenderbot-400M-distill",
                "google/flan-t5-small",
                "microsoft/DialoGPT-small"
            ]
            
            for model_name in models_to_try:
                try:
                    print(f"🔄 試行中モデル: {model_name}")
                    result = self._try_huggingface_model(model_name, video_title, content_type, age_group)
                    if result:
                        return result
                except Exception as model_error:
                    print(f"❌ {model_name} 失敗: {model_error}")
                    continue
            
            print("❌ 全てのHugging Faceモデルで失敗")
            return None
                
        except Exception as e:
            print(f"❌ Hugging Face実API エラー: {e}")
            return None

    def _try_huggingface_model(self, model_name, video_title, content_type, age_group):
        """個別モデルでの試行"""
        api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        # 日本語対応のプロンプト（短縮版）
        prompt = self.build_simple_japanese_prompt(video_title, content_type, age_group)
        
        # モデルに応じたペイロード調整
        if "flan-t5" in model_name:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "do_sample": True
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
        elif "blenderbot" in model_name:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "min_length": 50,
                    "temperature": 0.8
                },
                "options": {
                    "wait_for_model": True
                }
            }
        else:  # DialoGPT系
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.7,
                    "pad_token_id": 50256
                },
                "options": {
                    "wait_for_model": True
                }
            }
        
        import requests
        response = requests.post(
            api_url, 
            headers=headers, 
            json=payload, 
            timeout=30
        )
        
        print(f"📡 {model_name} 応答ステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {model_name} 成功応答")
            
            # 結果を解析してクイズ形式に変換
            quiz_data = self.parse_huggingface_response_enhanced(
                result, video_title, content_type, age_group, model_name
            )
            return quiz_data
            
        elif response.status_code == 503:
            print(f"⏳ {model_name} モデル読み込み中...")
            # 少し待ってリトライ
            import time
            time.sleep(3)
            return self._retry_huggingface_request(api_url, headers, payload, model_name)
            
        else:
            error_text = response.text
            print(f"❌ {model_name} エラー {response.status_code}: {error_text}")
            return None

    def _retry_huggingface_request(self, api_url, headers, payload, model_name):
        """Hugging Face APIのリトライ"""
        try:
            import requests
            import time
            
            print(f"🔄 {model_name} リトライ実行")
            time.sleep(2)
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {model_name} リトライ成功")
                return result
            else:
                print(f"❌ {model_name} リトライ失敗: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {model_name} リトライエラー: {e}")
            return None

    def build_simple_japanese_prompt(self, video_title, content_type, age_group):
        """シンプルな日本語プロンプト構築"""
        age_descriptions = {
            'elementary_low': '小学1-3年',
            'elementary_mid': '小学4-6年', 
            'junior_high': '中学生',
            'general': '一般'
        }
        
        age_desc = age_descriptions.get(age_group, '一般')
        
        # より短くシンプルなプロンプト
        return f"""動画「{video_title}」について、{age_desc}向けの{content_type}の4択クイズを1問作成してください。

形式:
問題: [問題文]
A) [選択肢1]
B) [選択肢2]  
C) [選択肢3]
D) [選択肢4]
正解: [A/B/C/D]
解説: [解説文]"""

    def parse_huggingface_response_enhanced(self, response, video_title, content_type, age_group, model_name):
        """Hugging Face応答の強化版解析"""
        try:
            # 応答からテキストを抽出
            generated_text = ""
            
            if isinstance(response, list) and len(response) > 0:
                if isinstance(response[0], dict):
                    generated_text = response[0].get('generated_text', '') or \
                                   response[0].get('text', '') or \
                                   response[0].get('translation_text', '') or \
                                   str(response[0])
                else:
                    generated_text = str(response[0])
            elif isinstance(response, dict):
                generated_text = response.get('generated_text', '') or \
                               response.get('text', '') or \
                               response.get('translation_text', '') or \
                               str(response)
            else:
                generated_text = str(response)
            
            print(f"🔍 {model_name} 生成テキスト:\n{generated_text[:200]}...")
            
            # テキストを解析してクイズ構造に変換
            questions = self.extract_questions_from_text_enhanced(generated_text, video_title, content_type)
            
            # 最低限の問題数を確保
            if len(questions) < 3:
                print(f"⚠️ {model_name} 生成問題数不足 - 補完実行")
                questions.extend(self.generate_fallback_hf_questions(video_title, content_type, 3 - len(questions)))
            
            return {
                "generation_method": "huggingface_real",
                "model": model_name,
                "content_type": content_type,
                "age_group": age_group,
                "video_title": video_title,
                "questions": questions[:5],  # 最大5問
                "raw_response": generated_text,
                "hf_success": True
            }
            
        except Exception as e:
            print(f"❌ {model_name} 応答解析エラー: {e}")
            # エラー時も基本的なクイズを返す
            return self.generate_hf_fallback_quiz(video_title, content_type, age_group, model_name)

    def extract_questions_from_text_enhanced(self, text, video_title, content_type):
        """強化版テキスト解析（より多様なパターンに対応）"""
        questions = []
        
        try:
            import re
            
            # 複数のパターンで問題を検索
            patterns = [
                r'問題[:：]\s*(.+?)(?=問題|$)',
                r'Q\d+[:：]\s*(.+?)(?=Q\d+|$)',
                r'質問[:：]\s*(.+?)(?=質問|$)',
                r'[1-9][:：]\s*(.+?)(?=[1-9][:：]|$)'
            ]
            
            extracted_problems = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                extracted_problems.extend(matches)
                if extracted_problems:
                    break
            
            # パターンマッチが失敗した場合は文章を分割
            if not extracted_problems:
                sentences = text.split('。')
                extracted_problems = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            for i, problem_text in enumerate(extracted_problems[:3]):
                # 選択肢を抽出または生成
                options = self.extract_or_generate_options(problem_text, content_type)
                
                question_data = {
                    "question": f"Hugging Face生成: {video_title}に関連する問題 {i+1}",
                    "options": options,
                    "correct": 2,  # デフォルトで2番目を正解
                    "explanation": f"Hugging Faceによる解析: {problem_text[:100]}..."
                }
                questions.append(question_data)
            
            return questions
            
        except Exception as e:
            print(f"❌ 強化版テキスト解析エラー: {e}")
            return []

    def extract_or_generate_options(self, problem_text, content_type):
        """選択肢を抽出または生成"""
        try:
            import re
            
            # A) B) C) D)パターンを検索
            option_pattern = r'[A-D]\)\s*([^\n\r]+)'
            options = re.findall(option_pattern, problem_text)
            
            if len(options) >= 4:
                return options[:4]
            
            # 数字パターンを検索
            number_pattern = r'[1-4][:：]\s*([^\n\r]+)'
            number_options = re.findall(number_pattern, problem_text)
            
            if len(number_options) >= 4:
                return number_options[:4]
            
            # 自動生成
            return self.generate_context_options(content_type)
            
        except Exception as e:
            print(f"❌ 選択肢抽出エラー: {e}")
            return self.generate_context_options(content_type)

    def generate_context_options(self, content_type):
        """コンテンツタイプに応じた選択肢生成"""
        options_map = {
            'math': [
                '計算を正確に行う',
                '概念を理解する', 
                '暗記に頼る',
                '答えだけ求める'
            ],
            'geography': [
                '地名を暗記する',
                '地図で位置を確認する',
                '興味を持たない',
                'テストのためだけ'
            ],
            'history': [
                '年号を覚える',
                '背景を理解する',
                '興味を持たない', 
                '表面的に学ぶ'
            ],
            'science': [
                '実験をする',
                '理論を学ぶ',
                '暗記だけする',
                '関心を持たない'
            ]
        }
        
        return options_map.get(content_type, [
            '積極的に学習',
            '理解を深める',
            '受動的学習',
            '表面的学習'
        ])

    def generate_fallback_hf_questions(self, video_title, content_type, count):
        """Hugging Face用フォールバック問題"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question": f"Hugging Face補完問題 {i+1}: {video_title}のような{content_type}学習で重要なのは？",
                "options": self.generate_context_options(content_type),
                "correct": 2,
                "explanation": f"Hugging Faceの解析を補完した{content_type}分野の学習ポイントです。"
            }
            questions.append(question_data)
        
        return questions

    def generate_hf_fallback_quiz(self, video_title, content_type, age_group, model_name):
        """Hugging Face完全フォールバック"""
        print(f"🔄 {model_name} 完全フォールバック実行")
        
        return {
            "generation_method": "huggingface_fallback",
            "model": model_name,
            "content_type": content_type,
            "age_group": age_group,
            "video_title": video_title,
            "questions": [
                {
                    "question": f"Hugging Face ({model_name}) 解析: {video_title}の学習で最も効果的なのは？",
                    "options": [
                        "表面的な理解",
                        "深い理解と応用",
                        "暗記中心",
                        "受動的学習"
                    ],
                    "correct": 2,
                    "explanation": f"{model_name}による{content_type}分野の学習分析結果です。"
                },
                {
                    "question": f"Hugging Face推奨: {content_type}分野の効果的な学習方法は？",
                    "options": self.generate_context_options(content_type),
                    "correct": 2,
                    "explanation": f"{model_name}が推奨する{content_type}学習のベストプラクティスです。"
                },
                {
                    "question": f"{age_group}向け学習で{model_name}が重視するのは？",
                    "options": [
                        "速度重視",
                        "理解重視",
                        "量重視", 
                        "評価重視"
                    ],
                    "correct": 2,
                    "explanation": f"{model_name}による{age_group}向け学習の最適化アドバイスです。"
                }
            ],
            "hf_fallback": True,
            "fallback_reason": f"{model_name} API応答解析失敗"
        }

    def test_huggingface_connection(self):
        """Hugging Face接続テスト"""
        if not self.huggingface_api_key:
            print("❌ Hugging Face APIキーが設定されていません")
            return False
        
        try:
            import requests
            
            # シンプルなテストリクエスト
            test_models = [
                "microsoft/DialoGPT-small",
                "google/flan-t5-small"
            ]
            
            for model in test_models:
                print(f"🔍 {model} 接続テスト中...")
                
                url = f"https://api-inference.huggingface.co/models/{model}"
                headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
                
                response = requests.post(
                    url,
                    headers=headers,
                    json={"inputs": "Hello, test"},
                    timeout=10
                )
                
                print(f"📡 {model} 応答: {response.status_code}")
                
                if response.status_code in [200, 503]:  # 503は「モデル読み込み中」
                    print(f"✅ {model} 接続成功")
                    return True
                else:
                    print(f"❌ {model} 接続失敗: {response.text[:100]}")
            
            return False
            
        except Exception as e:
            print(f"❌ Hugging Face接続テストエラー: {e}")
            return False

    def try_ai_generation_sync(self, video_title, content_type, age_group):
        """同期版AI生成試行（Hugging Face強化版）"""
        print(f"⏳ AI生成試行開始: {video_title}")
        
        try:
            # OpenAI API試行
            if self.openai_available:
                print("🚀 OpenAI GPTでクイズ生成")
                try:
                    test_result = self.test_openai_connection()
                    if test_result:
                        ai_result = self.generate_quiz_with_gpt_enhanced(
                            video_title, content_type, age_group
                        )
                        if ai_result and ai_result.get('questions'):
                            print(f"✅ OpenAI生成成功: {len(ai_result['questions'])}問")
                            self.display_ai_generated_quiz(ai_result, "OpenAI GPT")
                            return ai_result
                except Exception as e:
                    print(f"❌ OpenAI生成失敗: {e}")
            
            # Hugging Face API試行（強化版）
            if self.huggingface_api_key:
                print("🤗 Hugging Face API (強化版) でクイズ生成を試行")
                try:
                    # 接続テストを実行
                    if self.test_huggingface_connection():
                        hf_result = self.generate_quiz_with_huggingface_real(
                            video_title, content_type, age_group
                        )
                        if hf_result and hf_result.get('questions'):
                            print(f"✅ Hugging Face生成成功: {len(hf_result['questions'])}問")
                            self.display_ai_generated_quiz(hf_result, f"Hugging Face ({hf_result.get('model', 'Unknown')})")
                            return hf_result
                    else:
                        print("⚠️ Hugging Face接続テスト失敗 - シミュレーションに移行")
                except Exception as e:
                    print(f"❌ Hugging Face生成失敗: {e}")
            
            # ローカルAIシミュレーション
            print("🎭 AIクイズ生成シミュレーション（デモ用）")
            simulated_result = self.generate_ai_simulation_quiz(video_title, content_type, age_group)
            if simulated_result:
                self.display_ai_generated_quiz(simulated_result, "AI Simulation")
                return simulated_result
            
            print("❌ すべてのAI生成が失敗")
            return None
            
        except Exception as e:
            print(f"❌ AI生成試行エラー: {e}")
            return None

    def set_debug_mode(self, force_fallback=False, force_ai_failure=False, test_mode=False):
        """デバッグモードの設定"""
        self.debug_settings.update({
            'force_fallback': force_fallback,
            'force_ai_failure': force_ai_failure,
            'test_mode': test_mode
        })
        print(f"🔧 デバッグモード設定: {self.debug_settings}")

    def display_ai_generated_quiz(self, quiz_data, ai_source):
        """AI生成されたクイズの表示"""
        print(f"\n🤖 {ai_source} で生成されたクイズ:")
        print(f"  - 生成方法: {quiz_data.get('generation_method', 'unknown')}")
        print(f"  - 問題数: {len(quiz_data.get('questions', []))}")
        print(f"  - コンテンツタイプ: {quiz_data.get('content_type', 'unknown')}")
        print(f"  - 対象年齢: {quiz_data.get('age_group', 'unknown')}")
        
        for i, question in enumerate(quiz_data.get('questions', [])[:3], 1):
            print(f"\n  問題{i}: {question.get('question', '')[:50]}...")
            print(f"  正解: {question.get('correct', 0)}番 - {question.get('options', [''])[question.get('correct', 1)-1]}")

    def build_enhanced_prompt(self, video_title, content_type, age_group):
        """強化版プロンプト構築"""
        age_descriptions = {
            'elementary_low': '小学1-3年',
            'elementary_mid': '小学4-6年', 
            'junior_high': '中学生',
            'general': '一般'
        }
        
        age_desc = age_descriptions.get(age_group, '一般')
        
        prompt = f"""
動画「{video_title}」について、{age_desc}向けの{content_type}分野のクイズを5問作成してください。

以下のJSON形式で回答してください：
{{
    "questions": [
        {{
            "question": "問題文",
            "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
            "correct": 2,
            "explanation": "解説文",
            "difficulty_level": "medium"
        }}
    ]
}}

要件:
- 4択問題
- 正解は1-4の数字
- わかりやすい解説
- {age_desc}に適した難易度
"""
        return prompt

    def validate_quiz_structure(self, quiz_data):
        """クイズ構造の検証"""
        if not isinstance(quiz_data, dict):
            return False
        
        questions = quiz_data.get('questions', [])
        if not isinstance(questions, list) or len(questions) == 0:
            return False
        
        for question in questions:
            if not all(key in question for key in ['question', 'options', 'correct', 'explanation']):
                return False
            
            if not isinstance(question['options'], list) or len(question['options']) != 4:
                return False
            
            if not isinstance(question['correct'], int) or question['correct'] not in [1, 2, 3, 4]:
                return False
        
        return True

    def generate_age_specific_quiz(self, video_title, content_type, age_group, transcript):
        """年齢特化型クイズ生成"""
        print(f"🎯 年齢特化型クイズ生成: {age_group} - {content_type}")
        
        if age_group == 'elementary_low':
            return self.generate_elementary_low_quiz(video_title, content_type, transcript)
        elif content_type == 'math':
            return self.generate_math_fallback_quiz(video_title)
        else:
            return self.generate_general_fallback_quiz(video_title, content_type, age_group)

    def generate_general_fallback_quiz(self, video_title, content_type, age_group):
        """一般的なフォールバッククイズ"""
        print(f"📚 一般フォールバック生成: {content_type} - {age_group}")
        
        return {
            "quiz_type": "general_fallback",
            "content_type": content_type,
            "age_group": age_group,
            "generation_method": "fallback",
            "questions": [
                {
                    "question": f"「{video_title}」のような{content_type}の学習で重要なことは？",
                    "options": [
                        "暗記だけに集中する",
                        "理解を深めることを重視する",
                        "速度だけを追求する",
                        "他人と比較することを重視する"
                    ],
                    "correct": 2,
                    "explanation": f"{content_type}分野では理解を深めることが最も重要です。"
                },
                {
                    "question": f"{age_group}向けの学習方法として最適なのは？",
                    "options": [
                        "一度で完璧に覚える",
                        "段階的に学習を進める",
                        "難しい内容から始める",
                        "時間をかけずに終わらせる"
                    ],
                    "correct": 2,
                    "explanation": "段階的な学習が理解を深め、記憶定着に効果的です。"
                },
                {
                    "question": "効果的な復習のタイミングは？",
                    "options": [
                        "学習直後のみ",
                        "忘れかけた頃に行う",
                        "試験前だけ",
                        "気が向いた時に行う"
                    ],
                    "correct": 2,
                    "explanation": "忘却曲線に基づき、忘れかけた頃の復習が最も効果的です。"
                },
                {
                    "question": "学習内容を定着させるために有効なのは？",
                    "options": [
                        "見るだけの学習",
                        "手を動かして練習する",
                        "聞くだけの学習",
                        "考えずに暗記する"
                    ],
                    "correct": 2,
                    "explanation": "アクティブラーニングとして手を動かすことが記憶定着に有効です。"
                },
                {
                    "question": "継続的な学習のコツは？",
                    "options": [
                        "毎日長時間やる",
                        "短時間でも継続する",
                        "完璧を目指す",
                        "一人で頑張る"
                    ],
                    "correct": 2,
                    "explanation": "短時間でも継続することが長期的な学習効果につながります。"
                }
            ]
        }

    def generate_history_quiz(self, video, Quiz):
        """歴史専用クイズ生成"""
        history_questions = [
            {
                'question': '日本の元号で最も長く続いたのはどれですか？',
                'options': ['明治', '昭和', '平成', '大正'],
                'correct': 2,
                'explanation': '昭和は1926年から1989年まで64年間続き、日本史上最も長い元号です。'
            },
            {
                'question': '江戸幕府を開いた徳川家康が征夷大将軍に任命された年は？',
                'options': ['1600年', '1603年', '1615年', '1598年'],
                'correct': 2,
                'explanation': '徳川家康は1603年に征夷大将軍に任命され、江戸幕府を開きました。'
            },
            {
                'question': '明治維新で活躍した「維新の三傑」に含まれないのは？',
                'options': ['西郷隆盛', '大久保利通', '木戸孝允', '坂本龍馬'],
                'correct': 4,
                'explanation': '維新の三傑は西郷隆盛、大久保利通、木戸孝允です。坂本龍馬は維新の立役者ですが三傑には含まれません。'
            },
            {
                'question': '平安時代の都はどこに置かれましたか？',
                'options': ['奈良', '京都', '大阪', '東京'],
                'correct': 2,
                'explanation': '平安時代（794-1185年）の都は平安京、現在の京都に置かれました。'
            },
            {
                'question': '戦国時代の三英傑と呼ばれるのは？',
                'options': [
                    '織田信長・豊臣秀吉・徳川家康',
                    '武田信玄・上杉謙信・織田信長',
                    '足利尊氏・新田義貞・楠木正成',
                    '源頼朝・源義経・平清盛'
                ],
                'correct': 1,
                'explanation': '戦国三英傑は織田信長、豊臣秀吉、徳川家康です。この3人が戦国時代の統一を成し遂げました。'
            }
        ]
        
        created_count = 0
        for i, q_data in enumerate(history_questions, 1):
            try:
                quiz = Quiz.objects.create(
                    video=video,
                    question=q_data['question'],
                    option_1=q_data['options'][0],
                    option_2=q_data['options'][1],
                    option_3=q_data['options'][2],
                    option_4=q_data['options'][3],
                    correct_option=q_data['correct'],
                    explanation=q_data['explanation'],
                    difficulty_level='medium'
                )
                
                if hasattr(quiz, 'order'):
                    quiz.order = i
                    quiz.save()
                
                created_count += 1
                print(f"✅ 歴史問題{i}: {quiz.question[:50]}...")
                
            except Exception as e:
                print(f"❌ 歴史問題{i}作成エラー: {e}")
                continue
        
        return created_count

    def generate_quiz_with_whisper_pipeline(self, video_id, user=None):
        """Whisper音声処理→要約→クイズ生成の完全パイプライン"""
        try:
            print(f"🎵 Whisperパイプライン開始: 動画ID {video_id}")
            
            from django.apps import apps
            LearningVideo = apps.get_model('playlist', 'LearningVideo')
            video = LearningVideo.objects.get(id=video_id)
            
            print(f"🎬 処理対象動画: {video.title}")
            
            # Step 1: 音声ダウンロード
            audio_file_path = self.download_audio_from_youtube(video.video_id)
            if not audio_file_path:
                print("❌ 音声ダウンロード失敗 - フォールバックに移行")
                return self.execute_fallback_generation(video_id, user)
            
            # Step 2: Whisperで音声を字幕化
            transcript = self.transcribe_audio_with_whisper(audio_file_path)
            if not transcript:
                print("❌ 音声字幕化失敗 - フォールバックに移行")
                self.cleanup_temp_file(audio_file_path)
                return self.execute_fallback_generation(video_id, user)
            
            # Step 3: トランスクリプトを要約
            summary = self.summarize_transcript(transcript)
            if not summary:
                print("❌ 要約処理失敗 - フォールバックに移行")
                self.cleanup_temp_file(audio_file_path)
                return self.execute_fallback_generation(video_id, user)
            
            # Step 4: 要約からクイズ生成
            quiz_data = self.generate_quiz_from_summary(video.title, summary, user)
            
            # Step 5: クリーンアップ
            self.cleanup_temp_file(audio_file_path)
            
            if quiz_data and quiz_data.get('questions'):
                quiz_data['generation_method'] = 'whisper_pipeline'
                quiz_data['transcript_length'] = len(transcript)
                quiz_data['summary_length'] = len(summary)
                quiz_data['audio_processed'] = True
                
                print(f"✅ Whisperパイプライン完了: {len(quiz_data['questions'])}問生成")
                return quiz_data
            else:
                print("❌ クイズ生成失敗 - フォールバックに移行")
                return self.execute_fallback_generation(video_id, user)
                
        except Exception as e:
            print(f"❌ Whisperパイプラインエラー: {e}")
            return self.execute_fallback_generation(video_id, user, error_message=str(e))

    def download_audio_from_youtube(self, youtube_video_id):
        """YouTubeから音声をダウンロード"""
        try:
            print(f"⬇️ YouTube音声ダウンロード開始: {youtube_video_id}")
            
            # 一時ファイルの作成
            temp_dir = tempfile.gettempdir()
            audio_file = os.path.join(temp_dir, f"youtube_audio_{youtube_video_id}.wav")
            
            # yt-dlpの設定
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_file.replace('.wav', '.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': 192,
            }
            
            url = f"https://www.youtube.com/watch?v={youtube_video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 動画情報を取得
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration', 0)
                
                # 長時間動画の制限（10分以上は最初の10分のみ）
                if duration > 600:  # 10分
                    print(f"⚠️ 長時間動画({duration}秒) - 最初の10分のみ処理")
                    ydl_opts['postprocessor_args'] = ['-t', '600']
                
                # 音声ダウンロード実行
                ydl.download([url])
            
            # ダウンロードされたファイルを確認
            if os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file)
                print(f"✅ 音声ダウンロード完了: {audio_file} ({file_size} bytes)")
                return audio_file
            else:
                print(f"❌ 音声ファイルが見つかりません: {audio_file}")
                return None
                
        except Exception as e:
            print(f"❌ YouTube音声ダウンロードエラー: {e}")
            return None

    def transcribe_audio_with_whisper(self, audio_file_path):
        """OpenAI WhisperAPIで音声を字幕化"""
        try:
            print(f"🎤 Whisper音声字幕化開始: {audio_file_path}")
            
            if not self.openai_available:
                print("❌ OpenAI API利用不可")
                return None
            
            # ファイルサイズチェック（WhisperAPIは25MB制限）
            file_size = os.path.getsize(audio_file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB
                print(f"⚠️ ファイルサイズが大きすぎます: {file_size} bytes")
                # 音声ファイルを分割する処理を実装可能
                return None
            
            # Whisper APIを呼び出し
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=self.whisper_settings['model'],
                    file=audio_file,
                    response_format=self.whisper_settings['response_format'],
                    language=self.whisper_settings['language'],
                    temperature=self.whisper_settings['temperature']
                )
            
            if transcript and hasattr(transcript, 'text'):
                transcript_text = transcript.text
            else:
                transcript_text = str(transcript)
            
            print(f"✅ Whisper字幕化完了: {len(transcript_text)}文字")
            print(f"📝 字幕プレビュー: {transcript_text[:200]}...")
            
            return transcript_text
            
        except Exception as e:
            print(f"❌ Whisper字幕化エラー: {e}")
            return None

    def summarize_transcript(self, transcript):
        """トランスクリプトを要約"""
        try:
            print(f"📄 トランスクリプト要約開始: {len(transcript)}文字")
            
            if not self.openai_available:
                print("❌ OpenAI API利用不可")
                return None
            
            # 長いトランスクリプトをチャンク分割
            if len(transcript) > self.summary_settings['max_transcript_length']:
                print("📚 長文のため分割要約を実行")
                return self.summarize_long_transcript(transcript)
            
            # 要約プロンプト
            summary_prompt = f"""
以下は教育動画の音声を字幕化したテキストです。
この内容を学習者向けに分かりやすく要約してください。

要約のポイント:
1. 主要な学習ポイントを抽出
2. 重要な概念や用語を含める
3. 具体例があれば含める
4. 学習者が理解しやすい構造で整理
5. 400-600文字程度で簡潔に

元のテキスト:
{transcript}

要約:
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは教育コンテンツの要約の専門家です。学習者が理解しやすい要約を作成してください。"
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                max_tokens=self.summary_settings['summary_max_tokens'],
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            print(f"✅ 要約完了: {len(summary)}文字")
            print(f"📋 要約プレビュー: {summary[:200]}...")
            
            return summary
            
        except Exception as e:
            print(f"❌ 要約処理エラー: {e}")
            return None

    def summarize_long_transcript(self, transcript):
        """長いトランスクリプトの分割要約"""
        try:
            print("📚 長文トランスクリプトの分割要約開始")
            
            # チャンクに分割
            chunks = self.split_text_into_chunks(
                transcript, 
                self.summary_settings['chunk_size'],
                self.summary_settings['overlap_size']
            )
            
            print(f"📄 {len(chunks)}個のチャンクに分割")
            
            # 各チャンクを要約
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                print(f"📝 チャンク{i+1}/{len(chunks)}を要約中...")
                
                chunk_summary = self.summarize_single_chunk(chunk, i+1)
                if chunk_summary:
                    chunk_summaries.append(chunk_summary)
            
            # チャンク要約を統合
            if chunk_summaries:
                final_summary = self.combine_chunk_summaries(chunk_summaries)
                print(f"✅ 分割要約完了: {len(final_summary)}文字")
                return final_summary
            else:
                print("❌ チャンク要約に失敗")
                return None
                
        except Exception as e:
            print(f"❌ 分割要約エラー: {e}")
            return None

    def split_text_into_chunks(self, text, chunk_size, overlap_size):
        """テキストをオーバーラップ付きでチャンクに分割"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 文の境界で切る
            if end < len(text):
                # 最後の句点を探す
                last_period = text.rfind('。', start, end)
                if last_period > start:
                    end = last_period + 1
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # オーバーラップを考慮して次の開始位置を設定
            start = end - overlap_size
            if start >= len(text):
                break
        
        return chunks

    def summarize_single_chunk(self, chunk, chunk_number):
        """単一チャンクの要約"""
        try:
            prompt = f"""
以下は教育動画の一部(パート{chunk_number})の音声テキストです。
この部分の要点を200文字程度で要約してください。

テキスト:
{chunk}

要約:
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ チャンク{chunk_number}要約エラー: {e}")
            return None

    def combine_chunk_summaries(self, chunk_summaries):
        """チャンク要約を統合して最終要約を作成"""
        try:
            combined_text = "\n\n".join([f"パート{i+1}: {summary}" for i, summary in enumerate(chunk_summaries)])
            
            final_prompt = f"""
以下は教育動画の各パートの要約です。
これらを統合して、動画全体の学習内容を包括的に要約してください。

各パートの要約:
{combined_text}

最終的な統合要約(500-800文字):
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは教育コンテンツの要約統合の専門家です。"
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ 要約統合エラー: {e}")
            return None

    def generate_quiz_from_summary(self, video_title, summary, user=None):
        """要約からクイズを生成"""
        try:
            print(f"📝 要約ベースクイズ生成開始")
            
            if not self.openai_available:
                print("❌ OpenAI API利用不可")
                return None
            
            # コンテンツ分析
            content_type = self.detect_content_type(video_title)
            age_group = self.detect_age_group(video_title, user)
            
            print(f"📊 分析結果: {content_type} - {age_group}")
            
            # 要約ベースクイズ生成プロンプト
            quiz_prompt = self.build_summary_based_quiz_prompt(
                video_title, summary, content_type, age_group
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"あなたは{age_group}向けの教育クイズ作成の専門家です。動画の要約から適切な学習クイズを作成してください。"
                    },
                    {
                        "role": "user",
                        "content": quiz_prompt
                    }
                ],
                max_tokens=2500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            quiz_json = response.choices[0].message.content
            quiz_data = json.loads(quiz_json)
            
            # メタデータを追加
            quiz_data.update({
                'generation_method': 'summary_based',
                'content_type': content_type,
                'age_group': age_group,
                'video_title': video_title,
                'source_summary': summary[:200] + "..." if len(summary) > 200 else summary
            })
            
            if self.validate_quiz_structure(quiz_data):
                print(f"✅ 要約ベースクイズ生成完了: {len(quiz_data.get('questions', []))}問")
                return quiz_data
            else:
                print("❌ 生成されたクイズ構造が無効")
                return None
                
        except Exception as e:
            print(f"❌ 要約ベースクイズ生成エラー: {e}")
            return None

    def build_summary_based_quiz_prompt(self, video_title, summary, content_type, age_group):
        """要約ベースクイズ生成プロンプト構築"""
        age_descriptions = {
            'elementary_low': '小学1-3年',
            'elementary_mid': '小学4-6年', 
            'junior_high': '中学生',
            'general': '一般'
        }
        
        age_desc = age_descriptions.get(age_group, '一般')
        
        return f"""
動画「{video_title}」の内容要約から、{age_desc}向けの{content_type}分野のクイズを5問作成してください。

動画内容の要約:
{summary}

以下のJSON形式で回答してください：
{{
    "questions": [
        {{
            "question": "動画内容に基づく問題文",
            "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
            "correct": 2,
            "explanation": "動画内容を参照した詳しい解説",
            "content_reference": "要約のどの部分に基づいているか"
        }}
    ]
}}

要件:
- 動画の実際の内容に基づく問題のみ作成
- 一般論ではなく、この動画特有の内容を問う
- {age_desc}に適した難易度と表現
- 4択問題で正解は1-4の数字
- 解説は動画内容を参照
- 学習効果の高い良質な問題
"""

    def cleanup_temp_file(self, file_path):
        """一時ファイルの削除"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ 一時ファイル削除: {file_path}")
        except Exception as e:
            print(f"⚠️ 一時ファイル削除エラー: {e}")

    def generate_quiz(self, video_id, user=None, force_fallback=False, use_whisper=True):
        """動画IDからクイズを自動生成（Whisperパイプライン対応版）"""
        try:
            # デバッグモード: フォールバック強制実行
            if force_fallback or self.debug_settings.get('force_fallback', False):
                print("🔧 デバッグモード: フォールバック生成を強制実行")
                return self.execute_fallback_generation(video_id, user)
            
            from django.apps import apps
            
            try:
                LearningVideo = apps.get_model('playlist', 'LearningVideo')
                video = LearningVideo.objects.get(id=video_id)
                
                print(f"🤖 AIクイズ生成開始: ID={video_id}, タイトル={video.title}")
                
                # Whisperパイプラインの使用判定
                if use_whisper and self.openai_available and self.should_use_whisper_pipeline(video):
                    print("🎵 Whisperパイプラインを使用します")
                    return self.generate_quiz_with_whisper_pipeline(video_id, user)
                else:
                    print("📋 従来のタイトルベース生成を使用します")
                    return self.generate_quiz_title_based(video, user)
                
            except Exception as model_error:
                print(f"❌ モデル取得エラー: {model_error}")
                return self.execute_fallback_generation(video_id, user, error_message=str(model_error))
            
        except Exception as e:
            print(f"❌ クイズ生成エラー: {e}")
            return self.execute_fallback_generation(video_id, user, error_message=str(e))

    def should_use_whisper_pipeline(self, video):
        """Whisperパイプラインを使用すべきかの判定"""
        try:
            # YouTube APIで動画の詳細情報を取得
            if not self.youtube_api_key:
                print("⚠️ YouTube API未設定 - タイトルベース生成を使用")
                return False
            
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'contentDetails,snippet',
                'id': video.video_id,
                'key': self.youtube_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    
                    # 動画の長さをチェック
                    duration = item.get('contentDetails', {}).get('duration', '')
                    duration_seconds = self.parse_youtube_duration(duration)
                    
                    # 20分以下の動画のみWhisperパイプラインを使用
                    if duration_seconds and duration_seconds <= 1200:  # 20分
                        print(f"✅ Whisperパイプライン対象: {duration_seconds}秒")
                        return True
                    else:
                        print(f"⚠️ 動画が長すぎます: {duration_seconds}秒 - タイトルベース生成を使用")
                        return False
            
            print("⚠️ YouTube API応答エラー - タイトルベース生成を使用")
            return False
            
        except Exception as e:
            print(f"⚠️ Whisperパイプライン判定エラー: {e} - タイトルベース生成を使用")
            return False

    def parse_youtube_duration(self, duration_str):
        """YouTube duration文字列を秒に変換"""
        try:
            import re
            # PT1H2M30S -> 3750秒の変換
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return total_seconds
            
            return None
            
        except Exception as e:
            print(f"❌ duration解析エラー: {e}")
            return None

    def generate_quiz_title_based(self, video, user):
        """従来のタイトルベース生成"""
        print("📋 タイトルベースクイズ生成")
        
        content_type = self.detect_content_type(video.title)
        age_group = self.detect_age_group(video.title, user)
        
        # 既存のAI生成を試行
        ai_result = self.try_ai_generation_sync(video.title, content_type, age_group)
        if ai_result and ai_result.get('questions'):
            ai_result['generation_method'] = 'title_based'
            return ai_result
        
        # フォールバックに移行
        return self.execute_fallback_generation(video.id, user)
