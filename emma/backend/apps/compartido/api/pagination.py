"""Pagination classes for the EMMA API contract."""

from urllib.parse import urlsplit, urlunsplit

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class EmmaPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": _relative_url(self.get_next_link()),
                "previous": _relative_url(self.get_previous_link()),
                "results": data,
            }
        )


class ContractPaginationMixin:
    pagination_class = None

    def paginated_response(self, queryset, serializer_class):
        paginator_class = self.pagination_class or api_settings.DEFAULT_PAGINATION_CLASS
        if paginator_class is None:
            serializer = serializer_class(queryset, many=True)
            return Response(serializer.data)

        paginator = paginator_class()
        page = paginator.paginate_queryset(queryset, self.request, view=self)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)


def _relative_url(url):
    if not url:
        return None
    parsed = urlsplit(url)
    return urlunsplit(("", "", parsed.path, parsed.query, parsed.fragment))
