from select import select
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings as conf_settings
from django.core.paginator import Paginator

# THIS IS USED TO RENDER OUT TEMPLATE AND SEND IT AS A STRING TO THE BODY OF THE EMAIL
from django.template.loader import render_to_string 
# Create your views here.
from .forms import CreateUserForm, CustomerProfileFormSetup, UpdateCustomerAddress, UpdateTraderStoreAddress, UpdateProduct, ActivePtd, UpdateShippingAddress, SlideImage, VideoUrl, SaveCustomerAddress
from .models import Customer, Store, ProductReview, Comment, Product, Category, Brand, WishList, Order, OrderItem, CustomerAddress, ShippingAddress, Slide_image, Video_item, Payment, RecentViewItems
from .filters import ProductOverView
from time import gmtime, strftime
import datetime
from django.db.models import Q
from .decorators import unauthenticated_user, allowed_users, t_allowed_users
from eShopperAmuwo.utils import cartData

import re # USE TO VALIDATE URL LINK
import os
# PDF IMPORTS:
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import timedelta
# ================ END PDF IMPORTS ===================================

from . utils import authGetHomepageData, productRecord, updateCartItem, generalRequest, editCusOrder, categoryData, sideCategoryList





def homePage(request):
    _data = cartData(request)
    cartItems = _data['cartItems']
    cat_id = _data['cat_id']
    generalData = generalRequest(request)
    if request.user.is_authenticated:
        data = authGetHomepageData(request)
        if request.method == 'POST':
            call = json.loads(request.body)
            if call == 'recentViewItem':
                print(call)
                # REDIRECT TO TEMPLATE WHERE YOU VIEW ALL ITEMS
                return JsonResponse('redirect_to_recent_view_item', safe=False)
            
                
    else:
        data = {'recentViewItems': '', 'watchedItems': '', 'recentViewList': '', 'watchItemList': ''}
        
    context = {'recentViewItems': data['recentViewItems'], 'watchedItems': data['watchedItems'],
    'recentViewList': data['recentViewList'], 'watchItemList': data['watchItemList'], 'cartItems':cartItems,
    'dailyDeals': generalData['dailyDeals'], 'categoryDropdownList': _data['categoryList'],
    'dailyCats': generalData['dailyCat'], 'dailyBrands': generalData['dailyBrands'], 'cat_id': cat_id
    }
    return render(request, 'homePage/homepage.html', context)


