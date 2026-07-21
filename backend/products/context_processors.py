from .models import Cart, Category


def cart_count(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('product').all()
        count = sum(item.quantity for item in cart_items)
        total = sum(item.product.price * item.quantity for item in cart_items)
        return {'cart_item_count': count, 'mini_cart_items': cart_items, 'mini_cart_total': total}
    return {'cart_item_count': 0, 'mini_cart_items': [], 'mini_cart_total': 0}


def categories_processor(request):
    return {'all_categories': Category.objects.all()}