from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

from store.models import Product, Variation
from .models import Cart, CartItem


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    current_user = request.user

    # check if current user is authenticated
    if current_user.is_authenticated:
        product_variations = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST.get(key)

                try:
                    variation = Variation.objects.get(
                        product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass


        is_cart_item_exist = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exist:
            cart_item = CartItem.objects.filter(product=product, user=current_user)

            ex_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_variation_list.append(list(existing_variation))
                id.append(item.id)

            if product_variations in ex_variation_list:
                index = ex_variation_list.index(product_variations)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product,
                    user=current_user,
                    quantity=1
                )
                if len(product_variations) > 0:
                    item.variation.clear()
                    item.variation.add(*product_variations)

                # cart_item.quantity += 1
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                user=current_user,
                quantity=1
            )

            if len(product_variations) > 0:
                cart_item.variation.add(*product_variations)
            cart_item.save()
        return redirect('cart')
    else:
        product_variations = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST.get(key)

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) # the the cart using the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exist = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exist:
            cart_item = CartItem.objects.filter(product=product, cart=cart)

            ex_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_variation_list.append(list(existing_variation))
                id.append(item.id)

            print(ex_variation_list)

            if product_variations in ex_variation_list:
                index = ex_variation_list.index(product_variations)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                product=product,
                cart=cart,
                quantity=1
                    )
                if len(product_variations) > 0:
                    item.variation.clear()
                    item.variation.add(*product_variations)

                # cart_item.quantity += 1
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                cart=cart,
                quantity=1
            )

            if len(product_variations) > 0:
                cart_item.variation.add(*product_variations)
            cart_item.save()
        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax = None
    grand_total = None
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
        'tax': tax,
        'grand_total':grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required()
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = None
    grand_total = None
    try:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)
