from rest_framework.decorators import api_view, permission_classes
from homePage.api.serializers import *
from homePage.models import Product, Payment, WishList, Customer, ProductReview, CustomerAddress

from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from rest_framework.permissions import IsAuthenticated
from . api_utils import *
import datetime
from datetime import timedelta
from decimal import Decimal
from django.http import HttpRequest
from django.db.models import Q
import os
import uuid
from eShopperAmuwo.utils import manageRecentViewItm, getRecentlyViewItem
from decouple import config


@api_view(['POST'])
def api_homePage(request):
    homePageData = {}
    cartCounter = 0
    if request.method == 'POST':
       
        generalData = publicRequest(request)
        if request.user.is_authenticated:
            try:
                order = Order.objects.get(customer=request.user.customer.id, complete=False)
                cartCounter = order.get_cart_items
            except Order.DoesNotExist:
                serializer = OrderSerializer(data=request.data)
                print(request.data)
                if serializer.is_valid():
                    print('order')
                    order = serializer.save()
                
            
            # cartCounter = order.get_cart_items
            # WE WANT TO GET THE RECENTLY VIEWED ITEM AND WATCHED LIST 
            authUserData = authHomepageData(request)
            homePageData['authUserData'] = authUserData
            homePageData['cartCounter'] = cartCounter
        
        homePageData['generalData'] = generalData
    
    return JsonResponse(homePageData, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_allRecentView(request):
    recordList = []
    data = {}
    status = 'fail'
    errorMsg = ''
    try:
        recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer)
        if request.data['call'] == 'viewAll':
            for recentViewItem in recentViewItems:
                record = {
                    'id': recentViewItem.product.id,
                    'name': recentViewItem.product.name,
                    'imageURL': config('URL_ENDPOINT')+recentViewItem.product.imageURL,
                    'price': recentViewItem.product.price,
                    'discount': recentViewItem.product.discount,
                    'new_price': recentViewItem.product.get_unit_price,
                    'category': recentViewItem.product.category.category
                }
                recordList.append(record)
        elif request.data['call'] == 'deleteAll':
            recentViewItems.delete()
        status = 'success'
    except Exception as e:
        errorMsg = e.args
        status = 'fail'

    data = {'allRecentViewList': recordList, 'status': status, 'errorMsg': errorMsg}
    return JsonResponse(data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_allSellerItems(request):
    ptd_data = []
    cartCounter = 0
    status = 'fail'
    errorMsg = ''
    try:
        order = Order.objects.get(customer=request.user.customer.id, complete=False)
        cartCounter = order.get_cart_items

        oneStoreItems = Product.objects.filter(store_id= request.data['storeId'], active=True, store__active__contains=1)
        wishLists = WishList.objects.filter(customer_id=request.user.customer.id)
        ptd_data = customisePtdRecord(request, oneStoreItems, wishLists)
        status = 'success'
    except Exception as e:
        errorMsg = e.args
        status = 'fail'

    return JsonResponse({'ptd_data': ptd_data, 'cartCounter': cartCounter,
    'status': status, 'errorMsg': errorMsg}, safe=False)


@api_view(['POST'])
def api_registration(request):
    if request.method == 'POST':
        
        serializer = CreateUserForm(data=request.data)
        data = {}

        if serializer.is_valid():
            print("SERIALIZED")
            account = serializer.save()
            user_info = User.objects.filter(username=account.username)
            data = 'Account was successfully registered'
            for use in user_info:
                userData = {
                    'user': {
                        'id': use.id,
                        'email': use.email
                    },
                    'name': account.username,
                    'email': account.email,

                }
                serializer_customer = CustomCustomerSerializer(data=userData)
                if serializer_customer.is_valid():
                    serializer_customer.save()
                    print("serial customer:", serializer_customer.data)
                    data = 'Account was successfully registered'
                else:
                    data = serializer_customer.errors
            else:
                data = {}
        else:
            data = serializer.errors

        return JsonResponse(data)


@api_view(['POST'])
def api_login(request):
    username = request.data['username']
    password = request.data['password']
    user = authenticate(request, username=username.strip(), password=password)
    data = {}
    if user is not None:
        login(request, user)
        token = Token.objects.get(user=user.id).key

        customer = Customer.objects.get(user_id= user.id)
        
        
        data['user_id'] = user.id
        data['username'] = username.strip()
        data['email'] = user.email
        data['token'] = token
        data["is_staff"] = request.user.is_staff
        data['isSuccessLogin'] = True
        data['customer_id'] = customer.id
        data['custName'] = customer.name
        data['custEmail'] = customer.email
        print('Authenticated')

        return JsonResponse(data)
    else:
        data['isSuccessLogin'] = False
        data['error_msg'] = 'Fail to login. Username and password are case sensitive!'
        return JsonResponse(data)


@api_view(['POST'])
def api_logoutUser(request):
    logout(request)
    return HttpResponse("You've been logged out!")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_changePassword(request):
    data = {}
    try:
        user = User.objects.get(id = request.data.get('userId'))
        form = PasswordChangeForm(data= request.data, user= user)

        if form.is_valid():
            user = form.save()
            # update_session_auth_hash(request.data, user)  # Important! Otherwise the user’s auth session will be invalidated and she/he will have to log in again.
            print('FORM IS VALID')
            data['serverMsg'] = 'Password change successful'
        else:
            
            print('FORM IS INVALID')
            data['serverMsg'] = form.error_messages
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data, safe=False)


# THIS POST REQUEST IS USED TO GET ALL PRODUCTS THAT ARE ACTIVE AND THE 
# STORES THEY RESIDE IN ARE ALSO ACTIVE IN THE DATABASE
@api_view(['POST'])
def api_eShop(request):
    ptd_record = {}
    ptd_data = []
    cartCounter = 0
    status = 'fail'
    errorMsg = ''

    try:
        products = Product.objects.filter(active=True, store__active__contains=1)
        favoriteItems = ''
        print(request.data)
        # FILTER THE WISH LIST RECORD FOR AUTHENTICATED USER AND ADD THEM TO THE PRODUCT REOCRD
        if request.user.is_authenticated:
            user = User.objects.get(username= request.data['user']['name'])
            # print(user.id)
            customer = Customer.objects.get(user_id= user.id)
            favoriteItems = WishList.objects.filter(customer=customer.id)
            ptd_data = customisePtdRecord(request, products, favoriteItems)
        

            # I HAVE DECIDED TO CREATE AN ORDER FOR AUTHENTICATED USER ONCE THE E-STORE IS OPEN
            # IT WILL NOT CREATE AN ORDER FOR A CUSTOMER WHO'S ORDER COMPLETION STATUS IS FLASE
        
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                # CHECK IF CUSTOMER NAME EXIST IN DATABASE
                user_n = User.objects.get(username= user)
                cus_obj = Customer.objects.get(user_id=user_n.id)
                try:
                    order = Order.objects.get(customer=cus_obj.id, complete=False)
                    cartCounter = order.get_cart_items
                except Order.DoesNotExist:
                    order = serializer.save()
            else:
                order = Order.objects.get(customer=customer.id, complete=False)
                cartCounter = order.get_cart_items
                
        else:
            ptd_data = customisePtdRecord(request, products, favoriteItems)
        status = 'success'
    except Exception as e:
        status = 'fail'
        errorMsg = e.args
    
    return JsonResponse({'productData':ptd_data, 'cart_counter': cartCounter,
    'status': status, 'errorMsg': errorMsg}, safe=False)


# THIS POST REQUEST IS USED TO GET CUSTOMER'S ORDER USING ID NUMBER
# AND ORDER STATUS OF COMPLETE TO FALSE. THE ORDER IS THEN USED TO 
# GET THE CHILDREN-ORDERITEM BY CALLING 'getCartItems'.

# WHERE IT WILL BE USED ON THE MOBILE PHONE:
# WHEN A USER CLICK ON THE CART-ICON OR TAP ON ANY OF THE CART LINK TO VIEW
# TO VIEW THEIR OPEN CART ITEMS, THIS FUNCTON WILL HANDLE THE REQUEST
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cartData(request):
    data = {}
    # cart_list = []
    
    serializer = OrderSerializer(data=request.data)

    # GET RECENTLY VIEW ITEMS
    recentViewList = getRecentlyViewItem(request)
    data['recentViewList'] = recentViewList
    
    if serializer.is_valid():
        order = ''
        cus_ = request.data['customer']
        cus_name = cus_['name']
        # CHECK IF CUSTOMER NAME EXIST IN DATABASE
        user = User.objects.get(username= cus_name)
        cus = Customer.objects.get(user_id=user.id)
        
        try:
            order = Order.objects.get(customer=cus.id, complete=False)

        except Order.DoesNotExist:
            order = serializer.save()
        # GET CART DATA FROM THE DATABASE
        data['cartItm'] = getCartItems(order)
    
    # A REQUEST OF SAME CATGORY PRODUCT FROM MODAL BOTTOM SHEET
    # WHEN THE SIMILAR ITEM BUTTON IS CLICKED ON, THIS REQUEST IS CALLED
    elif request.data['call'] == 'catPtdFrmModalBottomSheet':
        limit = 0
        data['sameCatPtdList'] = getSameCategoryPtdList(request, limit)
    return JsonResponse(data, safe=False)