def allCategory(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    categories = Category.objects.all()
    if request.method == 'POST':
        jsondata = json.loads(request.body)
        if jsondata:
            catId = jsondata['categoryId']
            return JsonResponse('success', safe=False)
    else:
        catData = categoryData(request, pk)
        if catData['cat_title'].level > 1:
            return redirect('category_items', pk)
        context = {'categories': categories, 'cartItems':cartItems, 'categoryDropdownList': data['categoryList'],
            'titleCategory': catData['cat_title'], 'categoryListRecord': catData['categoryListRecord']
        }
        return render(request, 'allCategoryItem/all_categories.html', context)


def categoryItems(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    catData = sideCategoryList(request, pk)
    context = {'cartItems':cartItems, 'categoryDropdownList': data['categoryList'], 'categoryName': catData['categoryName'],
    'childrenCatList': catData['childrenCatList'], 'categoryProducts': catData['categoryProducts'], 
    'parentCategory': catData['parentCategory'], 'counter': catData['counter'], 'brands': catData['brands'],
    'isFilterBrandVisted': catData['isFilterBrandVisted'], 'selectBrandList': catData['selectBrandList'],
    'selectBrndCount': catData['selectBrndCount']}

    return render(request, 'allCategoryItem/category_item.html', context)


def shopByBrand(request):
    brandList = []
    selBrndName = ''
    wishLists = ''
    data = cartData(request)
    cartItems = data['cartItems']
    allBrands = Brand.objects.all()
    # FILTER PRODUCT BASED ON BRAND NAME 
    brandId = request.GET.get('shopByBrand')
    brandPtdItems = Product.objects.filter(brand= brandId, active=True, store__active__contains=1)
    count = brandPtdItems.count()
    # THIS IS DONE JUST TO DISPLAY THE NAME OF THE PRODUCT AT THE TOP OF THE PAGE
    for brnd in brandPtdItems:  
        selBrndName = brnd.brand.brand
        break
    # THIS IS DONE IN CASE OF GUEST USER THAT DOES NOT HAVE WISHLIST
    if request.user.is_authenticated:
        wishLists = WishList.objects.filter(customer_id=request.user.customer.id)
    # WE USED THIS TO SORT OUT THE BRAND NAME THAT WAS SELECTED
    # SINCE WE DON'T WANT THE SELECTED BRAND TO DISPLAY ON THE SIDE OF THE PAGE
    for bran in allBrands:
        if bran.id != int (brandId):
            brandRecd = {
                'id': bran.id,
                'brand': bran.brand
            }
            brandList.append(brandRecd)
    # FUNCTION CALL IS USED TO CUSTOMIZE PTD RECORD BY ADDING FAVORITE TO IT
    brandPtdItems = productRecord(request, brandPtdItems, wishLists)

    paginator_filtered_product = Paginator(brandPtdItems, 15)
    page_number = request.GET.get('page')
    brandPtdItems = paginator_filtered_product.get_page(page_number)

    context = {'brandPtdItems': brandPtdItems, 'count': count, 'cartItems': cartItems, 
    'categoryDropdownList': data['categoryList'], 'brandList': brandList, 'selBrndName': selBrndName}

    return render(request, 'homePage/shop_by_brands.html', context)


@unauthenticated_user
def allRecentView(request):
    data = cartData(request)
    cartItems = data['cartItems']
    if request.method == 'POST':
        fontendData = json.loads(request.body)
        if fontendData['call'] == 'deleteAll':
            recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer).delete()
            return JsonResponse('success', safe=False)
    recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer)
    
    myFilter = ProductOverView(request.GET, queryset=recentViewItems)
    recentViewItems = myFilter.qs

    paginator_filtered_product = Paginator(recentViewItems, 15)
    page_number = request.GET.get('page')
    recentViewItems = paginator_filtered_product.get_page(page_number)

    counter = RecentViewItems.objects.filter(customer= request.user.customer).count()
    
    context = {'recentViewItems': recentViewItems, 'counter': counter, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList']}
    return render(request, 'homePage/all_recent_view.html', context)


@unauthenticated_user
def allSellerItems(request, pk):

    data = cartData(request)
    cartItems = data['cartItems']

    oneStoreItems = Product.objects.filter(store_id= pk, active=True, store__active__contains=1)
    count = oneStoreItems.count()
    wishLists = WishList.objects.filter(customer_id=request.user.customer.id)

    # FUNCTION CALL IS USED TO CUSTOMIZE PTD RECORD BY ADDING FAVORITE TO IT
    oneStoreItems = productRecord(request, oneStoreItems, wishLists)

    paginator_filtered_product = Paginator(oneStoreItems, 15)
    page_number = request.GET.get('page')
    oneStoreItems = paginator_filtered_product.get_page(page_number)
   
    context = {'oneStoreItems': oneStoreItems, 'count': count, 'cartItems': cartItems, 
    'categoryDropdownList': data['categoryList']}
    return render(request, 'homePage/all_seller_items.html', context)


@unauthenticated_user
def updateFavorite(request):
    data = json.loads(request.body)
    productId = data['ptdId']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    
    if action == 'fillHeart':
        isWshList, created = WishList.objects.get_or_create(product=product, customer=request.user.customer, store_id=product.store.id)
        
    elif action == 'heart':
        WishList.objects.filter(product=product.id, customer= customer).delete()

    return JsonResponse('Item was added', safe=False)


def loginPage(request):
    myDictionary = {}
    if request.method == 'POST':
        try:
            email = request.POST.get('email').strip().lower()
            password = request.POST.get('password')
            username = User.objects.get(email=email)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('homePage')
            else:
                myDictionary['is_error'] = True
                myDictionary['error_message'] = 'Username or password is incorrect'
        except Exception as e:
            myDictionary['is_error'] = True
            myDictionary['error_message'] = e.args[0]
    else:
        # IF A ACTIVE USER TRY TO MANIPULATE 'IF STATEMENT' ON THE HTML BY DISABLING THE LOGIN BUTTON,
        # THIS ELSE STATEMENT WILL RE-DIRECT THEM TO HOME PAGE
        isAuthenticated = False
        isAuthenticated = request.user.is_authenticated
        if isAuthenticated:
            return redirect('homePage')
    context = {'myDictionary': myDictionary}
    return render(request, 'accounts/login.html', context)


@unauthenticated_user
def logoutUser(request):
    logout(request)
    return redirect('homePage')


def register(request):

    form = ''
    myDictionary = []
    if request.method == 'POST':
        isExist = User.objects.filter(email=request.POST.get('email')).exists()
        if not isExist:
           
            form = CreateUserForm(request.POST)
            print('NAME:', form.data['username'])
            if form.is_valid():
                user = form.save()
                print('USER:', user)
                user_info = User.objects.filter(username=user.username)
                for user_record in user_info:
                    userData = {
                        'user': user_record.id,
                        'name': user.username,
                        'email': user.email,
                    }
                customer_profile = CustomerProfileFormSetup(data=userData)
                if customer_profile.is_valid():
                    profile = customer_profile.save()
                    print('CUSTOMER PROFILE SAVED')

                    user = form.cleaned_data.get('username')
                    messages.success(request, 'Account was created for ' + user)
                    return redirect('login')
            else:
                err_msg = form.error_messages['password_mismatch']
                myDictionary['is_error'] = True
                myDictionary['error_message'] = err_msg
        else:
            myDictionary['is_error'] = True
            myDictionary['error_message'] = 'Email already exist'
    context = {'form': form, 'myDictionary': myDictionary}
    return render(request, 'accounts/register.html', context)


@unauthenticated_user
def updateCustomerAddress(request, pk):
    myDictionary = {}
    cus_addresses = ''

    data = cartData(request)
    cartItems = data['cartItems']
  
    customer_info = Customer.objects.get(user=request.user.id)
    
    if request.method == 'POST':
        if request.POST.get('saveAddress') == 'Save':
            # WE WANT TO LIMIT THE NUMBER OF ADDRESS A USER CAN SAVE TO 5
            cus_addresses = CustomerAddress.objects.filter(customer=customer_info, address_type='Shipping Address')
            if (len(cus_addresses)) < 3:

                cusShipData = {
                    'customer': customer_info.id,
                    'address_type': request.POST.get('address_type'),
                    'name': request.POST.get('name'),
                    'address': request.POST.get('address'),
                    'city': request.POST.get('city'),
                    'state': request.POST.get('state'),
                    'zipcode': request.POST.get('zipcode'),
                    'mobile': request.POST.get('mobile'),
                    'altMobile': request.POST.get('altMobile')
                }
                customer_address_info = SaveCustomerAddress(data= cusShipData)
                if customer_address_info.is_valid():
                    customer_address_info.save()
                    isSuccess = True
                    # IF THIS IS THE FIRST SHIPPING ADDRESS THE CUSTOMER IS 
                    # SAVING, SET IT AS DEFAULT SHIPPING ADDRESS
                    cusAdd = CustomerAddress.objects.filter(customer=customer_info, address_type='Shipping Address')
                    if len(cusAdd) == 1:
                        for cusAd in cusAdd:
                            cusAd.default = True
                            cusAd.save()
                    return redirect('addressOverview', isSuccess)
                else:
                    myDictionary['error'] = True
                    myDictionary['errorMessage'] = customer_address_info.errors
            else:
                isSuccess = 'too much address to add'
                return redirect('addressOverview', isSuccess)
        elif request.POST.get('updateAddress') == 'Update':
            cus_addresses = CustomerAddress.objects.get(id=pk)
            customer_address_info = SaveCustomerAddress(request.POST, instance=cus_addresses)
            if customer_address_info.is_valid():
                customer_address_info.save()
                isSuccess = True
                return redirect('addressOverview', isSuccess)
            else:
                myDictionary['error'] = True
                myDictionary['errorMessage'] = customer_address_info.errors
                myDictionary['updateShippingAddressForm'] = True
                cus_addresses = {
                    'customer': customer_info.id,
                    'address_type': request.POST.get('address_type'),
                    'name': request.POST.get('name'),
                    'address': request.POST.get('address'),
                    'city': request.POST.get('city'),
                    'state': request.POST.get('state'),
                    'zipcode': request.POST.get('zipcode'),
                    'mobile': request.POST.get('mobile'),
                    'altMobile': request.POST.get('altMobile')
                }
                
        elif request.POST.get('cancelAddress') == 'Cancel':
            return redirect('addressOverview', 'cancel')

        elif request.POST.get('cancelUpdateAddress') == 'Cancel':
            return redirect('addressOverview', 'cancel')

    elif request.method == 'GET':
        # GET THE SHIPPING INFO AND RENDER THEM ON THE TEMPLATE
        if pk != '0':   # USING THIS CONDITION TO DIFFERENTIATE 'ADD ANOTHER ADDRESS' & 'EDIT PEN' LINK CLICKED
            cus_addresses = CustomerAddress.objects.get(id=pk)
            myDictionary['updateShippingAddressForm'] = True
            context = {'form': cus_addresses, 'myDictionary': myDictionary, 'cartItems': cartItems}
            return render(request, 'accounts/settings/address.html', context)
    context = {'form': cus_addresses, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/settings/address.html', context)


@unauthenticated_user
def cusAcctCardForm(request):
    data = cartData(request)
    cartItems = data['cartItems']
    # if request.user.is_authenticated:
    #     pass
    # else:
    #     return redirect("login")
    context = {'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/acct_card_form.html', context)


@unauthenticated_user
# @t_allowed_users(allowed_roles = ['Trader group', 'Admin group'])
def traderStore(request, pk):
    store_data = ''
    counter = 0
    t_stores = ''
    myDictionary = {}
    isSuccess = False
    isUpdated = False
    isExistingStore = False
    trader_store_address = None
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myStore' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
    
    try:
        data = cartData(request)
        cartItems = data['cartItems']

        user = User.objects.get(id=pk)
        # IT'S POSSIBLE FOR A TRADER TO HAVE MORE THAN ONE STORE.
        # GET ALL DATA FROM STORE, LOOP THOURGH USING THE USER ID TO SEE IF IT'S NONE, ONE OR MORE
        store_record = Store.objects.all()
        active = request.POST.get("active")

        for store in store_record:
            if store.user_id.id == user.id:
                counter += 1
    
        if counter == 1 and request.GET.get('add_store') != 'Add Store':
            store_data = Store.objects.get(user_id=user.id)
        if request.method == "GET" and counter > 0:
            if request.GET.get("add_store"):
                print("Add store")
                store_data = ''
                counter = 0
                # ========= CHECK IF USER IS AN ADMIN STAFF. IF NOT DISPLAY AN ALERT MESSAGE =========
                # if not request.user.is_superuser:
                #     myDictionary["warning"] = True
                #     myDictionary["warning_msg"] = "Only Admin can add a new store"
                
            elif request.GET.get("store_udate"):
                if counter > 1:
                    t_stores = Store.objects.filter(user_id=user.id)
                    accept = request.GET.get("store_udate")
                    if accept == "Continue":
                        selected = request.GET['selected']
                        print(selected)
                        
                        t_stores = ''
                        counter = -1
                        # CHECKING IF THE USER FAIL TO SELECT STORE FROM COMBO BOX
                        if selected == '':
                            # HERE, I NEED TO TRIGGER AN ALERT TO TELL THE USER THAT AN INVALID SELECTION WAS MADE
                            pass
                        else:
                            store_data = Store.objects.get(store_name=selected)
                        
                        print('filter record from db:', store_data)
                else:
                    store_data = Store.objects.get(user_id=user.id)
                    counter = -1
                print("update store")
        # EXCUTE THIS CODE IF IT IS THE FIRST TIME OF ADDING STORE AND IF USER IS NOT SUPER USER
        # elif request.method == "GET" and counter == 0 and not request.user.is_superuser:
        #     myDictionary["warning"] = True
        #     myDictionary["warning_msg"] = "Only Admin can add a new store"
        # CONTACT ADMIN TO VERIFY YOUR STORE. THIS WILL EARN YOU BUYER'S TRUST WORTHINESS IN THE MARKET PLACE

        if request.method == 'POST':
            user_data = {
                'user_id': user.id,
                'store_name': request.POST.get('store_name'),
                'store_address': request.POST.get('store_address'),
                'city': request.POST.get('city'),
                'LGA': request.POST.get('LGA'),
                'state': request.POST.get('state'),
                'email': request.POST.get('email'),
                'mobile': request.POST.get('mobile'),
                'altMobile': request.POST.get('altMobile'),
                'active': (True if active == 'on' else False),
            }
            if counter > 0 and request.GET.get('store_udate') == "Update Store" or request.GET.get('store_udate') == "Continue":
                # WHEN COUNTER IS GREATER THAN ONE GET THE INSTANCE OF STORE BASE ON WHAT THE TRADER SELECTED
                if (request.GET.get('store_udate') == 'Continue' and request.POST.get('id')) or (request.GET.get('store_udate') == 'Update Store' and request.POST.get('id')):
                    store_data = Store.objects.get(id=request.POST.get('id'))
                    # UPDATE THE EXISTING RECORD
                    trader_store_address = UpdateTraderStoreAddress(data=user_data, instance=store_data)
                    counter = -1
                    isUpdated = True
            elif request.GET.get('add_store') == 'Add Store':
                # CHECK IF THE STORE NAME ALREADY EXIST IN DB BEFORE SAVING TO DATABASE
                existing_store_name = Store.objects.filter(store_name=request.POST.get('store_name'))
                if existing_store_name:
                    isExistingStore = True

                # CREATE A NEW STORE RECORD
            
                trader_store_address = UpdateTraderStoreAddress(data=user_data)
                counter = -1
                isSuccess = True
            elif request.method == 'POST':
                
                # CREATING A NEW RECORD FOR THE FIRST TIME
                trader_store_address = UpdateTraderStoreAddress(data=user_data)
                isSuccess = True
            if trader_store_address:
                if trader_store_address.is_valid(): 
                    # if not request.user.is_superuser and isUpdated == False:
                    #     myDictionary["warning"] = True
                    #     myDictionary["warning_msg"] = "Store was not saved. Only Admin can add a new store"
                    if isExistingStore:
                        store_data = {
                        'user_id': user.id,
                        'store_name': '',
                        'store_address': request.POST.get('store_address'),
                        'city': request.POST.get('city'),
                        'LGA': request.POST.get('LGA'),
                        'state': request.POST.get('state'),
                        'email': request.POST.get('email'),
                        'mobile': request.POST.get('mobile'),
                        'altMobile': request.POST.get('altMobile'),
                        'active': (True if active == 'on' else False),
                    }
                        myDictionary["warning"] = True
                        myDictionary["warning_msg"] = "Store was not saved. Store name already exist in the database"
                    else:
                        print("valid to save")
                        trader_store_address.save()
                        if isSuccess == True:
                            myDictionary["success"] = True
                            myDictionary["successmsg"] = "Form Submitted"
                        elif isUpdated == True:
                            myDictionary["success"] = True
                            myDictionary["successmsg"] = "Form updated successful"
                else:
                    store_data = {
                    'user_id': user.id,
                    'store_name': request.POST.get('store_name'),
                    'store_address': request.POST.get('store_address'),
                    'city': request.POST.get('city'),
                    'LGA': request.POST.get('LGA'),
                    'state': request.POST.get('state'),
                    'email': request.POST.get('email'),
                    'mobile': request.POST.get('mobile'),
                    'altMobile': request.POST.get('altMobile'),
                    'active': (True if active == 'on' else False),
                }
                    myDictionary["warning"] = True
                    myDictionary["warning_msg"] = trader_store_address.errors
    except Exception as e:
        myDictionary["warning"] = True
        myDictionary["warning_msg"] = e.args
    context = {'form': store_data, 't_stores': t_stores, 'counter': counter, 'myDictionary':myDictionary, 
    'cartItems': cartItems, 'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu,
    'selectedMenu': selectedMenu}
    return render(request, 'accounts/store.html', context)


@unauthenticated_user
def loginAndSecuritySetting(request):
    data = cartData(request)
    cartItems = data['cartItems']
   
    context = {'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/login_security.html', context)


@unauthenticated_user
def changePassword(request):
    data = cartData(request)
    cartItems = data['cartItems']

    myDictionary = {}
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Otherwise the user’s auth session will be invalidated and she/he will have to log in again.
            myDictionary["success"] = True
            myDictionary["successmsg"] = "Your password was successfully updated!"
        elif request.POST.get('cancel_btn') == 'Cancel':
            return redirect('login_Security')
        else:
            myDictionary['error'] = True
            myDictionary['errorMessage'] = form.error_messages
            myDictionary['errorMessage2'] = "New password must contain at least 8 characters. Both numeric and alphabet"
    else:
        form = PasswordChangeForm(user=request.user)
    context = {'form': form, 'myDictionary': myDictionary, 'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/change_password.html', context)


@unauthenticated_user
def pendingReview(request):
    data = cartData(request)
    cartItems = data['cartItems']

    pendingReviews = ProductReview.objects.filter(cus_name=request.user)
    myDictionary = {}
    pendingReviewObject = []
    counter = 0
    for pendingReview in pendingReviews:
        counter += 1
        pendingReviewObj = {
            'id': pendingReview.id,
            'ptd_review_id': pendingReview.ptd_review_id,
            'ptd_id': pendingReview.ptd_id,
            'counter': counter,
            'transaction_id': pendingReview.transaction_id,
            'cus_name': pendingReview.cus_name,
            'order_date': pendingReview.order_date,
        }
        pendingReviewObject.append(pendingReviewObj)
    # CHECKING IF THERE ARE PENDING REVIEWS
    myDictionary['isPendingReview'] = False
    if pendingReviews:
        myDictionary['isPendingReview'] = True
    context = {'pendingReviews': pendingReviewObject, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/pending_reviews.html', context)


@unauthenticated_user
def writePtdReview(request, pk, t_id):
    data = cartData(request)
    cartItems = data['cartItems']
    firstOnList = ''
    # THIS FILTER IS USED TO SELECT ALL PENDING REVIEWS PRODUCTS
    pendingReviews = ProductReview.objects.filter(ptd_review_id=pk, transaction_id=t_id)
    
    # THIS IS JUST LIKE THE PARENT UPON WHICH THE 'PENDINGREVIEWS' CHILDEREN ARE UNDER
   
    pending_Reviews = ProductReview.objects.get(id=pk)
    
    if not pendingReviews:
        pendingReviews = ProductReview.objects.filter(ptd_review_id=t_id)
    myDictionary = {}

    # IF THE FIRST PENDING_REVIEWS ARE EMPTY, MOST LIKELY IT WAS A REQUEST FROM ITEM LIST
    # FROM WRITE A REVIEW PAGE. QUERY THE TABLE USING 'GET' TO PULL THE RECORD REQUESTED BY THE USER
    # FIRST CHECK IF 'PENDING_REVIEWS' ARE EMPTY
    if pendingReviews:
        for pendingReview in pendingReviews:
            firstOnList = {
                'ptd_review_id': pendingReview.ptd_review_id,
                'order_date': pendingReview.order_date,
                'product_name': pendingReview.product_name,
                'product_image': pendingReview.product_image,
                'ptd_id': pendingReview.ptd_id,
                'id': pendingReview.id,
                'trans_id': pendingReview.transaction_id,
            }
            break
    if pending_Reviews.ptd_id:
            
        firstOnList = {
            'ptd_review_id': pending_Reviews.ptd_review_id,
            'order_date': pending_Reviews.order_date,
            'product_name': pending_Reviews.product_name,
            'product_image': pending_Reviews.product_image,
            'ptd_id': pending_Reviews.ptd_id,
            'id': pending_Reviews.id,
            'trans_id': pending_Reviews.transaction_id,
        }

    if request.method == 'POST':
        if request.POST.get('submit_comment') == 'Submit':
            pendingReview = ProductReview.objects.get(id=request.POST.get('productReview_id'))
            product = Product.objects.get(id=request.POST.get('ptd_id'))
            
            Comment.objects.create(
            product = product,
            customer = request.user.customer,
            subject = request.POST.get('subject'),
            comment = request.POST.get('comment'),
            rate = request.POST.get('rating'),
            )
            pendingReview.delete()

            myDictionary["success"] = True
            myDictionary['success_msg'] = 'Successful'
            pendingReviews = ProductReview.objects.filter(ptd_review_id=request.POST.get('ptd_review_id'), transaction_id=request.POST.get('trans_id'))

            if pendingReviews:
                for pendingReview in pendingReviews:
                    firstOnList = {
                        'ptd_review_id': pendingReview.ptd_review_id,
                        'order_date': pendingReview.order_date,
                        'product_name': pendingReview.product_name,
                        'product_image': pendingReview.product_image,
                        'ptd_id': pendingReview.ptd_id,
                        'id': pendingReview.id,
                        'trans_id': pendingReview.transaction_id,
                    }
                    break
            else:
                pendingList = ProductReview.objects.get(id=pk)
                pendingList.delete()
                return redirect('pending_review')
                
            
        elif request.POST.get('cancel_comment') == 'Cancel':
            return redirect('pending_review')   
        
    context = {'pendingReviews': pendingReviews, 'firstOnList': firstOnList, 'myDictionary': myDictionary, 
    'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/write_ptd_review.html', context)


@unauthenticated_user
def myOrder(request):
    data = cartData(request)
    cartItems = data['cartItems']
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myOrder' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
    jsonData = ''

    # myOrders = Order.objects.filter(customer__name=request.user.customer.name, transaction_id__isnull= False).order_by('-date_order')
    # FILTER RECORD BASED ON ORDER STATUS AND CUSTOMER NAME
    myOrders = Order.objects.filter((Q(status='Processing') | Q(status='On hold') | Q(status='Shipped')), customer__name=request.user.customer.name).order_by('-date_order')
    counter = 0
    myOrderData = []
    myDictionary = {}
    if request.method == 'POST':
        if request.POST.get('action_comboBox_selected') == 'complete':
            myOrders = Order.objects.filter (status='Completed', customer__name=request.user.customer.name).order_by('-date_order')

        elif request.POST.get('action_comboBox_selected') == 'processing':
            myOrders = Order.objects.filter (status='Processing', customer__name=request.user.customer.name).order_by('-date_order')

        elif request.POST.get('action_comboBox_selected') == 'on_hold':
            myOrders = Order.objects.filter (status='On hold', customer__name=request.user.customer.name).order_by('-date_order')

        elif request.POST.get('action_comboBox_selected') == 'shipped':
            myOrders = Order.objects.filter (status='Shipped', customer__name=request.user.customer.name).order_by('-date_order')
           
        elif request.POST.get('action_comboBox_selected') == 'cancelled':
            myOrders = Order.objects.filter (status='Cancelled', customer__name=request.user.customer.name).order_by('-date_order')
           
        elif request.POST.get('action_comboBox_selected') == 'refunded':
            myOrders = Order.objects.filter (status='Refunded', customer__name=request.user.customer.name).order_by('-date_order')
            
        elif request.POST.get('action_comboBox_selected') == 'rejected':
            myOrders = Order.objects.filter (status='Rejected', customer__name=request.user.customer.name).order_by('-date_order')
           
        elif request.POST.get('action_comboBox_selected') == 'failed':
            myOrders = Order.objects.filter (status='Failed', customer__name=request.user.customer.name).order_by('-date_order')
        
        if request.POST.get('search_btn') == 'Search':
            order_no = request.POST['order_no']
            if order_no:
                myOrders = Order.objects.filter (customer__name=request.user.customer.name, transaction_id__contains=order_no)

    for _myOrder in myOrders:
        counter += 1
        myOrderItms = _myOrder.orderitem_set.all()
        total = 0
        for myOrderItm in myOrderItms:
            total += myOrderItm.line_total
        my_order = {
            'transaction_id': _myOrder.transaction_id,
            'customer_name': _myOrder.customer.name,
            'date_order': customTimeFormat(_myOrder.date_order),
            'complete': _myOrder.complete,
            'paid': _myOrder.paid,
            'line_total': float (total),
            'status': _myOrder.status,
        }
        myOrderData.append(my_order)
    jsonData = json.dumps (myOrderData)
    myDictionary['counter'] = counter
    context = {'myOrderData': myOrderData, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu, 'selectedMenu': selectedMenu,
    'jsonData': jsonData}
    return render(request, 'accounts/my_order_list.html', context)

def customTimeFormat(dateTime):
    customDateTime = dateTime + timedelta(hours=1)
    customDateTime = customDateTime.strftime("%d, %b, %Y, %I:%M%p")

    return customDateTime

@unauthenticated_user
def cus_update_myOrder(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    order = Order.objects.get(transaction_id=pk)
    orderItems = order.orderitem_set.all()
    grandTotal = 0
    shipping_address = ''
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myOrder' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
    for orderItem in orderItems:
        grandTotal += orderItem.line_total
    shipping_address = ShippingAddress.objects.get(order__transaction_id=pk)
    orderData = []
    myDictionary = {}
    # CONFIRM IF CUSTOMER IS A REGISTERED USER
    if order.customer.user:
        user = User.objects.get(id=order.customer.user.id)
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': order.date_order,
            'complete': order.complete,
            'address': shipping_address.address,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'mobile': shipping_address.mobile,
            'altMobile': shipping_address.altMobile,
            'optional_note': shipping_address.optional_note,
            'user_name': user.username,
            'user_email': user.email,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'payment_option': order.payment_option,
            'paid': order.paid,
            'status': order.status,
            'private_note': order.order_private_note,
        }
    else:
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': order.date_order,
            'complete': order.complete,
            'address': shipping_address.address,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'mobile': shipping_address.mobile,
            'altMobile': shipping_address.altMobile,
            'optional_note': shipping_address.optional_note,
            'user_name': order.customer.name,
            'user_email': order.customer.email,
            'payment_option': order.payment_option,
            'paid': order.paid,
            'status': order.status,
            'date_joined': '',
            'last_login': '',
            'private_note': order.order_private_note,
        }

    if request.method == 'POST':
        # REQUEST TO UPDATE CUSTOMER SHIPPING ADDRESS
        if request.POST.get('update_shipping_address') == 'Update Shipping':
            updateShippingAddress = UpdateShippingAddress(request.POST, instance=shipping_address)
            if updateShippingAddress.is_valid:
                updateShippingAddress.save()
                return redirect('cus_update_myOrder', pk)

    myDictionary['grandTotal'] = grandTotal
    
    context = {'order_obj': order_obj, 'orderItems': orderItems, 'myDictionary': myDictionary, 'order': order,
    'cartItems': cartItems, 'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu,
    'selectedMenu': selectedMenu}
    return render(request, 'accounts/cus_update_myOrder.html', context)


# REQUEST TO EDIT CUSTOMER ORDER AFTER SHOPPING ITEMS WAS SUBMITTED
# THIS INCLUDE THE SELECTED/UPDATE BUTTON, REDUCTION OR DELETE OF ITEMS LIST
@unauthenticated_user
def custEditOrder(request):
    data = editCusOrder(request)
    
    return JsonResponse({'serverMsg': data['serverMsg']}, safe=False)


@unauthenticated_user
# @t_allowed_users(allowed_roles = ['Trader group', 'Admin group'])
def productOverView(request):
    data = cartData(request)
    cartItems = data['cartItems']
    
    t_stores = Store.objects.filter(user_id=request.user.id)
    trader_stores = []
    ptd_list = []
    ptd_counter = 0
    myDictionary = {}
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myProduct' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
    

    # THIS BLOCK OF CODE IS USED TO DEACTIVATE/ACTIVATE SELECTED PRODUCT(S)
    if request.method == 'POST':
        if request.POST.get('continue') == 'Continue':
            if request.POST.get('action_comboBox_selected') == 'inactive':
                active_ptd = {
                    'active': (False)
                }
                if request.POST.get('check_box_action'):
                    selected_values = request.POST.getlist('check_box_action')
                    for pk in selected_values:
                        selected_ptd = Product.objects.get(id=pk)
                        # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                        active_ptd['active']
                        deactivate_ptd = ActivePtd(data=active_ptd, instance=selected_ptd)
                        if deactivate_ptd.is_valid:
                            deactivate_ptd.save()

                    myDictionary['warning_msg'] = 'Product successfully deactivated...!\nThis product(s) are no longer avalible online'
                    myDictionary['isWarning'] = True
                else:
                    myDictionary['warning_msg'] = 'Items must be selected in order to perform actions on them. No items have been changed.'
                    myDictionary['isWarning'] = True
            elif request.POST.get('check_box_action') and request.POST.get('action_comboBox_selected') == 'False':
                myDictionary['warning_msg'] = 'No action selected from the drop down!'
                myDictionary['isWarning'] = True
            # BLOCK OF CODE TO ENSURE PRODUCT STATUS IS ACTIVE
            elif request.POST.get('action_comboBox_selected') == 'active':
                active_ptd = {
                    'active': (True)
                }
                if request.POST.get('check_box_action'):
                    selected_values = request.POST.getlist('check_box_action')
                    for pk in selected_values:
                        selected_ptd = Product.objects.get(id=pk)
                        # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                        active_ptd['active']
                        activate_ptd = ActivePtd(data=active_ptd, instance=selected_ptd)
                        if activate_ptd.is_valid:
                            activate_ptd.save()
                    myDictionary['successmsg'] = 'Product successfully activated...!\nThis product(s) are avalible online'
                    myDictionary['ptd_saved'] = True
                else:
                    myDictionary['warning_msg'] = 'Items must be selected in order to perform actions on them. No items have been changed.'
                    myDictionary['isWarning'] = True
            elif request.POST.get('check_box_action') and request.POST.get('action_comboBox_selected') == 'False':
                myDictionary['warning_msg'] = 'No action selected from the drop down!'
                myDictionary['isWarning'] = True
            # elif request.POST.get('action_btn') == 'Go':
            #         myDictionary['warning_msg'] = 'No action selected.'
            #         myDictionary['isWarning'] = True

    for t_store in t_stores:
        trader_stores.append(t_store.id)
    if trader_stores:
        products = Product.objects.all().order_by('-id')
        if request.method == 'POST':
            if request.POST.get('continue') == 'Continue':
                searched = request.POST['search_value']
                products = Product.objects.filter(name__contains=searched).order_by('-id')
        for store_id in trader_stores:
            for trader_ptd in products:
                if trader_ptd.store_id == store_id:
                    ptd_dic = {
                        'id': trader_ptd.id,
                        'name': trader_ptd.name,
                        'description': trader_ptd.description,
                        'brand': trader_ptd.brand,
                        'price': trader_ptd.price,
                        'discount': trader_ptd.discount,
                        'mfgDate': trader_ptd.mfgDate,
                        'expDate': trader_ptd.expDate,
                        'store': trader_ptd.store,
                        'active':trader_ptd.active
                    }
                    ptd_list.append(ptd_dic)
                    ptd_counter += 1
    
    context = {'trader_ptds': ptd_list, 'ptd_counter': ptd_counter, 'myDictionary': myDictionary, 
    'cartItems': cartItems, 'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu,
    'selectedMenu': selectedMenu}
    return render(request, 'accounts/product_over_view.html', context)


@unauthenticated_user
# @t_allowed_users(allowed_roles = ['Trader group', 'Admin group'])
def addProduct(request):
    data = cartData(request)
    cartItems = data['cartItems']

    myDictionary = {}
    t_stores = Store.objects.filter(user_id=request.user.id) # I WANT TRADER TO ONLY SEE THEIR STORE(S)
    categories = Category.objects.all()
    firstLevelCategories = Category.objects.filter(level = 0)
    categories_ = json.dumps (list(categories.values()))
    ptdRecord = ''
    ptd_form = UpdateProduct()
    isImage = False
    active = request.POST.get("active")
    imgSliders = ''
    video_url = ''
    brands = Brand.objects.all()
    ptdCatId = ''
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myProduct' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE

    if request.method == 'POST':

        # saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))

        active_ptd = {
            'active': (True if active == 'on' else False),
        }
        
        # ADD A NEW PRODUCT
        if request.POST.get('save-btn') == 'Save':
            # CHECK IF THE PRODUCT NAME ALREADY EXIST IN DB BEFORE SAVING
            existing_ptd = Product.objects.filter(name=request.POST.get('name'), store=request.POST.get('store'))
            if existing_ptd:
                myDictionary['warningmsg'] = 'This product already exist in this store'
                myDictionary['warning'] = True
            else:
                # SAVE THE PRODUCT
                
                productForm = UpdateProduct(request.POST, request.FILES)
                if productForm.is_valid():
                    productForm.save()
                    # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                    if active_ptd['active'] == True:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                            
                            active_btn.save()
                    else:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                         
                            active_btn.save()

                    # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
                    slide_ptd_images = request.FILES.getlist('slide_ptd_image')
                    if slide_ptd_images:
                        for slide_ptd_image in slide_ptd_images:
                            Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)

                    
                    # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                    video_path = request.POST.get('video_url')
                    if video_path:
                        Video_item.objects.create(product=saved_ptd, video=video_path)
                    
                   
                    # AFTER SAVING, RETURN TO OVER VIEW AND DISPLAY THE TRADER'S PRODUCT(S)
                    t_stores = Store.objects.filter(user_id=request.user.id)
                    ptd_counter = 0
                    trader_stores = []
                    ptd_list = []
                    for t_store in t_stores:
                        trader_stores.append(t_store.id)
                    if trader_stores:
                        products = Product.objects.all().order_by('-id')
                        for store_id in trader_stores:
                            for trader_ptd in products:
                                if trader_ptd.store_id == store_id:
                                    ptd_dic = {
                                        'id': trader_ptd.id,
                                        'name': trader_ptd.name,
                                        'description': trader_ptd.description,
                                        'brand': trader_ptd.brand,
                                        'price': trader_ptd.price,
                                        'discount': trader_ptd.discount,
                                        'mfgDate': trader_ptd.mfgDate,
                                        'expDate': trader_ptd.expDate,
                                        'store': trader_ptd.store,
                                        'active':trader_ptd.active
                                    }
                                    ptd_list.append(ptd_dic)
                                    ptd_counter += 1

                    myDictionary['successmsg'] = 'Product save successful'
                    myDictionary['ptd_saved'] = True
                    context = {'trader_ptds': ptd_list, 'ptd_counter': ptd_counter, 'myDictionary': myDictionary}
                    return render(request, 'accounts/product_over_view.html', context)

        elif request.POST.get('save-add-another-btn') == 'Save and add another':
            # CHECK IF THE PRODUCT NAME ALREADY EXIST IN DB BEFORE SAVING
            existing_ptd = Product.objects.filter(name=request.POST.get('name'), store=request.POST.get('store'))
            if existing_ptd:
                myDictionary['warningmsg'] = 'This product already exist in this store'
                myDictionary['warning'] = True
            else:
                # SAVE THE PRODUCT AND LEAVE FORM BLANK TO SAVE ANOTHER RECORD
                productForm = UpdateProduct(request.POST, request.FILES)
                if productForm.is_valid():
                   
                    productForm.save()
                    # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                    if active_ptd['active'] == True:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                            
                            active_btn.save()
                    else:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                            
                            active_btn.save()
                    
                    # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
                    slide_ptd_images = request.FILES.getlist('slide_ptd_image')
                    if slide_ptd_images:
                        for slide_ptd_image in slide_ptd_images:
                            Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)


                    # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                    video_path = request.POST.get('video_url')
                    if video_path:
                        Video_item.objects.create(product=saved_ptd, video=video_path)
                    

                    myDictionary['successmsg'] = 'Product save successful'
                    myDictionary['ptd_saved'] = True

        elif request.POST.get('save-edit-btn') == 'Save and continue editing':

            # GET THE PRODUCT CATEGORY ID. IT IS USED ON THE TEMPLATE
            # TO DISPLAY THE PRODUCT CATEGORY AND SUB-CATEGORIES SELECTED.
            ptdCatId = request.POST['category']

            # CHECK IF THE PRODUCT NAME ALREADY EXIST IN DB BEFORE UPDATING
            existing_ptd = Product.objects.filter(name=request.POST.get('name'), store=request.POST.get('store'))
            if existing_ptd:
                existing_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                updatePtd = UpdateProduct(request.POST, request.FILES, instance=existing_ptd)
                # THIS BLOCK SAVES AN EXISTING PRODUCT UNDER SAVE AND CONTINUE BLOCK
                if updatePtd.is_valid():
                    
                    updatePtd.save()
                    # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                    if active_ptd['active'] == True:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                            
                            active_btn.save()
                    else:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                          
                            active_btn.save()
                    ptdRecord = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                    ptd_form = UpdateProduct(instance=ptdRecord)
                    # CHECKING IF IMAGE EXIST; TO ENSURE HTML TEMPLATE IS PROPERLY ARRANGE
                    if ptdRecord.image:
                        isImage = True 
                    
                    # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
                    slide_ptd_images = request.FILES.getlist('slide_ptd_image')
                    if slide_ptd_images:
                        for slide_ptd_image in slide_ptd_images:
                            Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)

                    # IF IMAGE SLIDE WERE SELECTED TO BE DELETED, PERFORM THE ACTION HERE...
                    checkedImageList = request.POST.getlist('slideImg_path')
                    if checkedImageList:
                        dbImageSliders = Slide_image.objects.filter(product=saved_ptd)
                        for dbImageSlider in dbImageSliders:
                            if dbImageSlider.image_slideURL in checkedImageList:
                                dbImageSlider.delete()

                    imgSliders = Slide_image.objects.filter(product=saved_ptd) # FILTER ALL THE PRODUCT FROM THE TABLE.
                    

                    # GET THE VIDEO DATA FROM IT'S TABLE AND UPDATE THE INSTANCE WITH THE NEW CHANGES
                    video_url = Video_item.objects.filter(product=saved_ptd)
                    if video_url:
                        video_url = Video_item.objects.get(product=saved_ptd)
                        newChanges = {'video': request.POST.get('video_url')}
                        video = VideoUrl(data=newChanges, instance=video_url)
                        if video.is_valid:
                            video.save()

                    video_url = saved_ptd.video_item_set.all() # GET THE VIDEO OBJECT

                    myDictionary['successmsg'] = 'Product update successful'
                    myDictionary['ptd_saved'] = True
            else:
                # SAVE THE NEW PRODUCT AND CONTINUE EDITING
                productForm = UpdateProduct(request.POST, request.FILES)

                if productForm.is_valid():
                 
                    productForm.save()
                    # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
                    if active_ptd['active'] == True:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                           
                            active_btn.save()
                    else:
                        saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                        active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                        if active_btn.is_valid:
                            
                            active_btn.save()
                    ptdRecord = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                    ptd_form = UpdateProduct(instance=ptdRecord)
                    # CHECKING IF IMAGE EXIST; TO ENSURE HTML TEMPLATE IS PROPERLY ARRANGE
                    if ptdRecord.image:
                        isImage = True
                    
                    # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
                    slide_ptd_images = request.FILES.getlist('slide_ptd_image')
                    if slide_ptd_images:
                        for slide_ptd_image in slide_ptd_images:
                            Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)
                    
                    imgSliders = Slide_image.objects.filter(product=saved_ptd) # FILTER ALL THE PRODUCT FROM THE TABLE.
                    
                    # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                    video_url = request.POST.get('video_url')
                    if video_url:
                        Video_item.objects.create(product=saved_ptd, video=video_url)

                    video_url = saved_ptd.video_item_set.all() # GET THE VIDEO OBJECT
                
                    myDictionary['successmsg'] = 'Product save successful'
                    myDictionary['ptd_saved'] = True
                
    myDictionary['t_stores'] = t_stores
    # myDictionary['categories'] = categories
    myDictionary['brands'] = brands
    myDictionary['isImage'] = isImage
    context = {'form': ptdRecord, 'myDictionary': myDictionary, 'ptd_form': ptd_form, 'img_slides': imgSliders,
     'video_url': video_url, 'cartItems': cartItems, 'categoryDropdownList': data['categoryList'], 
     'firstLevelCategories': (firstLevelCategories), 'categories_': categories_, 'ptdCatId': ptdCatId,
     'acctMenu': acctMenu, 'selectedMenu': selectedMenu}
    return render(request, 'accounts/add_product.html', context)


