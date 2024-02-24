from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
# THIS IS USED TO RENDER OUT TEMPLATE AND SEND IT AS A STRING TO THE BODY OF THE EMAIL
from django.template.loader import render_to_string 
from .filters import OrderFilter
import uuid
from django.core.paginator import Paginator
from homePage . models import *
from homePage .forms import PaymentForm
from homePage.utils import productRecord
# from homePage . utils import cookiesCart, cartData, guestOrder
from . utils import cookiesCart, cartData, guestOrder, weightAverageRating, manageRecentViewItm, updateInputItemRow
from time import gmtime, strftime

from pypaystack import Transaction, Customer, Plan
import requests
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
# Create your views here.




def eShopAmuwo(request):

    data = cartData(request)
    cartItems = data['cartItems']
    all_active_ptd = []
    wishLists = ''
    products = Product.objects.filter(active=True, store__active__contains=1)
    categories = Category.objects.all()
    
    # UPDATE NEW PRICE FIELD IF THERE IS DISCOUNT ON THE PRODUCT
    for product in products:
        if product.discount > 0:
            product.new_price = product.get_unit_price
            product.save()
        else:
            product.new_price = 0
            product.save()
    
    myFilter = OrderFilter(request.GET, queryset=products)
    products = myFilter.qs
    if request.user.is_authenticated:
        wishLists = WishList.objects.filter(customer_id=request.user.customer.id)
    # FUNCTION CALL IS USED TO CUSTOMIZE PTD RECORD BY ADDING FAVORITE & AVERAGE STAR WEIGHT RATING FOR EACH PTD
    products = productRecord(request, products, wishLists)

    paginator_filtered_product = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator_filtered_product.get_page(page_number)


    # CHECK IF CATEGORY WAS SELECTED. IF SELECTED, REDIRECT TO CATEGORY SHOP METHOD
    if request.GET.get('name') == '' and int(request.GET.get('category')) > 0:
        return redirect('amuwoCategoryShop', int(request.GET.get('category')))

              
    context = {'products': products, 'cartItems':cartItems, 'myFilter': myFilter, 'categories': categories}

    return render(request, 'eShopperAmuwo/amuwo_store.html', context)


def amuwoCategoryShop(request, pk):

    data = cartData(request)
    cartItems = data['cartItems']
    categories = Category.objects.all()
    category = Category.objects.get(id=pk)
    categoryProducts = Product.objects.filter(category_id= pk)
    categoryParentPtds = Product.objects.filter(category_id= category.parent_id)
    categoryLevelPtds = Product.objects.filter(category_id__level__contains= category.level)
    for categoryProduct in categoryLevelPtds:
        print(categoryProduct)
    paginator_filtered_product = Paginator(categoryProducts, 6)
    page_number = request.GET.get('page')
    categoryProducts = paginator_filtered_product.get_page(page_number)

    context = {'categories': categories, 'category': category, 'categoryProducts': categoryProducts, 'cartItems': cartItems}
    return render(request, 'eShopperAmuwo/amuwo_category_shop.html', context)


def cartAmuwo(request):

    # THIS POST METHOD HANDLE THE FOLLOWING:
    # 1. WHEN THE USER WANT TO DELETE A SAVED ITEM ON THE CART PAGE
    if request.method == 'POST':
        jsonData = json.loads(request.body)
        call = jsonData['call']
        ptdId = jsonData['ptdId']
        val = jsonData['val']
        # IF BLOCK TO DELETE SAVED ITEM. THIS REQUEST IS COMING FROM THE CART PAGE
        if call == 'deleteSaveItm':
            WishList.objects.get(product_id= ptdId, customer_id= request.user.customer.id).delete()
            return JsonResponse('success', safe=False)
        # THIS BLOCK IS USED TO UPDATE INPUTTED QUANTITY OF ITEM ON THE CART ROW  
        elif call == 'updateInputItmRow':
            updateInputItemRow(request, ptdId, int (val))
            return JsonResponse('success', safe=False)
        # THIS BLOCK IS USED TO DELETE CART ITEM ROW 
        elif call == 'delCartRow':
            updateInputItemRow(request, ptdId, int (val))
            return JsonResponse('success', safe=False)

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    isOut_of_stock = data['isOut_of_stock']
    inactive_ptd = data['inactive_ptd']
    wishLists = data['wishLists']
    recentViewList = data['recentViewList']

    context = {'items': items, 'order': order, 'cartItems':cartItems, 'isOut_of_stock': isOut_of_stock, 
    'inactive_ptd': inactive_ptd, 'wishLists': wishLists, 'recentViewList': recentViewList,
    'categoryDropdownList': data['categoryList'],}
    return render(request, 'eShopperAmuwo/amuwo_cart.html', context)


