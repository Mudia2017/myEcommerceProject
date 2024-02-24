from homePage.models import Customer, Product, Order, OrderItem
from homePage.api.serializers import *
from homePage.api.views import *


def getCartItems(order):
    # ENSURE USER IS AUTHENTICATED. GET THE ORDER CREATED AND
    # UPDATE ORDER-ITEM BASE ON ACTION (ADD OR REMOVE) RECEIVED
    data = {}
    cart_list = []
    grandTotal = 0
    items = order.orderitem_set.all()
    cartCounter = order.get_cart_items

    for item in items:
        new_data = {
            "id": item.product.id,
            "name": item.product.name,
            "price": float(item.get_unit_price),
            "quantity": item.quantity,
            "image": "http://192.168.43.50:8000"+item.product.imageURL,
            "mfgDate": item.product.mfgDate,
            "expDate": item.product.expDate,
            "discount": float(item.product.discount),
            "line_total": float(item.get_total),
            "out_of_stock": bool(item.product.out_of_stock),
            "active": item.product.active,
            "activeStore": item.product.store.active
        }

        cart_list.append(new_data)
        grandTotal += item.get_total

    data["cart item"] = cart_list
    data["cart total count"] = cartCounter
    data["grand total"] = float( grandTotal)
    return data


def confirmCartItems(order):
    response = ''
    orderItems = order.orderitem_set.all().order_by('store_name')  # ITEMS WERE ORDERED BY STORE NAME SO THAT EMAILS CAN BE SENT TO STORE OWN TO MAKE ORDERD ITEM AVALIABLE
    for item in orderItems:
        if item.product.active == False or item.product.out_of_stock == True or item.product.store.active == False:
            print('All items in the cart are not valid...!')
            response =  "item(s) not valid"
    return response


def createGuestOrder(request):
    print('You are a guest user...')
    guestName = request.data['shippingInfo']['name']
    guestEmail = request.data['shippingInfo']['email']
    guestCartData = request.data['guestCartData']
    order = ''
    guestOrderData = {}
    isInactiveItem = False
    guestUser = ''
    for ptdId in guestCartData:
        print(ptdId['guestCartPtdId'])
        product = Product.objects.get(id= ptdId['guestCartPtdId'])
        print(ptdId)
        if product.out_of_stock == True or product.active == False or product.store.active == False:
            isInactiveItem = True
            break
    if isInactiveItem == False:
        
        try:
           
            print('all active product')
            guestUser = Customer.objects.create(name=guestName, email=guestEmail)
            order = Order.objects.create(customer=guestUser, complete=False)
            
            for guestItem in guestCartData:
                product = Product.objects.get(id= guestItem['guestCartPtdId'])
                line_total = product.get_unit_price * guestItem['guestCartPtdQuantity']
                unitPrice = product.get_unit_price
                
                OrderItem.objects.create(product=product, order=order, quantity=guestItem['guestCartPtdQuantity'],
                unit_price=product.get_unit_price, line_total=line_total, store_name=product.store.store_name)
            
            guestOrderItems = order.orderitem_set.all()
            guestOrderData = {
                'guest_items': guestOrderItems
            }
        except Exception as e:
            raise e

    return guestUser, order, guestOrderData, isInactiveItem



# ONLY FOR AUTHENTICATED USER.
# USE THE CUSTOMER ID TO CHECK IF IT EXIST IN THE DATABASE
# USE THE CUSTOMER ID WITH COMPLETE-ORDER TO FALSE TO SEARCH IF AN OPEN ORDER EXIST
# USE THE LIST OF REQUESTED ORDER TO LOOP IF IT DOESN'T CREATE ONE THROUGH SERIALIZING

def addMultiItemsToCart(request):
    isSuccess = False
    inactive_outOfStock = False
    cartCounter = 0
    if request.user.is_authenticated:
        selectedItems = request.data.get('selectedList')
        try:
            customer = Customer.objects.get(id= request.data.get('customerId'))
            try:
                
                order = Order.objects.get(customer=customer.id, complete=False)
            except Order.DoesNotExist:
                serializer = OrderSerializer(data=request.data)
                if serializer.is_valid():
                    print('SERIALIZER PASSED')
                    order = serializer.save()

            # LOOP THROUGH THE REQUESTED ITEMS, CHECK IF THE ORDER-ITEM EXIST BEFORE,
            # IF IT DOES, ADD TO THE EXISTING ONE, ELSE CREATE THE ORDER-ITEM THEN 
            # ADD THE ITEM TO THE CART AND SAVE. THEN LOOP THROUGH THE ITEM LIST AGAIN...
            for selectedItem in selectedItems:
                product = Product.objects.get(id=selectedItem['ptdId'])

                # BEFORE ADDING OR CREATING THE ORDER-ITEM, WE NEED TO CHECK THE FOLLOWING
                # (1) IF THE ITEM IS ACTIVE
                # (2) IF THE STORE ITEM IS ACTIVE
                # (3) IF THE ITEM IS IN-STOCK BEFORE ADDING...
                if product.active == True and product.store.active == True and product.out_of_stock == False:

                    try:
                        orderItem = OrderItem.objects.get(order=order, product=product)
                    except OrderItem.DoesNotExist:
                        orderItem = OrderItem.objects.create(order=order, product=product)
                    
                    orderItem.quantity = (orderItem.quantity + 1)
                    orderItem.store_name = (product.store.store_name)
                    orderItem.unit_price = (orderItem.get_unit_price)
                    orderItem.line_total = (orderItem.get_total)
                    
                    orderItem.save()
                else:
                    inactive_outOfStock = True
            
            isSuccess = True
        except Exception as e:
            e.args
            # raise e
        
    return isSuccess, inactive_outOfStock