# THIS POST REQUEST IS USED TO GET CUSTOMER'S ORDER USING ID NUMBER
# AND ORDER STATUS OF COMPLETE TO FALSE. JUST IN CASE THE ORDER DOES NOT 
# EXIST, THE FUNCTION CREATE A NEW ORDER, FROM THE CUSTOMER'S REQUEST,
# GET THE PRODUCT ID AND ACTION TO EITHER ADD THE REQUESTED PRODUCT ITEM
# TO THE CART OR REMOVE AN EXISTING ITEM FROM THE CART. IF AN ITEM REMOVED
# FROM THE CART IS LESS THAN OR EQUAL TO ZERO, DELETE THAT ITEM FROM THE CART
# AND GET UPDATED CART LIST BY CALLING 'getCartItems'.

# WHERE WILL THIS BE USEFUL ON THE MOBILE PHONE?
# WHEN THE USER CLICK ON THE ADD OR REMOVE ICON-BUTTON, THIS WILL SEND A
# REQUEST THAT WILL UPDATE THE RECORD ON THE DATABASE AN SEND A RESPONSE DATA
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_updateCartData(request):
    data = {}
    wishListData = []
    
    user = User.objects.get(username = request.data['customer']['name'])
    
    customer = Customer.objects.filter(name= user.customer)
    
    if customer.exists():
        customer = Customer.objects.get(name= user.customer)
        try:
            order = Order.objects.get(customer=customer.id, complete=False)
            
        except Order.DoesNotExist:
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                order = serializer.save()
        if Order:
            product_id = request.data["ptd_id"]
            action = request.data["action"]
            product = Product.objects.get(id=product_id)
            try:
                orderItem = OrderItem.objects.get(order=order, product=product)
            except OrderItem.DoesNotExist:
                orderItem = OrderItem.objects.create(order=order, product=product)
            if action == 'add':
                orderItem.quantity = (orderItem.quantity + 1)
                orderItem.store_name = (product.store.store_name)
                orderItem.unit_price = (orderItem.get_unit_price)
                orderItem.line_total = (orderItem.get_total)

            
            elif action == 'remove':
                orderItem.quantity = (orderItem.quantity - 1)
                orderItem.unit_price = (orderItem.get_unit_price)
                orderItem.line_total = (orderItem.get_total)
            # FOR MOBILE APP ALONE, I HAVE ADDED THE OPTION TO DELETE A ROW OF CART-ITEM
            elif action == 'delete':
                orderItem.delete()

            if action != 'delete':
                orderItem.save()

                if orderItem.quantity <= 0:
                    orderItem.delete()
            # SINCE THE CART-ITEM HAVE BEEN UPDATED, GET UPDATED CART ITEM FROM DB
            data = getCartItems(order)

            # GET ALL CUSTOMER'S WISH-LIST AND COMMENT RELATING TO THOSE PRODUCT
            wishLists = WishList.objects.filter(customer_id= customer.id)
            for wishList in wishLists:
                # GET ALL THE COMMENT RECORD FROM EACH PRODUCT
                # RECORD USED TO DISPLAY STAR & NUMBER OF COMMENT OF WISH-LIST ON THE CART PAGE
                ptdComment = Comment.objects.filter(product= wishList.product.id).order_by('-created_at')
            
                # CALL THE FUNCTION WITH COMMENT RECORD TO PROCESS STAR RATING AND NUMBER OF COMMENT
                averageRating = weightAverageRating(request, ptdComment)
                wishListRecord = {
                    'ptdImage': config('URL_ENDPOINT')+wishList.product.imageURL,
                    'ptdName': wishList.product.name,
                    'ptdPrice': wishList.product.price,
                    'ptdNewPrice': wishList.product.get_unit_price,
                    'mfgData': wishList.product.mfgDate,
                    'expData': wishList.product.expDate,
                    'discount': wishList.product.discount,
                    'isCheck': False,
                    'ptdId': wishList.product.id,
                    'category': wishList.product.category.category,
                    'out_of_stock': wishList.product.out_of_stock,
                    'isActive': wishList.product.active,
                    'averageStarRate': averageRating['myDictionary']['weighted_average_rating'],
                    'commentCount': averageRating['myDictionary']['counter'],
                    'isActiveStore': wishList.product.store.active,
                }
                wishListData.append(wishListRecord)
            
            data['wishListData'] = wishListData
    else:
        data['system message'] = "Customer name does not exist in the system"
    return JsonResponse(data, safe=False)
    
    

# THIS REQUEST IS USED TO GET PRODUCT DETAIL, PRODUCTS OF THE SAME CATEGORY
# AND COMMENT OF THE ITEM DETAIL. THIS STAR RATINGS ON THE COMMENT SECTION
# WAS USED TO COMPUTE WEIGHT-AVERAGE-RATING.

