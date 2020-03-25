# _*_ coding:utf-8 _*_
__author__ = 'cc'
__date__ = '2019/6/3 15:26'
import re
from .models import UserProfile,Address
from django import forms

def email_check(email):
    pattern = re.compile(r"\"?([-a-zA-Z0-9.~?{}]+@\w+\.\w+)\"?")
    return re.match(pattern,email)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20)
    password1 = forms.CharField(min_length=6)
    password2 = forms.CharField(min_length=6)
    email = forms.EmailField()
    is_xy = forms.BooleanField(required=False)

    def clean_username(self):
        username = self.cleaned_data.get('username')

        filter_result = UserProfile.objects.filter(username=username)
        if len(filter_result) > 0:
            raise forms.ValidationError("username is exist!")

        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        if len(password1) < 6:
            raise forms.ValidationError("password is too short")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1!=password2:
            raise forms.ValidationError("password inconformity!")

        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email_check(email):
            filter_result = UserProfile.objects.filter(email=email)
            if len(filter_result) > 0:
                raise forms.ValidationError('email 已注册过了')
        else:
            raise forms.ValidationError('email error!')

        return email

class LoginForm(forms.Form):
    username = forms.CharField(label='username',max_length=20)
    pwd = forms.CharField(label='pwd',min_length=6)

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['receiver','address','zip_code','phone']

    def clean_zip_code(self):
        zip_code = self.cleaned_data['zip_code']

        if len(zip_code) > 6 or len(zip_code) < 6:
            raise forms.ValidationError("邮箱格式不正确！")

        return zip_code

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        REGEX_MOBILE = "^1[358]\d{9}$|^147\d{8}$|^176\d{8}$"  # 正则手机号
        p = re.compile(REGEX_MOBILE)
        if p.match(phone):
            return phone
        else:
            raise forms.ValidationError("手机号非法！")