def checkoutAmuwo(request):
    
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    shippingAddress = data['shippingAddress']
    allShippingAddresses = data['allShippingAddresses']
    ref = str(uuid.uuid4().time_low)   # USED AS REFERENCE FOR PAYSTACK PAYMENT

    context = {'items': items, 'order': order, 'cartItems':cartItems, 'shippingAddress': shippingAddress, 
    'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY, 'ref': ref, 'allShippingAddresses': allShippingAddresses,
    'categoryDropdownList': data['categoryList'],}
    return render(request, 'eShopperAmuwo/amuwo_checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('Action:', action)
    print('productId:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
        orderItem.store_name = (product.store.store_name)
        orderItem.unit_price = (orderItem.get_unit_price)
        orderItem.line_total = (orderItem.get_total)
       
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
        orderItem.unit_price = (orderItem.get_unit_price)
        orderItem.line_total = (orderItem.get_total)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    print('Data:', request.body)
    # transaction_id = datetime.datetime.now().timestamp()
    transaction_id = str(uuid.uuid4().time_low)[:6]
    data = json.loads(request.body)
    itemList = ''
    payStackReference = data['payStackReference']
    payStackAmount = data['amt'] / 100  # I AM DIVIDING BY 100 BECAUSE IT'S COMING FROM PAYSTACK
    status = data['status']
    payment_option = data['selectedValue']

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # FOR THE LAST TIME, I WANT TO CONFIRM IF ALL THE ITEM(S) IN THE CART IS ACTIVE AND IN STOCK
        if order:
            orderItems = order.orderitem_set.all().order_by('store_name')   # ITEMS WERE ORDERED BY STORE NAME SO THAT EMAILS CAN BE SENT TO STORE OWN TO MAKE ORDERD ITEM AVALIABLE
            
            # I HAVE DECIDED TO SKIP THE PROCESS OF CHECKING IF PRODUCT IS ACTIVE, OUT_OF_STOCK OR ACTIVE STORE FOR PAYMENT
            # OPTION WITH "CARD PAYMENT". THE REASON IS
            # BECAUSE IF PAYMENT HAVE BEEN RECIEVED AND RECORD WAS NOT CREATED ON THE DATABASE CREATING ANOTHER RECORD
            # ON THE DB WILL BE INPOSSIBLE TO RECONSILE AS THE AMOUNT OF ITEM PURCHASE WILL NOT TALLY WITH WHAT WAS INITIALLY PAID 
            # AND THERE IS NO WAY THE INITIAL PAYMENT CAN BE TIE TO THE NEW ITEMS PURCHASED 
            if payment_option != 'Card Payment':
                for item in orderItems:
                    if item.product.active == False or item.product.out_of_stock == True or item.product.store.active == False:
                        print('All item(s) not valid...!')
                        return JsonResponse('item(s) not valid', safe=False)
            itemList = orderItems
    else:

        customer, order, invalidItm, guestOrderData = guestOrder(request, data, payment_option)
        itemList = guestOrderData['guest_items']

        if invalidItm['invalid_item'] == True:
            return JsonResponse('item(s) not valid', safe=False)
    form_total = data['form']['total']
    # WE ARE REMOVING THE COMMAS BECAUSE CONVERTING TO FLOAT WILL GIVE AN ERROR
    string_figure = form_total.replace(',', '')
    total = float(string_figure)
    order.transaction_id = transaction_id

    # GET THE PAYMENT OPTION AND PROCESS
    if payment_option == 'Card Payment':
        
        
        # =========== CREATE THE PAYMENT RECORD ON THE DB TABLE =================
        Payment.objects.create(
            amount= total,
            ref= payStackReference,
            email= customer.email,
            status= status,
        )

        # ========== CALL THIS FUNCTION TO VERIFY PAYMENT FROM PAYSTACK... ==========
        status, result = verify_payment(request, payStackReference)
        # I NEED TO ADD MORE INFO OF PAYMENT MADE FROM PAYSTACK INTO OUR PAYMENT TABLE
        payment = Payment.objects.get(ref= payStackReference)

        payment.channel = result['channel']
        payment.card_type = result['authorization']['card_type']
        payment.bank= result['authorization']['bank']

        if status:
            order.paid = True
            order.status = 'Processing'
        else:
            order.paid = False
            order.status = 'On hold'
            payment.message = result['message']

        payment.save()

        order.paymentReference = payStackReference

    elif payment_option == 'Pay on Delivery':
        order.status = 'On hold'

    
    order.payment_option = payment_option

    if total == float(order.get_cart_total):
        order.complete = True
    
    else:
        order.status = 'On hold'
    # order.date_order = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    order.date_order = datetime.datetime.now()
    order.save()

    # CREATE THE SHIPPING INFORMATION IN THE DATABASE
    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address_type='Shipping Address',
        name=data['shipping']['name'],
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        state=data['shipping']['state'],
        mobile=data['shipping']['mobile'],
        altMobile=data['shipping']['alt_mobile'],
        optional_note=data['shipping']['optional_note'],
    ) 

    # TRY AND SEND AN EMAIL TO THE CUSTOMER TO CONFIRM THE ORDER THAT HAVE BEEN CREATED
    # try:
    #     if request.user.is_authenticated:
    #         template = render_to_string('eShopperAmuwo/email_template.html', 
    #         {'user': 'registered_acct', 'name': request.user.customer.name, 'order_no': str(order.transaction_id), 'order_items': orderItems, 'total': order.get_cart_total}
    #         )

    #         email = EmailMessage(
    #             'Your Purchased Order...!',
    #             template,
    #             settings.EMAIL_HOST_USER,
    #             [request.user.customer.email,]
    #         )
    #         fail_silently=False
    #         email.send()
    #     else:
    #         template = render_to_string('eShopperAmuwo/email_template.html', 
    #         {'user': 'guest', 'name': guestOrderData['guest_name'], 'order_no': str(order.transaction_id), 'order_items': guestOrderData['guest_items'], 'total': order.get_cart_total}
    #         )

    #         email = EmailMessage(
    #             'Your Purchased Order...!',
    #             template,
    #             settings.EMAIL_HOST_USER,
    #             [guestOrderData['guest_email'],]
                
    #         )
    #         fail_silently=False
    #         email.send()
    # except Exception as e:
    #     # IF E-MAIL FAIL, ALERT THE USER OF FAILED E-MAIL & SHOULD MAKE A COMPLAIN TO CS BUT COMPLETE THE ORDER PROCESS
    #     # ON THE CUSTOMER SERVICE, THEY SHOULD BE ABLE TO PROVIDE THEIR E-MAIL AND PHONE No USED FOR THE ORDER
    #     # THIS SERVICES SHOULD BE AVAILABLE TO BOTH GUEST AND REGISTERED USER
    #     pass

    # # SEND AN EMAIL TO ADMIN WITH A MORE DETAIL INFO OF ITEMS AND STORE LOCATION FOR PICKUP.
    # try:
    #     template = render_to_string('eShopperAmuwo/email_template.html', {
    #         'name': 'Admin', 'transaction_id': str(order.transaction_id), 
    #         'date_order': order.date_order, 'order_items': itemList, 
    #         'total': order.get_cart_total, 'user': 'admin',
    #     })

    #     email = EmailMessage(
    #         'Purchased Order',
    #         template,
    #         settings.EMAIL_HOST_USER,
    #         ['don4life247@gmail.com',]
    #     )
    #     fail_silently=False
    #     email.send()
    # except Exception as e:
    #     # e.strerror
    #     pass

    # # ALSO SEND AN EMAIL TO STORE OWERS WHERE ITEM(S) WHERE PURCHASE TO MAKE THE ITEM(S) AVALIABLE FOR DELIVERY
    
    # sortedList = []
    # storeName = ''
    # grand_total = 0
    # for itmList in itemList:
    #     if storeName == '':
            
    #         itemObj = {
    #             'ptd_name': itmList.product.name,
    #             'store_name': itmList.product.store.store_name,
    #             'store_location': itmList.product.store.store_address,
    #             'store_city': itmList.product.store.city,
    #             'storeLGA': itmList.product.store.LGA,
    #             'store_state': itmList.product.store.state,
    #             'ptd_quantity': itmList.quantity,
    #             'unit_price': itmList.unit_price,
    #             'line_total': itmList.line_total,
    #         }
    #         sortedList.append(itemObj)
    #         storeName = itmList.product.store.store_name
    #         trader_name = itmList.product.store.user_id.username
    #         grand_total += itmList.line_total
    #         trader_email = itmList.product.store.email
    #     elif storeName == itmList.product.store.store_name:
    #         itemObj = {
    #             'ptd_name': itmList.product.name,
    #             'store_name': itmList.product.store.store_name,
    #             'store_location': itmList.product.store.store_address,
    #             'store_city': itmList.product.store.city,
    #             'storeLGA': itmList.product.store.LGA,
    #             'store_state': itmList.product.store.state,
    #             'ptd_quantity': itmList.quantity,
    #             'unit_price': itmList.unit_price,
    #             'line_total': itmList.line_total,
    #         }
    #         sortedList.append(itemObj)
    #         storeName = itmList.product.store.store_name
    #         trader_name = itmList.product.store.user_id.username
    #         grand_total += itmList.line_total
    #         trader_email = itmList.product.store.email
    #     else:
    #         # SEND AN EMAIL TO THE STORE OWNER
    #         # CLEAR THE LIST, CREATE THE NEW OBJECT, APPEND TO THE LIST AND ASSIGN THE STORE NAME

    #         try:
    #             template = render_to_string('eShopperAmuwo/email_template.html', {
    #                 'name': trader_name, 'transaction_id': str(order.transaction_id), 
    #                 'date_order': order.date_order, 'sortedList': sortedList, 
    #                 'total': grand_total, 'user': 'traderStore',
    #             })

    #             email = EmailMessage(
    #                 'Purchased Order',
    #                 template,
    #                 settings.EMAIL_HOST_USER,
    #                 [trader_email,]
    #             )
    #             fail_silently=False
    #             email.send()
    #         except Exception as e:
    #             # e.strerror
    #             pass
    #         sortedList = []
    #         grand_total = 0
    #         itemObj = {
    #             'ptd_name': itmList.product.name,
    #             'store_name': itmList.product.store.store_name,
    #             'store_location': itmList.product.store.store_address,
    #             'store_city': itmList.product.store.city,
    #             'storeLGA': itmList.product.store.LGA,
    #             'store_state': itmList.product.store.state,
    #             'ptd_quantity': itmList.quantity,
    #             'unit_price': itmList.unit_price,
    #             'line_total': itmList.line_total,
    #         }
    #         sortedList.append(itemObj)
    #         storeName = itmList.product.store.store_name
    #         trader_name = itmList.product.store.user_id.username
    #         grand_total += itmList.line_total
    #         trader_email = itmList.product.store.email
    # if sortedList:
    #     try:
    #         template = render_to_string('eShopperAmuwo/email_template.html', {
    #             'name': trader_name, 'transaction_id': str(order.transaction_id), 
    #             'date_order': order.date_order, 'sortedList': sortedList, 
    #             'total': grand_total, 'user': 'traderStore',
    #         })

    #         email = EmailMessage(
    #             'Purchased Order',
    #             template,
    #             settings.EMAIL_HOST_USER,
    #             [trader_email,]
    #         )
    #         fail_silently=False
    #         email.send()
    #     except Exception as e:
    #         pass

    return JsonResponse('Payment complete', safe=False)



def productDetail(request, id):
    data = cartData(request)
    cartItems = data['cartItems']
    product = Product.objects.get(id=id)
    video_item = product.video_item_set.all()
    same_ptd_category = []
    same_category_products = []
    myDictionary = {}
    count = 0
    isSame_category_product = False
    isHeartFill = False
    isSamePtdRecentViewItem = False

    # THIS FUNCTION CALL IS USED TO MANAGE RECENTLY VIEWED ITEM ON HOW IT 
    # IS BEEN CREATED AND DELETED IF IT IS MORE THAN THE MAXIMUM NUMBER REQUIRED 
    if request.user.is_authenticated:
        manageRecentViewItm(request, product)
        

    # BLOCK OF CODE TO ADD WISHLIST ITEM TO DATABASE
    wishList_btn = request.POST.get('wishList.x')
    if wishList_btn: 
        if request.user.is_authenticated:
            created = WishList.objects.get_or_create(
                product=product, customer=request.user.customer, store_id=product.store.id
            )

        else:
            myDictionary['warning'] = True
            myDictionary['warningMsg'] = 'Guest user cannot add item to wish list'
    
    # BLOCK OF CODE TO REMOVE WISHLIST ITEM FROM DATABASE
    heartFill_wishList_btn = request.POST.get('heartFill.x')
    if heartFill_wishList_btn:
        if request.user.is_authenticated:
            wishListItem = WishList.objects.get(product_id=id, customer_id=request.user.customer.id).delete()
            

    # USED TO CHECK IF ITEM EXIST IN THE WISHLIST TABLE TO KNOW IF HEART FILL OR HEART SHALLOW BE USED IN TEMPLATE
    if request.user.is_authenticated:
        wishListItem = WishList.objects.filter(product_id=id, customer_id=request.user.customer.id)
        if wishListItem:
            isHeartFill = True

    if product.category_id != None:
        # FILTER ACTIVE PRODUCT FROM THE SAME CATEGORY
        same_category_products = Product.objects.filter(category_id=product.category_id, active=True)
        for same_category_product in same_category_products:
            
            # FILTER PRODUCTS FROM ACTIVE STORIES
            if same_category_product.store.active == True:
                if same_category_product.category:
                    # TO GET THE WEIGHT AVERAGE RATING OF EACH PRODUCT, FILTER EACH PRODUCT FROM COMMENT TABLE.
                    # CALL A METHOD TO COMPUTE THE CALCULATION AND RETURN THE VALUE
                    ptd_comment = Comment.objects.filter(product=same_category_product.id)
                    averageStarRated = weightAverageRating(request, ptd_comment)

                    new_unit_price = (same_category_product.price - ((same_category_product.price / 100) * same_category_product.discount))
                    full_active_ptd = {
                        'id': same_category_product.id,
                        'name': same_category_product.name,
                        'description': same_category_product.description,
                        'category': same_category_product.category,
                        'brand': same_category_product.brand,
                        'price': same_category_product.price,
                        'new_unit_price': new_unit_price,
                        'imageURL': same_category_product.imageURL,
                        'mfgDate': same_category_product.mfgDate,
                        'expDate': same_category_product.expDate,
                        'discount': same_category_product.discount,
                        'out_of_stock': same_category_product.out_of_stock,
                        'store': same_category_product.store,
                        'active': same_category_product.active,
                        'averageStarRated': averageStarRated['weighted_average_rating'],
                        'counter': averageStarRated['counter']
                    }
                    same_ptd_category.append(full_active_ptd)
                    count += 1

        if count > 1:
            isSame_category_product = True
            
    # FILTER COMMENT ONLY FOR THE PRODUCT DETAIL, LOOP TO GET THE FIRST THREE COMMENTS. 
    # SINCE THIS IS WHAT WE WANT TO DISPLAY FIRST
    comments = Comment.objects.filter(product=product).order_by('-created_at')
    counter = 0
    five_star = 0
    four_half_star = 0
    four_star = 0
    three_half_star = 0
    three_star = 0
    two_half_star = 0
    two_star = 0
    one_half_star = 0
    one_star = 0
    isCusReview = False
   
    customLatestFewComments = []
    for comment in comments:
        counter += 1
        if comment.rate == 5:
            five_star += comment.rate
        elif comment.rate == 4.5:
            four_half_star += comment.rate
        elif comment.rate == 4:
            four_star += comment.rate
        elif comment.rate == 3.5:
            three_half_star += comment.rate
        elif comment.rate == 3:
            three_star += comment.rate
        elif comment.rate == 2.5:
            two_half_star += comment.rate
        elif comment.rate == 2:
            two_star += comment.rate
        elif comment.rate == 1.5:
            one_half_star += comment.rate
        else:
            one_star += comment.rate
        
        # USE TO BUILD THE FIRST THREE COMMENTS ON THE DETAIL PAGE
        if counter < 4:
            customComment = {
            'product': comment.product,
            'customer': comment.customer,
            'subject': comment.subject,
            'comment': comment.comment,
            'rate': comment.rate,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at
        }
            customLatestFewComments.append(customComment)

    if comments:

        # SUM THE TOTAL NUMBER OF RATING FROM ONE TO FIVE SEPERATLY
        total_five_star = five_star
        total_four_star = four_half_star + four_star
        total_three_star = three_half_star + three_star
        total_two_star = two_half_star + two_star
        total_one_star = one_half_star + one_star

        # TOTAL STAR 
        total_star = total_five_star + total_four_star + total_three_star + total_two_star + total_one_star

        # PERCENTAGE STAR FROM ONE TO FIVE
        five_star_percent = (total_five_star / total_star) * 100
        four_star_percent = (total_four_star / total_star) * 100
        three_star_percent = (total_three_star / total_star) * 100
        two_star_percent = (total_two_star / total_star) * 100
        one_star_percent = (total_one_star / total_star) * 100

        
        # Calculate weighted average for each product
        weighted_average_rating = (((5 * five_star) + (4.5 * four_half_star) + (4 * four_star) + (3.5 * three_half_star) + (3 * three_star) + (2.5 * two_half_star) + (2 * two_star) + (1.5 * one_half_star) + (1 * one_star)) / (five_star + four_half_star + four_star + three_half_star + three_star + two_half_star + two_star + one_half_star + one_star))
        #  USED TO CHECK IF THERE IS NO CUSTOMER REVIEW
        isCusReview = True
        
        myDictionary['five_star_percent'] = five_star_percent
        myDictionary['four_star_percent'] = four_star_percent
        myDictionary['three_star_percent'] = three_star_percent
        myDictionary['two_star_percent'] = two_star_percent
        myDictionary['one_star_percent'] = one_star_percent
        myDictionary['weighted_average_rating'] = weighted_average_rating
    myDictionary['counter'] = counter
    myDictionary['isCusReview'] = isCusReview
    myDictionary['customLatestFewComments'] = customLatestFewComments
    myDictionary['isSame_category_product'] = isSame_category_product
    myDictionary['isHeartFill'] = isHeartFill
    
    context = {'product': product, 'cartItems': cartItems, 'same_category_products': same_ptd_category,
    'comments':comments, 'myDictionary': myDictionary, 'video_item': video_item, 
    'categoryDropdownList': data['categoryList'],
    }
    return render (request, 'eShopperAmuwo/amuwo_product_detail.html', context)


def customerProductReviews(request, id):
    
    data = cartData(request)
    cartItems = data['cartItems']
    
    product = Product.objects.get(id=id)
    comments = Comment.objects.filter(product=product).order_by('-created_at')
    positive_comments = Comment.objects.filter(product=product, rate__gte = 4).order_by('-created_at')
    critical_comments = Comment.objects.filter(product=product, rate__lte = 3).order_by('-created_at')

    counter = 0
    five_star = 0
    four_half_star = 0
    four_star = 0
    three_half_star = 0
    three_star = 0
    two_half_star = 0
    two_star = 0
    one_half_star = 0
    one_star = 0
    myDictionary = {}
    for comment in comments:
        counter += 1
        if comment.rate == 5:
            five_star += comment.rate
        elif comment.rate == 4.5:
            four_half_star += comment.rate
        elif comment.rate == 4:
            four_star += comment.rate
        elif comment.rate == 3.5:
            three_half_star += comment.rate
        elif comment.rate == 3:
            three_star += comment.rate
        elif comment.rate == 2.5:
            two_half_star += comment.rate
        elif comment.rate == 2:
            two_star += comment.rate
        elif comment.rate == 1.5:
            one_half_star += comment.rate
        else:
            one_star += comment.rate
    
    # SUM THE TOTAL NUMBER OF RATING FROM ONE TO FIVE SEPERATLY
    total_five_star = five_star
    total_four_star = four_half_star + four_star
    total_three_star = three_half_star + three_star
    total_two_star = two_half_star + two_star
    total_one_star = one_half_star + one_star

    # TOTAL STAR 
    total_star = total_five_star + total_four_star + total_three_star + total_two_star + total_one_star

    # PERCENTAGE STAR FROM ONE TO FIVE
    five_star_percent = (total_five_star / total_star) * 100
    four_star_percent = (total_four_star / total_star) * 100
    three_star_percent = (total_three_star / total_star) * 100
    two_star_percent = (total_two_star / total_star) * 100
    one_star_percent = (total_one_star / total_star) * 100


    # Calculate weighted average for each product
    weighted_average_rating = (((5 * five_star) + (4.5 * four_half_star) + (4 * four_star) + (3.5 * three_half_star) + (3 * three_star) + (2.5 * two_half_star) + (2 * two_star) + (1.5 * one_half_star) + (1 * one_star)) / (five_star + four_half_star + four_star + three_half_star + three_star + two_half_star + two_star + one_half_star + one_star))
       
    # SINCE POSITIVE RESPONSE WITH 4 or 5 STARS WILL BE MORE THAN ONE, LET GET JUST 1 OF THE MOST RECENT 5 STAR
    recent_positive_comment = []
    # USED TO CHECK IF THERE IS ANY POSITIVE RESPONSE

    # SINCE CRITICAL RESPONSE WITH 3 or LESS STARS WILL BE MORE THAN ONE, LET GET JUST 1 OF THE MOST RECENT 3 STAR
    recent_critic_comment = []
    # USED TO CHECK IF THERE IS ANY CRITICAL RESPONSE
    isCritical_comment = False

    # LOGIC TO GET JUST ONE MOST RECENT POSITIVE COMMENT
    isPositive_comment = False
    if positive_comments:
        isPositive_comment = True
        count = 0
        for positive_comment in positive_comments:
            count += 1
            ptve_comment = {
            'product': positive_comment.product,
            'customer': positive_comment.customer,
            'subject': positive_comment.subject,
            'comment': positive_comment.comment,
            'rate': positive_comment.rate,
            'created_at': positive_comment.created_at,
            'updated_at': positive_comment.updated_at
            }
            if count == 1:
                recent_positive_comment.append(ptve_comment)
            if count > 1:
                for rpc in recent_positive_comment:
                    if positive_comment.rate > rpc['rate']:
                        recent_positive_comment.clear()
                        recent_positive_comment.append(ptve_comment)

    # LOGIC TO GET JUST ONE MOST RECENT CRITICAL COMMENT
    if critical_comments:
        isCritical_comment = True
        count = 0
        for critical_comment in critical_comments:
            count += 1
            critic_comment = {
            'product': critical_comment.product,
            'customer': critical_comment.customer,
            'subject': critical_comment.subject,
            'comment': critical_comment.comment,
            'rate': critical_comment.rate,
            'created_at': critical_comment.created_at,
            'updated_at': critical_comment.updated_at
            }
            if count == 1:
                recent_critic_comment.append(critic_comment)
            if count > 1:
                for rcc in recent_critic_comment:
                    if critical_comment.rate > rcc['rate']:
                        recent_critic_comment.clear()
                        recent_critic_comment.append(critic_comment)
                        
    # LOGIC TO DISPLAY ALL POSITIVE COMMENTS
    isAll_positive_comment = False
   
    if request.GET.get("all-positive-comment") == "yes":
        isAll_positive_comment = True

    # LOGIC TO DISPLAY ALL CRITICAL COMMENTS
    isAll_critical_comment = False
    if request.GET.get("all-critical-comment") == "yes":
        isAll_critical_comment = True

    # LOGIC TO CANCEL ALL POSITIVE/CRITICAL COMMENTS
    if request.GET.get("cancel-filter") == "yes":
        isAll_positive_comment = False
        isAll_critical_comment = False

    myDictionary['five_star_percent'] = five_star_percent
    myDictionary['four_star_percent'] = four_star_percent
    myDictionary['three_star_percent'] = three_star_percent
    myDictionary['two_star_percent'] = two_star_percent
    myDictionary['one_star_percent'] = one_star_percent
    myDictionary['weighted_average_rating'] = weighted_average_rating
    myDictionary['counter'] = counter
    myDictionary['positive_comment'] = recent_positive_comment
    myDictionary['isPositive_comment'] = isPositive_comment
    myDictionary['critical_comment'] = recent_critic_comment
    myDictionary['isCritical_comment'] = isCritical_comment
    myDictionary['isAll_positive_comment'] = isAll_positive_comment
    myDictionary['positive_comments'] = positive_comments
    myDictionary['critical_comments'] = critical_comments
    myDictionary['isAll_critical_comment'] = isAll_critical_comment

    context = {'product': product, 'cartItems': cartItems, 'comments':comments, 'myDictionary': myDictionary}
    return render(request, 'eShopperAmuwo/all_cus_product_reviews.html', context)


# def initiate_payment(request: HttpRequest) -> HttpResponse:
#     if request.method == 'POST':
#         payment_form = PaymentForm(request.POST)
#         if payment_form.is_valid():
#             payment = payment_form.save()
#             return render(request, 'eShopperAmuwo/make_payment.html', {'payment': payment, 'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY})
#     else:
#         payment_form = PaymentForm()
#         context = {'payment_form': payment_form}
#     return render(request, 'eShopperAmuwo/initiate_payment.html', context)



def verify_payment(request: HttpRequest, ref: str):
    payment = Payment.objects.get(ref=ref)
    status, result = payment.verify_payment()
    # if verified:
    #     messages.success(request, "Verification successful")
    # else:
    #     messages.error(request, "Verification Failed")
    return status, result



# def verify_payment(request: HttpRequest, ref: str) -> HttpResponse:
#     payment = get_object_or_404(Payment, ref=ref)
#     verified = payment.verify_payment()
#     if verified:
#         messages.success(request, "Verification successful")
#     else:
#         messages.error(request, "Verification Failed")
#     return redirect('initiate-payment')