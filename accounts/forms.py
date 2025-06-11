from django import forms
from .models import UserProfile
from datetime import date

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'birth_date']
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ニックネームを入力してください',
                'maxlength': 50,
                'required': True
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'nickname': 'ニックネーム',
            'birth_date': '生年月日',
        }
        help_texts = {
            'nickname': '学習画面で表示される名前です（50文字以内）',
            'birth_date': '年齢に応じたクイズが生成されます',
        }

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname or not nickname.strip():
            raise forms.ValidationError('ニックネームは必須です。')
        return nickname.strip()

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if not birth_date:
            raise forms.ValidationError('生年月日は必須です。')
        
        # 年齢制限チェック（5歳〜120歳）
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        if age < 5:
            raise forms.ValidationError('5歳以上の方のみご利用いただけます。')
        if age > 120:
            raise forms.ValidationError('正しい生年月日を入力してください。')
        
        return birth_date
