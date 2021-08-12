from django.core import paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q

from django.contrib.auth.decorators import login_required

# from different app
from carts.models import CartItem
from carts.views import _cart_id

from .models import Product
from  category.models import Category

@login_required()
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

    not_available = single_product.stock <= 0
    context = {
        'single_product'    : single_product,
        'not_available'     : not_available,
        'in_cart'           : in_cart
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
