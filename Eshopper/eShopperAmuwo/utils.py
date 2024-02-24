import json
from homePage.models import *
from django.http import HttpResponseRedirect


def cookiesCart(request, payment_option):
    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}

    print('cart:', cart)
    items = []
    order = {'get_cart_total':0, 'get_cart_items':0,}
    cartItems = order['get_cart_items']
    isOut_of_stock = False
    inactive_ptd = []
    recentViewList = []
    
    for i in cart:
        try:
            # GET THE PRODUCT FROM STORE
            product = Product.objects.get(id=i)

            # CHECK IF PRODUCT IS INACTIVE, OUT-OF-STOCK AND IF STORE IS INACTIVE

            # OPTION WITH "CARD PAYMENT". THE REASON IS
            # BECAUSE IF PAYMENT HAVE BEEN RECIEVED AND RECORD WAS NOT CREATED ON THE DATABASE CREATING ANOTHER RECORD
            # ON THE DB WILL BE INPOSSIBLE TO RECONSILE AS THE AMOUNT OF ITEM PURCHASE WILL NOT TALLY WITH WHAT WAS INITIALLY PAID 
            # AND THERE IS NO WAY THE INITIAL PAYMENT CAN BE TIE TO THE NEW ITEMS PURCHASED 
            if payment_option != 'Card Payment':
                if product.active == False or product.out_of_stock == True or product.store.active == False:
                    inactive_item_dic = {
                        'ptd_id': i
                    }
                    inactive_ptd.append(int(i))
                    isOut_of_stock = True
            
            new_price = round(product.price - ((product.price / 100) * product.discount), 2)
            total = new_price * cart[i]["quantity"]
            order['get_cart_total'] += total
            order['get_cart_items'] += cart[i]["quantity"]

            item = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': new_price,
                    'imageURL': product.imageURL,
                    'out_of_stock': product.out_of_stock,
                    'active': product.active,
                    'store': product.store
                },
                'quantity': cart[i]['quantity'],
                'get_total': total
            }
            items.append(item)
            cartItems += cart[i]["quantity"]
            
        except:
            pass
    # GET THE ITEM CATEGORY LIST
    categoryList = Category.objects.all()

    return {'cartItems': cartItems, 'order': order, 'items': items, 'isOut_of_stock': isOut_of_stock, 
    'inactive_ptd': inactive_ptd, 'categoryList': categoryList, 'recentViewList': recentViewList}


def cartData(request):
    isOut_of_stock = False
    inactive_ptd = []
    shippingAddress = ''
    allShippingAddresses = ''
    wishLists = ''
    cat_id = ''

    # I WANT TO GET THE ID OF THE FIRST CATEGORY OF LEVEL 0, 
    # SINCE IT'S ORDER-NAME. THIS WILL BE USED ON THE HOMEPAGE 
    # TEMPLATE WHEN THE USER CLICK ON VIEW ALL CATEGORY.
    cats = Category.objects.filter(level = 0) 
    for cat in cats:
        cat_id = cat.id
        break

    
    if request.user.is_authenticated:
        try:
            shippingAddress = CustomerAddress.objects.get(customer=request.user.customer.id, address_type='Shipping Address', default=True)
        except:
            pass
        customer = request.user.customer
        print('USER IS VALID')
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()

        # CHECK IF ITEMS EXIST AND UPDATE CURRENT PRICE OF PRODUCT IN THE CART
        if items:
            for item in items:
                item.unit_price = item.get_unit_price
                item.line_total = item.get_total
                item.save()

        # CHECKING IF ITEM IS OUT OF STOCK...!
        for itm in items:
            if itm.product.out_of_stock == True or itm.product.active == False or itm.product.store.active == False:
                isOut_of_stock = True
                break
            
        # REQUEST TO REMOVE OUT OF STOCK ITEM FROM CART
        if request.method == 'POST':
            for item in items:
                if request.POST.get('remove_item_frm_cart') == 'Remove out of stock or inactive item':
                    # REMOVE OUT OF STOCK OR INACTIVE OR ITEM FROM INACTIVE STORE ITEM FROM CART
                    if item.product.out_of_stock == True or item.product.active == False or item.product.store.active == False:
                        item.delete()
                    
            isOut_of_stock = False
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items

        #  GET ALL SHIPPING ADDRESS FOR THE CUSTOMER
        allShippingAddresses = CustomerAddress.objects.filter(customer=request.user.customer.id, address_type='Shipping Address')
        # GET WISH LIST ITEMS
        wishLists = WishList.objects.filter(customer_id=request.user.customer.id).order_by('-date_added')
        wishLists = productRecord(request, wishLists)

        # GET RECENTLY VIEW ITEMS
        recentViewList = getRecentlyViewItem(request)
        
        # GET THE ITEM CATEGORY LIST. FOR THE NAVBAR CATEGORY DROPDOWN LIST
        categoryList = Category.objects.all() 

    else:
        cookieData = cookiesCart(request, '')
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']
        recentViewList = cookieData['recentViewList']
        isOut_of_stock = cookieData['isOut_of_stock']
        inactive_ptd = json.dumps(cookieData['inactive_ptd']) 
        categoryList = cookieData['categoryList']
    return {'cartItems': cartItems, 'order': order, 'items': items, 
    'isOut_of_stock': isOut_of_stock, 'inactive_ptd': inactive_ptd, 
    'shippingAddress': shippingAddress, 'allShippingAddresses': allShippingAddresses, 
    'wishLists': wishLists, 'recentViewList': recentViewList, 'categoryList': categoryList,
    'cat_id': cat_id}


