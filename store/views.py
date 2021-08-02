from django.shortcuts import get_object_or_404, render

from .models import Product
from  category.models import Category


def store(request, category_slug=None):

    categories      = None
    products        = None

    if category_slug is not None:
        categories      = get_object_or_404(Category, slug=category_slug)
        products        = Product.objects.filter(category=categories, is_available=True)
        product_count   = products.count()
    else:
        products        = Product.objects.all().filter(is_available=True)
        product_count   = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    not_available = single_product.stock <= 0
    context = {
        'single_product':single_product,
        'not_available':not_available,
    }
    return render(request, 'store/product_detail.html', context)
