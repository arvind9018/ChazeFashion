# catalog/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST # Import require_POST

# Import your models
from .models import Product, UserProfile, Cart, Wishlist, Order, CartItem 
from .forms import UserProfileForm

# Helper function to get or create cart for authenticated/anonymous users
def _get_or_create_cart(request):
    if request.user.is_authenticated:
        # For authenticated users, try to get their cart or create one
        cart, created = Cart.objects.get_or_create(user=request.user)
        # If there's an anonymous cart in session, merge it
        session_key = request.session.session_key
        if session_key:
            try:
                anonymous_cart = Cart.objects.get(session_key=session_key)
                # Merge items from anonymous cart into user's cart
                for item in anonymous_cart.items.all():
                    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                    if not item_created:
                        cart_item.quantity += item.quantity
                    else:
                        cart_item.quantity = item.quantity # If new, set quantity
                    cart_item.save()
                anonymous_cart.delete() # Delete the anonymous cart after merging
                del request.session['session_key'] # Clear the session key
            except Cart.DoesNotExist:
                pass # No anonymous cart to merge
    else:
        # For anonymous users, use session_key
        session_key = request.session.session_key
        if not session_key:
            request.session.save() # Ensure a session key exists
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    return cart


def home(request):
    """Home/Landing page"""
    products = Product.objects.all()[:8]  # Show first 8 products
    context = {
        'products': products,
    }
    return render(request, 'catalog/home.html', context)

def signup(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            # Cart and Wishlist will be created on first access or merged if anonymous cart exists

            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'catalog/signup.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Merge anonymous cart if exists before logging in the user
            _get_or_create_cart(request) # This will handle merging if anonymous cart exists
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'catalog/login.html')

@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    """User profile page"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'catalog/profile.html', context)

def product_list(request):
    """Product catalog with filtering"""
    products = Product.objects.all()
    
    # Filtering
    category = request.GET.get('category')
    season = request.GET.get('season')
    fabric = request.GET.get('fabric')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    brand = request.GET.get('brand')
    
    if category:
        products = products.filter(pr_cate=category)
    if season:
        products = products.filter(pr_season=season)
    if fabric:
        products = products.filter(pr_fabric__icontains=fabric)
    if price_min:
        products = products.filter(pr_price__gte=price_min)
    if price_max:
        products = products.filter(pr_price__lte=price_max)
    if brand:
        products = products.filter(pr_brand__icontains=brand)
    
    context = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'seasons': Product.SEASON_CHOICES,
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page"""
    product = get_object_or_404(Product, pr_id=product_id)
    reviews = product.review_set.all().order_by('-created_at')
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'catalog/product_detail.html', context)

@require_POST # Ensure this view only accepts POST requests
def add_to_cart(request, product_id):
    """Add product to cart (with quantity)"""
    product = get_object_or_404(Product, pr_id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product_detail', product_id=product.pr_id)

    cart = _get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f'{product.pr_name} (x{quantity}) added to cart!')
    return redirect('cart') # Redirect to cart view

def cart(request):
    """View cart and update quantities"""
    cart_obj = _get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()
    total = cart_obj.get_total_price() # Use the method from the Cart model

    if request.method == 'POST':
        if 'update_cart' in request.POST: # Check if this is an update request
            for item in cart_items:
                # Use a specific name for the quantity input to avoid conflicts
                qty_str = request.POST.get(f'quantity_{item.id}')
                try:
                    qty = int(qty_str)
                    if qty > 0:
                        item.quantity = qty
                        item.save()
                    else:
                        item.delete() # Remove if quantity is 0 or less
                except (ValueError, TypeError):
                    messages.error(request, "Invalid quantity provided.")
                    return redirect('cart')
            messages.success(request, 'Cart updated successfully!')
        elif 'remove_item' in request.POST: # Check if this is a remove request (optional, can use separate URL)
            item_id = request.POST.get('item_id')
            if item_id:
                try:
                    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart_obj)
                    product_name = cart_item.product.pr_name
                    cart_item.delete()
                    messages.info(request, f'{product_name} removed from cart.')
                except:
                    messages.error(request, "Error removing item.")
        
        return redirect('cart') # Always redirect after POST to prevent re-submission

    context = {
        'cart': cart_obj, # Pass the cart object
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'catalog/cart.html', context)


@require_POST # Ensure this view only accepts POST requests
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    cart_obj = _get_or_create_cart(request)
    # Ensure the item belongs to the current user's cart
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart_obj)
    
    product_name = cart_item.product.pr_name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart.')
    return redirect('cart')

@login_required
def wishlist(request):
    """User wishlist"""
    user_wishlist, created = Wishlist.objects.get_or_create(user=request.user) # Ensure wishlist exists
    context = {
        'wishlist': user_wishlist,
    }
    return render(request, 'catalog/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, pr_id=product_id)
    user_wishlist, created = Wishlist.objects.get_or_create(user=request.user) # Ensure wishlist exists
    if product not in user_wishlist.products.all():
        user_wishlist.products.add(product)
        messages.success(request, f'{product.pr_name} added to wishlist!')
    else:
        messages.info(request, f'{product.pr_name} is already in your wishlist.')
    return redirect('product_detail', product_id=product_id)


@login_required # Checkout usually requires a logged-in user
def checkout(request):
    cart_obj = _get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()
    total_price = cart_obj.get_total_price()

    if not cart_items:
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('product_list')

    # In a real application, you'd process payment, create an order, clear the cart here.
    # For now, it's just a placeholder.

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
        'total_price': total_price,
        'messages': messages.get_messages(request), # Ensure messages are passed
    }
    return render(request, 'catalog/checkout.html', context)

@login_required
@require_POST # It's good practice for removal actions to be POST requests
def remove_from_wishlist(request, product_id):
    """
    Removes a product from the user's wishlist.
    """
    product = get_object_or_404(Product, pr_id=product_id)
    user_wishlist = get_object_or_404(Wishlist, user=request.user) # Get the user's wishlist

    if product in user_wishlist.products.all():
        user_wishlist.products.remove(product)
        messages.success(request, f"'{product.pr_name}' removed from your wishlist.")
    else:
        messages.info(request, f"'{product.pr_name}' was not in your wishlist.")
    
    return redirect('wishlist') # Redirect back to the wishlist page