from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Product, Cart, CartItem, Order, OrderItem, Category, UserProfile, ContactMessage, SiteContactInfo, SitePage, FAQItem
from django.contrib import messages
import csv
from django.http import HttpResponse


def home(request):
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')

    product_list = Product.objects.all()

    if query:
        product_list = product_list.filter(name__icontains=query)

    if category_slug:
        product_list = product_list.filter(category__slug=category_slug)

    if min_price:
        product_list = product_list.filter(price__gte=min_price)

    if max_price:
        product_list = product_list.filter(price__lte=max_price)

    if sort == 'price_asc':
        product_list = product_list.order_by('price')
    elif sort == 'price_desc':
        product_list = product_list.order_by('-price')
    elif sort == 'newest':
        product_list = product_list.order_by('-created_at')

    categories = Category.objects.all()

    context = {
        'products': product_list,
        'categories': categories,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'selected_sort': sort,
    }
    return render(request, 'home.html', context)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            remember_me = request.POST.get('remember_me')
            if remember_me:
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            if user.is_superuser:
                return redirect('my_admin_dashboard')
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock and cannot be added to cart.")
        return redirect('home')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} quantity updated in cart.")
        else:
            messages.warning(request, f"Sorry, only {product.stock} units of {product.name} are available. You cannot add more.")
    else:
        messages.success(request, f"{product.name} added to cart!")

    return redirect('home')


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart')


@login_required
def update_cart_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, f"Sorry, only {cart_item.product.stock} units of {cart_item.product.name} are available.")
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()

    return redirect('cart')


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


@login_required
def checkout_review(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        return redirect('cart')

    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f"Sorry, only {item.product.stock} units of {item.product.name} are available. Please update your cart.")
            return redirect('cart')

    total = sum(item.total_price() for item in cart_items)

    return render(request, 'checkout_review.html', {'cart_items': cart_items, 'total': total})


@login_required
def checkout(request):
    if request.method != 'POST':
        return redirect('cart')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        return redirect('cart')

    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f"Sorry, only {item.product.stock} units of {item.product.name} are available. Please update your cart.")
            return redirect('cart')

    total = sum(item.total_price() for item in cart_items)

    order = Order.objects.create(user=request.user, total_amount=total)

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            quantity=item.quantity,
            price=item.product.price
        )
        item.product.stock -= item.quantity
        item.product.save()

    cart_items.delete()

    return redirect('order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})


def about_us(request):
    page, created = SitePage.objects.get_or_create(
        page_key='about_us',
        defaults={'title': 'About Us', 'content': ''}
    )
    return render(request, 'about_us.html', {'page': page})


def privacy_policy(request):
    page, created = SitePage.objects.get_or_create(
        page_key='privacy_policy',
        defaults={'title': 'Privacy Policy', 'content': ''}
    )
    return render(request, 'privacy_policy.html', {'page': page})


def terms_conditions(request):
    page, created = SitePage.objects.get_or_create(
        page_key='terms_conditions',
        defaults={'title': 'Terms & Conditions', 'content': ''}
    )
    return render(request, 'terms_conditions.html', {'page': page})


def faq(request):
    faq_items = FAQItem.objects.all()
    faq_by_category = {}
    for item in faq_items:
        faq_by_category.setdefault(item.category, []).append(item)

    context = {
        'faq_by_category': faq_by_category,
        'category_labels': dict(FAQItem.CATEGORY_CHOICES),
    }
    return render(request, 'faq.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    product_list = Product.objects.filter(category=category)
    return render(request, 'category_detail.html', {'category': category, 'products': product_list})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'pending':
        messages.error(request, "This order cannot be cancelled anymore.")
        return redirect('my_orders')

    for item in order.items.all():
        if item.product:
            item.product.stock += item.quantity
            item.product.save()

    order.status = 'cancelled'
    order.save()

    messages.success(request, f"Order #{order.id} has been cancelled.")
    return redirect('my_orders')


@login_required
def my_admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
    pending_count = pending_orders.count()
    total_users = User.objects.filter(is_superuser=False).count()
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0).order_by('stock')
    out_of_stock_products = Product.objects.filter(stock=0)
    total_revenue = Order.objects.exclude(status='cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    chart_labels = []
    chart_data = []
    today = timezone.now().date()

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_revenue = Order.objects.filter(
            created_at__date=day
        ).exclude(status='cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        chart_labels.append(day.strftime('%d %b'))
        chart_data.append(float(day_revenue))

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'pending_count': pending_count,
        'total_users': total_users,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }
    return render(request, 'my_admin_dashboard.html', context)


@login_required
def update_order_status(request, order_id, new_status):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to do this.")
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)

    if new_status in ['pending', 'shipped', 'delivered', 'cancelled']:
        if new_status == 'cancelled' and order.status != 'cancelled':
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()

        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status.title()}.")

    return redirect('my_admin_dashboard')


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_product_list(request):
    query = request.GET.get('q')
    products = Product.objects.all().order_by('-created_at')

    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'admin_product_list.html', {'products': products, 'search_query': query})


