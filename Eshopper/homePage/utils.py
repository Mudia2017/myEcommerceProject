import json
from . models import *
from django.shortcuts import render, redirect
from eShopperAmuwo.utils import weightAverageRating


def authGetHomepageData(request):
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
                'imageURL': recentViewItem.product.imageURL,
                'price': recentViewItem.product.price,
                'discount': recentViewItem.product.discount,
                'new_price': recentViewItem.product.get_unit_price
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
                'imageURL': watchItem.product.imageURL,
                'price': watchItem.product.price,
                'discount': watchItem.product.discount,
                'new_price': watchItem.product.get_unit_price
            }
            watchItemList.append(watchPtd)
            if _counter == 15:
                _counter = 0
                break

        # if request.method == 'POST':
        #     call = json.loads(request.body)
        #     print(call)
        #     if call == 'recentViewItem':
        #         # REDIRECT TO TEMPLATE WHERE YOU VIEW ALL ITEMS
        #         context = {}
        #         # return render(request, 'homepage/view_all.html', context)
        #         # recentViewItems = RecentViewItems.objects.filter(customer= request.user.customer)
                
    except:
        pass
    return {'recentViewItems': recentViewItems, 'watchedItems': watchedItems, 'recentViewList': recentViewList,
    'watchItemList': watchItemList
     }


# CUSTOMIZE PRODUCT RECORD LIST THAT HOLD WISHLIST RECORD FOR EACH PRODUCT
def productRecord(request, ptdList, wishList):
    productList = []
    
    for _ptdList in ptdList:
        comments = Comment.objects.filter(product= _ptdList.id)
        averageStarRated = weightAverageRating(request, comments)
        isMatching = False
        for _wishList in wishList:
            if _ptdList.id == _wishList.product.id:
                ptdRecord = {
                    'id': _ptdList.id,
                    'name': _ptdList.name,
                    'description': _ptdList.description,
                    'category': _ptdList.category,
                    'brand': _ptdList.brand,
                    'price': _ptdList.price,
                    'new_price': _ptdList.get_unit_price,
                    'imageURL': _ptdList.imageURL,
                    'mfgDate': _ptdList.mfgDate,
                    'expDate': _ptdList.expDate,
                    'discount': _ptdList.discount,
                    'out_of_stock': _ptdList.out_of_stock,
                    'store': _ptdList.store,
                    'active': _ptdList.active,
                    'isHeartFill': True,
                    'averageStarRated': averageStarRated['weighted_average_rating'],
                    'counter': averageStarRated['counter']
                }
                productList.append(ptdRecord)
                isMatching = True
                break
        if isMatching == False:
            ptdRecord = {
                'id': _ptdList.id,
                'name': _ptdList.name,
                'description': _ptdList.description,
                'category': _ptdList.category,
                'brand': _ptdList.brand,
                'price': _ptdList.price,
                'new_price': _ptdList.get_unit_price,
                'imageURL': _ptdList.imageURL,
                'mfgDate': _ptdList.mfgDate,
                'expDate': _ptdList.expDate,
                'discount': _ptdList.discount,
                'out_of_stock': _ptdList.out_of_stock,
                'store': _ptdList.store,
                'active': _ptdList.active,
                'isHeartFill': False,
                'averageStarRated': averageStarRated['weighted_average_rating'],
                'counter': averageStarRated['counter']
            }
            productList.append(ptdRecord)
    return productList


# UPDATE CART RECORD 
def updateCartItem(request, ptdId, action):
    customer = request.user.customer
    product = Product.objects.get(id=ptdId)
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

    return 'success'


def generalRequest(request):
    try:
        dailyDeals = []
        dailyCat = []
        dailyBrands = []
        counter = 0
        _counter = 0
        _count = 0
        randomPtds = Product.objects.filter(active=True, store__active__contains=1).order_by('?')
        randomCats = Category.objects.filter(level__in= [0, 1] ).order_by('?')
        randomBrands = Brand.objects.order_by('?')

        # FOR STATEMENT TO DISPLAY DAILY DEALS
        for randomPtd in randomPtds:
            counter += 1
            item = {
                'id': randomPtd.id,
                'name': randomPtd.name,
                'imageURL': randomPtd.imageURL,
                'price': randomPtd.price,
                'discount': randomPtd.discount,
                'new_price': randomPtd.get_unit_price
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
                'image': randomCat.imgURL,
                'parent_id': randomCat.parent_id
            }
           
            dailyCat.append(_item)
            if _counter == 10:
                break
        
        # RANDOMLY GET BRANDS
        for randomBrand in randomBrands:
            _count += 1
            brandItem = {
                'id': randomBrand.id,
                'brand': randomBrand.brand
            }
            dailyBrands.append(brandItem)
            if _count == 10:
                break
    except Exception as e:
        e.args
        pass
    return {'dailyDeals': dailyDeals, 'dailyCat': dailyCat, 'dailyBrands': dailyBrands,
   
     }


