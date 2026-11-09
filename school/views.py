import logging
import os

import requests

from django.contrib import messages
from django.contrib.auth import login, logout
from django.db.models import F
from django.http import FileResponse, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ApplicationForm,
    SchoolFeedbackForm,
    UserLoginForm,
    UserRegisterForm,
)
from .models import (
    Application,
    Book,
    CustomUser,
    SchoolImage,
    SchoolMapInfo,
    SiteStat,
    Teacher,
    NewsEvent,
    TopStudent,
)

logger = logging.getLogger(__name__)


def _telegram_send(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "8896873421")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN sozlanmagan; Telegram xabari yuborilmadi.")
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            logger.error("Telegram API xabarni qabul qilmadi: %s", result)
            return False
        return True
    except (requests.RequestException, ValueError) as exc:
        logger.error("Telegram xabarini yuborishda xatolik: %s", type(exc).__name__)
        return False


def home_view(request: HttpRequest):
    print(">>> QANDAY METOD KELDI:", request.method)
    if request.method == "POST":
        return redirect("school:submit_application")
    if not request.session.get("site_visitor_counted"):
        SiteStat.objects.get_or_create(pk=1)
        SiteStat.objects.filter(pk=1).update(
            total_views=F("total_views") + 1,
            unique_visitors=F("unique_visitors") + 1,
        )
        request.session["site_visitor_counted"] = True
    site_stat = SiteStat.objects.get(pk=1)
    map_info = SchoolMapInfo.objects.filter(is_active=True).prefetch_related("images").first()
    gallery_images = [
        image
        for image in SchoolImage.objects.filter(map_info=map_info)
        .exclude(title__iexact="inomjonov ibrohimjon")
        if image.image and image.image.storage.exists(image.image.name)
    ] if map_info else []
    return render(
        request,
        "index.html",
        {
            "map_info": map_info,
            "gallery": gallery_images,
            "application_form": ApplicationForm(),
            "feedback_form": SchoolFeedbackForm(),
            "login_form": UserLoginForm(),
            "register_form": UserRegisterForm(),
            "books": Book.objects.all(),
            "book_subjects": Book.objects.values_list("subject", flat=True).distinct(),
            "teachers": Teacher.objects.all(),
            "visitor_count": site_stat.total_views,
            "registered_users_count": CustomUser.objects.count(),
            "news_events": NewsEvent.objects.filter(is_active=True),
            "top_students": TopStudent.objects.all(),
        },
    )


def submit_application(request: HttpRequest):
    if request.method != "POST":
        print(">>> ARIZA XATOSI: POST emas:", request.method)
        return redirect("school:home")

    print(">>> YANGI ARIZA POST SO'ROVI KELDI:", request.POST)
    student_name = request.POST.get("student_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    grade = request.POST.get("grade", "Ko'rsatilmadi").strip()
    print(">>> ARIZA MAYDONLARI:", student_name, phone, grade)

    if not student_name or not phone:
        print(">>> ARIZA XATOSI: majburiy maydon bo'sh")
        messages.error(request, "Iltimos, barcha maydonlarni to'ldiring!")
        return redirect("school:home")

    try:
        grade_level = int(grade)
    except (TypeError, ValueError):
        grade_level = Application.Grade.FIRST

    application = Application.objects.create(
        student_name=student_name,
        phone=phone,
        grade_level=grade_level,
    )
    print(">>> ARIZA BAZAGA SAQLANDI:", application.tracking_code)

    telegram_sent = _telegram_send(
        f"Yangi ariza (46-maktab)!\n\n"
        f"O'quvchi: {student_name}\n"
        f"Telefon: {phone}\n"
        f"Sinf: {grade}\n"
        f"Ariza ID: {application.tracking_code}"
    )
    print(">>> TELEGRAM YUBORILDI:", telegram_sent)
    messages.success(request, "Arizangiz muvaffaqiyatli qabul qilindi!")
    return redirect("school:home")


def application_status(request: HttpRequest):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"success": False, "message": "ID yoki telefon raqamini kiriting."}, status=400)
    application = Application.objects.filter(tracking_code__iexact=query).first()
    if not application:
        phone_query = "".join(character for character in query if character.isdigit())
        if len(phone_query) == 9:
            phone_query = f"+998{phone_query}"
        elif len(phone_query) == 12 and phone_query.startswith("998"):
            phone_query = f"+{phone_query}"
        application = Application.objects.filter(phone=phone_query or query).first()
    if not application:
        return JsonResponse({"success": False, "message": "Ariza topilmadi."}, status=404)
    return JsonResponse(
        {
            "success": True,
            "id": application.tracking_code,
            "status": application.get_status_display(),
            "status_code": application.status,
            "interview_at": application.interview_at.strftime("%d.%m.%Y %H:%M")
            if application.interview_at else None,
            "student_name": application.student_name,
            "grade": application.get_grade_level_display(),
            "created_at": application.created_at.strftime("%d.%m.%Y"),
        }
    )


def submit_feedback(request: HttpRequest):
    if request.method != "POST":
        return redirect("school:home")
    form = SchoolFeedbackForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Taklif va mulohaza ma'lumotlarini tekshiring.")
        return redirect("school:home")
    feedback = form.save()
    telegram_sent = _telegram_send(
        f"Yangi mulohaza (46-maktab)!\n\n"
        f"Kimdan: {feedback.sender_name}\n"
        f"Telefon: {feedback.phone}\n"
        f"Turi: {feedback.feedback_type}\n"
        f"Matn: {feedback.message}"
    )
    messages.success(request, "Taklif va mulohazangiz muvaffaqiyatli saqlandi.")
    if not telegram_sent:
        messages.warning(request, "Murojaat saqlandi, ammo Telegram orqali xabar yuborilmadi.")
    return redirect("school:home")


def download_book(request: HttpRequest, book_id: int):
    book = get_object_or_404(Book, pk=book_id)
    book.downloads += 1
    book.save(update_fields=["downloads"])
    return FileResponse(book.pdf.open("rb"), as_attachment=True, filename=f"{book.title}.pdf")


def register(request: HttpRequest):
    if request.method != "POST":
        return redirect("school:home")
    form = UserRegisterForm(request.POST)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Hisobingiz muvaffaqiyatli yaratildi.")
    else:
        messages.error(request, "; ".join(form.errors.get("__all__", [])) or "Ro'yxatdan o'tish ma'lumotlarini tekshiring.")
    return redirect("school:home")


def user_login(request: HttpRequest):
    form = UserLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        login(request, user)
        messages.success(request, "Tizimga muvaffaqiyatli kirdingiz.")
    else:
        messages.error(request, "Username yoki telefon, yoki parol noto'g'ri.")
    return redirect("school:home")


def logout_view(request: HttpRequest):
    logout(request)
    return redirect("school:home")
