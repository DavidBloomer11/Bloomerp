import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse

from bloomerp.router import router
from bloomerp.services.sql_services import SqlExecutor


@router.register(path="api/sql/execute/", name="api_sql_execute")
@login_required
def execute_sql(request: HttpRequest) -> JsonResponse | HttpResponseNotAllowed:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.has_perm("bloomerp.execute_sql_query"):
        return JsonResponse({"error": "Permission denied"}, status=403)

    payload = _extract_payload(request)
    query = str(payload.get("query") or payload.get("sql_query") or "").strip()
    if not query:
        return JsonResponse({"error": "No SQL query provided"}, status=400)

    page = _parse_positive_int(payload.get("page") or payload.get("sql_page"), default=1)
    page_size = _parse_positive_int(payload.get("page_size") or payload.get("sql_page_size"), default=25)

    executor = SqlExecutor(request.user)

    try:
        result = executor.execute_query(query, page=page, page_size=page_size)
    except PermissionError as error:
        return JsonResponse({"error": str(error)}, status=403)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception as error:
        return JsonResponse({"error": f"Query execution failed: {error}"}, status=500)

    return JsonResponse(
        {
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "page_rows_count": result.page_rows_count,
            "execution_ms": result.execution_ms,
            "policy_message": result.policy_message,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "page_start": result.page_start,
            "page_end": result.page_end,
            "output_fields": result.output_fields.model_dump() if result.output_fields else None,
        }
    )


def _extract_payload(request: HttpRequest) -> dict:
    content_type = request.headers.get("Content-Type", "")

    if "application/json" in content_type:
        try:
            body = request.body.decode("utf-8")
            payload = json.loads(body) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    return request.POST.dict()


def _parse_positive_int(value, default: int) -> int:
    try:
        parsed = int(value or "")
    except (TypeError, ValueError):
        return default

    return parsed if parsed > 0 else default
