"""Providers de notification — interfaces préparées, aucune implémentation V1.

Chaque provider est un stub qui implémente NotificationProvider mais
ne contient aucune logique d'envoi. Ils seront implémentés en V2+.

Providers prévus :
- FirebaseCloudMessaging (FCM) — notifications push Android/Web
- ApplePushNotification (APNS) — notifications push iOS
- WebPushProvider — notifications push navigateur (VAPID)
- EmailProvider — envoi d'emails (SMTP ou API type SendGrid)
- SmsProvider — envoi de SMS (API type Twilio, local)
- WhatsAppProvider — envoi via WhatsApp Business API (future extension)
"""

from __future__ import annotations

from app.notifications.base import NotificationProvider
from app.notifications.schemas import NotificationMessage, NotificationResult


class FirebaseCloudMessagingProvider(NotificationProvider):
    """Provider Firebase Cloud Messaging (FCM) — push Android/Web.

    TODO V2: Implémenter l'envoi via l'API FCM HTTP v1.
    Dépendances futures : google-auth, httpx.
    """

    @property
    def channel(self) -> str:
        return "fcm"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("FCM provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass


class ApplePushNotificationProvider(NotificationProvider):
    """Provider Apple Push Notification Service (APNS) — push iOS.

    TODO V2: Implémenter l'envoi via APNs JWT auth.
    Dépendances futures : httpx, cryptography (pour le JWT).
    """

    @property
    def channel(self) -> str:
        return "apns"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("APNS provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass


class WebPushProvider(NotificationProvider):
    """Provider Web Push — notifications push navigateur (VAPID).

    TODO V2: Implémenter l'envoi via Web Push Protocol (RFC 8030).
    Dépendances futures : py-vapid, httpx.
    """

    @property
    def channel(self) -> str:
        return "web_push"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("Web Push provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass


class EmailProvider(NotificationProvider):
    """Provider Email — envoi d'emails.

    TODO V2: Implémenter via SMTP ou API tierce (SendGrid, Mailgun, etc.).
    Dépendances futures : aiosmtplib ou httpx (selon l'API choisie).
    """

    @property
    def channel(self) -> str:
        return "email"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("Email provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass


class SmsProvider(NotificationProvider):
    """Provider SMS — envoi de SMS.

    TODO V2: Implémenter via API tierce (Twilio, Vonage, ou opérateur local).
    Dépendances futures : httpx.
    """

    @property
    def channel(self) -> str:
        return "sms"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("SMS provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass


class WhatsAppProvider(NotificationProvider):
    """Provider WhatsApp Business — envoi via WhatsApp Cloud API.

    TODO V3: Implémenter via Meta WhatsApp Business Cloud API.
    Dépendances futures : httpx.
    Note: Extension future — le webhook WhatsApp existe déjà côté Gateway.
    """

    @property
    def channel(self) -> str:
        return "whatsapp"

    async def send(self, message: NotificationMessage) -> NotificationResult:
        raise NotImplementedError("WhatsApp provider non implémenté en V1.")

    async def aclose(self) -> None:
        pass
