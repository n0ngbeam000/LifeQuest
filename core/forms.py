from django import forms
from django.contrib.auth.models import User
import re

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_email(self):
        """ตรวจสอบ email format ว่ามี @ และมี domain ที่ถูกต้อง"""
        email = self.cleaned_data.get('email')
        
        # ตรวจสอบ email pattern - extension ต้องอย่างน้อย 3 ตัวอักษร (com, org, co.th ฯลฯ)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise forms.ValidationError('กรุณากรอก email ให้ถูกต้อง (เช่น example@gmail.com)')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password doesn't match")

class LoginForm(forms.Form): # user forms.Form because in register we use ModelForm because we want to create data to database but in this case we just want to check data that why we use froms.Form
    username = forms.CharField(max_length=65)  # to tell django it get charecter naka 
    password = forms.CharField(widget=forms.PasswordInput) # we use forms.PasswordInput becasue password it a sensitive infomation we want when use input just show ****** not text or number