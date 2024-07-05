from django.urls import path, include

from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),  # Ensure admin URLs end with a slash
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("listing/", views.listing, name="listing"),
    path("categories/", views.categories, name="categories"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path('save_to_watchlist/<int:listing_id>/', views.save_to_watchlist, name='save_to_watchlist'),
    path("watchlist/", views.watchlist, name="watchlist"),
    path('watchlist/remove/<int:listing_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('listing/<int:listing_id>/place_bid/', views.place_bid, name='place_bid'),
    path('listing/<int:listing_id>/close/', views.close_auction, name='close_auction'),
]

if settings.DEBUG:
    urlpatterns+=static(settings.MEDIA_URL,
                        document_root=settings.MEDIA_ROOT)