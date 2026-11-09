from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Max
from django.utils import timezone
from urllib.parse import quote, urlparse


phone_validator = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon +998XXXXXXXXX ko'rinishida bo'lishi kerak.",
)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = "teacher", "Ustoz"
        STUDENT = "student", "Mustaqil o'quvchi"
        DIRECTOR = "director", "Direktor"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    academic_info = models.CharField("Sinf yoki fan", max_length=100, blank=True)


class SiteStat(models.Model):
    total_views = models.PositiveBigIntegerField("Jami tashriflar", default=0)
    unique_visitors = models.PositiveBigIntegerField("Noyob tashrif buyuruvchilar", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sayt statistikasi"
        verbose_name_plural = "Sayt statistikasi"

    def __str__(self):
        return f"{self.total_views} tashrif"


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        INTERVIEW = "interview", "Suhbatga chaqirildi"
        ACCEPTED = "accepted", "Qabul qilindi"
        REJECTED = "rejected", "Rad etildi"

    class Grade(models.IntegerChoices):
        FIRST = 1, "1-sinf boshlang'ich"
        SECOND = 2, "2-sinf"
        THIRD = 3, "3-sinf"
        FOURTH = 4, "4-sinf"
        FIFTH = 5, "5-sinf"
        SIXTH = 6, "6-sinf"
        SEVENTH = 7, "7-sinf"
        EIGHTH = 8, "8-sinf"
        NINTH = 9, "9-sinf"
        TENTH = 10, "10-sinf ixtisoslashgan"
        ELEVENTH = 11, "11-sinf"

    student_name = models.CharField("O'quvchining ismi va familiyasi", max_length=150)
    phone = models.CharField("Telefon raqami", max_length=20, validators=[phone_validator])
    grade_level = models.PositiveSmallIntegerField(
        "Qaysi sinfga?", choices=Grade.choices, default=Grade.FIRST
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    tracking_code = models.CharField(max_length=12, unique=True, editable=False, null=True, blank=True)
    interview_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Maktabga qabul arizasi"
        verbose_name_plural = "Maktabga qabul arizalari"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            next_number = 4600 + (Application.objects.aggregate(max_id=Max("id"))["max_id"] or 0) + 1
            self.tracking_code = f"MK-{next_number:04d}"
            while Application.objects.filter(tracking_code=self.tracking_code).exclude(pk=self.pk).exists():
                next_number += 1
                self.tracking_code = f"MK-{next_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_name} — {self.get_status_display()}"


class Student(models.Model):
    full_name = models.CharField("Ism-familiya", max_length=150)
    class_group = models.CharField("Sinf guruhi", max_length=30)
    photo = models.ImageField("Rasm", upload_to="students/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["class_group", "full_name"]
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"

    def __str__(self):
        return f"{self.full_name} ({self.class_group})"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Keldi"
        ABSENT = "absent", "Kelmadi"
        EXCUSED = "excused", "Sababli"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "student__class_group", "student__full_name"]
        constraints = [
            models.UniqueConstraint(fields=["student", "date"], name="unique_student_attendance_day")
        ]
        verbose_name = "Davomat"
        verbose_name_plural = "Davomat"

    def __str__(self):
        return f"{self.student} — {self.date}"


class SchoolMapInfo(models.Model):
    title = models.CharField(max_length=150, default="46-maktab")
    address = models.TextField("Maktab manzili")
    embed_url = models.URLField("Xarita iframe URL manzili", blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=41.311081)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=69.240562)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Maktab xaritasi"
        verbose_name_plural = "Maktab xaritasi"

    def __str__(self):
        return self.title

    @property
    def iframe_url(self):
        """Return a URL that can be used directly as an iframe source."""
        if not self.embed_url:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}&output=embed"

        parsed = urlparse(self.embed_url)
        if parsed.netloc.endswith("google.com") and (
            "/maps/embed" in parsed.path or parsed.query.endswith("output=embed")
        ):
            return self.embed_url

        if parsed.netloc.endswith("google.com") and "/maps" in parsed.path:
            return f"https://www.google.com/maps?q={quote(self.embed_url, safe='')}&output=embed"

        return self.embed_url


# Public name used by integrations and project documentation.
SchoolMap = SchoolMapInfo


class SchoolImage(models.Model):
    map_info = models.ForeignKey(SchoolMapInfo, on_delete=models.CASCADE, related_name="images")
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="school-gallery/%Y/%m/")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "Maktab yoki o'qituvchi rasmi"
        verbose_name_plural = "Maktab va o'qituvchi rasmlari"

    def __str__(self):
        return self.title


