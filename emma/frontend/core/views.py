from django.shortcuts import render

from .errors import ApiClientError, to_user_message


def render_api_list(request, template_name, fetcher, context_name, form=None):
    items = []
    alert = None

    try:
        response = fetcher()
        if isinstance(response, dict):
            items = response.get("results", response.get(context_name, []))
        elif isinstance(response, list):
            items = response
    except ApiClientError as exc:
        alert = {"level": "danger", "message": to_user_message(exc)}

    return render(
        request,
        template_name,
        {
            context_name: items,
            "form": form,
            "alert": alert,
        },
    )


def error_404(request, exception=None):
    return render(
        request,
        "errors/404.html",
        status=404,
    )


def error_500(request):
    return render(
        request,
        "errors/500.html",
        status=500,
    )