@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        category = Category.objects.get(id=category_id) if category_id else None

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            image=image
        )
        messages.success(request, f"Product '{name}' added successfully.")
        return redirect('admin_product_list')

    categories = Category.objects.all()
    return render(request, 'admin_product_form.html', {'categories': categories, 'product': None})


@admin_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        product.category = Category.objects.get(id=category_id) if category_id else None

        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully.")
        return redirect('admin_product_list')

    categories = Category.objects.all()
    return render(request, 'admin_product_form.html', {'categories': categories, 'product': product})


@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted.")
    return redirect('admin_product_list')


@admin_required
def admin_category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'admin_category_list.html', {'categories': categories})


@admin_required
def admin_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(name=name)
        messages.success(request, f"Category '{name}' added successfully.")
        return redirect('admin_category_list')

    return render(request, 'admin_category_form.html', {'category': None})


@admin_required
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        messages.success(request, f"Category '{category.name}' updated successfully.")
        return redirect('admin_category_list')

    return render(request, 'admin_category_form.html', {'category': category})


@admin_required
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    name = category.name
    category.delete()
    messages.success(request, f"Category '{name}' deleted.")
    return redirect('admin_category_list')


@admin_required
def admin_all_orders(request):
    status_filter = request.GET.get('status')

    orders = Order.objects.all().order_by('-created_at')

    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'selected_status': status_filter,
    }
    return render(request, 'admin_all_orders.html', context)


@admin_required
def admin_user_list(request):
    query = request.GET.get('q')
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    if query:
        users = users.filter(username__icontains=query)

    user_data = []
    for user in users:
        order_count = Order.objects.filter(user=user).count()
        avatar = None
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar = user.profile.avatar.url
        user_data.append({
            'user': user,
            'order_count': order_count,
            'avatar': avatar,
        })

    return render(request, 'admin_user_list.html', {'user_data': user_data, 'search_query': query})


