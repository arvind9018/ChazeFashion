# catalog/context_processors.py
from .models import Cart

def cart_total_items(request):
    """
    Context processor to make the total number of items in the cart
    available in all templates.
    """
    cart_total_items = 0
    try:
        if request.user.is_authenticated:
            # Try to get the authenticated user's cart
            cart = Cart.objects.get(user=request.user)
        else:
            # For anonymous users, get cart by session key
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.get(session_key=session_key)
            else:
                cart = None # No session key, no anonymous cart
        
        if cart:
            cart_total_items = cart.get_total_items()
    except Cart.DoesNotExist:
        pass # No cart found for the user/session
    
    # The key 'cart_total_items' will be available in your templates
    return {'cart_total_items': cart_total_items}