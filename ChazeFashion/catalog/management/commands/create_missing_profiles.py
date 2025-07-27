# catalog/management/commands/create_missing_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import UserProfile, Cart, Wishlist # Import your models

class Command(BaseCommand):
    help = 'Creates UserProfile, Cart, and Wishlist for existing users who do not have them.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to check for missing UserProfiles, Carts, and Wishlists...")

        users = User.objects.all()
        total_users = users.count()
        self.stdout.write(f"Found {total_users} users.")

        for user in users:
            self.stdout.write(f"Processing user: {user.username}")

            # Create UserProfile if it doesn't exist
            user_profile, created_profile = UserProfile.objects.get_or_create(user=user)
            if created_profile:
                self.stdout.write(self.style.SUCCESS(f"  - Created UserProfile for {user.username}"))
            else:
                self.stdout.write(f"  - UserProfile already exists for {user.username}")

            # Create Cart if it doesn't exist (ensuring no session_key for authenticated carts)
            cart, created_cart = Cart.objects.get_or_create(user=user, defaults={'session_key': None})
            if created_cart:
                self.stdout.write(self.style.SUCCESS(f"  - Created Cart for {user.username}"))
            else:
                self.stdout.write(f"  - Cart already exists for {user.username}")

            # Create Wishlist if it doesn't exist
            wishlist, created_wishlist = Wishlist.objects.get_or_create(user=user)
            if created_wishlist:
                self.stdout.write(self.style.SUCCESS(f"  - Created Wishlist for {user.username}"))
            else:
                self.stdout.write(f"  - Wishlist already exists for {user.username}")

        self.stdout.write(self.style.SUCCESS("Finished checking/creating missing profiles, carts, and wishlists."))