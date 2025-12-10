from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Categories(models.Model):
    name = models.CharField(max_length= 100, null=False)

    def __str__(self):
        return f"{self.name}"

class Listings(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.CharField(max_length=400)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name="categorized", default=1)
    image_url = models.CharField(max_length=300, blank=True)
    lister = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listed_by", null=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="won", null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title}"

class Bids(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids", null=True)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="bids_on", null=True)

    def __str__(self):
        return f"{self.amount}"

class Comments(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commented", null=True)
    comment = models.CharField(max_length= 500, null=False)
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="comments_on", null=True)

    def __str__(self):
        return f"{self.commenter}: {self.comment}"

class Watchlist(models.Model):
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="watchlisted", null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlister", null=True)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.listing}"
