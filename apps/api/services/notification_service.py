from typing import List, Optional
from datetime import datetime

class NotificationService:
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email notification"""
        # Placeholder - would integrate with SMTP
        print(f"Email to {to}: {subject}")
        return True

    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS notification"""
        # Placeholder - would integrate with Twilio
        print(f"SMS to {to}: {message}")
        return True

    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "INFO"
    ) -> dict:
        """Create in-app notification"""
        return {
            "id": 1,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
        }
