from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Listings, Bids, Comments, Categories, Watchlist
from decimal import Decimal


def index(request):
    listings = Listings.objects.filter(active=True).order_by('-id')
    return render(request, "auctions/index.html", {
        "listings": listings
    })

def closed(request):
    listings = Listings.objects.filter(active=False).order_by('-id')
    return render(request, "auctions/closed.html", {
        "listings": listings
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

def category_list(request):
   categories = Categories.objects.all()
   return render(request, "auctions/categories.html", {
        "categories": categories,
    })

def categories(request, category_name):
    category = get_object_or_404(Categories, name=category_name)
    listings = category.categorized.filter(active=True).order_by("-id")
    return render(request, "auctions/category.html", {
        "category": category,
        "listings" : listings
        })

@login_required
def create(request):
    if request.method=="POST":
        title = request.POST.get("title")
        if not title:
            return render(request, "auctions/error.html", {
                "message": "Please enter the name of the item to be listed."
            })

        description = request.POST.get("description")
        if not description:
            return render(request, "auctions/error.html", {
                "message": "Please enter the description of the item to be listed :("
            })

        price = request.POST.get("starting_bid")
        if not price:
            return render(request, "auctions/error.html", {
                "message": "Please enter the price (starting bid) of the item to be listed :("
            })

        category_id = request.POST.get("category_id")
        if not category_id:
            return render(request, "auctions/error.html", {
                "message": "Please choose a category for the item to be listed :("
            })

        category = Categories.objects.get(id=category_id)
        image_url = request.POST.get("image_url")

        lister = request.user

        listing = Listings(title=title, price=price, description=description, category=category, image_url=image_url, lister=lister)
        listing.save()
        return HttpResponseRedirect(reverse("auctions:listing", args=[listing.id]))
    return render(request, "auctions/create.html")


def listing(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    if not listing:
        return render(request, "auctions/error.html", {
                "message": "Listing not found. :("
            })

    if request.method=="POST":

        # handling comments
        if not request.user.is_authenticated:
            return render(request, "auctions/error.html", {
                    "message": "Sign in or register to add new comments!"
                })
        comment = request.POST.get("comment")
        if not comment:
            return render(request, "auctions/error.html", {
                    "message": "Cannot add an empty comment :("
                })
        commenter = request.user

        comments = Comments(comment=comment, commenter = commenter, listing = listing)
        comments.save()

        return HttpResponseRedirect(reverse("auctions:listing", args=[listing.id]))

    highest_bid = Bids.objects.filter(listing = listing).order_by("-amount").first()
    in_watchlist = False
    if request.user.is_authenticated:
        in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "comments": listing.comments_on.all().order_by('-id'),
        "in_watchlist": in_watchlist,
        "highest_bid" : highest_bid
    })

def opt_watchlist(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    if not listing:
        return render(request, "auctions/error.html", {
                "message": "Listing not found. :("
            })
    if request.method=="POST":
        if not request.user.is_authenticated:
            return render(request, "auctions/error.html", {
                "message": "Sign in or register to add items to your watchlist. :)"
            })
        in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()
        if not in_watchlist:
            add_to_watchlist = Watchlist(listing=listing, user=request.user)
            add_to_watchlist.save()
        else:
            Watchlist.objects.filter(user=request.user, listing=listing).delete()

    return HttpResponseRedirect(reverse("auctions:listing", args=[listing.id]))

@login_required
def watchlist(request):
   watchlisted = Watchlist.objects.filter(user=request.user).order_by('-id')
   listings = [watchlist.listing for watchlist in watchlisted]
   return render(request, "auctions/watchlist.html", {
        "watchlisted": watchlisted,
        "listings": listings
    })

def bidding(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    if not listing:
        return render(request, "auctions/error.html", {
                "message": "Listing not found. :("
            })
    if request.method=="POST":
        if not request.user.is_authenticated:
            return render(request, "auctions/error.html", {
                "message": "Sign in or register to bid on items. :)"
            })
        bid = request.POST.get("bid")
        if not bid:
           return render(request, "auctions/error.html", {
                "message": "Please enter a valid amount to bid. :("
            })
        try:
            bid = Decimal(bid)
        except ValueError:
            return render(request, "auctions/error.html", {
                "message": "Please enter a positive integer to place your bid."
            })
        highest_bid = Bids.objects.filter(listing = listing).order_by("-amount").first()
        success_message = None
        if bid < 0:
            return render(request, "auctions/error.html", {
                "message": "Please enter a positive integer to place your bid."
            })

        if highest_bid is None and bid >= listing.price:
            bids = Bids(amount = bid, bidder = request.user, listing = listing)
            bids.save()
            success_message = "Your bid was placed successfully!"

        elif highest_bid is not None and bid > highest_bid.amount:
            bids = Bids(amount = bid, bidder = request.user, listing = listing)
            bids.save()
            success_message = "Your bid was placed successfully!"
            highest_bid = Bids.objects.filter(listing = listing).order_by("-amount").first()

        else:
            return render(request, "auctions/error.html", {
                "message": "Your bid must be at least as large as the starting bid, and must be greater than any other bids that have been placed."
            })

        in_watchlist = False
        if request.user.is_authenticated:
            in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "in_watchlist" : in_watchlist,
            "success_message": success_message,
            "highest_bid": highest_bid
        })
    return HttpResponseRedirect(reverse("auctions:listing", args=[listing.id]))

def close(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    if not listing:
        return render(request, "auctions/error.html", {
                "message": "Listing not found. :("
            })
    if request.method=="POST":
        close = request.POST.get("close")
        if not close:
            return render(request, "auctions/error.html", {
                "message": "Try closing the auction for the listing again. :("
            })
        if listing.lister == request.user:
            user = request.user
            listing.active = False
            listing.save()
            winning_bid= Bids.objects.filter(listing = listing).order_by('-amount').first()
            if not winning_bid:
                listing.winner = None
                listing.save()
            else:
                listing.winner = winning_bid.bidder
                listing.save()
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "user" : user,
                "comments": listing.comments_on.all().order_by('-id'),
            })
    return HttpResponseRedirect(reverse("auctions:listing", args=[listing.id]))