# EDIT CUSTOMER ORDER AFTER SHOPPING ITEMS WAS SUBMITTED 
def editCusOrder(request):
    data = json.loads(request.body)
    item_id = data['item_id']
    action = data['action']
    trans_id = data['trans_id']
    selected_value = data['selected_value'] # USED TO UPDATE ORDER STATUS
    private_note = data['private_note']
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
        elif selected_value == 'cancelled':
            order.status = 'Cancelled'
            order.order_private_note = private_note
        elif selected_value == 'rejected':
            order.status = 'Rejected'
            order.order_private_note = private_note
        order.save()
        serverMsg = 'successful'
    except Exception as e:
        serverMsg = e.args

    return {'serverMsg': serverMsg}


# CATEGORY DATA
def categoryData(request, pk):
    try:
        categoryListRecord = []
        cat = Category.objects.get(id = pk)
        if cat.level == 0:
            levelOnes = Category.objects.filter(parent_id = pk)
            for levelOne in levelOnes:
                levelTwos = Category.objects.filter(parent_id = levelOne.id)
                cateRecord = {
                    'catSubTitle': levelOne.category, # GET THE NAME OF LEVEL ONE (DISPLAY ON THE RIGHT SIDE OF THE SCREEN)
                    'levelTwos': levelTwos, # CHILDREN OF LEVEL ONE (THIS WILL DISPLAY UNDER ITS' CATEGORY ON THE RIGHT SIDE OF THE SCREEN)
                    'imageURL': levelOne.imgURL # IMAGE OF CATEGORY ONE (DISPLAY ON RIGHT SIDE OF THE SCREEN)
                }
                categoryListRecord.append(cateRecord)
        elif cat.level == 1:
            levelOnes = Category.objects.filter(parent_id = cat.parent_id)
            for levelOne in levelOnes:
                levelTwos = Category.objects.filter(parent_id = levelOne.id)
                cateRecord = {
                    'catSubTitle': levelOne.category,
                    'levelTwos': levelTwos,
                    'imageURL': levelOne.imgURL
                }
                categoryListRecord.append(cateRecord)
        
    except Exception as e:
        serverError = e.args

    return {'cat_title': cat, 'categoryListRecord': categoryListRecord}


def sideCategoryList(request, pk):
    try:
        sameTreeId = []
        categoryProducts = []
        counter = 0
        selectBrndCount = 0
        isFilterBrandVisted = False
        selectBrandList = []
        brands = Brand.objects.all()
        cat = Category.objects.get(id = pk)
        childrenCatList = Category.objects.filter(parent_id = cat.parent_id)
        parentCategory = Category.objects.get(id = cat.parent_id)
        if request.GET.get('filter_cat') == 'filterCategory':
            if cat.level > 1:
                sameTree = Category.objects.filter(tree_id = cat.tree_id)
                for tree in sameTree:
                    if tree.level > 1:
                        sameTreeId.append(tree.id)
                for catId in sameTreeId:
                    products = Product.objects.filter(category_id= catId, active=True, store__active__contains=1)
                    
                    for ptd in products:
                        record = recordProduct(ptd)
                        categoryProducts.append(record)
                        counter += 1
        elif request.GET.get('filter_cat') == 'sameCatLevelOnly':
            for tree in childrenCatList:
                sameTreeId.append(tree.id)
            for catId in sameTreeId:
                products = Product.objects.filter(category_id= catId, active=True, store__active__contains=1)
                    
                for ptd in products:
                    record = recordProduct(ptd)
                    categoryProducts.append(record)
                    counter += 1
        elif request.GET.get('filterCat') == 'Apply' and request.GET.getlist('chckbox_id'):
            brandIds = request.GET.getlist('chckbox_id')
            selectBrandList, selectBrndCount, isFilterBrandVisted, counter, categoryProducts, childrenCatList = processCatFilter(pk, brandIds)
            
        elif request.GET.get('unselect') and request.GET.getlist('chckbox_id'):
            brandIds = request.GET.getlist('chckbox_id')
            removeFrmList = request.GET.get('unselect')
            brandIds.remove(removeFrmList)
            if not brandIds:
                categoryProducts = Product.objects.filter(category_id= pk, active=True, store__active__contains=1)
                counter = categoryProducts.count()
            else:
                selectBrandList, selectBrndCount, isFilterBrandVisted, counter, categoryProducts, childrenCatList = processCatFilter(pk, brandIds)
        else:
            categoryProducts = Product.objects.filter(category_id= pk, active=True, store__active__contains=1)
            counter = categoryProducts.count()
    except Exception as e:
        serverError = e.args
    
    return {'categoryName': cat, 'childrenCatList': childrenCatList, 'categoryProducts': categoryProducts, 'parentCategory': parentCategory,
    'counter': counter, 'brands': brands, 'isFilterBrandVisted': isFilterBrandVisted, 'selectBrandList': selectBrandList,
    'selectBrndCount': selectBrndCount}


