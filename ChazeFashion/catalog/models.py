# catalog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings # Import settings to use AUTH_USER_MODEL
from django.db.models import Q
# Product Model (No changes needed here for cart functionality, but including for context)
class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Boys", "Boys"),
        ("Girls", "Girls"),
        ("Men", "Men"),
        ("Women", "Women"),
        ("Toddler", "Toddler"),
    ]
    SEASON_CHOICES = [
        ("Summer", "Summer"),
        ("Winter", "Winter"),
        ("All Season", "All Season"),
    ]
    pr_id = models.AutoField(primary_key=True)
    pr_cate = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    pr_name = models.CharField(max_length=100)
    pr_price = models.DecimalField(max_digits=10, decimal_places=2)
    pr_reviews = models.FloatField(default=0)
    pr_buy_quant = models.PositiveIntegerField(default=0)
    pr_stk_quant = models.PositiveIntegerField(default=0)
    pr_dimensions = models.CharField(max_length=100, blank=True)
    pr_weights = models.CharField(max_length=50, blank=True)
    pr_offers = models.CharField(max_length=100, blank=True)
    pr_images = models.ImageField(upload_to='product_images/', blank=True, null=True)
    pr_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default="All Season")
    pr_fabric = models.CharField(max_length=50, blank=True)
    pr_texture = models.CharField(max_length=50, blank=True)
    pr_brand = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True, verbose_name="Product Description")
    def __str__(self):
        return self.pr_name

# Seller Model (No changes)
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    shop_address = models.TextField()
    contact = models.CharField(max_length=20)

    def __str__(self):
        return self.shop_name

# Cart Model (MODIFIED)
class Cart(models.Model):
    # Use settings.AUTH_USER_MODEL for a more robust reference to the User model
    # Make user nullable for anonymous carts
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    # Add a session key for anonymous users
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Add updated_at for better tracking

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Anonymous Cart {self.session_key}"

    def get_total_price(self):
        return sum(item.get_item_total() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    class Meta:
        # Ensure that either user or session_key is present, but not both
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='user_or_session_key_present'
            ),
            models.UniqueConstraint(
                fields=['session_key'], condition=models.Q(session_key__isnull=False), name='unique_session_key_if_not_null'
            )
        ]


# User Profile Extension (MODIFIED - remove cart field, as Cart is now independent)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Removed: cart = models.OneToOneField('Cart', on_delete=models.SET_NULL, null=True, blank=True)
    # The cart is now accessed directly via the user or session key

    def __str__(self):
        return self.user.username

# Wishlist Model (No changes)
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

# Ordered Item Model (No changes)
class OrderedItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

# Order Model (No changes)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderedItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

# Review Model (No changes)
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.pr_name}"

# Payment Model (No changes)
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"

# CartItem Model (MODIFIED - add a method for total price)
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

    def get_item_total(self):
        return self.quantity * self.product.pr_price

    class Meta:
        unique_together = ('cart', 'product') # Prevent duplicate product entries in a cart