@unauthenticated_user
# @t_allowed_users(allowed_roles = ['Trader group', 'Admin group'])
def editProduct(request, pk):

    data = cartData(request)
    cartItems = data['cartItems']

    myDictionary = {}
    product = Product.objects.get(id=pk)
    categories = Category.objects.all()
    t_stores = Store.objects.filter(user_id=request.user.id) # I WANT TRADER TO ONLY SEE THEIR STORE(S)
    brands = Brand.objects.all()
    isImage = False
    is_product_over_view = False
    Is_error = False
    Is_error2 = False
    active = request.POST.get("active")
    slideImg_path = request.POST.getlist('slideImg_path') # GET THE PATH OF THE IMAGE IF CHECKBOX WAS SELECTED. THE CHECK IMAGE WILL BE DELETED
    imgSliders = Slide_image.objects.filter(product=product) # FILTER ALL THE PRODUCT FROM THE TABLE.
    video_url = Video_item.objects.filter(product=product) # FILTER THE VIDEO OBJ IF ANY IS AVAILABLE
    ptdCatId = product.category_id
    categories_json = json.dumps(list(categories.values()))
    firstLevelCategories = Category.objects.filter(level = 0)
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myProduct' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
    
    img_slides = SlideImage(imgSliders)
    active_ptd = {
                'active': (True if active == 'on' else False)
            }

    
    if slideImg_path:
        # IF CHECKBOX WAS SELECTED, LOOP THROUGH THE FILTERED SLIDE IMAGE, COMPARE PATH WITH SELECTED CHECKBOX AND DELETE MATCHED PATHS
        for imgSlider in imgSliders:
            if imgSlider.image_slideURL in slideImg_path:
                imgSlider.delete()
    

    ptdRecord = product
    ptd = UpdateProduct(instance=product)
    # CHECKING IF IMAGE EXIST; TO ENSURE HTML TEMPLATE IS PROPERLY ARRANGE
    if product.image:
        isImage = True
    if request.POST.get('save-btn') == 'Save':
        # UPDATE THE POST DATA
        productForm = UpdateProduct(request.POST, request.FILES, instance=product)
        if productForm.is_valid:
            # WHEN PTD IMAGE ARE DELETED FROM THE DATABASE, TO ENSURE THE IMAGE FILE 
            # IS ALSO DELETED FROM ITS FOLDER, CHECK FOR THIS CONDITION
            if request.POST.get('image-clear') == 'on':
                os.remove(ptdRecord.image.path)
            productForm.save()

            # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
            if active_ptd['active'] == True:
                saved_ptd = Product.objects.get(id=pk)
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()
            else:
                saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()

            is_product_over_view = True

            # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
            slide_ptd_images = request.FILES.getlist('slide_ptd_image')
            if slide_ptd_images:
                for slide_ptd_image in slide_ptd_images:
                    Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)
            




            # =================== CHECK AND GET ANY RECORD FROM THE VIDEO URL FIELD ====================
            video_path = request.POST.get('video_url')
            # IF IT EXIST, IT'S EIGHER IT WAS PULLED FROM DB OR THE USER UPDATED THE RECORD FROM DB OR THE USER ADDED THE LINK FOR THE FIRST
            if video_path:
                # IF THE CHECK BOX TO DELETE WAS SELECTED, THIS MEANS IT ALREADY EXIST IN DB. DELETE THE VIDEO
                if request.POST.get('videoUrl_chckBox') == 'delete video':
                    video_url = Video_item.objects.get(product=saved_ptd)
                    video_url.delete()
                    video_url = Video_item.objects.filter(product=saved_ptd)
                else:
                    # UPDATE OR CREATE THE VIDEO
                    newChanges = {'video': request.POST.get('video_url')}

                    #  ========== CHECKING IF THE URL IS VALID...=============
                    regex = re.compile(
                        r'^(?:http|ftp)s?://' # http:// or https://
                        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                        r'localhost|' #localhost...
                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                        r'(?::\d+)?' # optional port
                        r'(?:/?|[/?]\S+)$', re.IGNORECASE
                    )

                    if re.match(regex, newChanges['video']) is not None:
                        # CHECK IF THE VIDEO EXIST IN DATABASE
                        video_frm_db = Video_item.objects.filter(product=saved_ptd)
                        # ========= UPDATE AN EXISTING VIDEO FROM DATABASE =================
                        if video_frm_db:
                            video_url = Video_item.objects.get(product=saved_ptd)
                            video = VideoUrl(data=newChanges, instance=video_url)
                    
                            if video.is_valid:
                                try:
                                    # I HAD TO FILTER FIRST BEFORE SAVING IN CASE THE URL IS NOT VALIDATED AT THE POINT OF SAVING
                                    # IF VALIDATION WAS SUCCESSFUL AND RECORD SAVED, WE FILTER AGAIN TO GET THE NEW CHANGES SAVED
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                                    video.save()
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                            
                                except:
                                    Is_error = True
                                    error_msg = video.errors['video']
                        else:
                            # =============== SAVE A NEW VIDEO INTO IT'S DATABASE TABLE ==============
                            # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                            video_path = request.POST.get('video_url')
                            # ============= VALIDATED URL =============
                            if video_path and re.match(regex, video_path):
                                Video_item.objects.create(product=saved_ptd, video=video_path)
                                video_url = Video_item.objects.filter(product=saved_ptd)
                    else:
                        error2_msg = 'Product update successful. Video link is not valid!'
                        Is_error2 = True
            


    
    elif request.POST.get('save-add-another-btn') == 'Save and add another':
        # UPDATE THE POST DATA
        productForm = UpdateProduct(request.POST, request.FILES, instance=product)
        if productForm.is_valid:
            # WHEN PTD IMAGE ARE DELETED FROM THE DATABASE, TO ENSURE THE IMAGE FILE 
            # IS ALSO DELETED FROM ITS FOLDER, CHECK FOR THIS CONDITION
            if request.POST.get('image-clear') == 'on':
                os.remove(ptdRecord.image.path)
            productForm.save()

            # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
            if active_ptd['active'] == True:
                saved_ptd = Product.objects.get(id=pk)
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()
            else:
                saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()
            ptdRecord = ''
            ptd = UpdateProduct()
            categories = Category.objects.all()
            t_stores = Store.objects.filter(user_id=request.user.id) # I WANT TRADER TO ONLY SEE THEIR STORE(S)
            brands = Brand.objects.all()

            # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
            slide_ptd_images = request.FILES.getlist('slide_ptd_image')
            if slide_ptd_images:
                for slide_ptd_image in slide_ptd_images:
                    Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)
            


            # =================== CHECK AND GET ANY RECORD FROM THE VIDEO URL FIELD ====================
            video_path = request.POST.get('video_url')
            # IF IT EXIST, IT'S EIGHER IT WAS PULLED FROM DB OR THE USER UPDATED THE RECORD FROM DB OR THE USER ADDED THE LINK FOR THE FIRST
            if video_path:
                # IF THE CHECK BOX TO DELETE WAS SELECTED, THIS MEANS IT ALREADY EXIST IN DB. DELETE THE VIDEO
                if request.POST.get('videoUrl_chckBox') == 'delete video':
                    video_url = Video_item.objects.get(product=saved_ptd)
                    video_url.delete()
                    video_url = Video_item.objects.filter(product=saved_ptd)
                else:
                    # UPDATE OR CREATE THE VIDEO
                    newChanges = {'video': request.POST.get('video_url')}

                    #  ========== CHECKING IF THE URL IS VALID...=============
                    regex = re.compile(
                        r'^(?:http|ftp)s?://' # http:// or https://
                        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                        r'localhost|' #localhost...
                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                        r'(?::\d+)?' # optional port
                        r'(?:/?|[/?]\S+)$', re.IGNORECASE
                    )

                    if re.match(regex, newChanges['video']) is not None:
                        # CHECK IF THE VIDEO EXIST IN DATABASE
                        video_frm_db = Video_item.objects.filter(product=saved_ptd)
                        # ========= UPDATE AN EXISTING VIDEO FROM DATABASE =================
                        if video_frm_db:
                            video_url = Video_item.objects.get(product=saved_ptd)
                            video = VideoUrl(data=newChanges, instance=video_url)
                    
                            if video.is_valid:
                                try:
                                    # I HAD TO FILTER FIRST BEFORE SAVING IN CASE THE URL IS NOT VALIDATED AT THE POINT OF SAVING
                                    # IF VALIDATION WAS SUCCESSFUL AND RECORD SAVED, WE FILTER AGAIN TO GET THE NEW CHANGES SAVED
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                                    video.save()
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                            
                                except:
                                    Is_error = True
                                    error_msg = video.errors['video']
                        else:
                            # =============== SAVE A NEW VIDEO INTO IT'S DATABASE TABLE ==============
                            # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                            video_path = request.POST.get('video_url')
                            # ============= VALIDATED URL =============
                            if video_path and re.match(regex, video_path):
                                Video_item.objects.create(product=saved_ptd, video=video_path)
                                video_url = Video_item.objects.filter(product=saved_ptd)
                    else:
                        error2_msg = 'Product update successful. Video link is not valid!'
                        Is_error2 = True
            if Is_error:
                myDictionary['successmsg'] = 'Product update successful. ' + error_msg[0]
            elif Is_error2:
                myDictionary['successmsg'] = error2_msg
            else:
                myDictionary['successmsg'] = 'Product update successful'
            myDictionary['ptd_saved'] = True



            myDictionary['t_stores'] = t_stores
            myDictionary['categories'] = categories
            myDictionary['brands'] = brands
            
            context = {'form': ptdRecord, 'ptd_form': ptd, 'myDictionary': myDictionary, 
            'cartItems': cartItems, 'categoryDropdownList': data['categoryList'],
            'firstLevelCategories': firstLevelCategories, 'categories_': categories_json}
            return render(request, 'accounts/add_product.html', context)

    elif request.POST.get('save-edit-btn') == 'Save and continue editing':
        # GET THE PRODUCT CATEGORY ID. IT IS USED ON THE TEMPLATE
        # TO DISPLAY THE PRODUCT CATEGORY AND SUB-CATEGORIES SELECTED.
        ptdCatId = request.POST['category']

        isImage = False
        # SAVE AND CONTINUE EDITING...
        productForm = UpdateProduct(request.POST, request.FILES, instance=product)
        if productForm.is_valid:
            # WHEN PTD IMAGE ARE DELETED FROM THE DATABASE, TO ENSURE THE IMAGE FILE 
            # IS ALSO DELETED FROM ITS FOLDER, CHECK FOR THIS CONDITION
            if request.POST.get('image-clear') == 'on':
                os.remove(ptdRecord.image.path)
            productForm.save()

            # ENSURING THE ACTIVE STATUS BUTTON IS SAVED TO THE BACKEND
            if active_ptd['active'] == True:
                saved_ptd = Product.objects.get(id=pk)
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()
            else:
                saved_ptd = Product.objects.get(name=request.POST.get('name'), store=request.POST.get('store'))
                active_btn = ActivePtd(data=active_ptd, instance=saved_ptd)
                if active_btn.is_valid:
                    active_btn.save()
            ptdRecord = Product.objects.get(id=pk)
            ptd = UpdateProduct(instance=ptdRecord)
            # CHECKING IF IMAGE EXIST; TO ENSURE HTML TEMPLATE IS PROPERLY ARRANGE
            if ptdRecord.image:
                isImage = True

            # GET THE LIST OF SLIDER IMAGES, LOOP AND CREATE THEM AGAINST THE PRODUCT NAME
            slide_ptd_images = request.FILES.getlist('slide_ptd_image')
            if slide_ptd_images:
                for slide_ptd_image in slide_ptd_images:
                    Slide_image.objects.create(product=saved_ptd, slide_ptd_image=slide_ptd_image)
            
            # =================== CHECK AND GET ANY RECORD FROM THE VIDEO URL FIELD ====================
            video_path = request.POST.get('video_url')
            # IF IT EXIST, IT'S EIGHER IT WAS PULLED FROM DB OR THE USER UPDATED THE RECORD FROM DB OR THE USER ADDED THE LINK FOR THE FIRST
            if video_path:
                # IF THE CHECK BOX TO DELETE WAS SELECTED, THIS MEANS IT ALREADY EXIST IN DB. DELETE THE VIDEO
                if request.POST.get('videoUrl_chckBox') == 'delete video':
                    video_url = Video_item.objects.get(product=saved_ptd)
                    video_url.delete()
                    video_url = Video_item.objects.filter(product=saved_ptd)
                else:
                    # UPDATE OR CREATE THE VIDEO
                    newChanges = {'video': request.POST.get('video_url')}

                    #  ========== CHECKING IF THE URL IS VALID...=============
                    regex = re.compile(
                        r'^(?:http|ftp)s?://' # http:// or https://
                        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                        r'localhost|' #localhost...
                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                        r'(?::\d+)?' # optional port
                        r'(?:/?|[/?]\S+)$', re.IGNORECASE
                    )

                    if re.match(regex, newChanges['video']) is not None:
                        # CHECK IF THE VIDEO EXIST IN DATABASE
                        video_frm_db = Video_item.objects.filter(product=saved_ptd)
                        # ========= UPDATE AN EXISTING VIDEO FROM DATABASE =================
                        if video_frm_db:
                            video_url = Video_item.objects.get(product=saved_ptd)
                            video = VideoUrl(data=newChanges, instance=video_url)
                    
                            if video.is_valid:
                                try:
                                    # I HAD TO FILTER FIRST BEFORE SAVING IN CASE THE URL IS NOT VALIDATED AT THE POINT OF SAVING
                                    # IF VALIDATION WAS SUCCESSFUL AND RECORD SAVED, WE FILTER AGAIN TO GET THE NEW CHANGES SAVED
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                                    video.save()
                                    video_url = Video_item.objects.filter(product=saved_ptd)
                            
                                except:
                                    Is_error = True
                                    error_msg = video.errors['video']
                        else:
                            # =============== SAVE A NEW VIDEO INTO IT'S DATABASE TABLE ==============
                            # GET THE VIDEO URL, LINK IT TO THE CURRENT PRODUCT AND CREATE THE RECORD ON VIDEO_ITEM TABLE
                            video_path = request.POST.get('video_url')
                            # ============= VALIDATED URL =============
                            if video_path and re.match(regex, video_path):
                                Video_item.objects.create(product=saved_ptd, video=video_path)
                                video_url = Video_item.objects.filter(product=saved_ptd)
                    else:
                        error2_msg = 'Product update successful. Video link is not valid!'
                        Is_error2 = True
            if Is_error:
                myDictionary['successmsg'] = 'Product update successful. ' + error_msg[0]
            elif Is_error2:
                myDictionary['successmsg'] = error2_msg
            else:
                myDictionary['successmsg'] = 'Product update successful'
            myDictionary['ptd_saved'] = True

    
    # THIS BLOCK OF CODE IS ONLY EXECUTED WHEN "SAVE" BUTTON IS CLICK
    if is_product_over_view:
        t_stores = Store.objects.filter(user_id=request.user.id)
        trader_stores = []
        ptd_list = []
        ptd_counter = 0
        for t_store in t_stores:
            trader_stores.append(t_store.id)
        if trader_stores:
            products = Product.objects.all().order_by('-id')
            for store_id in trader_stores:
                for trader_ptd in products:
                    if trader_ptd.store_id == store_id:
                        ptd_dic = {
                            'id': trader_ptd.id,
                            'name': trader_ptd.name,
                            'description': trader_ptd.description,
                            'brand': trader_ptd.brand,
                            'price': trader_ptd.price,
                            'discount': trader_ptd.discount,
                            'mfgDate': trader_ptd.mfgDate,
                            'expDate': trader_ptd.expDate,
                            'store': trader_ptd.store,
                            'active':trader_ptd.active
                        }
                        ptd_list.append(ptd_dic)
                        ptd_counter += 1

        if Is_error:
            myDictionary['successmsg'] = 'Product update successful. ' + error_msg[0]
        elif Is_error2:
            myDictionary['successmsg'] = error2_msg
        else:
            myDictionary['successmsg'] = 'Product update successful'
        myDictionary['ptd_saved'] = True
        
        context = {'trader_ptds': ptd_list, 'ptd_counter': ptd_counter, 'myDictionary': myDictionary, 
        'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
        return render(request, 'accounts/product_over_view.html', context)

    imgSliders = Slide_image.objects.filter(product=product) # FILTER ALL THE PRODUCT FROM THE TABLE.
    myDictionary['t_stores'] = t_stores
    myDictionary['categories'] = categories
    myDictionary['brands'] = brands
    myDictionary['isImage'] = isImage
    context = {'form': ptdRecord, 'ptd_form': ptd, 'myDictionary': myDictionary, 'img_slides': imgSliders, 
    'video_url': video_url, 'cartItems': cartItems, 'categoryDropdownList': data['categoryList'],
    'categories_json': categories_json, 'ptdCatId': ptdCatId, 'acctMenu': acctMenu, 
    'selectedMenu': selectedMenu}
    return render(request, 'accounts/edit_product.html', context)


@unauthenticated_user
def wishList(request):
    
    wishLists = WishList.objects.filter(customer_id=request.user.customer.id)
    myDictionary = {}
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'myWishList' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
  

    # THIS BLOCK OF CODE IS USED TO DELETE OR ADD SELECTED WISH LIST PRODUCT(S)
    if request.method == 'POST':
        if request.POST.get('delete_btn') == 'Go':
            if request.POST.get('select_comboBox') == 'Delete':
                if request.POST.get('chk_box_action'):
                    selected_values = request.POST.getlist('chk_box_action')
                    for pk in selected_values:
                        selected_ptd = WishList.objects.get(id=pk)
                        selected_ptd.delete()
                    myDictionary['isSuccess'] = True
                    myDictionary['success_msg'] = 'Wish list item successfully deleted'
                else:
                    myDictionary['isWarning'] = True
                    myDictionary['warning_msg'] = 'Select the check box you wish to perform action on'
            elif request.POST.get('select_comboBox') == 'add_to_cart':
                if request.POST.get('chk_box_action'):
                    selected_values = request.POST.getlist('chk_box_action')
                    for pk in selected_values:
                        wish_listItem = WishList.objects.get(id = pk)
                        ptdId = wish_listItem.product.id
                        updateCartItem(request, ptdId, 'add')

            else:
                myDictionary['isWarning'] = True
                myDictionary['warning_msg'] = 'No action was selected...!'
                
    # CHECKING IF THERE ARE PENDING REVIEWS
    wishLists = WishList.objects.filter(customer_id=request.user.customer.id)
    data = cartData(request)
    cartItems = data['cartItems']
    myDictionary['isWishList'] = False
    if wishLists:
        myDictionary['isWishList'] = True
    context = {'wishLists': wishLists, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu, 'selectedMenu': selectedMenu}
    return render(request, 'accounts/wish_list.html', context)



@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def adminSession(request):
    myDictionary = {}
    myDictionary['isOrderList'] = False
    orderData = ''

    data = cartData(request)
    cartItems = data['cartItems']
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'admin' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
  
    order_data = []
    # orderData = Order.objects.filter (Q(complete=True) | Q(transaction_id__isnull=False)).order_by('-date_order')
    if request.META.get('HTTP_REFERER') == 'http://127.0.0.1:8000/admin_session/':
        orderData = Order.objects.filter (Q(status='Processing') | Q(status='On hold') | Q(status='Shipped')).order_by('-date_order')
    else:
        orderData = Order.objects.filter (Q(status='Processing') | Q(status='On hold') | Q(status='Shipped')).order_by('-date_order')
        myDictionary['isOrderList'] = True
    if request.method == 'POST':
        # FILTER CONDITIONS
        
        searched_value = request.POST.get('searched_value')
        if searched_value:
            orderData = Order.objects.filter(Q(customer__name__contains=str(searched_value)) | Q(transaction_id__contains=str(searched_value))).order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'complete':
            orderData = Order.objects.filter (status='Completed').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'processing':
            orderData = Order.objects.filter (status='Processing').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'on_hold':
            orderData = Order.objects.filter (status='On hold').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'shipped':
            orderData = Order.objects.filter (status='Shipped').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'cancelled':
            orderData = Order.objects.filter (status='Cancelled').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'refunded':
            orderData = Order.objects.filter (status='Refunded').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'rejected':
            orderData = Order.objects.filter (status='Rejected').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'failed':
            orderData = Order.objects.filter (status='Failed').order_by('-date_order')
            myDictionary['isOrderList'] = True
        elif request.POST.get('action_comboBox_selected') == 'False':
            orderData = Order.objects.filter (Q(status='Processing') | Q(status='On hold') | Q(status='Shipped')).order_by('-date_order')
            myDictionary['isOrderList'] = True
        try:
            data = json.loads(request.body)
            myDictionary['isOrderList'] = True
            if data['admin_order'] == 'get_admin_order':
                return JsonResponse('admin order', safe=False)
        except:
            pass

    # LET'S LOOP TO GET THE TOTAL NUMBER OF ALL ORDER, PROCESSING ORDER AND TOTAL ORDER
    counter = 0
    for orderRecord in orderData:
        if orderRecord.transaction_id:
            counter += 1
            # GET THE TOTAL AMOUNT OF EACH ORDER 
            orderItems = OrderItem.objects.filter(order__transaction_id= orderRecord.transaction_id)
            total_amt = 0
            for orderItem in orderItems:
                total_amt += orderItem.line_total

            order_record = {
                'transaction_id': orderRecord.transaction_id,
                'customer_name': orderRecord.customer.name,
                'date_order': orderRecord.date_order,
                'complete': orderRecord.complete,
                'paid': orderRecord.paid,
                'total': total_amt,
                'status': orderRecord.status,
                'counter': counter,
            }
            order_data.append(order_record)
    myDictionary['counter'] = counter
    context = {'orderData': order_data, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu, 'selectedMenu': selectedMenu}
    
    return render(request, 'accounts/admin_processing_session.html', context)


@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def adminEditOrder(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    
    order = Order.objects.get(transaction_id=pk)
    orderItems = order.orderitem_set.all()
    grandTotal = 0
    isVerifiedPayment = False
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'admin' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
  
    # THIS BLOCK OF CODE IS USED TO NAVIGATE BACK TO ORDER LIST VIEW
    if request.POST.get('admin_orderList_btn') == 'Order List':
        return redirect('admin_session')
        # orderData = Order.objects.filter (Q(complete=True) | Q(transaction_id__isnull=False)).order_by('-date_order')
        # counter = 0
        # order_data = []
        # myDictionary = {}
        # for orderRecord in orderData:
        #     counter += 1
        #     # GET THE TOTAL AMOUNT OF EACH ORDER 
        #     orderItems = OrderItem.objects.filter(order__transaction_id= float(orderRecord.transaction_id))
        #     total_amt = 0
        #     for orderItem in orderItems:
        #         total_amt += orderItem.line_total

        #     order_record = {
        #         'transaction_id': orderRecord.transaction_id,
        #         'customer_name': orderRecord.customer.name,
        #         'date_order': orderRecord.date_order,
        #         'complete': orderRecord.complete,
        #         'paid': orderRecord.paid,
        #         'total': total_amt,
        #         'status': orderRecord.status,
        #         'counter': counter,
        #     }
        #     order_data.append(order_record)
        
        # myDictionary['isOrderList'] = True
        # myDictionary['counter'] = counter
        # context = {'orderData': order_data, 'myDictionary': myDictionary}
        # return render(request, 'accounts/admin_processing_session.html', context)


    for orderItem in orderItems:
        grandTotal += orderItem.line_total
    shipping_address = ShippingAddress.objects.get(order__transaction_id=pk)
    orderData = []
    myDictionary = {}
    # CONFIRM IF CUSTOMER IS A REGISTERED USER
    if order.customer.user:
        user = User.objects.get(id=order.customer.user.id)
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': order.date_order,
            'complete': order.complete,
            'name': shipping_address.name,
            'address': shipping_address.address,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'mobile': shipping_address.mobile,
            'altMobile': shipping_address.altMobile,
            'optional_note': shipping_address.optional_note,
            'user_name': user.username,
            'user_email': user.email,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'payment_option': order.payment_option,
            'paid': order.paid,
            'status': order.status,
            'private_note': order.order_private_note,
            'refund_status': order.refund_status,
        }
    else:
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': order.date_order,
            'complete': order.complete,
            'name': shipping_address.name,
            'address': shipping_address.address,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'mobile': shipping_address.mobile,
            'altMobile': shipping_address.altMobile,
            'optional_note': shipping_address.optional_note,
            'user_name': order.customer.name,
            'user_email': order.customer.email,
            'payment_option': order.payment_option,
            'paid': order.paid,
            'status': order.status,
            'date_joined': '',
            'last_login': '',
            'private_note': order.order_private_note,
            'refund_status': order.refund_status,
        }
    if request.method == 'POST':
        # GET RECORD FROM USER AND SEND A MAIL RELATING TO CUSTOMER ORDER
        if request.POST.get('email_btn') == 'Send Email' and request.POST['customer_email']:
            try:
                myDictionary['isEmailSuccess'] = True
                body_of_email = request.POST['customer_email']
                template = body_of_email
                # THIS CONDITION IS PLACED BECAUSE A REGISTERED USER AND 
                # GUEST USER EMAIL ARE FROM DIFFERENT TABLES
                if order.customer.user:
                    email = EmailMessage(
                        'Your Order Status...!',
                        template,
                        conf_settings.EMAIL_HOST_USER,
                        [order.customer.user.email]
                    )
                else:
                    email = EmailMessage(
                        'Your Order Status...!',
                        template,
                        conf_settings.EMAIL_HOST_USER,
                        [order.customer.email]
                    )
                fail_silently=False
                # email.send()
                myDictionary['success_msg'] = 'Email sent successful'

                # LOG USER ACTIVITIES OF THIS PAGE ON THE ORDER TABLE
                acct_activity = order.acct_activities
                if acct_activity:
                    order.acct_activities = str(acct_activity) + ' // ' + str (request.user.username) + ' ' + str (strftime("%Y-%m-%d %H:%M:%S", gmtime()))
                else:
                    order.acct_activities = str (request.user.username) + ' ' + str (strftime("%Y-%m-%d %H:%M:%S", gmtime()))
                # order.save()

            except Exception as e:
                # print (e.strerror, type(e))
                myDictionary['isEmailSuccess'] = False
                myDictionary['warning_msg'] = e.strerror + '. Email not sent...!'
        
        # REQUEST TO UPDATE CUSTOMER SHIPPING ADDRESS
        elif request.POST.get('update_shipping_address') == 'Update Shipping':
            shipping_address = UpdateShippingAddress(request.POST, instance=shipping_address)
            if shipping_address.is_valid:
                # shipping_address.save()

                # LOG USER ACTIVITIES OF THIS PAGE ON THE ORDER TABLE
                acct_activity = order.acct_activities
                if acct_activity:
                    order.acct_activities = str(acct_activity) + ' // ' + str (request.user.username) + ' ' + str (strftime("%Y-%m-%d %H:%M:%S", gmtime()))
                else:
                    order.acct_activities = str (request.user.username) + ' ' + str (strftime("%Y-%m-%d %H:%M:%S", gmtime()))
                # order.save()
                return redirect('admin_edit_order', pk)
        
        # THIS BLOCK OF CODE IS USED TO GENERATE PACKING SLIP IN PFT FORMAT
        elif request.POST.get('packing_slip_btn') == 'Packing Slip':
           
            template_path = 'accounts/packingSlip_pdf.html'
            context = {'orderItems': orderItems, 'order': order, 'shipping_address': shipping_address, 'order_obj': order_obj}

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'filename="packing_slip.pdf"'

            template = get_template(template_path)
            html = template.render(context)

            pisa_status = pisa.CreatePDF(
                html, dest=response
            )
           
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response

        # THIS BLOCK OF CODE IS USED TO GENERATE THE INVOICE TO PDF FORMAT
        elif request.POST.get('generate_invoice_btn') == 'Generate Invoice':
            invoice_date = datetime.date.today()
            print(invoice_date)
            template_path = 'accounts/pdf_invoice.html'
            context = {'orderItems': orderItems, 'order': order, 'shipping_address': shipping_address, 'grandTotal': grandTotal, 'invoice_date': invoice_date}

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'filename="invoice.pdf"'

            template = get_template(template_path)
            html = template.render(context)

            pisa_status = pisa.CreatePDF(
                html, dest=response
            )
           
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response

    # ======== CHECK PAYMENT TABLE IF PAYMENT WAS MADE AND VERIFIED ==========
    if order.paymentReference:
        payment = Payment.objects.get(ref= order.paymentReference)
        isVerifiedPayment = payment.verified
    else:
        payment = Payment.objects.filter(ref= order.transaction_id)
        if payment:
            payment = Payment.objects.get(ref= order.transaction_id)
            isVerifiedPayment = payment.verified

    myDictionary['grandTotal'] = grandTotal
    myDictionary['isVerifiedPayment'] = isVerifiedPayment
    
    context = {'order_obj': order_obj, 'orderItems': orderItems, 'myDictionary': myDictionary, 
    'order': order, 'cartItems': cartItems, 'categoryDropdownList': data['categoryList'],
    'acctMenu': acctMenu, 'selectedMenu': selectedMenu}
    return render(request, 'accounts/admin_edit_order.html', context)