def getPtdBrand(self):
    try:
        ptdBrand = self.brand.id
    except:
        ptdBrand = '0'
    return ptdBrand


def getSameCategoryPtdList(request, limit):
    counter = 0
    ptd_categoryData = []

    category = Category.objects.get(category=request.data['categoryName'])
    ptd_same_category = Product.objects.filter(category=category.id, active=True, store__active__contains=1)
    for product in ptd_same_category:
        if product.id != request.data['ptdId']:
            ptd_comment = Comment.objects.filter(product=product.id)
            averageStarRated = weightAverageRating(request, ptd_comment)
            ptd_record = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': product.category.category,
                'brand': product.brand.brand, 
                'price': product.price,
                'new_price': product.get_unit_price,
                'imageURL': "http://192.168.43.50:8000"+product.imageURL,
                'mfgDate': (product.mfgDate),
                'expDate': product.expDate,
                'discount': product.discount,
                'out_of_stock': product.out_of_stock,
                'store': {
                    'store_name': product.store.store_name,
                    'store_address': product.store.store_address,
                    'city': product.store.city,
                    'LGA': product.store.LGA,
                    'state': product.store.state,
                    'email': product.store.email,
                    'mobile': product.store.mobile,
                    'altMobile': product.store.altMobile,
                    'verified': product.store.verified,
                    'active': product.store.active
                },
                'active': product.active,
                'averageStarRated': averageStarRated['myDictionary']['weighted_average_rating'],
                'counter': averageStarRated['myDictionary']['counter']
            }
            ptd_categoryData.append(ptd_record)
            counter += 1
            if counter == limit:
                break

    return ptd_categoryData



# THIS ARGUEMENT PASSED IN WAS ALL THE COMMENTS RECEIVED FROM ONE CATEGORY PRODUCT
# WE WILL LOOP TO COUNT THE NUMBER OF COMMENTS, SUM THE STAR RATINGS AND COMPUTE 
# THE WEIGHT-AVERAGE-RATE. ON THE FONT-END, FOR EACH OF THE CATEGORY OR SIMILAR
# PRODUCT, THE WEIGHT-AVERAGE-RATE WILL REPRESENT THE NUMBER OF STAR(S) WHILE THE
# COUNTER WILL REPRESENT THE NUMBER OF COMMENT(S).
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
    weighted_average_rating = 0
    customLatest_FewComments = []
    
    myDictionary = {}
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

        # USE TO BUILD THE FIRST FOUR COMMENTS ON THE DETAIL PAGE
        if counter < 5:
            customComment = {
            'product': comment.product,
            'customer': comment.customer,
            'subject': comment.subject,
            'comment': comment.comment,
            'rate': comment.rate,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at
        }
            customLatest_FewComments.append(customComment)


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

        
        # CALCULATE WEIGHTED AVERAGE FOR EACH PRODUCT
        weighted_average_rating = (((5 * five_star) + (4.5 * four_half_star) + (4 * four_star) + (3.5 * three_half_star) + (3 * three_star) + (2.5 * two_half_star) + (2 * two_star) + (1.5 * one_half_star) + (1 * one_star)) / (five_star + four_half_star + four_star + three_half_star + three_star + two_half_star + two_star + one_half_star + one_star))
        #  USED TO CHECK IF THERE IS NO CUSTOMER REVIEW
        isCusReview = True

        myDictionary['five_star_percent'] = five_star_percent
        myDictionary['four_star_percent'] = four_star_percent
        myDictionary['three_star_percent'] = three_star_percent
        myDictionary['two_star_percent'] = two_star_percent
        myDictionary['one_star_percent'] = one_star_percent
    else:
        myDictionary['five_star_percent'] = 0
        myDictionary['four_star_percent'] = 0
        myDictionary['three_star_percent'] = 0
        myDictionary['two_star_percent'] = 0
        myDictionary['one_star_percent'] = 0
    myDictionary['customLatest_FewComments'] = customLatest_FewComments
    myDictionary['weighted_average_rating'] = weighted_average_rating
    myDictionary['counter'] = counter
    
    
    return { 'myDictionary': myDictionary }


