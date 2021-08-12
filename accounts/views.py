from django.shortcuts import redirect, render
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# VERIFICATION EMAIL
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import  urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from .forms import RegistrationForm
from .models import Account


# import from cart
from carts.models import Cart, CartItem
from carts.views import _cart_id

import requests

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name = first_name,
                last_name = last_name,
                email = email,
                username = username,
                password = password
            )
            user.phone_number = phone_number
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            email_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.id)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(email_subject, message, to=[to_email,])
            send_email.send()

            # messages.success(request, 'Thank you for your registration! We have sent you a verification email. Kindly check your emmail.')
            return redirect(f'/accounts/login/?command=verification&email={email}')
    else:
        form = RegistrationForm()
    context = {
        'form':form
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    # redirect user if logged in already
    # if request.user.is_authenticated:
    #     return redirect('home')
    # else:
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        strg = 'hello-world'
        # print('params:-----> ' + strg.split())
        user = auth.authenticate(email=email, password=password)
        if user is not None:

            # transfer cart to logged in user
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)

                    # get product variations
                    product_variations = []
                    for item in cart_items:
                        variations = item.variation.all()
                        product_variations.append(list(variations))

                    # get cart items by user to access product variations
                    cart_items = CartItem.objects.filter(user=user)
                    ex_variation_list = []
                    id = []
                    for item in cart_items:
                        existing_variation = item.variation.all()
                        ex_variation_list.append(list(existing_variation))
                        id.append(item.id) 
                    
                    for product_v in product_variations:
                        if product_v in ex_variation_list:
                            index = ex_variation_list.index(product_v)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.user = user
                            item.quantity += 1
                            item.save()
                        else:
                            cart_items = CartItem.objects.filter(cart=cart)
                            for item in cart_items:
                                item.user = user
                                item.save()
            except:
                pass

            auth.login(request,user)
            messages.success(request, 'You are now logged in')
            url = request.META.get('HTTP_REFERER')

            try:
                query = requests.utils.urlparse(url).query
                print('Query:-----> '+query)
                print('---------------')
                
               
                if 'next' in query:
                    return redirect('checkout')
            except:
                return redirect('dashboard')
        else:
            messages.error(request,'Email or Password is incorrect')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


def activate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(id=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account has been activated.')
        return redirect('login')
    else:
        messages.error(request, 'invalid activation link')
    return redirect('register')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def forgotPassword(request):

    if request.method == 'POST':
        email = request.POST.get('email')

        if Account.objects.filter(email__exact=email).exists():
            user = Account.objects.get(email=email)

            # account reset
            current_site = get_current_site(request)
            email_subject = 'Reset password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.id)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(email_subject, message, to=[to_email, ])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('login')
            
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def reset_password_validate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(id=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'please reset you password')
        return redirect('reset_password')
    else:
        messages.error(request, 'Reset link has expired')
        return redirect('forgotPassword')


def reset_password(request):

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(id=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Your password was changed successfully')
            return redirect('login')
        else:
            messages.error(request, 'The two password did not match!')
            return redirect('reset_password')
    return render(request, 'accounts/reset_password.html')
