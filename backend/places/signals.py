import json
import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Place


logger = logging.getLogger(__name__)
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8000")


def _normalize_text(value):
    return str(value).strip() if value is not None else ""


@receiver(post_save, sender=Place)
def auto_vectorize_on_approve(sender, instance, **kwargs):
    if instance.status != "APPROVED":
        return
    if instance.embedding_vector:
        return

    tag_names = " ".join(
        tag_name
        for tag_name in (
            _normalize_text(tag) for tag in instance.tags.values_list("name", flat=True)
        )
        if tag_name
    )
    category_name = _normalize_text(instance.category.name if instance.category else "")
    text = " ".join(
        filter(
            None,
            [
                _normalize_text(instance.name),
                category_name,
                _normalize_text(instance.address),
                _normalize_text(instance.description),
                tag_names,
            ],
        )
    )
    payload = {"place_id": str(instance.id), "text": text}

    try:
        logger.info(
            "Vectorize payload for place '%s': %s",
            instance.name,
            json.dumps(payload, ensure_ascii=False),
        )
        response = requests.post(
            f"{AI_SERVICE_URL}/vectorize",
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        vector = data.get("vector")
        if vector:
            Place.objects.filter(pk=instance.pk).update(embedding_vector=vector)
            logger.info("Auto-vectorized place '%s' (id=%s)", instance.name, instance.id)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not vectorize place '%s': %s", instance.name, exc)