def guestOrder(request, data, payment_option):
    print('User is not logged in...')
    guestOrderData = {}

    print('COOKIES:', request.COOKIES)
    name = data['form']['name']
    email = data['form']['email']
    order = ''
    customer = ''
    cookieData = cookiesCart(request, payment_option)
    items = cookieData['items']
    # CHECKING FOR THE LAST TIME IF ANY OF THE ITEM(S) IS INACTIVE/OUT-OF-STOCK
    invalidItm = {'invalid_item': False}
    if cookieData['isOut_of_stock'] == True:
        customer = ''
        order = ''
        invalidItm = {'invalid_item': True}
        return customer, order, invalidItm, guestOrderData

    try:
        customer, created = Customer.objects.get_or_create(email=email)
        customer.name = name
        customer.save()
    except Exception as e:
        raise e
        
    order = Order.objects.create(customer=customer, complete=False)

    # CREATE THE GUEST ORDER-ITEMS ON THE DATABASE
    for item in items:
        product = Product.objects.get(id=item['product']['id'])
        if product.discount > 0:
            new_price = round(product.price - ((product.price / 100) * product.discount), 2)
        else:
            new_price = product.price
        line_total = new_price * item['quantity']
        orderItem = OrderItem.objects.create( product=product, order=order, quantity=item['quantity'], 
            unit_price=new_price, line_total=line_total, 
            store_name=product.store.store_name
            )
    order_items = order.orderitem_set.all()
    guestOrderData = {
        'guest_name': name,
        'guest_email': email,
        'guest_items': order_items
    }


    return customer, order, invalidItm, guestOrderData


def weightAverageRating(request, ptdComments):
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
    data = {}
    customLatestFewComments = []
    weighted_average_rating = 0
    for comment in ptdComments:
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
        # THIS 'IF' STATEMENT WAS NEVER USED WHEN THIS METHOD WAS CALLED
        # I HAVE NOT REMOVE IT BECAUSE I STILL WANT TO CONFIRM AND BE SURE
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

    if ptdComments:

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
    
    
    return { 'weighted_average_rating': weighted_average_rating, 'counter': counter }


# CUSTOMIZE PRODUCT RECORD LIST THAT HOLD WISHLIST RECORD FOR EACH PRODUCT
def productRecord(request, ptdList):
    productList = []
    
    for _ptdList in ptdList:
        comments = Comment.objects.filter(product= _ptdList.product.id)
        averageStarRated = weightAverageRating(request, comments)
        
        ptdRecord = {
            'id': _ptdList.product.id,
            'name': _ptdList.product.name,
            'description': _ptdList.product.description,
            'category': _ptdList.product.category,
            'brand': _ptdList.product.brand,
            'price': _ptdList.product.price,
            'new_price': _ptdList.product.new_price,
            'imageURL': _ptdList.product.imageURL,
            'mfgDate': _ptdList.product.mfgDate,
            'expDate': _ptdList.product.expDate,
            'discount': _ptdList.product.discount,
            'out_of_stock': _ptdList.product.out_of_stock,
            'store': _ptdList.product.store,
            'active': _ptdList.product.active,
            # 'isHeartFill': False,
            'averageStarRated': averageStarRated['weighted_average_rating'],
            'counter': averageStarRated['counter']
        }
        productList.append(ptdRecord)
    return productList



