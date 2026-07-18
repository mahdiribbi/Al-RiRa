from .models import Cart, Category

def cart_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        count = sum(item.quantity for item in cart.items.all())
        return {'cart_item_count': count}
    return {'cart_item_count': 0}


def categories_processor(request):
    return {'all_categories': Category.objects.all()}