@login_required
def profile_edit(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'update_info' in request.POST:
            new_username = request.POST.get('username', '').strip()

            if new_username != request.user.username:
                if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                    messages.error(request, "This username is already taken.")
                    return redirect('profile_edit')
                request.user.username = new_username

            request.user.first_name = request.POST.get('first_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()

            if request.FILES.get('avatar'):
                profile.avatar = request.FILES.get('avatar')
                profile.save()

            messages.success(request, "Your profile information has been updated.")
            return redirect('profile_edit')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect('profile_edit')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error.as_text())
                return redirect('profile_edit')

        elif 'delete_account' in request.POST:
            request.user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect('home')

    total_orders = Order.objects.filter(user=request.user).count()
    total_spent = Order.objects.filter(user=request.user).exclude(status='cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'profile': profile,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'profile_edit.html', context)


@admin_required
def admin_profile(request):
    if request.method == 'POST':
        if 'update_info' in request.POST:
            request.user.first_name = request.POST.get('first_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            messages.success(request, "Your profile information has been updated.")
            return redirect('admin_profile')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect('admin_profile')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error.as_text())
                return redirect('admin_profile')

    return render(request, 'admin_profile.html')


@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    return render(request, 'admin_order_detail.html', {'order': order, 'order_items': order_items})


@admin_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Date', 'Amount', 'Status'])

    orders = Order.objects.all().order_by('-created_at')
    for order in orders:
        writer.writerow([
            order.id,
            order.user.username,
            order.user.email,
            order.created_at.strftime('%d %b %Y, %I:%M %p'),
            order.total_amount,
            order.get_status_display(),
        ])

    return response


@admin_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Date Joined', 'Total Orders'])

    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    for user in users:
        order_count = Order.objects.filter(user=user).count()
        writer.writerow([
            user.username,
            user.email,
            user.date_joined.strftime('%d %b %Y'),
            order_count,
        ])

    return response


def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        messages.success(request, "Thank you for reaching out! We'll get back to you soon.")
        return redirect('contact_us')

    return render(request, 'contact_us.html')


@admin_required
def admin_contact_messages(request):
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    return render(request, 'admin_contact_messages.html', {'contact_messages': contact_messages, 'unread_count': unread_count})


@admin_required
def mark_message_read(request, message_id):
    message = get_object_or_404(ContactMessage, id=message_id)
    message.is_read = True
    message.save()
    return HttpResponse(status=204)

@admin_required
def admin_contact_info_list(request):
    contact_info = SiteContactInfo.objects.all()
    return render(request, 'admin_contact_info_list.html', {'contact_info': contact_info})


@admin_required
def admin_contact_info_add(request):
    if request.method == 'POST':
        type_ = request.POST.get('type')
        value = request.POST.get('value')
        label = request.POST.get('label')
        order = request.POST.get('order') or 0

        SiteContactInfo.objects.create(
            type=type_,
            value=value,
            label=label,
            order=order
        )
        messages.success(request, "Contact info added successfully.")
        return redirect('admin_contact_info_list')

    return render(request, 'admin_contact_info_form.html', {'contact': None})


@admin_required
def admin_contact_info_edit(request, contact_id):
    contact = get_object_or_404(SiteContactInfo, id=contact_id)

    if request.method == 'POST':
        contact.type = request.POST.get('type')
        contact.value = request.POST.get('value')
        contact.label = request.POST.get('label')
        contact.order = request.POST.get('order') or 0
        contact.save()
        messages.success(request, "Contact info updated successfully.")
        return redirect('admin_contact_info_list')

    return render(request, 'admin_contact_info_form.html', {'contact': contact})


@admin_required
def admin_contact_info_delete(request, contact_id):
    contact = get_object_or_404(SiteContactInfo, id=contact_id)
    contact.delete()
    messages.success(request, "Contact info deleted.")
    return redirect('admin_contact_info_list')


@admin_required
def admin_site_pages_list(request):
    pages = SitePage.objects.all()
    existing_keys = [p.page_key for p in pages]

    all_keys = dict(SitePage.PAGE_CHOICES)
    missing = [{'page_key': key, 'title': label} for key, label in all_keys.items() if key not in existing_keys]

    return render(request, 'admin_site_pages_list.html', {'pages': pages, 'missing': missing})


@admin_required
def admin_site_page_edit(request, page_key):
    page, created = SitePage.objects.get_or_create(
        page_key=page_key,
        defaults={'title': dict(SitePage.PAGE_CHOICES).get(page_key, page_key), 'content': ''}
    )

    if request.method == 'POST':
        page.title = request.POST.get('title')
        page.content = request.POST.get('content')
        page.save()
        messages.success(request, f"{page.title} updated successfully.")
        return redirect('admin_site_pages_list')

    return render(request, 'admin_site_page_form.html', {'page': page})


@admin_required
def admin_faq_list(request):
    faq_items = FAQItem.objects.all()
    return render(request, 'admin_faq_list.html', {'faq_items': faq_items})


@admin_required
def admin_faq_add(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        order = request.POST.get('order') or 0

        FAQItem.objects.create(
            category=category,
            question=question,
            answer=answer,
            order=order
        )
        messages.success(request, "FAQ item added successfully.")
        return redirect('admin_faq_list')

    return render(request, 'admin_faq_form.html', {'faq_item': None})


@admin_required
def admin_faq_edit(request, faq_id):
    faq_item = get_object_or_404(FAQItem, id=faq_id)

    if request.method == 'POST':
        faq_item.category = request.POST.get('category')
        faq_item.question = request.POST.get('question')
        faq_item.answer = request.POST.get('answer')
        faq_item.order = request.POST.get('order') or 0
        faq_item.save()
        messages.success(request, "FAQ item updated successfully.")
        return redirect('admin_faq_list')

    return render(request, 'admin_faq_form.html', {'faq_item': faq_item})


@admin_required
def admin_faq_delete(request, faq_id):
    faq_item = get_object_or_404(FAQItem, id=faq_id)
    faq_item.delete()
    messages.success(request, "FAQ item deleted.")
    return redirect('admin_faq_list')