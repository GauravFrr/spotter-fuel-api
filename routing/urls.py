from django.urls import path
from routing.views import route_api_view, route_map_view

urlpatterns = [
    path("route/", route_api_view, name="route_api"),
    path("route/map/", route_map_view, name="route_map"),
]
