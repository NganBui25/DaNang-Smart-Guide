from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class LimitedPageNumberPagination(PageNumberPagination):
    """Pagination with a hard cap to prevent excessive page sizes."""

    page_size = getattr(settings, "PAGE_SIZE_DEFAULT", 12)
    page_size_query_param = 'page_size'
    max_page_size = getattr(settings, "PAGE_SIZE_MAX", 50)