def processCatFilter(pk, brandIds):
    selectBrandList = []
    selectBrndCount = 0
    counter = 0
    sameTreeId = []
    categoryProducts = []
    cat = Category.objects.get(id = pk)
    childrenCatList = Category.objects.filter(parent_id = cat.parent_id)
    for brnd in brandIds:
        brn = Brand.objects.get(id= brnd)
        rec = {
            'id': brn.id,
            'brand': brn.brand
        }
        selectBrandList.append(rec)
        selectBrndCount += 1
    for tree in childrenCatList:
        sameTreeId.append(tree.id)

    for catId in sameTreeId:
        for brandId in brandIds:
            products = Product.objects.filter(category_id= catId, brand= brandId, active=True, store__active__contains=1)
                
            for ptd in products:
                record = recordProduct(ptd)
                categoryProducts.append(record)
                counter += 1
    isFilterBrandVisted = True

    return selectBrandList, selectBrndCount, isFilterBrandVisted, counter, categoryProducts, childrenCatList


def recordProduct(ptd):
    record = {
        'id': ptd.id,
        'description': ptd.description,
        'name': ptd.name,
        'category': ptd.category,
        'brand': ptd.brand,
        'price': ptd.price,
        'new_price': ptd.new_price,
        'imageURL': ptd.imageURL,
        'mfgDate': ptd.mfgDate,
        'expDate': ptd.expDate,
        'discount': ptd.discount,
        'out_of_stock': ptd.out_of_stock,
        'store': ptd.store,
        'active': ptd.active
    }

    return record



# def cookiesCart(request):
#     try:
#         cart = json.loads(request.COOKIES['cart'])
#     except:
#         cart = {}

#     print('cart:', cart)
#     items = []
#     order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
#     cartItems = order['get_cart_items']

#     for i in cart:
#         try:
#             cartItems += cart[i]["quantity"]

#             product = Product.objects.get(id=i)
#             total = (product.price * cart[i]["quantity"])

#             order["get_cart_total"] += total
#             order["get_cart_items"] += cart[i]["quantity"]

#             item = {
#                 'product': {
#                     'id': product.id,
#                     'name': product.name,
#                     'price': product.price,
#                     'imageURL': product.imageURL,
#                 },
#                 'quantity': cart[i]["quantity"],
#                 'get_total': total
#             }
#             items.append(item)
#         except:
#             pass
#     return {'cartItems': cartItems, 'order': order, 'items': items}


# def cartData(request):
#     if request.user.is_authenticated:
#         customer = request.user.customer
#         print('USER IS VALID')
#         order, created = Order.objects.get_or_create(customer=customer, complete=False)
#         items = order.orderitem_set.all()
#         cartItems = order.get_cart_items
#     else:
#         cookieData = cookiesCart(request)
#         cartItems = cookieData['cartItems']
#         order = cookieData['order']
#         items = cookieData['items']
#     return {'cartItems': cartItems, 'order': order, 'items': items}


# def guestOrder(request, data):
#     print('User is not logged in...')

#     print('COOKIES:', request.COOKIES)
#     name = data['form']['name']
#     email = data['form']['email']

#     cookieData = cookiesCart(request)
#     items = cookieData['items']

#     customer, created = Customer.objects.get_or_create(
#         email=email,
#     )
#     customer.name = name
#     customer.save()
    
#     order = Order.objects.create(
#         customer=customer,
#         complete=False,
#     )

#     for item in items:
#         product = Product.objects.get(id=item['product']['id'])

#         orderItem = OrderItem.objects.create(
#             product=product,
#             order=order,
#             quantity=item['quantity']
#         )
#     return customer, order