# THE LOGIC OF THIS FUNCTION IS USED TO CREATE / MANAGE RECENTLY VIEWED ITEM
# ON THE DATABASE
# NOTE: THIS FUNCTION IS CALLED BY BOTH DESKTOP AND MOBILE APP
def manageRecentViewItm(request, product):
    isSamePtdRecentViewItem = False

    # BLOCK OF CODE TO ADD PRODUCT TO RECENT VIEWED ITEM TABLE
    # WE DON'T WANT TO STORE MORE THAN 15 ITEMS FOR EACH CUSTOMER
    # WHEN THE 16th ITEM IS STORED, DELETE THE 1st ITEM ON THE TABLE

    recentViewedItems = RecentViewItems.objects.filter(customer=request.user.customer)
    if recentViewedItems:
        if recentViewedItems.count() < 10: # NOT MORE THAN 10 RECENT VIEW ITEM ADDED TO DB FOR EACH USER
            for recentViewItem in recentViewedItems:
                # IF THE PTD VIEWED ALREADY EXIST IN DB, DELETE THE OLD ONE AND CREATE A NEW ONE
                # THIS WILL BE CREATED WITH THE LATEST TIME. IT WILL DISPLAY FIRST WHEN LISTING 
                # ON THE FONT END
                if recentViewItem.product == product:
                    isSamePtdRecentViewItem = True
                    recentViewItem.delete()
                    RecentViewItems.objects.create(
                        product = product,
                        customer = request.user.customer
                    )
                    break
            # AFTER LOOPING AND THE PTD HAVE NOT BEEN ADDED BEFORE, SINCE IT'S LESS THAN
            # THE MAXIMUM NUMBER REQUIRED PER USER, THE CONDITION IS EXECUTED TO CREATE THE PRODUCT.
            if isSamePtdRecentViewItem == False:
                RecentViewItems.objects.create(
                    product = product,
                    customer = request.user.customer
                )    
        else:
            # SINCE THE USER HAVE REACH MAXIMUM NUMBER, CHECK IF THE PTD HAVE BEEN SAVED BEFORE, IF YES,
            # DELETE IT AND CREATE ANOTHER ONE WITH THE LATEST TIME STAMP. THIS TIME STAMP WILL ENABLE
            # THE ITEM BE ON THE FIRST TO DISPLAY ON THE FONT END
            for recentViewItem in recentViewedItems:
                if recentViewItem.product == product:
                    isSamePtdRecentViewItem = True
                    recentViewItem.delete()
                    RecentViewItems.objects.create(
                        product = product,
                        customer = request.user.customer
                    )
                    break
            # IF THE ITEM IS NOT IN THE DB BEFORE, DELETE THE LAST ITEM AND SAVE THE CURRENT ONE
            if isSamePtdRecentViewItem == False:
                for viewItem in recentViewedItems:
                    viewItem.delete()
                    break
                RecentViewItems.objects.create(
                    product = product,
                    customer = request.user.customer
                )
    # CREATE THE RECORD IF THIS IS THE FIRST TIME 
    else:
        RecentViewItems.objects.create(
            product = product,
            customer = request.user.customer
        )


# NOTE: THIS FUNCTION IS CALLED FROM BOTH DESKTOP AND MOBILE APP
# IT IS USED TO GET RECENTLY VIEWED ITEMS FOR EVERY CUSTOMER 
def getRecentlyViewItem(request):
    # GET RECENTLY VIEW ITEMS
    recentViewList = []
    counter = 0
    recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer).order_by('date_added')
    
    # FOR STATEMENT TO DISPLAY FIRST 10 RECENT VIEW ITEMS
    for recentViewItem in recentViewItems:
        counter += 1
        viewItem = {
            'id': recentViewItem.product.id,
            'name': recentViewItem.product.name,
            'imageURL': recentViewItem.product.imageURL,
            'price': recentViewItem.product.price,
            'discount': recentViewItem.product.discount,
            'new_price': recentViewItem.product.get_unit_price,
            'category': recentViewItem.product.category.category,
        }
        recentViewList.append(viewItem)
        if counter == 10:
            counter = 0
            break 
    
    return recentViewList


# FUNCTION CALL FROM CART PAGE ROW ITEM. THE FOLLOWING LOGIC IS PERFORM
# 1. IT UPDATE THE DATABASE WITH THE INPUTTED QUANTITY. IF THE QUANTITY
# INPUTTED IS ZERO, THE ITEM ROW IS DELETED
# 2. IF THE DELETE BUTTON ON THE ITEM ROW IS CLICKED, IT COMES WITH 
# VALUE ZERO AND THE SECOND IF CONDITION IS ALWAYS EXECUTED
def updateInputItemRow(request, ptdId, val):
    order = Order.objects.get(customer=request.user.customer, complete=False)
    product = Product.objects.get(id=ptdId)

    orderItem = OrderItem.objects.get(order=order, product=product)

    if val > 0:
        orderItem.quantity = val
        orderItem.unit_price = (orderItem.get_unit_price)
        orderItem.line_total = (orderItem.get_total)
        
        orderItem.save()
    elif val <= 0:
        orderItem.delete()
