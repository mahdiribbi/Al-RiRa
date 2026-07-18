from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order, OrderItem, Category
from django.contrib import messages


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
            if user.is_superuser:
                return redirect('/admin/')
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
def checkout(request):
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
    return render(request, 'about_us.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def terms_conditions(request):
    return render(request, 'terms_conditions.html')


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    product_list = Product.objects.filter(category=category)
    return render(request, 'category_detail.html', {'category': category, 'products': product_list})