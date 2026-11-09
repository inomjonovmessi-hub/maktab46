from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import SchoolFeedback, TopStudent


class PublicSchoolSectionsTests(TestCase):
    def test_home_displays_top_students_in_configured_order(self):
        second = TopStudent.objects.create(
            full_name="Ikkinchi o'quvchi",
            grade="9-A",
            achievement_title="Fan olimpiadasi",
            score_or_rank="2-o'rin",
            order=2,
        )
        first = TopStudent.objects.create(
            full_name="Birinchi o'quvchi",
            grade="9-A",
            achievement_title="Matematika olimpiadasi",
            score_or_rank="1-o'rin",
            order=1,
        )

        response = self.client.get(reverse("school:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["top_students"]), [first, second])
        self.assertContains(response, "Iqtidorli o'quvchilar reytingi")
        self.assertContains(response, "Qabul hujjatlari cheklisti")

    @patch("school.views.requests.post")
    def test_feedback_is_saved_and_sent_to_telegram(self, telegram_post):
        telegram_post.return_value.json.return_value = {"ok": True}
        payload = {
            "sender_name": "Ali Valiyev",
            "phone": "+998901234567",
            "feedback_type": "taklif",
            "message": "Kutubxona ish vaqtini uzaytirish taklifi.",
        }

        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "test-token"}):
            response = self.client.post(reverse("school:submit_feedback"), payload)

        feedback = SchoolFeedback.objects.get()
        self.assertRedirects(response, reverse("school:home"))
        self.assertEqual(feedback.sender_name, payload["sender_name"])
        self.assertEqual(feedback.phone, payload["phone"])
        self.assertEqual(feedback.feedback_type, payload["feedback_type"])
        self.assertEqual(feedback.message, payload["message"])
        telegram_post.assert_called_once_with(
            "https://api.telegram.org/bottest-token/sendMessage",
            data={
                "chat_id": "8896873421",
                "text": (
                    "Yangi mulohaza (46-maktab)!\n\n"
                    "Kimdan: Ali Valiyev\n"
                    "Telefon: +998901234567\n"
                    "Turi: taklif\n"
                    "Matn: Kutubxona ish vaqtini uzaytirish taklifi."
                ),
            },
            timeout=10,
        )

    @patch("school.views.requests.post")
    def test_invalid_feedback_is_not_saved_or_sent(self, telegram_post):
        response = self.client.post(
            reverse("school:submit_feedback"),
            {
                "sender_name": "",
                "phone": "90",
                "feedback_type": "not-a-choice",
                "message": "",
            },
        )

        self.assertRedirects(response, reverse("school:home"))
        self.assertFalse(SchoolFeedback.objects.exists())
        telegram_post.assert_not_called()
