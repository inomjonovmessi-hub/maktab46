from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import (
    Application,
    Attendance,
    Book,
    CustomUser,
    DirectorFeedback,
    Facility,
    SchoolImage,
    SchoolMapInfo,
    SiteStat,
    Student,
    Teacher,
    NewsEvent,
    StudentAchievement,
    SchoolFeedback,
    TopStudent,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "role", "phone", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Maktab ma'lumotlari", {"fields": ("role", "phone", "academic_info")}),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "student_name", "phone", "grade_level", "status", "interview_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tracking_code", "student_name", "phone")
    readonly_fields = ("tracking_code", "created_at")
    actions = ["approve_applications", "reject_applications"]

    @admin.action(description="Tanlangan arizalarni tasdiqlash")
    def approve_applications(self, request, queryset):
        queryset.update(status=Application.Status.ACCEPTED)

    @admin.action(description="Tanlangan arizalarni rad etish")
    def reject_applications(self, request, queryset):
        queryset.update(status=Application.Status.REJECTED)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "class_group", "created_at")
    search_fields = ("full_name", "class_group")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status", "updated_at")
    list_filter = ("date", "status")
    search_fields = ("student__full_name",)


class SchoolImageInline(admin.TabularInline):
    model = SchoolImage
    extra = 1


@admin.register(SchoolMapInfo)
class SchoolMapInfoAdmin(admin.ModelAdmin):
    list_display = ("title", "address", "latitude", "longitude", "is_active")
    inlines = [SchoolImageInline]


@admin.register(SchoolImage)
class SchoolImageAdmin(admin.ModelAdmin):
    list_display = ("title", "map_info", "order")
    list_filter = ("map_info",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "subject", "grade_category", "downloads")
    list_filter = ("grade_category", "subject")
    search_fields = ("title", "author", "subject")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "qualification", "experience")
    list_filter = ("qualification",)
    search_fields = ("full_name", "position")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ()


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ("id", "total_views", "unique_visitors", "updated_at")
    search_fields = ("id",)
    list_filter = ("updated_at",)
    readonly_fields = ("updated_at",)


@admin.register(DirectorFeedback)
class DirectorFeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "feedback_type", "created_at")
    list_filter = ("feedback_type", "created_at")
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created_at",)


@admin.register(NewsEvent)
class NewsEventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "is_active", "image_preview")
    list_filter = ("category", "is_active", "date")
    search_fields = ("title", "short_description", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("image_preview",)

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" width="100" height="70" style="object-fit:cover;border-radius:6px;">', obj.image.url)


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ("student_name", "grade", "competition_name", "rank", "year", "image_preview")
    list_filter = ("year",)
    search_fields = ("student_name", "grade", "competition_name", "rank", "description")
    readonly_fields = ("image_preview",)

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if not obj.student_photo:
            return "—"
        return format_html(
            '<img src="{}" width="100" height="70" style="object-fit:cover;border-radius:6px;">',
            obj.student_photo.url,
        )


@admin.register(TopStudent)
class TopStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "grade", "achievement_title", "score_or_rank", "order")
    list_display_links = ("full_name",)
    list_editable = ("order",)
    search_fields = ("full_name", "grade", "achievement_title", "score_or_rank")
    ordering = ("order", "full_name")


@admin.register(SchoolFeedback)
class SchoolFeedbackAdmin(admin.ModelAdmin):
    list_display = ("sender_name", "phone", "feedback_type", "created_at")
    list_filter = ("feedback_type", "created_at")
    search_fields = ("sender_name", "phone", "message")
    readonly_fields = ("created_at",)
