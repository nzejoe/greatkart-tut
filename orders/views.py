import datetime, json
from django.shortcuts import render, redirect

from carts.models import CartItem
from .forms import OrderForm

from .models import Order, OrderProduct, Payment

from store.models import Product

from django.http.response import JsonResponse


# ORDER EMAIL
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage



def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, order_number=body.get('orderID'), is_ordered=False)

    payment = Payment(
        user=request.user,
        payment_id=body.get('transID'),
        payment_method=body.get('payment_method'),
        amount_paid=order.order_total,
        status=body.get('status'),
    )

    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()
    
    # move the cart item to order product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        # reduce the quantity of the sold product
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Delete cart item on successful transaction
    CartItem.objects.filter(user=request.user).delete()

    # send order received email to customer
    email_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_received_email.html',{
        'user': request.user,
        'order':order
    })

    to_email = request.user.email
    send_email = EmailMessage(email_subject, message, to=[to_email,])
    send_email.send()

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }

    return JsonResponse(data)

def place_order(request, tax=0, total=0):

    current_user = request.user

    # check if user has item in cart, if not redirect
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    quantity = 0
    for item in cart_items:
        total += (item.product.price * item.quantity)
        quantity += item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data.get('first_name')
            data.last_name = form.cleaned_data.get('last_name')
            data.email = form.cleaned_data.get('email')
            data.phone = form.cleaned_data.get('phone')
            data.address_line_1 = form.cleaned_data.get('address_line_1')
            data.address_line_2 = form.cleaned_data.get('address_line_2')
            data.country = form.cleaned_data.get('country')
            data.state = form.cleaned_data.get('state')
            data.city = form.cleaned_data.get('city')
            data.order_note = form.cleaned_data.get('order_note')
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(id=data.id)

            context = {
                'order': order,
                'cart_items':cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total
            }

            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')
    
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        tax = 0
        for product in order_products:
            subtotal += (product.product_price * product.quantity)

        payment = Payment.objects.get(payment_id=transID)
        
        tax = (2 * subtotal) / 100
        grand_total = subtotal + tax
        context = {
            'order': order,
            'order_products':order_products,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'tax': tax,
            'grand_total': grand_total,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