def authHomepageData(request):
    try:
        recentViewList = []
        watchItemList = []
        counter = 0
        _counter = 0
        recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer)
        
        # FOR STATEMENT TO DISPLAY FIRST 15 RECENT VIEW ITEMS
        for recentViewItem in recentViewItems:
            counter += 1
            viewItem = {
                'id': recentViewItem.product.id,
                'name': recentViewItem.product.name,
                'imageURL': "http://192.168.43.50:8000"+recentViewItem.product.imageURL,
                'price': recentViewItem.product.price,
                'discount': recentViewItem.product.discount,
                'new_price': recentViewItem.product.get_unit_price,
                'category': recentViewItem.product.category.category
            }
            recentViewList.append(viewItem)
            if counter == 15:
                counter = 0
                break

        watchedItems = WishList.objects.filter(customer= request.user.customer)

        # FOR STATEMENT TO DISPLAY FIRST 15 WATCHED ITEMS
        for watchItem in watchedItems:
            _counter += 1
            watchPtd = {
                'id': watchItem.product.id,
                'name': watchItem.product.name,
                'imageURL': "http://192.168.43.50:8000"+watchItem.product.imageURL,
                'price': watchItem.product.price,
                'discount': watchItem.product.discount,
                'new_price': watchItem.product.get_unit_price,
                'category': watchItem.product.category.category
            }
            
            watchItemList.append(watchPtd)
            if _counter == 15:
                _counter = 0
                break
                
    except:
        pass
    return {'recentViewList': recentViewList, 'watchItemList': watchItemList
     }



def publicRequest(request):
    try:
        dailyDeals = []
        dailyCat = []
        dailyBrands = []
        ptdData = []
        counter = 0
        _counter = 0
        _count = 0
        randomPtds = Product.objects.filter(active=True, store__active__contains=1).order_by('?')
        randomCats = Category.objects.order_by('?')
        randomBrands = Brand.objects.order_by('?')
        
        # FOR STATEMENT TO DISPLAY DAILY DEALS
        for randomPtd in randomPtds:
            counter += 1
            item = {
                'id': randomPtd.id,
                'name': randomPtd.name,
                'imageURL': "http://192.168.43.50:8000"+randomPtd.imageURL,
                'price': randomPtd.price,
                'discount': randomPtd.discount,
                'new_price': randomPtd.get_unit_price,
                'category': randomPtd.category.category
            }
            dailyDeals.append(item)
            if counter == 15:
                counter = 0
                break
        
        # RANDOMLY GET CATEGORY
        for randomCat in randomCats:
            _counter += 1
            _item = {
                'id': randomCat.id,
                'category': randomCat.category,
                'tree_id': randomCat.tree_id,
                'level': randomCat.level,
                'image': "http://192.168.43.50:8000"+ randomCat.imgURL,
                'parent_id': randomCat.parent_id
            }
            dailyCat.append(_item)
            if _counter == 6:
                break
        
        # RANDOMLY GET BRANDS
        for randomBrand in randomBrands:
            _count += 1
            brandItem = {
                'id': randomBrand.id,
                'brand': randomBrand.brand
            }
            dailyBrands.append(brandItem)
            if _count == 6:
                break
        
        # USED FOR SEARCHING PRODUCTS WITH THEIR CATEGORY NAME 
        for ptd in randomPtds:
            ptd_record = {
                'id': ptd.id,
                'name': ptd.name,
                'description': ptd.description,
                'category': ptd.category.category,
                'brand': ptd.brand.brand,
                'price': ptd.price,
                'new_price': ptd.get_unit_price,
                'imageURL': "http://192.168.43.50:8000"+ptd.imageURL,
                'mfgDate': ptd.mfgDate,
                'expDate': ptd.expDate,
                'discount': ptd.discount,
                'out_of_stock': ptd.out_of_stock,
                'store': ptd.store.store_name,
                'active': ptd.active,
            }
            ptdData.append(ptd_record)
    except Exception as e:
        e.args
    return {'dailyDeals': dailyDeals, 'dailyCat': dailyCat, 'dailyBrands': dailyBrands,
    'ptdData': ptdData
     }


def customisePtdRecord(request, products, favoriteItems):
    ptd_data = []
    for product in products:
        ptd_comment = Comment.objects.filter(product=product.id)
        averageStarRated = weightAverageRating(request, ptd_comment)
        isFavorite = False
        for favoriteItem in favoriteItems:
            if favoriteItem.product.id == product.id:
                isFavorite = True
                break
        ptd_record = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category.category,
            'brand': product.brand.brand,
            'price': product.price,
            'new_price': product.get_unit_price,
            'imageURL': "http://192.168.43.50:8000"+product.imageURL,
            'mfgDate': product.mfgDate,
            'expDate': product.expDate,
            'discount': product.discount,
            'out_of_stock': product.out_of_stock,
            'store': {
                'store_name': product.store.store_name,
                'store_address': product.store.store_address,
                'city': product.store.city,
                'LGA': product.store.LGA,
                'state': product.store.state,
                'email': product.store.email,
                'mobile': product.store.mobile,
                'altMobile': product.store.altMobile,
                'verified': product.store.verified,
                'active': product.store.active
            },
            'active': product.active,
            'isFavorite': isFavorite,
            'averageStarRated': averageStarRated['myDictionary']['weighted_average_rating'],
            'counter': averageStarRated['myDictionary']['counter']
        }

        ptd_data.append(ptd_record)

    return ptd_data

