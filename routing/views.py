import json
import re
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from routing.planner import build_plan


def get_cache_key(start: str, finish: str) -> str:
    """Generate a normalised, memcached-safe cache key for start and finish location string pair."""
    clean_s = re.sub(r"[^\w]", "_", start.strip().lower())
    clean_f = re.sub(r"[^\w]", "_", finish.strip().lower())
    return f"route_v1_{clean_s}_{clean_f}"


@csrf_exempt
def route_api_view(request):
    """
    API endpoint returning fuel route calculation JSON.
    Supports GET /api/route/?start=...&finish=... and POST JSON {"start": "...", "finish": "..."}
    """
    if request.method not in ("GET", "POST"):
        return JsonResponse({"error": "Method not allowed. Use GET or POST."}, status=405)

    start = ""
    finish = ""

    if request.method == "GET":
        start = request.GET.get("start", "")
        finish = request.GET.get("finish", "")
    elif request.method == "POST":
        # Check for JSON payload or form data
        if request.content_type == "application/json":
            try:
                body = json.loads(request.body.decode("utf-8") or "{}")
                start = body.get("start", "")
                finish = body.get("finish", "")
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON request body."}, status=400)
        else:
            start = request.POST.get("start", "")
            finish = request.POST.get("finish", "")

    if not start or not finish:
        return JsonResponse(
            {"error": "Both 'start' and 'finish' parameters are required."},
            status=400,
        )

    cache_key = get_cache_key(start, finish)
    cached_res = cache.get(cache_key)
    if cached_res:
        return JsonResponse(cached_res)

    try:
        plan_res = build_plan(start, finish, request_obj=request)
    except ValueError as e:
        err_msg = str(e)
        # Determine appropriate status code: 400 for bad user input, 422 for unprocessable routing
        if any(term in err_msg for term in ["could not be resolved", "outside the continental US", "Location must be", "empty"]):
            return JsonResponse({"error": err_msg}, status=400)
        return JsonResponse({"error": err_msg}, status=422)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

    ttl = getattr(settings, "RESULT_CACHE_TTL_S", 3600)
    cache.set(cache_key, plan_res, ttl)

    return JsonResponse(plan_res)


def route_map_view(request):
    """
    Renders an HTML Leaflet map page displaying route geometry and fuel stop popups.
    """
    start = request.GET.get("start", "")
    finish = request.GET.get("finish", "")

    if not start or not finish:
        return render(
            request,
            "routing/map.html",
            {"landing": True, "start": start, "finish": finish},
        )

    cache_key = get_cache_key(start, finish)
    plan_res = cache.get(cache_key)

    if not plan_res:
        try:
            plan_res = build_plan(start, finish, request_obj=request)
            ttl = getattr(settings, "RESULT_CACHE_TTL_S", 3600)
            cache.set(cache_key, plan_res, ttl)
        except Exception as e:
            return render(request, "routing/map.html", {"error": str(e)})

    return render(
        request,
        "routing/map.html",
        {
            "plan": plan_res,
            "plan_json": json.dumps(plan_res),
            "start": start,
            "finish": finish,
        },
    )
