from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm

from . models import Customer, Store, Product, ShippingAddress, Payment, Slide_image, Video_item, CustomerAddress

class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(), required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CustomerProfileFormSetup(ModelForm):

    class Meta:
        model = Customer
        fields = ['user', 'name', 'full_name', 'email', 'mobile', 'home_tel', 'address', 'city', 'state']


class UpdateCustomerAddress(ModelForm):

    class Meta:
        model = Customer
        fields = ['full_name', 'email', 'mobile', 'home_tel', 'address', 'city', 'state']


class SaveCustomerAddress(ModelForm):

    class Meta:
        model = CustomerAddress
        fields = ['customer', 'address_type', 'name', 'address', 'city', 'state', 'zipcode',  'mobile', 'altMobile',]


class UpdateTraderStoreAddress(ModelForm):

    class Meta:
        model = Store
        fields = ['user_id', 'store_name', 'store_address', 'city', 'LGA', 'state', 'email', 'mobile', 'altMobile', 'verified', 'active']


# class DateInput(forms.DateInput):
#     input_type = 'date'

class UpdateProduct(ModelForm):
    price = forms.DecimalField(required=True)
    class Meta:
        model = Product
        
        # widgets = {'mfgDate': DateInput()}
        # OR
        # fields = '__all__'
        fields = ['name', 'description', 'category', 'brand', 'price', 'image', 'mfgDate', 'expDate', 'discount', 'out_of_stock', 'store', 'active']


class SlideImage(ModelForm):
    class Meta:
        model = Slide_image
        fields = ['product', 'slide_ptd_image']


class VideoUrl(ModelForm):
    class Meta:
        model = Video_item
        fields = ['video']


class ActivePtd(ModelForm):
    class Meta:
        model = Product
        fields = ['active']


class UpdateShippingAddress(ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'mobile']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'email']