@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def adminUpdateItem(request):
    data = json.loads(request.body)
    item_id = data['item_id']
    action = data['action']
    trans_id = data['trans_id']
    selected_value = data['selected_value'] # USED TO UPDATE ORDER STATUS
    private_note = data['private_note']
    amt_paid = data['amtPaid']
    payment_mode = data['paymentMode']
    payment_note = data['paymentNote']
    email_sent_status = ''
    serverMsg = ''
    try:
        if item_id:
            orderItem = OrderItem.objects.get(id=item_id)
        order = Order.objects.get(transaction_id=trans_id)
        if action == 'reduction':
            orderItem.quantity = (orderItem.quantity - 1)
            orderItem.line_total = orderItem.unit_price * orderItem.quantity
            orderItem.save()
            if orderItem.quantity < 1:
                orderItem.delete()
        elif action == 'delete':
            print('Delete')
            orderItem.delete()
        
        # IF THE USER DELETE THE LAST CART ITEM IN THE TABLE, CHANGE THE ORDER STATUS TO CANCELLED
        order_items = order.orderitem_set.all()
        if not order_items:
            order.status = 'Cancelled'
            # CHECK IF USER ENTERED A PRIVATE NOTE OR USE THE DEFAULT IN ELSE STATEMENT
            if private_note:
                order.order_private_note = private_note
            else:
                order.order_private_note = '' + request.user.username + ' deleted all order-items. Status automatically changed to cancel.'
            order.save()
            try:
                # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR ORDER WAS CANCELLED
                template = render_to_string('accounts/email_template_admin_order.html', {
                    'order_status': order.status, 'cus_name': order.customer.name,
                    'transaction_id': order.transaction_id, 'date_order': order.date_order,
                    
                })
                email = EmailMessage(
                    'HAPPY SHOPPERS - Cancelled Order!',
                    template,
                    conf_settings.EMAIL_HOST_USER,
                    [order.customer.email,]
                )
                fail_silently=False
                # email.send()
                # email_sent_status = 'cancelled'
            except Exception as e:
                print(e.strerror)
                email_sent_status = 'failed'
        
        # CONDITION TO UPDATE ORDER STATUS
        if selected_value == 'completed':
            order.status = 'Completed'
            if order.paid == False:
                order.paid = True
            if order.complete == False:
                order.complete = True

            # GET THE PAYMENT FOR THIS ORDER IF IT EXIST AND UPDATE THE AMOUNT IF IT WAS NOT
            # VERIFIED OR...
            # CREATE THE PAYMENT RECORD FOR THIS ORDER IN THE PAYMENT TABLE.
            if order.paymentReference:
                payment = Payment.objects.get(ref= order.paymentReference)
                if not payment.verified:
                    payment.amount = amt_paid
                    payment.verified = True
                    payment.save()
            elif amt_paid:
                payment, created = Payment.objects.get_or_create(
                amount= amt_paid,
                ref= order.transaction_id,
                email= order.customer.email,
                verified= True,
                channel= payment_mode,
                message= payment_note,
                status= 'success',
            )


            # SINCE THE ORDER IS COMPLETE, THIS MEANS THE CUSTOMER HAVE RECEIVED THEIR ORDER.
            # CREATE THE ITEMS IN THE PRODUCT REVIEW TABLE. THIS IS ONLY FOR REGISTERED CUSTOMER
            if order.customer.user and order_items:

                ptd_review, created = ProductReview.objects.get_or_create(
                    cus_name = order.customer.user.username,
                    transaction_id = trans_id,
                    order_date = order.date_order
                )
                
                ptdReview = ProductReview.objects.get(transaction_id= trans_id)

                for order_item in order_items:
                    ProductReview.objects.create(
                        ptd_review_id = ptdReview.id,
                        ptd_id = order_item.product.id,
                        product_name = order_item.product.name,
                        product_image = order_item.product.imageURL,
                        transaction_id = trans_id,
                    )
                

            try:
                # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR ORDER WAS COMPLETED
                template = render_to_string('accounts/email_template_admin_order.html', {
                    'order_status': order.status, 'cus_name': order.customer.name,
                    'transaction_id': order.transaction_id, 'date_order': order.date_order,
                    'registered_user': order.customer.user,
                    
                })
                email = EmailMessage(
                    'HAPPY SHOPPERS - Order Completed and Closed!',
                    template,
                    conf_settings.EMAIL_HOST_USER,
                    [order.customer.email,]
                )
                fail_silently=False
                # email.send()
                # email_sent_status = 'completed'
            except Exception as e:
                print(e.args)
                email_sent_status = 'failed'

        elif selected_value == 'processing':
            order.status = 'Processing'
        elif selected_value == 'on_hold':
            order.status = 'On hold'
        elif selected_value == 'shipped':
            order.status = 'Shipped'
            try:
                # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR ORDER WAS SHIPPED
                template = render_to_string('accounts/email_template_admin_order.html', {
                    'order_status': order.status, 'cus_name': order.customer.name,
                    'transaction_id': order.transaction_id, 'date_order': order.date_order,
                    
                })
                email = EmailMessage(
                    'HAPPY SHOPPERS - Shipped Order!',
                    template,
                    conf_settings.EMAIL_HOST_USER,
                    [order.customer.email,]
                )
                fail_silently=False
                # email.send()
                # email_sent_status = 'shipped'
            except Exception as e:
                print(e.strerror)
                email_sent_status = 'failed'

        elif selected_value == 'cancelled':
            order.status = 'Cancelled'
            order.order_private_note = private_note
            if request.user.is_staff:
                try:
                    # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR ORDER WAS CANCELLED
                    template = render_to_string('accounts/email_template_admin_order.html', {
                        'order_status': order.status, 'cus_name': order.customer.name,
                        'transaction_id': order.transaction_id, 'date_order': order.date_order,
                        
                    })
                    email = EmailMessage(
                        'HAPPY SHOPPERS - Cancelled Order!',
                        template,
                        conf_settings.EMAIL_HOST_USER,
                        [order.customer.email,]
                    )
                    fail_silently=False
                    # email.send()
                    # email_sent_status = 'cancelled'
                except Exception as e:
                    print(e.strerror)
                    email_sent_status = 'failed'

        elif selected_value == 'rejected':
            order.status = 'Rejected'
            order.order_private_note = private_note
        elif selected_value == 'failed':
            order.status = 'Failed'
            order.order_private_note = private_note

        order.save()
        serverMsg = 'successful'
    except Exception as e:
        serverMsg = e.args

    return JsonResponse({'email_sent_status': email_sent_status, 'serverMsg': serverMsg}, safe=False)


