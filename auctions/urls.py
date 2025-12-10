from django.urls import path

from . import views

app_name = "auctions"

urlpatterns = [
    path("", views.index, name="index"),
    path("closed_listings", views.closed, name="closed"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("category_list", views.category_list, name="category_list"),
    path("categories/<str:category_name>", views.categories, name="categories"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("create_listing", views.create, name="create"),
    path("<int:listing_id>", views.listing, name="listing"),
    path("watchlisting/<int:listing_id>", views.opt_watchlist, name="watchlisting"),
    path("bidding/<int:listing_id>", views.bidding, name="bidding"),
    path("close/<int:listing_id>", views.close, name="close")
]
