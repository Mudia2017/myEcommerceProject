from django.contrib.auth.forms import UserCreationForm
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.forms import ModelForm

from homePage.models import *


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)

        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already exist')
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')


class CustomCustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = ('user', 'name', 'email')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.get(**user_data)
        return Customer.objects.create(**validated_data, user=user)


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('store_name', 'store_address', 'city', 'LGA', 'state', 'email', 'mobile', 'altMobile', 'verified', 'active')
        

class CustomerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customer
        fields = ('name', 'email')

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = ('customer', 'date_order')

        # This function was used to create a new Order and link the Customer info to it.
        # It is called when the save function is called in views.py
    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        print("CUSTOMER_DATA:", customer_data)
        customer = Customer.objects.get(**customer_data)
        return Order.objects.create(customer=customer, **validated_data)



class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('name', 'description', 'category', 'brand', 'price', 'image', 'mfgDate', 'expDate', 'discount', 'out_of_stock', 'store', 'active')