@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def adminProcessRefundOrder(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']

    totalAmt = 0
    totalRefund = 0
    difference = 0
    myDictionary = {}
    
    refundOrder = Order.objects.get(transaction_id= pk)
    refundItems = refundOrder.orderitem_set.all()
    
    
    # USED TO CHECK IF REFUND PROCESS WAS COMPLETED. IF NOT THIS BOOLEAN IS SET TO DISPLAY ALERT
    myDictionary['isIncompleteRefundProcess'] = False
    if not refundOrder.reason_for_refund:
        for refundItem in refundItems:
            if refundItem.refundAmt > 0:
                myDictionary['isIncompleteRefundProcess'] = True
                break
    for refundAmt in refundItems:
        totalAmt += refundAmt.line_total
        totalRefund += refundAmt.refundAmt
    if request.method == 'POST':
        
        # BLOCK OF CODE THAT EXECUTE REQUEST TO SUBMIT REFUND IF REASON FOR REFUND WAS NOT SELECTED
        if request.POST.get('refund_btn') == 'Submit Refund':
            # CHECK IF REASON FOR REFUND WAS SAVED BEFORE ON THE DATABASE. IF IT WAS, PREVENT SAVING
            if not refundOrder.reason_for_refund:
                reason_for_refund = request.POST.get('action_comboBox_selected')
                if not reason_for_refund == 'False' and totalRefund > 0:
                    # CHECKING IF PAYMENT WAS MADE ON THE ORDER BEFORE PROCESSING REFUND IF PAYMENT IS TRUE.
                    if refundOrder.paid:
                        # SAVE THE COMPLETE REFUND PROCESS BY UPDATING THE STATUS AND REASON FOR REFUND
                        
                        # CHECKING IF IT'S A FULL REFUND OR PARTIAL REFUND
                        if totalRefund == totalAmt:
                            refundOrder.refund_status = 'Full Refund'
                            refundOrder.status = 'Refunded' # CONDITION USED TO DETERMINE WHICH EMAIL TEMPLATE TO LOAD...
                        else:
                            refundOrder.refund_status = 'Partial Refund'
                            emailTemp = 'Refunded' # CONDITION USED TO DETERMINE WHICH EMAIL TEMPLATE TO LOAD...
                            
                        refundOrder.reason_for_refund = reason_for_refund
                        refundOrder.refund_private_note = request.POST.get('private_note')
                        # refundOrder.save()

                        try:
                            # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR REFUND IS UNDER PROCESS
                            template = render_to_string('accounts/email_template_admin_order.html', {
                                'order_status': refundOrder.status, 'cus_name': refundOrder.customer.name,
                                'transaction_id': refundOrder.transaction_id, 'date_order': refundOrder.date_order,
                                'totalRefund': totalRefund, 'emailTemp': emailTemp,
                            })
                            email = EmailMessage(
                                'HAPPY SHOPPERS - Refund under process!',
                                template,
                                conf_settings.EMAIL_HOST_USER,
                                [refundOrder.customer.email,]
                            )
                            fail_silently=False
                            # email.send()
                            myDictionary['success_msg'] = 'Refund submitted successful. Email was sent to customer with the status of refund.'
                        except Exception as e:
                            print('EMAIL ERROR:', e.strerror)
                            email_sent_status = 'failed'

                            myDictionary['success_msg'] = 'Refund submitted successful. Error while sending email to customer!'
                        myDictionary['isSuccessMsg'] = True
                    else:
                        # NO PAYMENT WAS MADE ON THIS ORDER. REFUND CANNOT BE PROCESSED
                        pass
                else:
                    # DON'T SAVE
                    myDictionary['isSuccessMsg'] = False
                    myDictionary['warning_msg'] = 'Refund submit unsuccessful'
            else:
                # DON'T SAVE
                myDictionary['isSuccessMsg'] = False
                myDictionary['warning_msg'] = 'Refund submit unsuccessful'
    
    difference = totalAmt - totalRefund
    myDictionary['totalAmt'] = totalAmt
    myDictionary['totalRefund'] = totalRefund
    myDictionary['difference'] = difference

    context = {'refundOrder': refundOrder, 'refundItems': refundItems, 'myDictionary': myDictionary, 
    'cartItems': cartItems, 'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/admin_process_refund_order.html', context)


@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def updateRefund(request):
    data = json.loads(request.body)
    row_id = data['row_id']
    inputValue = data['inputValue']
    transaction_id = data['transaction_id']
    callBtn = data['callBtn']
    selectedVal = data['selectedVal']
    privateNote = data['privateNote']
    
    refundOrder = Order.objects.get(transaction_id= transaction_id)
    refundItems = refundOrder.orderitem_set.all()
    totalAmt = 0
    totalRefund = 0
    myDictionary = {}
    itemsRefund = []

    try:
        if request.method == 'POST':
            for refundAmt in refundItems:
                totalAmt += refundAmt.line_total
                totalRefund += refundAmt.refundAmt

            if inputValue == 'full_refund':
                for refundItem in refundItems:
                    refundItem.refundAmt = refundItem.line_total
                    refundItem.save()
            elif callBtn == 'max' or callBtn == 'inputVal':
                stringVal = inputValue.replace(',', '')
                floatVal = float (stringVal)
                refundItem = refundOrder.orderitem_set.get(id= row_id)
                refundItem.refundAmt = floatVal
                refundItem.save()
            
            # IF THE SUBMIT REFUND BUTTON IS CLICKED ON, EXECUTE THIS BLOCK OF CODE
            if callBtn == 'Submit Refund' and not refundOrder.reason_for_refund and totalRefund > 0 and refundOrder.paid:
                # CHECKING IF IT'S A FULL REFUND OR PARTIAL REFUND
                if totalRefund == totalAmt:
                    refundOrder.refund_status = 'Full Refund'
                    refundOrder.status = 'Refunded' # CONDITION USED TO DETERMINE WHICH EMAIL TEMPLATE TO LOAD...
                else:
                    refundOrder.refund_status = 'Partial Refund'
                    emailTemp = 'Refunded' # CONDITION USED TO DETERMINE WHICH EMAIL TEMPLATE TO LOAD...
                    
                refundOrder.reason_for_refund = selectedVal
                refundOrder.refund_private_note = privateNote
                refundOrder.save()
                
                try:
                    # SEND AN EMAIL AUTOMATICALLY TO THE CUSTOMER LETING THEM KNOW THAT THEIR REFUND IS UNDER PROCESS
                    template = render_to_string('accounts/email_template_admin_order.html', {
                        'order_status': refundOrder.status, 'cus_name': refundOrder.customer.name,
                        'transaction_id': refundOrder.transaction_id, 'date_order': refundOrder.date_order,
                        'totalRefund': totalRefund, 'emailTemp': emailTemp,
                    })
                    email = EmailMessage(
                        'HAPPY SHOPPERS - Refund under process!',
                        template,
                        conf_settings.EMAIL_HOST_USER,
                        [refundOrder.customer.email,]
                    )
                    fail_silently=False
                    # email.send()
                    myDictionary['success_msg'] = 'Refund submitted successful. Email was sent to customer with the status of refund.'
                except Exception as e:
                    print('EMAIL ERROR:', e.strerror)
                    email_sent_status = 'failed'

                # DISPLAY A TOAST MESSAGE: DATA SUBMITTED SUCCESSFUL
            status = 'successful'
    except Exception as e:
        status = e.args

    return JsonResponse(status, safe=False)
    

def settings(request):
    store_names = Store.objects.all()
    myDictionary = {}
    
    data = cartData(request)
    cartItems = data['cartItems']
    acctMenu = 'acctMenu' # USED TO DISPLAY ACCT MENU ON THE TEMPLATE.
    selectedMenu = 'settings' # USED TO HIGHLIGHT THE SELECTED MENU ON THE TEMPLATE
  
    if request.method == 'GET':
        # CHECK IF EDIT SHIPPING BUTTON WAS CLICKED ON
        if request.GET.get('shippingAddressBtn') == 'Edit':
            cus_addresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
            context = {'cus_addresses': cus_addresses, 'cartItems': cartItems}
            return render(request, 'accounts/settings/shipping_address_overview.html', context)
        
        if request.GET.get('addAnotherAddressBtn') == 'add address':
            

            context = {'store_names': store_names, 'myDictionary': myDictionary}
            return render(request, 'accounts/add_address.html', context)
    elif request.method == 'POST':
        myDictionary["success"] = True
        myDictionary["successmsg"] = "Address saved successfully"
    context = {'store_names': store_names, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList'], 'acctMenu': acctMenu, 'selectedMenu': selectedMenu}
    return render(request, 'accounts/settings/settings.html', context)


def addressOverview(request, data):
    data = cartData(request)
    cartItems = data['cartItems']

    cus_addresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
    myDictionary = {}
    if data == 'True':
        myDictionary["success"] = True
        myDictionary["successmsg"] = "Address saved successfully"
    elif data == 'too much address to add':
        myDictionary["error"] = True
        myDictionary["errorMessage"] = "Shipping address exceed limit!"
    context = {'cus_addresses': cus_addresses, 'myDictionary':myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/settings/shipping_address_overview.html', context)


# USED TO UPDATE DEFAULT CUSTOMER ADDRESS
@unauthenticated_user
def updateOverviewAddress(request):
    data = json.loads(request.body)
    if request.method == 'POST':
        # LOOP THROUGH THE CUSTOMER SHIPPING ADDRESS AND TURN DEFAULT 
        # SHIPPING ADDRESS FALSE
        cusAddresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type=data['addressType'])
        for cusAdd in cusAddresses:
            if cusAdd.default == True:
                cusAdd.default = False
                cusAdd.save()
             
        # UPDATE THE NEW DEFAULT ADDRESS
        cusAddress = CustomerAddress.objects.get(id=data['addressId'])
        cusAddress.default = True
        cusAddress.save()
    return JsonResponse('record received', safe=False)


@unauthenticated_user
def updateSetting(request):
    data = json.loads(request.body)
    store_id = data['store_id']
    flexSwitchBox = data['flexSwitchBox']
    store_obj = Store.objects.get(id=store_id)
    verify = store_obj.verified
    success_msg = ''
    # FLEX SWITCH BOX IS ONLY EMPTY WHEN A USER SELECT A STORE. FOR EVERY STORE SELECTED,
    # THE SYSTEM CHECK THE DATABASE IF THE STORE HAVE BEEN VERIFIED IN ORDER TO SWITCH THE CHECK BOX ON
    # THIS CONDITION ONLY EXECUTE WHEN THE UPDATE BUTTON IS CLICKED ON
    if flexSwitchBox != '':
        store_obj.verified = flexSwitchBox
        store_obj.save()
        success_msg = 'Record updated'
    return JsonResponse({'verify': verify, 'success_msg': success_msg, }, safe=False)


@unauthenticated_user
# @allowed_users(allowed_roles=['Admin group'])
def adminSetting(request):
    data = cartData(request)
    cartItems = data['cartItems']

    store_names = Store.objects.all()
    myDictionary = {}
    

    context = {'store_names': store_names, 'myDictionary': myDictionary, 'cartItems': cartItems,
    'categoryDropdownList': data['categoryList']}
    return render(request, 'accounts/settings/settings_adminSetting.html', context)


# FOR NOW, NO ACTION ON THIS TEMPLATE YET
def generalSetting(request):

    context = {}

    return render(request, 'accounts/settings/general_setting.html', context)