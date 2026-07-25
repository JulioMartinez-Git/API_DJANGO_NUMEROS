from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    if response.status_code == 403:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        if isinstance(detail, dict) and detail.get("code"):
            response.data = detail

    return response