class Book(models.Model):
    class GradeCategory(models.TextChoices):
        PRIMARY = "1-4", "1-4-sinflar"
        MIDDLE = "5-9", "5-9-sinflar"
        HIGH = "10-11", "10-11-sinflar"

    title = models.CharField("Sarlavha", max_length=200)
    author = models.CharField("Muallif", max_length=150)
    grade_category = models.CharField("Sinf toifasi", max_length=10, choices=GradeCategory.choices)
    subject = models.CharField("Fan nomi", max_length=100)
    cover = models.ImageField("Muqova rasmi", upload_to="library/covers/", blank=True, null=True)
    pdf = models.FileField("PDF fayli", upload_to="library/books/")
    downloads = models.PositiveIntegerField("Yuklab olishlar soni", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subject", "title"]
        verbose_name = "Elektron kitob"
        verbose_name_plural = "Elektron kutubxona"

    def __str__(self):
        return self.title


class Teacher(models.Model):
    class Qualification(models.TextChoices):
        HIGHEST = "highest", "Oliy toifa"
        FIRST = "first", "1-toifa"
        BEGINNER = "beginner", "Boshlang'ich"

    full_name = models.CharField("F.I.SH", max_length=150)
    position = models.CharField("Lavozimi/Fani", max_length=150)
    qualification = models.CharField("Malaka toifasi", max_length=20, choices=Qualification.choices)
    achievements = models.TextField("Ilmiy unvoni/Yutuqlari", blank=True)
    image = models.ImageField("Rasmi", upload_to="teachers/", blank=True, null=True)
    experience = models.CharField("Tajribasi", max_length=50)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Ustoz yoki rahbariyat"
        verbose_name_plural = "Ustozlar va rahbariyat"

    def __str__(self):
        return self.full_name


class Facility(models.Model):
    name = models.CharField("Xona/Bino nomi", max_length=200)
    image = models.ImageField("Rasmi", upload_to="facilities/")
    description = models.TextField("Qisqa imkoniyatlari")

    class Meta:
        ordering = ["name"]
        verbose_name = "Maktab xonasi yoki binosi"
        verbose_name_plural = "Maktab xonalari va binolari"

    def __str__(self):
        return self.name


class DirectorFeedback(models.Model):
    class FeedbackType(models.TextChoices):
        SUGGESTION = "suggestion", "Taklif"
        COMPLAINT = "complaint", "Shikoyat"

    name = models.CharField("Ism", max_length=150)
    phone = models.CharField("Telefon", max_length=20)
    feedback_type = models.CharField("Murojaat turi", max_length=20, choices=FeedbackType.choices)
    message = models.TextField("Xabar matni")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Direktorga murojaat"
        verbose_name_plural = "Direktorga murojaatlar"

    def __str__(self):
        return f"{self.name} — {self.get_feedback_type_display()}"


class NewsEvent(models.Model):
    class Category(models.TextChoices):
        IMPORTANT = "important", "Muhim"
        EVENT = "event", "Tadbir"
        COMPETITION = "competition", "Musobaqa"
        ANNOUNCEMENT = "announcement", "E'lon"

    title = models.CharField("Sarlavha", max_length=250)
    slug = models.SlugField("Slug", max_length=280, unique=True)
    category = models.CharField("Kategoriya", max_length=20, choices=Category.choices)
    image = models.ImageField("Rasm", upload_to="news/", blank=True, null=True)
    short_description = models.TextField("Qisqa tavsif")
    date = models.DateTimeField("Sana", default=timezone.now)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Yangilik yoki e'lon"
        verbose_name_plural = "Yangiliklar va e'lonlar"

    def __str__(self):
        return self.title


class StudentAchievement(models.Model):
    student_name = models.CharField("O'quvchining F.I.SH", max_length=150)
    grade = models.CharField("Sinfi", max_length=30)
    competition_name = models.CharField("Musobaqa/Olimpiada nomi", max_length=250)
    rank = models.CharField("O'rin / Yutuq", max_length=150)
    year = models.PositiveIntegerField("Yil", default=timezone.now().year)
    student_photo = models.ImageField(
        "O'quvchi, diplom va medal rasmi", upload_to="achievements/", blank=True, null=True
    )
    description = models.TextField("Qisqa izoh yoki ustozining ismi", blank=True)

    class Meta:
        ordering = ["-year", "student_name"]
        verbose_name = "Maktab faxri va yutug'i"
        verbose_name_plural = "Maktab faxrlari va yutuqlari"

    def __str__(self):
        return f"{self.student_name} — {self.competition_name}"


class TopStudent(models.Model):
    full_name = models.CharField(max_length=150)
    grade = models.CharField(max_length=20)
    achievement_title = models.CharField(max_length=255)
    score_or_rank = models.CharField(max_length=50)
    photo = models.ImageField(upload_to="top_students/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "full_name"]
        verbose_name = "Iqtidorli o'quvchi"
        verbose_name_plural = "Iqtidorli o'quvchilar"

    def __str__(self):
        return f"{self.full_name} — {self.grade}"


class SchoolFeedback(models.Model):
    class FeedbackType(models.TextChoices):
        SUGGESTION = "taklif", "Taklif"
        COMPLAINT = "shikoyat", "Shikoyat"
        THANKS = "tashakkur", "Tashakkurnoma"

    sender_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    feedback_type = models.CharField(max_length=30, choices=FeedbackType.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Taklif va mulohaza"
        verbose_name_plural = "Taklif va mulohazalar"

    def __str__(self):
        return f"{self.sender_name} — {self.get_feedback_type_display()}"
