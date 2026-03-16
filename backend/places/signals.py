import logging
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Place

logger = logging.getLogger(__name__)
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8000")


@receiver(post_save, sender=Place)
def auto_vectorize_on_approve(sender, instance, **kwargs):
    """
    Khi Admin duyệt địa điểm (status → APPROVED), tự động gửi request
    đến AI Service để sinh vector ngữ nghĩa và lưu lại.
    """
    if instance.status != 'APPROVED':
        return
    if instance.embedding_vector:
        # Đã có vector rồi, bỏ qua
        return

    # Tạo text đầu vào cho model: tên + địa chỉ + mô tả + tags
    tag_names = ' '.join(instance.tags.values_list('name', flat=True))
    category_name = instance.category.name if instance.category else ''
    text = ' '.join(filter(None, [
        instance.name,
        category_name,
        instance.address or '',
        instance.description or '',
        tag_names,
    ]))

    try:
        resp = requests.post(
            f"{AI_SERVICE_URL}/vectorize",
            json={"place_id": str(instance.id), "text": text},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        vector = data.get("vector")
        if vector:
            # Cập nhật trực tiếp để tránh kích hoạt signal lại
            Place.objects.filter(pk=instance.pk).update(embedding_vector=vector)
            logger.info("Auto-vectorized place '%s' (id=%s)", instance.name, instance.id)
    except requests.exceptions.RequestException as e:
        logger.warning("Could not vectorize place '%s': %s", instance.name, e)
