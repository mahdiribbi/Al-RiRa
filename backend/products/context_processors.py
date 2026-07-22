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

def unread_messages_count(request):
    if request.user.is_authenticated and request.user.is_superuser:
        from .models import ContactMessage
        count = ContactMessage.objects.filter(is_read=False).count()
        display_count = '99+' if count > 99 else count
        return {'unread_messages_count': count, 'unread_messages_display': display_count}
    return {'unread_messages_count': 0, 'unread_messages_display': 0}

def contact_info(request):
    from .models import SiteContactInfo
    return {'site_contact_info': SiteContactInfo.objects.all()}