from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
import eShopperAmuwo

# app_name = 'homePage'

urlpatterns = [
    path('', views.homePage, name="homePage"),
    path('all_category/<str:pk>/', views.allCategory, name="all_category"),
    path('category_items/<str:pk>/', views.categoryItems, name="category_items"),
    path('shop_by_brands/', views.shopByBrand, name="shop_by_brands"),
    path('all_recent_view/', views.allRecentView, name="all_recent_view"),
    path('all_seller_items/<str:pk>/', views.allSellerItems, name="all_seller_items"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.register, name="register"),
    path('trader/store/<str:pk>/', views.traderStore, name="trader_store"),
    path('customer/acct/add/<str:pk>/', views.updateCustomerAddress, name="updatecustomerAddress"),
    path('customer/acct/card/', views.cusAcctCardForm, name="customer_acct_card"),
    path('login_Security/', views.loginAndSecuritySetting, name="login_Security"),
    path('login_Security/change_pwd', views.changePassword, name="change_pwd"),
    path('pending_reviews', views.pendingReview, name="pending_review"),
    path('pending_reviews/write_ptd_review/<str:pk>/<str:t_id>/', views.writePtdReview, name="write_ptd_review"),
    path('acct/my_order_list/', views.myOrder, name="my_order"),
    path('acct/cus_update_myOrder/<str:pk>/', views.cus_update_myOrder, name="cus_update_myOrder"),
    path('cust_edit_order/', views.custEditOrder, name="cust_edit_order"),
    path('acct/product_overview/', views.productOverView, name="product_over_view"),
    path('acct/product_overview/add_product', views.addProduct, name="add_product"),
    path('acct/product_overview/edit_product/<str:pk>/', views.editProduct, name="edit_product"),
    path('acct/wish_list/', views.wishList, name="wishList"),
    path('update_favorite/', views.updateFavorite, name="update_favorite"),
    path('product_details/<str:id>/', eShopperAmuwo.views.productDetail, name="product_details"),
    path('admin_session/', views.adminSession, name="admin_session"),
    path('admin_session/edit_order/<str:pk>/', views.adminEditOrder, name="admin_edit_order"),
    path('admin_update_item/', views.adminUpdateItem, name="admin_update_item"),
    path('refund_order/<str:pk>/', views.adminProcessRefundOrder, name="refund_order"),
    path('update_refund/', views.updateRefund, name="update_refund"),
    path('account/settings/', views.settings, name="settings"),
    path('update_setting/', views.updateSetting, name="update_setting"),
    path('update_overviewAddress/', views.updateOverviewAddress, name="update_overviewAddress"),
    path('account/settings/shippingAddressBtn/<str:data>/', views.addressOverview, name="addressOverview"),
    path('adminSetting/', views.adminSetting, name="adminSetting"),
    path('setting/generalSetting/', views.generalSetting, name="generalSetting"),

    # path('pdf_view/', views.ViewPDF.as_view(), name="pdf_view"),

    # URLS FOR RESETING PASSWORD THROUGH EMAIL
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_form.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_complete"),
]