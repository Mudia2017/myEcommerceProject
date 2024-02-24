from django.urls import path
from . import views

urlpatterns = [
    path('eshop_amuwo/', views.eShopAmuwo, name="eShopAmuwo"),
    path('amuwo_cart/', views.cartAmuwo, name="amuwo_cart"),
    path('amuwo_checkout/', views.checkoutAmuwo, name="amuwo_checkout"),
    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),
    path('product_detail/<int:id>/', views.productDetail, name="product_detail"),
    path('product_detail/all_comments/<int:id>/', views.customerProductReviews, name="all_cus_ptd_comments"),
    path('eshop_amuwo/category/<str:pk>/', views.amuwoCategoryShop, name="amuwoCategoryShop"),
    # path('initiate_payment', views.initiate_payment, name="initiate_payment"),
    # path('verify_payment/<str:ref>/', views.verify_payment, name="verify-payment"),
]