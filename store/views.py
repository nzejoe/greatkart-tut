from django.core import paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import ReviewForm

# from different app
from carts.models import CartItem
from carts.views import _cart_id

from .models import Product, ReviewRating
from  category.models import Category

from orders.models import OrderProduct

def store(request, category_slug=None):

    categories      = None
    products        = None

    if category_slug is not None:
        categories      = get_object_or_404(Category, slug=category_slug)
        products        = Product.objects.filter(category=categories, is_available=True)
        paginator       = Paginator(products, 1)
        page            = request.GET.get('page')
        paged_products  = paginator.get_page(page)
        product_count   = products.count()
        
    else:
        products        = Product.objects.all().filter(is_available=True).order_by('id')
        paginator       = Paginator(products, 3)
        page            = request.GET.get('page')
        paged_products  = paginator.get_page(page)
        product_count   = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    # check if user made a purchase for this product
    if request.user.is_authenticated:
        try:
            is_purchased = OrderProduct.objects.filter(user=request.user, product__id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            is_purchased = None
    else:
        is_purchased = None

    # get product reviews
    reviews = ReviewRating.objects.filter(product__id=single_product.id, status=True)

    not_available = single_product.stock <= 0
    context = {
        'single_product'    : single_product,
        'not_available'     : not_available,
        'in_cart'           : in_cart,
        'is_purchased': is_purchased,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = None
    product_count = 0
    if request.method == 'GET':
        search_keyword = request.GET.get('keyword')
        if search_keyword:
            products = Product.objects.filter(Q(product_name__icontains=search_keyword) | Q(description__icontains=search_keyword))
            product_count = products.count()
    context = {
        'products':products,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        try:
            review = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data.get('subject')
                data.rating = form.cleaned_data.get('rating')
                data.review = form.cleaned_data.get('review')
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted')
                return redirect(url)
