from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max


class User(AbstractUser):
    pass
class Category(models.Model):
    category_name=models.CharField(max_length=60)
    def __str__(self):
        return self.category_name


class Listing (models.Model):
    title= models.CharField(max_length=30)
    description= models.CharField(max_length=300)
    image = models.CharField(max_length=1000) 
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active=models.BooleanField(default=True)
    owner=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="user")
    category= models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name="category")
    created_at = models.DateTimeField(auto_now_add=True) 
    def __str__(self):
        return self.title
    def highest_bid(self):
        # Aggregate to get the maximum bid amount for this listing
        highest_bid = self.bids.aggregate(Max('amount'))['amount__max']
        if highest_bid is None:
            return 0.00  # Return 0.00 if there are no bids yet
        return highest_bid
    def close_auction(self):
        if self.is_active:
            # Obtener la oferta más alta y el último postor antes de cerrar la subasta
            winning_bid = self.bids.order_by('-created_at').first()
            
            if winning_bid:
                self.is_active = False
                self.save()
                return winning_bid.user
        return None
    
class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comentari = models.CharField(max_length=500)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments', default= None)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.comentari
    
class Watch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watches')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='watchlist_entries')
    has_won = models.BooleanField(default=False) 

    def __str__(self):
        return 'Personal watchlist for %s' % (self.user)
class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid of {self.amount} on {self.listing.title} by {self.user.username}"

    