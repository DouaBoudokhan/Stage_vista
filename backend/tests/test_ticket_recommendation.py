import unittest

from app.services.jira_service import JiraRecommendationService


class TestJiraRecommendationService(unittest.TestCase):
    def test_rank_recommendations_prefers_urgent_ticket(self):
        service = JiraRecommendationService()
        tickets = [
            {
                "id": "IT-100",
                "title": "Hardware refresh next month",
                "description": "Need a monitor later this quarter",
                "priority": "Low",
                "status": "Open",
                "requester": "Ana",
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "IT-200",
                "title": "Need headset urgently for meeting in 15 minutes",
                "description": "Urgent headset request for today",
                "priority": "High",
                "status": "Open",
                "requester": "Ben",
                "created_at": "2026-08-03T00:00:00Z",
            },
            {
                "id": "IT-300",
                "title": "Need a keyboard for a new developer",
                "description": "Keyboard for onboarding",
                "priority": "Medium",
                "status": "Open",
                "requester": "Celine",
                "created_at": "2026-08-02T00:00:00Z",
            },
        ]

        ranked = service.rank_tickets(
            detected_product="Headset",
            category="Headset",
            quantity=1,
            available_quantity=2,
            tickets=tickets,
        )

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["ticket"]["id"], "IT-200")
        self.assertIn("urgent", ranked[0]["reason"].lower())
