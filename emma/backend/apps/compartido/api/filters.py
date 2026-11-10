"""Small query helpers shared by API views."""

from django.db.models import Q


def apply_search(queryset, search_term, fields):
    if not search_term:
        return queryset

    query = Q()
    for field in fields:
        query |= Q(**{f"{field}__icontains": search_term})
    return queryset.filter(query)


def apply_ordering(queryset, ordering, allowed_fields):
    if not ordering:
        return queryset

    requested_fields = []
    for raw_field in ordering.split(","):
        field = raw_field.strip()
        clean_field = field.removeprefix("-")
        if clean_field in allowed_fields:
            requested_fields.append(field)

    if not requested_fields:
        return queryset
    return queryset.order_by(*requested_fields)
