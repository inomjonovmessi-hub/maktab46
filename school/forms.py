from django import forms
from django.contrib.auth import authenticate

from .models import (
    Application,
    Attendance,
    CustomUser,
    DirectorFeedback,
    SchoolFeedback,
    Student,
    phone_validator,
)


class ApplicationForm(forms.ModelForm):
    grade = forms.TypedChoiceField(
        choices=Application.Grade.choices,
        coerce=int,
        label="Qaysi sinfga?",
        widget=forms.Select(attrs={"class": "field", "required": True}),
    )

    class Meta:
        model = Application
        fields = ["student_name", "phone"]
        labels = {
            "student_name": "O'quvchining ismi va familiyasi",
            "phone": "Telefon raqami",
        }
        widgets = {
            "student_name": forms.TextInput(attrs={"placeholder": "Masalan: Sardor Aliyev"}),
            "phone": forms.TextInput(
                attrs={
                    "type": "tel",
                    "inputmode": "tel",
                    "placeholder": "90 123 45 67",
                    "autocomplete": "tel",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
        if self.instance and self.instance.pk:
            self.initial["grade"] = self.instance.grade_level

    def save(self, commit=True):
        application = super().save(commit=False)
        application.grade_level = self.cleaned_data["grade"]
        if commit:
            application.save()
        return application


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["full_name", "class_group", "photo"]
        labels = {"full_name": "Ism-familiya", "class_group": "Sinf guruhi", "photo": "Rasm"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"


def normalize_phone(value):
    digits = "".join(character for character in value if character.isdigit())
    return f"+998{digits[-9:]}" if len(digits) == 9 else value


class UserRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Ism va familiya")
    phone = forms.CharField(max_length=20, label="Telefon raqami")
    username = forms.CharField(max_length=150, label="Username")
    password = forms.CharField(min_length=8, label="Parol", widget=forms.PasswordInput)

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not phone_validator.regex.search(phone):
            raise forms.ValidationError(phone_validator.message)
        if CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqami bilan hisob allaqachon mavjud.")
        return phone

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Bu username allaqachon band.")
        return username

    def save(self):
        return CustomUser.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            phone=self.cleaned_data["phone"],
            first_name=self.cleaned_data["full_name"],
        )


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username yoki telefon")
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        identity = data.get("username", "").strip()
        user_record = CustomUser.objects.filter(username__iexact=identity).first()
        if not user_record:
            user_record = CustomUser.objects.filter(phone=normalize_phone(identity)).first()
        user = user_record and authenticate(
            username=user_record.username,
            password=data.get("password"),
        )
        if not user or not user.is_active:
            raise forms.ValidationError("Username yoki telefon, yoki parol noto'g'ri.")
        data["user"] = user
        return data


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["status"]


class DirectorFeedbackForm(forms.ModelForm):
    class Meta:
        model = DirectorFeedback
        fields = ["name", "phone", "feedback_type", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5, "class": "field h-auto"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field")


class SchoolFeedbackForm(forms.ModelForm):
    class Meta:
        model = SchoolFeedback
        fields = ["sender_name", "phone", "feedback_type", "message"]
        widgets = {
            "sender_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"}),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field")