# ON THE MOBILE APP, RESPONSE RECEIVED WAS USED TO DISPLAY RECORD OF THE 
# PRODUCT ON THE DETAIL PAGE
@api_view(['POST'])
def api_get_PtdDetail_SameCategoryPtd(request):
    ptd_categoryData = []
    limit = 15
    customLatest_FewComments = []
    ptdReviewData = []
    isHeartFill = False
    ptdDetailRecord = {}
    data = {}

    # ========== WE ARE GETTING THE PRODUCT DETAIL ================
    ptd_detail = Product.objects.get(id=request.data['ptdId'])
    ptd_comments = Comment.objects.filter(product=ptd_detail.id).order_by('-created_at')
    if (request.data.get('wishList') != 'heartFill' and request.data.get('wishList') != 'heart'):
        average_StarRated = weightAverageRating(request, ptd_comments)
        ptdDetailRecord = {
            'ptdId': ptd_detail.id,
            'ptdName': ptd_detail.name,
            'ptdDescription': ptd_detail.description,
            'imageURL': config('URL_ENDPOINT')+ptd_detail.imageURL,
            'ptdPrice': ptd_detail.price,
            'newPrice': ptd_detail.get_unit_price,
            'discount': ptd_detail.discount,
            'mfgDate': ptd_detail.mfgDate,
            'expDate': ptd_detail.expDate,
            'category': ptd_detail.category.category,
            'out_of_stock': ptd_detail.out_of_stock,
            'active': ptd_detail.active,
            'active_store': ptd_detail.store.active,
            'averageStarRated': average_StarRated['myDictionary']['weighted_average_rating'],
            'counter': average_StarRated['myDictionary']['counter'],
            'percentage star rated': { 'one star percent': average_StarRated['myDictionary']['one_star_percent'],
                'two star percent': average_StarRated['myDictionary']['two_star_percent'],
                'three star percent': average_StarRated['myDictionary']['three_star_percent'],
                'four star percent': average_StarRated['myDictionary']['four_star_percent'],
                'five star percent': average_StarRated['myDictionary']['five_star_percent']
            }
        }
        
        # GET ALL THE PRODUCT WITH THE SAME CATEGORY EXCEPT FOR THE CURRENT PRODUCT DETAIL
        # THE NUMBER OF PRODUCT FROM THE SAME CATEGORY HAVE BEEN SET TO 15
        ptd_categoryData = getSameCategoryPtdList(request, limit)

        # CUSTOMER COMMENT SECTION. THIS ARE THE FIRST LATEST COMMENT FOR THE RELATED PRODUCT DETAIL.
        for recentCusComments in average_StarRated['myDictionary']['customLatest_FewComments']:
            cusLatestFewComment = {
                'customer': recentCusComments['customer'].name,
                'subject': recentCusComments['subject'],
                'comment': recentCusComments['comment'],
                'rate': recentCusComments['rate'],
                'created_at': recentCusComments['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                'updated_at': recentCusComments['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            }
            customLatest_FewComments.append(cusLatestFewComment)
        
        # =========== ALL THE DETAIL PRODUCT REVIEWS ============
        for ptdReview in ptd_comments:
            reviewRecord = {
                'customer': ptdReview.customer.name,
                'subject': ptdReview.subject,
                'comment': ptdReview.comment,
                'rate': ptdReview.rate,
                'created_at': ptdReview.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'updated_at': ptdReview.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            ptdReviewData.append(reviewRecord)

        #  ON THE DETAIL PAGE, TO DISPLAY THE NUMBER OF ITEMS IN THE CART, WE NEED TO GET 
        # THE RECORD FROM THE DATABASE TABLE.
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid() and request.user.is_authenticated:
            order = ''
            cus_ = request.data['customer']
            user_name = cus_['name']
            
            # CHECK IF CUSTOMER NAME EXIST IN DATABASE
            userN = User.objects.get(username= user_name)
            cus_obj = Customer.objects.get(user_id=userN.id)
            
            try:
                order = Order.objects.get(customer=cus_obj.id, complete=False)

            except Order.DoesNotExist:
                order = serializer.save()
            # GET CART DATA FROM THE DATABASE
            data = getCartItems(order)
    elif request.data.get('wishList') == 'heartFill' or request.data.get('wishList') == 'heart':
        
        # BLOCK OF CODE TO ADD OR DELETE WISHLIST ITEM FROM DATABASE
        wishList_btn = request.data['wishList']
        if wishList_btn == 'heartFill' or wishList_btn == 'heart': 
            if request.user.is_authenticated:
                isWshList = WishList.objects.filter(customer=request.user.customer, product=ptd_detail).exists()
                if isWshList == False:
                    WishList.objects.create(
                        product=ptd_detail,
                        customer=request.user.customer,
                        store_id=ptd_detail.store.id,
                    )
                else:
                    WishList.objects.get(product_id=request.data['ptdId'], customer_id=request.user.customer.id).delete()
        # BLOCK OF CODE TO REMOVE WISHLIST ITEM FROM DATABASE
        # elif wishList_btn == 'heart':
        #     if request.user.is_authenticated:
        #         wishListItem = WishList.objects.get(product_id=request.data['ptdId'], customer_id=request.user.customer.id)
        #         print('PASSED!!!')
        #         wishListItem.delete()

    # USED TO CHECK IF ITEM EXIST IN THE WISHLIST TABLE TO KNOW IF HEART FILL OR HEART SHALLOW IS RETURN AS THE RESPONSE
    if request.user.is_authenticated:
        wishListItem = WishList.objects.filter(product_id=request.data['ptdId'], customer_id=request.user.customer.id)
        if wishListItem:
            isHeartFill = True

    # THIS FUNCTION CALL IS USED TO MANAGE RECENTLY VIEWED ITEM ON HOW IT 
    # IS BEEN CREATED AND DELETED IF IT IS MORE THAN THE MAXIMUM NUMBER REQUIRED
    if request.user.is_authenticated:
        manageRecentViewItm(request, ptd_detail)

    return JsonResponse({'ptd_categoryData': ptd_categoryData, 'ptdDetailRecord': ptdDetailRecord, 
    'customLatest_FewComments': customLatest_FewComments, 'ptdReviewData': ptdReviewData, 
    'cartData': data, 'isHeartFill': isHeartFill }, safe=False)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_getShippingAdd(request):
    shippingData = {}
    shipping_addressRecord = {}
    itemData = {}
    data = []
    allShipAddresses = []
    allShipAddresses.append('Select Shipping Address')
    allShipAddressRecord = []

    # WITH THE CUSTOMER INFO GET THE ORDER ITEM WHOSE ORDER COMPLETE IS FALSE 
    # WITH THE ORDER-ITEM RECORD, CALCULATE THE GRAND-TOTAL. 

    # FIRST CHECK THE CUSTOMER ADDRESS TABLE IF ANY ADDRESS WAS SAVED
    # IF NOT, SEARCH FOR THE LAST SHIPPING ADDRESS THE CUSTOMER USED TO MAKE PURCHASE
    # IF THEY'VE MADE PURCHASES BEFORE. 
    
    # IF NO RECORD WAS FOUND, RETURN EMPTY SHIPPING ADDRESS  
    try:
        customerInfo = Customer.objects.get(user__username= request.data['name'])
        order = Order.objects.get(customer=customerInfo.id, complete=False)
        item_data = getCartItems(order)
        itemData = item_data
        data.append(itemData)
       
        isShipAddress = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address', default=True).exists()
        if isShipAddress:
            shipAddress = CustomerAddress.objects.get(customer=request.user.customer.id, address_type='Shipping Address', default=True)
            shipping_addressRecord = {
                    'userName': customerInfo.name,
                    'customerName': shipAddress.name,
                    'address': shipAddress.address,
                    'city': shipAddress.city,
                    'state': shipAddress.state,
                    'zipcode': shipAddress.zipcode,
                    'mobile': shipAddress.mobile,
                    'altMobile': shipAddress.altMobile,
                    'optionalNote': ''
                }
        else:
            shippingAddresses = ShippingAddress.objects.filter (customer= customerInfo.id)
            counter = 0
            for shippingAddress in shippingAddresses:
                if shippingAddress.id > counter:
                    counter = shippingAddress.id
                    shipping_addressRecord = {
                        'userName': shippingAddress.customer.name,
                        'customerName': shippingAddress.customer.full_name,
                        'address': shippingAddress.address,
                        'city': shippingAddress.city,
                        'state': shippingAddress.state,
                        'zipcode': shippingAddress.zipcode,
                        'mobile': shippingAddress.mobile,
                        'altMobile': shippingAddress.altMobile,
                        'optionalNote': shippingAddress.optional_note,
                        
                    }

        #  GET ALL SHIPPING ADDRESS FOR THE CUSTOMER
        allShippingAddresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
        for allShipAddress in allShippingAddresses:
            ship_addressRecord = {
                    'customerName': allShipAddress.name,
                    'address': allShipAddress.address,
                    'city': allShipAddress.city,
                    'state': allShipAddress.state,
                    'zipcode': allShipAddress.zipcode,
                    'mobile': allShipAddress.mobile,
                    'altMobile': allShipAddress.altMobile,
                }
            allShipAddresses.append(allShipAddress.address)
            allShipAddressRecord.append(ship_addressRecord)
        
    except:
        shippingData = {'errorMsg': 'An error occured'}
        data.append(shippingData)

    shippingData = {'shipping_addressRecord': shipping_addressRecord, 'allShipAddresses': allShipAddresses, 'allShipAddressRecord': allShipAddressRecord}
    data.append(shippingData)

    return JsonResponse(data, safe=False)


@api_view(['POST'])
def api_processOrder(request):
    data = {}
    itemList = ''
    amount = request.data['amount']
    userName = request.data['userName']
    paymentMethod = request.data['paymentMethod']
    shippingInfo = request.data['shippingInfo']
    payStackReference = request.data['payStackReference']
    paymentStatus = request.data['paymentStatus']

    try:
        if request.user.is_authenticated:
            userN = User.objects.get(username= userName)
            customer = Customer.objects.get(user_id=userN.id)
            
            order = Order.objects.get(customer=customer.id, complete=False)

            # FOR THE LAST TIME, I WANT TO CONFIRM IF ALL THE ITEM(S) IN THE CART IS ACTIVE AND IN STOCK
            data = confirmCartItems(order)
            if data == "item(s) not valid":
                return JsonResponse(data, safe=False)
        else:
            # ITS A GUEST USER 
            customer, order, guestOrderData, isInactiveItem = createGuestOrder(request)
         
        if order:
            
            # itemList = orderItems I DONT REALLY KNOW WHY THIS ASSIGNEMENT WAS MADE
    
            # transaction_id = datetime.datetime.now().timestamp()
            transaction_id = str(uuid.uuid4().time_low)[:6]
            order.transaction_id = transaction_id

            # GET THE PAYMENT OPTION AND PROCESS
            if paymentMethod == 'Pay on delivery':
                order.status = 'On hold'
            elif paymentMethod == 'Debit card':

                # ======== CREATE THE PAYMENT METHOD ON THE DB TABLE ========
                Payment.objects.create(
                    amount=amount,
                    ref=payStackReference,
                    email=customer.email,
                    status=paymentStatus,
                )
                print('Payment created...')
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

            order.payment_option = paymentMethod
            if float(amount) == float(order.get_cart_total):
                order.complete = True
            else:
                order.status = 'On hold'
            order.date_order = datetime.datetime.now()
            order.save()

            # CREATE THE SHIPPING INFORMATION IN THE DATABASE
            # CHECKING IF THE SAME SHIPPING ADDRESS HAVE BEEN CREATED BEFORE
            # MULTIPLE SHIPPING ADDRESS WITH THE SAME ORDER ID WILL THROW AN ERROR
            # IF THE ADMIN OR CUSTOMER WANT TO OPEN THE ORDER INFO IN THE ACCOUNT PAGE
            shipInfo = ShippingAddress.objects.filter(order=order.id)
            if not shipInfo:
                print("create shipping")
                ShippingAddress.objects.create(
                    customer=customer,
                    order=order,
                    address_type='Shipping Address',
                    address=shippingInfo['address'],
                    city=shippingInfo['city'],
                    state=shippingInfo['state'],
                    zipcode=shippingInfo['zipcode'],
                    mobile=shippingInfo['mobile'],
                    altMobile=shippingInfo['altMobile'],
                    optional_note=shippingInfo['optionalNote'],
                    ) 
            data = "transaction completed"
    except Exception as e:
        data = {"serverResponse": e.args}

    return JsonResponse(data, safe=False)



# THIS API CALL IS USED TO VERIFY GUEST CART ITEM(S) FOR STOCK STATUS, ITEM PRICE AND 
# STORE/ITEM ACTIVE STATUS 
@api_view(['POST'])
def api_guestVerifyCartItems(request):
    data = []
    guestCartReport = {}
    guestCartPtds = request.data
    for guestCartPtd in guestCartPtds:
        product = Product.objects.get(id=guestCartPtd['guestCartPtdId'])
        if product.out_of_stock == True or product.active == False or product.store.active == False or float(product.get_unit_price) != float(guestCartPtd['guestCartPtdPrice']):
            guestCartReport = {
                'ptdId': product.id,
                'out_of_stock': product.out_of_stock,
                'unit_price': product.get_unit_price,
                'activePtd': product.active,
                'activeStore': product.store.active
            }
            data.append(guestCartReport)
        elif guestCartPtd['guestCartOutOfStock'] == 'true' or guestCartPtd['guestCartActivePtd'] == 'false' or guestCartPtd['guestCartActiveStore'] == 'false':
            guestCartReport = {
                'ptdId': product.id,
                'out_of_stock': product.out_of_stock,
                'unit_price': product.get_unit_price,
                'activePtd': product.active,
                'activeStore': product.store.active
            }
                
            data.append(guestCartReport)
    if not data:
        data.insert(0, 'valid')
    return JsonResponse({'serverResponse': data}, safe=False)



def verify_payment(request: HttpRequest, ref: str):
    payment = Payment.objects.get(ref=ref)
    status, result = payment.verify_payment()
    # if verified:
    #     messages.success(request, "Verification successful")
    # else:
    #     messages.error(request, "Verification Failed")
    return status, result


# ====================== OVER VIEW OF ADMIN SESSION =======================
@api_view(['POST'])
def api_adminSession(request):
    data = {}
    order_data = []
    if request.user.is_authenticated:
        orderData = Order.objects.filter(Q(status='Processing') | Q(status='On hold') | Q(status='Shipped') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Refunded') | Q(status='Failed') | Q(status='Rejected')).order_by('-date_order')
        
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
                    'date_order': customTimeFormat (orderRecord.date_order),
                    'complete': orderRecord.complete,
                    'paid': orderRecord.paid,
                    'total': total_amt,
                    'status': orderRecord.status,
                    'counter': counter,
                }
                order_data.append(order_record)
        totalCount = counter
    return JsonResponse({'order_data': order_data, 'totalCount': totalCount}, safe=False)


def customTimeFormat(dateTime):
    customDateTime = dateTime + timedelta(hours=1)
    customDateTime = customDateTime.strftime("%b, %d, %Y %I:%M %p")

    return customDateTime


@api_view(['POST'])
def api_adminEditOrder(request):
    
    orderItemData = []
    order_obj = {}
    grandTotal = 0
    isVerifiedPayment = False
    if request.user.is_authenticated:
        if request.data.get('isAdminUpdateOrder') == True:
            apiAdminUpdateItem(request)

        order = Order.objects.get(transaction_id= request.data.get('order_no'))
        orderItems = order.orderitem_set.all()

        for orderItem in orderItems:
            orderItemRecord = {
                'itemRowId': orderItem.id,
                'ptdId': orderItem.product.id,
                'ptdImage': config('URL_ENDPOINT')+orderItem.product.imageURL,
                'ptdName' : orderItem.product.name,
                'storeLocation': orderItem.store_name,
                'price': orderItem.unit_price,
                'qty' : orderItem.quantity,
                'lineTotal': orderItem.line_total
            }
            orderItemData.append(orderItemRecord)
            grandTotal += orderItem.line_total
        shipping_address = ShippingAddress.objects.get(order__transaction_id=request.data.get('order_no'))
        orderData = []
        myDictionary = {}

        # CONFIRM IF CUSTOMER IS A REGISTERED USER
        if order.customer.user:
            user = User.objects.get(id=order.customer.user.id)
            order_obj = {
                'transaction_id': order.transaction_id,
                'order_date': customTimeFormat (order.date_order),
                'complete': order.complete,
                'address': shipping_address.address,
                'city': shipping_address.city,
                'state': shipping_address.state,
                'mobile': shipping_address.mobile,
                'altMobile': shipping_address.altMobile,
                'optional_note': shipping_address.optional_note,
                'user_name': user.username,
                'user_email': user.email,
                'date_joined': customTimeFormat (user.date_joined),
                'last_login': customTimeFormat (user.last_login),
                'payment_option': order.payment_option,
                'paid': order.paid,
                'status': order.status,
                'private_note': order.order_private_note,
                'refund_status': order.refund_status,
                'orderId': order.id
            }
        else:
            order_obj = {
                'transaction_id': order.transaction_id,
                'order_date': customTimeFormat (order.date_order),
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
                'refund_status': order.refund_status,
                'orderId': order.id
            }
    # ======== CHECK PAYMENT TABLE IF PAYMENT WAS MADE AND VERIFIED ==========
    if order.paymentReference:
        payment = Payment.objects.get(ref= order.paymentReference)
        isVerifiedPayment = payment.verified
    else:
        payment = Payment.objects.filter(ref= order.transaction_id)
        if payment:
            payment = Payment.objects.get(ref= order.transaction_id)
            isVerifiedPayment = payment.verified

    return JsonResponse({'order_obj': order_obj, 'isVerifiedPayment': isVerifiedPayment, 'orderItemData': orderItemData, 'grandTotal': grandTotal}, safe=False)


def apiAdminUpdateItem(request):
    
    itemRowId = request.data.get('itemRowId')
    action = request.data.get('action')
    trans_id = request.data.get('order_no')
    selected_value = request.data.get('selectedValue')
    amt_paid = request.data.get('amtPaid')
    payment_mode = request.data.get('paymentMode')
    payment_note = request.data.get('paymentNote')
    updateShippingAddress = request.data.get('updateShippingInfo')
    orderPrivateNote = request.data.get('closeOrderNote')
    
    private_note = ''
    if itemRowId:
        orderItem = OrderItem.objects.get(id=itemRowId)
    order = Order.objects.get(transaction_id=trans_id)
    
    # USED TO REDUCE OR DELETE ORDER ITEM THAT WAS CREATED
    if action == 'reduction':
        orderItem.quantity = (orderItem.quantity - 1)
        orderItem.line_total = orderItem.unit_price * orderItem.quantity
        orderItem.save()
        if orderItem.quantity < 1:
            orderItem.delete()
    elif action == 'delete':
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

    # ========= CONDITION TO UPDATE ORDER STATUS ============
    if selected_value == 'complete':
        print('COMPLETE EXECUTING...')
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
            
        else:
            Payment.objects.create(
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
        if order.customer.user:
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

            
    elif selected_value == 'processing':
        print('PROCESSING...')
        order.status = 'Processing'
    elif selected_value == 'on_hold':
        print('ON HOLD...')
        order.status = 'On hold'
    elif selected_value == 'shipped':
        print('SHIPPING...')
        order.status = 'Shipped'
    elif selected_value == 'cancelled':
        print('CANCELLING...')
        order.status = 'Cancelled'
        order.order_private_note = orderPrivateNote
    elif selected_value == 'rejected':
        print('REJECTING...')
        order.status = 'Rejected'
        order.order_private_note = orderPrivateNote
    elif selected_value == 'failed':
        print('FAILING...')
        order.status = 'Failed'
        order.order_private_note = orderPrivateNote

    order.save()

    # ===== ADMIN UPDATING SHIPPING ADDRESS =============
    if updateShippingAddress:
        updateShipAddress = ShippingAddress.objects.get(order=updateShippingAddress['orderId'])
        updateShipAddress.address = updateShippingAddress['address']
        updateShipAddress.city = updateShippingAddress['city']
        updateShipAddress.state = updateShippingAddress['state']
        updateShipAddress.mobile = updateShippingAddress['mobile']
        updateShipAddress.altMobile = updateShippingAddress['altMobile']
        updateShipAddress.save()


@api_view(['POST'])
def api_adminProcessRefundOrder(request):
    data = {}
    refundOrderItem = []
    totalAmt = 0
    totalRefundAmt = 0
    isRefundAmtUpdated = False # USED TO CHECK IF RECORD SHOULD BE RELOADED FROM THE WIDGET OF THE MOBILE APP
    isPaidOrder = False # ON THE PHONE WIDGET, IT'S USED TO CHECK IF PAYMENT MADE WAS VERIFIED
    
    if request.user.is_authenticated:
        if request.data.get('isAdminUpdateRefund') == True:
            isRefundAmtUpdated = apiAdminUpdateRefundItem(request)
        refundOrder = Order.objects.get(transaction_id= request.data.get('transId'))
        refundItems = refundOrder.orderitem_set.all()
        isPaidOrder = refundOrder.paid # ON THE PHONE WIDGET, IT'S USED TO CHECK IF PAYMENT MADE WAS VERIFIED
        reasonForRefund = refundOrder.reason_for_refund # THIS IS USED TO DECIDE IF REFUND IS CLOSE OR OPEN ON THE PHONE APP
        refundPrivateNote = refundOrder.refund_private_note # IF THERE WAS A REFUND NOTE, WE WILL BE ABLE TO VIEW IT ON THE PHONE WIDGET
        for refundItem in refundItems:
            isRefundAmt = False # USED TO DECIDE IF ZERO OR REFUNDED AMT SHOULD DISPLAY IN THE FONT END
            if refundItem.refundAmt:
                totalRefundAmt += refundItem.refundAmt # USED TO ADD ALL TOTAL AMOUNT THAT IS REFUNDED
                isRefundAmt = True # AN AMOUNT WILL DISPLAY ON THE FONT END. ELSE ZERO WILL DISPLAY
            orderItemRecord = {
                'itemRowId': refundItem.id,
                'ptdImage': config('URL_ENDPOINT')+refundItem.product.imageURL,
                'ptdName' : refundItem.product.name,
                'storeName': refundItem.store_name,
                'qty' : refundItem.quantity,
                'lineTotal': refundItem.line_total,
                'refundAmt': refundItem.refundAmt,
                'isRefundAmt': isRefundAmt
            }
            refundOrderItem.append(orderItemRecord)
            totalAmt += refundItem.line_total # USED TO DISPLAY THE TOTAL AMOUNT OF THE ORDER
            refundInfo = {
                'totalAmt': totalAmt,
                'isRefundAmtUpdated': isRefundAmtUpdated,
                'totalRefundAmt': totalRefundAmt,
                'isPaidOrder': isPaidOrder,
                'reasonForRefund': reasonForRefund,
                'refundPrivateNote': refundPrivateNote
            }

    data = {'refundOrderItem': refundOrderItem, 'refundInfo': refundInfo}
    return JsonResponse(data, safe=False)


def apiAdminUpdateRefundItem(request):
    itemRowId = request.data.get('itemRowId')
    inputValue = request.data.get('inputAmt')
    transaction_id = request.data.get('transId')
    refundNote = request.data.get('refundNote')
    reasonForRefund = request.data.get('reasonForRefund')
    isRefundAmtUpdated = False # USED TO CHECK IF RECORD SHOULD BE RELOADED FROM THE WIDGET OF THE MOBILE APP
    dbTotalRefundAmt = 0
    
    refundOrder = Order.objects.get(transaction_id= transaction_id)
    refundItems = refundOrder.orderitem_set.all()
    if inputValue == 'full_refund': # CHECKING IF A FULL REFUND CHECKBOX WAS SELECTED FOR THE ORDER
        for refundItem in refundItems:
            refundItem.refundAmt = refundItem.line_total
            refundItem.save()
        refundOrder.refund_status = 'Full Refund'
        refundOrder.status = 'Refunded'
        isRefundAmtUpdated = True
    elif inputValue == 'no_refund': # CHECKING IF 'FULL REFUND CHECKBOX' WAS UNCHECKED. THIS WILL REVERSE ALL FULL REFUNED AMT
        for refundItem in refundItems:
            refundItem.refundAmt = 0
            refundItem.save()
        isRefundAmtUpdated = True
    elif itemRowId:
        # GET THE ROW ITEM AND UPDATE THE DB WITH THE REFUND AMOUNT
        refundItem = refundOrder.orderitem_set.get(id= itemRowId)
        refundItem.refundAmt = inputValue
        refundItem.save()
        isRefundAmtUpdated = True
    elif inputValue == 'cancelBtn':
        for refundItem in refundItems:
            refundItem.refundAmt = 0
            refundItem.save()
        isRefundAmtUpdated = True
    
    if reasonForRefund:
        # SUBMITING REFUND...
        # ON THE MOBILE APP, WE HAVE DONE ALL THE CHECKS BEFORE SENDING DATA TO THE BACKEND.
        # CHECKING IF IT'S A FULL REFUND OR PARTIAL REFUND...
        for _refundItem in refundItems:
            dbTotalRefundAmt += _refundItem.line_total
        if dbTotalRefundAmt == inputValue:
            refundOrder.refund_status = 'Full Refund'
            refundOrder.status = 'Refunded'
        else:
            refundOrder.refund_status = 'Partial Refund'
        refundOrder.refund_private_note = refundNote
        refundOrder.reason_for_refund = reasonForRefund
        
        refundOrder.save()
        isRefundAmtUpdated = True

    return isRefundAmtUpdated


@api_view(['POST'])
def api_myOrder(request):
    myOrderData = []

    # WE NEED TO FILTER THE ORDER TABLE BASED ON CUSTOMER NAME AND ORDER STATUS
    myOrders = Order.objects.filter((Q(status='Processing') | Q(status='On hold') | Q(status='Shipped') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Refunded') | Q(status='Rejected') | Q(status='Failed')), customer__name=request.user.customer.name).order_by('-date_order')
   
    for _myOrder in myOrders:
        myOrderItems = _myOrder.orderitem_set.all()
        total = 0
        for myOrderItm in myOrderItems:
            total += myOrderItm.line_total
        my_order = {
            'transaction_id': _myOrder.transaction_id,
            'customer_name': _myOrder.customer.name,
            'date_order': customTimeFormat(_myOrder.date_order),
            'complete': _myOrder.complete,
            'paid': _myOrder.paid,
            'line_total': total,
            'status': _myOrder.status,
        }
        myOrderData.append(my_order)

    return JsonResponse(myOrderData, safe=False)


@api_view(['POST'])
def api_updateMyOrder(request):
    data = {}
    orderItemData = []
    order = Order.objects.get(transaction_id= request.data.get('order_no'))
    orderItems = order.orderitem_set.all()
    grandTotal = 0
    updateShippingAddress = request.data.get('updateShippingInfo')
    
    for orderItem in orderItems:
        grandTotal += orderItem.line_total
    
    # ===== ADMIN UPDATING SHIPPING ADDRESS =============
    if updateShippingAddress:
        updateShipAddress = ShippingAddress.objects.get(order__transaction_id=request.data.get('order_no'))
       
        updateShipAddress.address = updateShippingAddress['address']
        updateShipAddress.city = updateShippingAddress['city']
        updateShipAddress.state = updateShippingAddress['state']
        updateShipAddress.mobile = updateShippingAddress['mobile']
        updateShipAddress.altMobile = updateShippingAddress['altMobile']
        updateShipAddress.save()

    shipping_address = ShippingAddress.objects.get(order__transaction_id= request.data.get('order_no'))
    # CONFIRM IF CUSTOMER IS A REGISTERED USER
    if order.customer.user:
        user = User.objects.get(id=order.customer.user.id)
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': customTimeFormat(order.date_order),
            'complete': order.complete,
            'address': shipping_address.address,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'mobile': shipping_address.mobile,
            'altMobile': shipping_address.altMobile,
            'optional_note': shipping_address.optional_note,
            'user_name': user.username,
            'user_email': user.email,
            'date_joined': customTimeFormat(user.date_joined),
            'last_login': customTimeFormat(user.last_login),
            'payment_option': order.payment_option,
            'paid': order.paid,
            'status': order.status,
            'private_note': order.order_private_note,
        }
    else:
        order_obj = {
            'transaction_id': order.transaction_id,
            'order_date': customTimeFormat(order.date_order),
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
    for orderItm in orderItems:
        orderItem = {
                'itemRowId': orderItm.id,
                'ptdImage': config('URL_ENDPOINT')+orderItm.product.imageURL,
                'ptdName' : orderItm.product.name,
                'price': orderItm.unit_price,
                'qty' : orderItm.quantity,
                'lineTotal': orderItm.line_total,
        }
        orderItemData.append(orderItem)

    data['grandTotal'] = grandTotal
    data['order_obj'] = order_obj
    data['orderItemData'] = orderItemData

    return JsonResponse(data, safe=False)


@api_view(['POST'])
def api_pendingReview(request):
    orderPendingReviews = ProductReview.objects.filter(cus_name=request.data.get('userName'))
    print(orderPendingReviews)
    pendingReviewOrders = []

    if request.user.is_authenticated:
        for pendingReview in orderPendingReviews:
            pendingReviewObj = {
                'id': pendingReview.id,
                'ptd_review_id': pendingReview.ptd_review_id,
                'ptd_id': pendingReview.ptd_id,
                'transaction_id': pendingReview.transaction_id,
                'cus_name': pendingReview.cus_name,
                'order_date': customTimeFormat(pendingReview.order_date),
            }
            
            pendingReviewOrders.append(pendingReviewObj)
    
    return JsonResponse(pendingReviewOrders, safe=False)


@api_view(['POST'])
def api_writePtdReview(request):
    pendingReviewItems = []
    commentRecord = request.data.get('commentData')
    rated = request.data.get('rated')
    if request.user.is_authenticated:
    
        if rated:
            
            _pendingReview = ProductReview.objects.get(id=request.data.get('ptdReviewId'))
            product = Product.objects.get(id=request.data.get('ptdId'))

            Comment.objects.create(
            product = product,
            customer = request.user.customer,
            subject = commentRecord['subject'],
            comment = commentRecord['comment'],
            rate = commentRecord['rating'],
            )
            _pendingReview.delete()
       
        # THIS FILTER IS USED TO SELECT ALL CHILD PENDING REVIEWS PRODUCTS
        pendingReviews = ProductReview.objects.filter(ptd_review_id=request.data.get('parentPtdReviewId'), transaction_id=request.data.get('transId'))
        
        # GET THE PARENT REVIEW ORDER. THIS IS STILL FROM THE SAME TABLE
        pending_Review = ProductReview.objects.get(id=request.data.get('parentPtdReviewId'))

        if pendingReviews:
            # GET ALL THE PRODUCT ITEM ON THE LIST
            for pendingReview in pendingReviews:
                ptdItem = {
                    'ptd_review_id': pendingReview.ptd_review_id,
                    'order_date': pendingReview.order_date,
                    'product_name': pendingReview.product_name,
                    'product_image': config('URL_ENDPOINT')+pendingReview.product_image,
                    'ptd_id': pendingReview.ptd_id,
                    'id': pendingReview.id,
                    'trans_id': pendingReview.transaction_id,
                }
                pendingReviewItems.append(ptdItem)
            
        else:
            pending_Review.delete()

    return JsonResponse(pendingReviewItems, safe=False)


@api_view(['POST'])
def api_wishList(request):
    wishListData = []
    inactive_outOfStock = False
    action = request.data.get('action')
    cartCounter = 0
   
    if request.user.is_authenticated:
        if action:
            selectedList = request.data.get('selectedList')
            if action == 'deleteWishList':
                print('DELETING COMMAND')
                for selection in selectedList:
                    WishList.objects.get(customer_id= selection['customerId'], product_id= selection['ptdId']).delete()
            elif action == 'deleteWishListFrmBtn':
                WishList.objects.get(customer_id= request.data.get('customerId'), product_id= selectedList).delete()
               
            elif action == 'addToCart':
                # CALL TO CREATE LOOP ORDER ITEMS FROM WISHLIST 
                isSuccess, inactive_outOfStock = addMultiItemsToCart(request)

        wishLists = WishList.objects.filter(customer_id= request.data.get('customerId'))

        for wishList in wishLists:
            # GET ALL THE COMMENT RECORD FROM EACH PRODUCT
            # RECORD USED TO DISPLAY STAR & NUMBER OF COMMENT OF WISH-LIST ON THE CART PAGE
            ptdComment = Comment.objects.filter(product= wishList.product.id).order_by('-created_at')
           
            # CALL THE FUNCTION WITH COMMENT RECORD TO PROCESS STAR RATING AND NUMBER OF COMMENT
            averageRating = weightAverageRating(request, ptdComment)
          
            wishListRecord = {
                'ptdImage': config('URL_ENDPOINT')+wishList.product.imageURL,
                'ptdName': wishList.product.name,
                'ptdPrice': wishList.product.price,
                'ptdNewPrice': wishList.product.get_unit_price,
                'mfgData': wishList.product.mfgDate,
                'expData': wishList.product.expDate,
                'discount': wishList.product.discount,
                'isCheck': False,
                'ptdId': wishList.product.id,
                'category': wishList.product.category.category,
                'out_of_stock': wishList.product.out_of_stock,
                'storeId': wishList.product.store.id,
                'isActiveStore': wishList.product.store.active,
                'isActive': wishList.product.active,
                'averageStarRate': averageRating['myDictionary']['weighted_average_rating'],
                'commentCount': averageRating['myDictionary']['counter']
            }
            wishListData.append(wishListRecord)
        order = Order.objects.get(customer=request.user.customer.id, complete=False)
        cartCounter = order.get_cart_items

    return JsonResponse({'wishListData': wishListData, 'inactive_outOfStock': inactive_outOfStock,
    'cartCounter': cartCounter}, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_traderStore(request):
    data = {}
    counter = 0
    storeMenuList = []
    storeData = {}
    response = ''
    serverMsg = ''
    storeMenuList.append('Select Store')
    userRequest = request.data.get('storeRecord')

    user = User.objects.get(id=request.data.get('user_id'))
    # IT'S POSSIBLE FOR A TRADER TO HAVE MORE THAN ONE STORE.
    # GET ALL DATA FROM STORE, LOOP THOURGH USING THE USER ID TO SEE IF IT'S NONE, ONE OR MORE STORES
    store_record = Store.objects.all()
    active = request.data.get('isActive')

    # USED TO FILTER ALL THE TRADER'S STORE NAME.
    for store in store_record:
        if store.user_id.id == user.id:
            storeMenuList.append(store.store_name)
            counter += 1
    
    # ====== REQUEST TO ADD A NEW STORE ===========
    try:
        if request.data.get('action') == 'addStore':
            # CHECK IF THE STORE NAME ALREADY EXIST IN THE SYSTEM BEFORE ADDING
            existing_store_name = Store.objects.filter(store_name__icontains= (userRequest['storeName']).strip())
            if existing_store_name:
                print('STORE EXIST')
        
                response = 'storeAlreadyExist'
            else:
                Store.objects.create(
                    user_id= user,
                    store_name= (userRequest['storeName']).strip(),
                    store_address= (userRequest['storeAddress']).strip(),
                    city= (userRequest['city']).strip(),
                    LGA= (userRequest['LGA']).strip(),
                    state= (userRequest['state']).strip(),
                    email= (userRequest['email']).strip(),
                    mobile= (userRequest['mobile']).strip(),
                    altMobile= (userRequest['altMobile']).strip(),
                    active= active
                )
                response = 'storeCreated'
    except Exception as e:
        serverMsg = e.args
        response = 'errorCreatingStore'

    # ======= REQUESTING TO GET STORE RECORD. (FOR UPDATE PURPOSE) ========
    try:
        if request.data.get('action') == 'updateStore':
            storeRec = Store.objects.get(store_name=userRequest)
            storeData = {
                'id': storeRec.id,
                'storeName': storeRec.store_name,
                'storeAddress': storeRec.store_address,
                'city': storeRec.city,
                'LGA': storeRec.LGA,
                'state': storeRec.state,
                'email': storeRec.email,
                'mobile': storeRec.mobile,
                'altMobile': storeRec.altMobile,
                'isVerified': storeRec.verified,
                'isActive': storeRec.active
            }
            response = 'storeRecordPulled'
    except Exception as e:
        serverMsg = e.args
        response = 'errorPullingStoreRecord'
    
    # ======= REQUEST TO UPDATE STORE DATA ===========
    try:
        if request.data.get('action') == 'updateButton':
            storeRec = Store.objects.get(id=userRequest['storeDbId'])

            storeRec.store_name = userRequest['storeName']
            storeRec.store_address = userRequest['storeAddress'].strip()
            storeRec.city = userRequest['city'].strip()
            storeRec.LGA = userRequest['LGA'].strip()
            storeRec.state = userRequest['state'].strip()
            storeRec.email = userRequest['email'].strip()
            storeRec.mobile = userRequest['mobile'].strip()
            storeRec.altMobile = userRequest['altMobile'].strip()
            storeRec.active = userRequest['isActiveSwitch']
            
            storeRec.save()
            response = 'storeUpdateSuccessful'
    except Exception as e:
        serverMsg = e.args
        response = 'storeNotUpdated'
    print(storeMenuList)
    data = {
        'counter': counter,
        'storeMenuList': storeMenuList,
        'storeData': storeData,
        'response': response,
        'serverMsg': serverMsg,
    }
    

    return JsonResponse(data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_productOverView(request):
    data = {}
    storesIdList = []
    ptd_list = []
    active = request.data.get('value')

    t_stores = Store.objects.filter(user_id=request.data.get('userId'))

    # THIS BLOCK OF CODE IS USED TO SAVE ACTIVE/INACTIVE ITEM TO THE DB
    try:
        if request.data.get('caller') == 'btnContinue':
            activePtd = {'active': (True if active == 'active' else False)}
            products = Product.objects.all().order_by('-id')
            for selectedPtdId in request.data.get('list'):
                
                for product in products:
                    
                    if int (selectedPtdId) == product.id:
                        
                        product.active = activePtd['active']
                        product.save()
                        break
            data['serverMsg'] = 'success'
    except Exception as e:
        data['serverMsg'] = 'failed'
        data['errorMsg'] = e.args

    # ====== USE THE STORE ID TO FILTER THE PRODUCT FROM THE TABLE ======
    for t_store in t_stores:
        storesIdList.append(t_store.id)
    if storesIdList:
        products = Product.objects.all().order_by('-id')
       
        for storeIdList in storesIdList:
            for trader_ptd in products:
                if trader_ptd.store_id == storeIdList:
                    ptd_dic = {
                        'id': trader_ptd.id,
                        'name': trader_ptd.name,
                        'description': trader_ptd.description,
                        # 'brand': trader_ptd.brand,
                        'price': trader_ptd.price,
                        'discount': trader_ptd.discount,
                        'mfgDate': trader_ptd.mfgDate,
                        'expDate': trader_ptd.expDate,
                        'store': trader_ptd.store.store_name,
                        'active':trader_ptd.active,
                        'isCheck': False
                    }
                    ptd_list.append(ptd_dic)
   
    data['traderPtdList'] = ptd_list
    
    return JsonResponse(data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_editProduct(request):
    data = {}
    categoryMenuList = []
    brandMenuList = []
    storeMenuList = []
    # brandMenuList.append('Select brand')
    catData = {
        'id': 0,
        'category': 'Select category'
    }
    categoryMenuList.append(catData)
    storeRecord = {
        'id': 0,
        'store': 'Select store'
    }
    storeMenuList.append(storeRecord)
    brandRecord = {
        'id': 0,
        'brand': 'Select brand'
    }
    brandMenuList.append(brandRecord)
    try:
        categories = Category.objects.all()
        t_stores = Store.objects.filter(user_id=request.data.get('userId')) # I WANT TRADER TO ONLY SEE THEIR STORE(S)
        brands = Brand.objects.all()
         
        for cat in categories:
            catData = {
                'id': cat.id,
                'category': cat.category
            }
            categoryMenuList.append(catData)

        for bran in brands:
            brandRecord = {
                'id': bran.id,
                'brand': bran.brand
            }
            brandMenuList.append(brandRecord)

        for tStore in t_stores:
            storeRecord = {
                'id': tStore.id,
                'store': tStore.store_name
            }
            storeMenuList.append(storeRecord)

        # ====== LOAD EDITABLE PAGE =========
        if request.data.get('call') == 'loadPage':
            product = Product.objects.get(id= request.data.get('ptdId'))
            
            # ARRANGE THE EDITABLE RECORD THAT WILL DISPLAY ON THE WIDGET
            ptdRecord = {
                'ptdId': product.id,
                'ptdName': product.name,
                'ptdDescription': product.description,
                'ptdCagetoryId': product.category.id,
                'ptdBrand': getPtdBrand(product),
                'price': product.price,
                'image': config('URL_ENDPOINT')+product.imageURL,
                'imageName': str(product.image),
                'mfgDate': product.mfgDate,
                'expDate': product.expDate,
                'discount': product.discount,
                'out_of_stock': product.out_of_stock,
                'store': product.store.id,
                'active': product.active,
                'categoryMenuList': categoryMenuList,
                'brandMenuList': brandMenuList,
                'storeMenuList': storeMenuList
            }
            data['ptdRecord'] = ptdRecord
            data['serverMsg'] = 'success'
            

        # ======== REQUEST TO SAVE EDITED PRODUCT ITEM ===========
        elif request.data.get('call') == 'updateBtn':
            product = Product.objects.get(id= request.data.get('ptdId'))
            editablePtd = {}
            editablePtd = request.data.get('editPrdRcd')
            editedCategory = Category.objects.get(id = editablePtd['categoryId'])
            editedStore = Store.objects.get(id = editablePtd['storeId'])
            if int (editablePtd['brand']) > 0:
                editedBrand = Brand.objects.get(id = editablePtd['brand'])
                product.brand = editedBrand
            product.name = editablePtd['name']
            product.description = editablePtd['description']
            product.category = editedCategory
            product.price = editablePtd['price']
            product.image = removeImageFile(product, editablePtd['imageName'])
            product.mfgDate = validateDate(editablePtd['mfgDate'])
            product.expDate = validateDate(editablePtd['expDate'])
            product.discount = editablePtd['discount']
            product.out_of_stock = editablePtd['outOfStock']
            product.store = editedStore
            product.active = editablePtd['isActive']
            
            product.save()
            data['serverMsg'] = 'success'
        

        # ======== REQUEST TO EDIT IMAGE PRODUCT ===========
        elif request.data.get('call') == 'editImgRequest':
            product = Product.objects.get(id= request.data.get('ptdId'))
            print(request.data.get('category'))
            editCategory = Category.objects.get(id= request.data.get('categoryId'))
            editStore = Store.objects.get(id= request.data.get('storeId'))
            if int (request.data.get('brandId')) > 0:
                editBrand = Brand.objects.get(id= request.data.get('brandId'))
                product.brand = editBrand
            if request.FILES.get("image", None) is not None:
                # IF THERE IS AN OLD IMAGE FILE, GO INTO THE IF STATEMENT AND
                # REMOVE IT BEFORE REPLACING IT WITH THE NEW ONE
                if product.image != request.FILES.get('image') and (product.image != '' and product.image is not None):
                    removeImageFile(product, '')
                product.image = request.FILES.get('image')
            product.name = request.data.get('name')
            product.description = request.data.get('description')
            product.category = editCategory
            product.price = request.data.get('price')
            product.mfgDate = validateDate(request.data.get('mfgDate'))
            product.expDate = validateDate(request.data.get('expDate'))
            product.discount = request.data.get('discount')
            product.out_of_stock = getBoolValue(request.data.get('outOfStock'))
            product.store = editStore
            product.active = getBoolValue(request.data.get('isActive'))
          
            product.save()
            data = 'success'
            
        
        # REQUEST TO LOAD EMPTY NEW PAGE WITH THE DROP DOWN ITEMS 
        elif request.data.get('call') == 'loadEmptyPage':
            data['categoryMenuList'] = categoryMenuList
            data['brandMenuList'] = brandMenuList
            data['storeMenuList'] = storeMenuList

        
    except Exception as e:
        data['serverMsg'] = 'failed'
        data['errorMsg'] = e.args

    
    return JsonResponse(data, safe=False) 

    # WHEN PTD IMAGE ARE DELETED FROM THE DATABASE, TO ENSURE THE IMAGE FILE 
    # IS ALSO DELETED FROM ITS FOLDER, CALL THIS FUNCTION CHECK FOR THIS CONDITION
    # HERE, THE 'VALUE' IS THE IMAGE NAME FROM THE DATABASE. IF THE IMAGE NAME
    # DOES NOT EXIST IN THE DATABASE, REMOVE THE IMAGE FROM APP FOLDER
def removeImageFile(ptd, value):
    print(value)
    if not value:
        try:
            os.remove(ptd.image.path)
        except:
            pass
    return value

def validateDate(validDate):
    validatedDate = None
    if validDate != '0000-01-01':
        validatedDate = validDate
    return validatedDate


def getBoolValue(value):
    isActive = None
    if value == 'yes':
        isActive = True
    elif value == 'no':
        isActive = False
    return isActive

def checkBrandName(value):
    if value != '':
        return value.id 
    else:
        return ''


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_addProduct(request):
    # data = {}
    try:
        # productRecord = request.data.get('itmRecord')
        brandName = ''
        categoryName = Category.objects.get(id = request.data.get('categoryId'))
        if request.data.get('brandId') != '0':
            brandName = Brand.objects.get(id = request.data.get('brandId'))
        storeName = Store.objects.get(id = request.data.get('storeId'))
        
        recordData = {
            'price': request.data.get('price'),
            'name': request.data.get('name'),
            'description': request.data.get('description'),
            'category': categoryName.id,
            'image': request.data.get('image'),
            # 'brand': checkBrandName(brandName),
            'discount': request.data.get('discount'),
            'store': storeName.id,
            'out_of_stock': getBoolValue(request.data.get('outOfStock')),
            'mfgDate': validateDate(request.data.get('mfgDate')),
            'expDate': validateDate(request.data.get('expDate')),
            'active': getBoolValue(request.data.get('isActive'))
        }
        if request.data.get('call') == 'saveBtn':
            print('SAVE BUTTON')
            if request.FILES.get("image", None) is not None:
                print('IMAGE EXIST...')
                img = request.FILES
                print(img['image'])
                print(request.data)
            # print(productRecord)
            # print(request.data.get('file'))
            serializer = ProductSerializer(data= recordData)
            if serializer.is_valid():
                print('VALID SERIALIZER')
                serializer.save()
            else:
                print(serializer.errors)
            
        data = 'success'
    except Exception as e:
        data = 'failed'
        print(e.args)


    return JsonResponse(data, safe=False)


# THIS FUNCTION DOES TWO THINGS. (1) GET THE DEFAULT SHIPPING ADDRESS OF THE CUSTOMER
# (2) GET ALL SHIPPING ADDRESS OF THE CUSTOMER
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_settings(request):
    data = {}
    defaultAddressRecord = {}
    allShipAddressData = []
    if request.data.get('call') == 'defaultShipAddress':
        isDefaultAddress = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address', default=True).exists()
        if isDefaultAddress:
            cus_defaultAddress = CustomerAddress.objects.get(customer=request.user.customer.id, address_type='Shipping Address', default=True)
            defaultAddressRecord = {
                'name': cus_defaultAddress.name,
                'address': cus_defaultAddress.address,
                'city': cus_defaultAddress.city,
                'state': cus_defaultAddress.state,
                'zipcode': cus_defaultAddress.zipcode,
                'mobile': cus_defaultAddress.mobile,
                'altMobile': cus_defaultAddress.altMobile,
            }
    elif request.data.get('call') == 'allShipAddress':
        allShipAddresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
        for shipAddress in allShipAddresses:
            allShipAddressRecord = {
                'id': shipAddress.id,
                'name': shipAddress.name,
                'address': shipAddress.address,
                'city': shipAddress.city,
                'state': shipAddress.state,
                'zipcode': shipAddress.zipcode,
                'mobile': shipAddress.mobile,
                'altMobile': shipAddress.altMobile,
                'isDefault': shipAddress.default,
            }
            allShipAddressData.append(allShipAddressRecord)

    data['cus_defaultAddress'] = defaultAddressRecord
    data['allShipAddressData'] = allShipAddressData
    return JsonResponse(data, safe=False)


# THIS FUNCTION IS USED TO CREATE AND UPDATE CUSTOMER ADDRESS
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_updateCustomerAddress(request):
    data = {}
    # allShipAddressData = []
    try:
        if request.data.get('call') == 'updateShipAddress':
            cus_address = CustomerAddress.objects.get(id= request.data.get('shipAddressId'))
            cus_address.name = request.data.get('addressRecord')['name']
            cus_address.address = request.data.get('addressRecord')['address']
            cus_address.city = request.data.get('addressRecord')['city']
            cus_address.state = request.data.get('addressRecord')['state']
            cus_address.zipcode = request.data.get('addressRecord')['zipcode']
            cus_address.mobile = request.data.get('addressRecord')['mobile']
            cus_address.altMobile = request.data.get('addressRecord')['altMobile']
            
            cus_address.save()
            data['isSuccess'] = True
        
        # REQUEST TO SET SHIPPING DEFAULT
        elif request.data.get('call') == 'setDefault':
            # LOOP THROUGH THE CUSTOMER SHIPPING ADDRESS AND TURN DEFAULT 
            # SHIPPING ADDRESS FALSE
            cusAddresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
            
            for cusAdd in cusAddresses:
                if cusAdd.default == True:
                    cusAdd.default = False
                    cusAdd.save()
                
            # UPDATE THE NEW DEFAULT ADDRESS
            cus_address = CustomerAddress.objects.get(id= request.data.get('shipAddressId'))
            cus_address.default = True

            cus_address.save()
            data['isSuccess'] = True
        # REQUEST TO ADD SHIPPING ADDRESS 
        elif request.data.get('call') == 'addShipAddress':
            customer_info = Customer.objects.get(user=request.user.id)
            # WE WANT TO LIMIT THE NUMBER OF ADDRESS A USER CAN SAVE TO 5
            cus_addresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
            if (len(cus_addresses)) < 3:
                print(request.data.get('addressRecord')['name'])
                CustomerAddress.objects.create(
                    customer= customer_info,
                    address_type= 'Shipping Address',
                    name= request.data.get('addressRecord')['name'],
                    address= request.data.get('addressRecord')['address'],
                    city= request.data.get('addressRecord')['city'],
                    state= request.data.get('addressRecord')['state'],
                    zipcode= request.data.get('addressRecord')['zipcode'],
                    mobile= request.data.get('addressRecord')['mobile'],
                    altMobile= request.data.get('addressRecord')['altMobile']
                ) 

                # IF THIS IS THE FIRST SHIPPING ADDRESS THE CUSTOMER IS 
                # SAVING, SET IT AS DEFAULT SHIPPING ADDRESS
                cusAdd = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
                if len(cusAdd) == 1:
                    for cusAd in cusAdd:
                        cusAd.default = True
                        cusAd.save()
                data['isSuccess'] = True
            else:
                data['isSuccess'] = False
                data['error_msg'] = 'too much address to add'
        
    except Exception as e:
        data['isSuccess'] = False
        data['error_msg'] = e.args

            
    return JsonResponse(data, safe=False)


# ADMIN SETTING FUNCTION
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_adminSetting(request):
    data = {}
    storeData = []
    
    try:
        # CALL TO UPDATE VERIFIED STORE
        if request.data.get('call') == 'updateBtn':
            store_obj = Store.objects.get(id=request.data.get('id'))
            store_obj.verified = request.data.get('isActiveSwitch')
            store_obj.save()

            # data['isSuccess'] = True

        store_names = Store.objects.all()
        # WILL STAY AT THE TOP OF DROPDOWN LIST ON THE APP
        record = {
            'id': 0,
            'name': 'Select Store',
            'verified': False,
        }
        storeData.append(record)
        for storeName in store_names:
            record = {
                'id': storeName.id,
                'name': storeName.store_name,
                'verified': storeName.verified,
            }
            storeData.append(record)
        
        # CALL TO UPDATE CATEGORY RECORD
        if request.data.get('call') == 'updateCategory':
            category = Category.objects.get(id= request.data.get('id'))
            category.category = request.data.get('value')
           
            category.save()
            
            # data['isSuccess'] = True
        
        # CALL TO ADD CATEGORY
        if request.data.get('call') == 'addCategory':
            Category.objects.create(
                category = request.data.get('value')
            )
            # data['isSuccess'] = True
        
        # CALL TO UPDATE BRAND RECORD
        if request.data.get('call') == 'updateBrand':
            brand = Brand.objects.get(id= request.data.get('id'))
            brand.brand = request.data.get('value')
           
            brand.save()
            
            # data['isSuccess'] = True
        
        # CALL TO ADD BRAND
        if request.data.get('call') == 'addBrand':
            Brand.objects.create(
                brand = request.data.get('value')
            )
            # data['isSuccess'] = True

        data['isSuccess'] = True
        data['storeData'] = storeData
        
    except Exception as e:
        data['isSuccess'] = False
        data['error_msg'] = e.args

    return JsonResponse(data, safe=False)


# REQUEST TO GET ALL CATEGORIES
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_ptdCategoryBrand(request):
    data = {}
    menuList = []

    try:
        if request.data.get('call') == 'category':
            categories = Category.objects.all()
            
            for cat in categories:
                catData = {
                    'id': cat.id,
                    'category': cat.category
                }
                menuList.append(catData)
            data['menuList'] = menuList
            data['isSuccess'] = True
        elif request.data.get('call') == 'brand':
            brands = Brand.objects.all()
            for brand in brands:
                brandData = {
                    'id': brand.id,
                    'brand': brand.brand
                }
                menuList.append(brandData)
            data['menuList'] = menuList
            data['isSuccess'] = True
    except Exception as e:
        data['isSuccess'] = False
        data['error_msg'] = e.args

    return JsonResponse(data, safe=False)


