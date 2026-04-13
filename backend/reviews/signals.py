import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from places.models import Place

from .models import Review


logger = logging.getLogger(__name__)
SENTIMENT_TIMEOUT_SECONDS = 10


@receiver(post_save, sender=Review)
def update_place_sentiment_summary(sender, instance, created, **kwargs):
    if not created:
        return

    comments = [
        comment.strip()
        for comment in Review.objects.filter(place_id=instance.place_id)
        .order_by("-created_at")
        .values_list("comment", flat=True)[:50]
        if comment and comment.strip()
    ]
    payload = {"reviews": comments}
    ai_service_url = getattr(settings, "AI_SERVICE_URL", "http://localhost:8000")

    try:
        response = requests.post(
            f"{ai_service_url}/sentiment",
            json=payload,
            timeout=SENTIMENT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        summary = response.json().get("summary")
        if summary is not None:
            Place.objects.filter(pk=instance.place_id).update(ai_sentiment_summary=summary)
            logger.info("Updated AI sentiment summary for place %s", instance.place_id)
    except requests.exceptions.RequestException as exc:
        logger.error(
            "Could not update AI sentiment summary for place %s: %s",
            instance.place_id,
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected error while updating AI sentiment summary for place %s",
            instance.place_id,
        )
