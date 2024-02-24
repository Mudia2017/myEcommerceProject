# Generated by Django 3.1.7 on 2023-03-19 17:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import embed_video.fields
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, default='', max_length=200, null=True, unique=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('active', models.BooleanField(default=True, null=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='homePage.category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('full_name', models.CharField(blank=True, default='', max_length=200)),
                ('email', models.EmailField(blank=True, default='', max_length=200)),
                ('mobile', models.CharField(blank=True, default='', max_length=15)),
                ('home_tel', models.CharField(blank=True, default='', max_length=15)),
                ('address', models.CharField(blank=True, default='', max_length=200)),
                ('city', models.CharField(blank=True, default='', max_length=200)),
                ('state', models.CharField(blank=True, default='', max_length=200)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_order', models.DateTimeField(blank=True, null=True)),
                ('complete', models.BooleanField(default=False, null=True)),
                ('transaction_id', models.CharField(max_length=200, null=True)),
                ('payment_option', models.CharField(max_length=200, null=True)),
                ('paid', models.BooleanField(default=False, null=True)),
                ('paymentReference', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(blank=True, max_length=50)),
                ('reason_for_refund', models.CharField(max_length=200, null=True)),
                ('order_private_note', models.TextField(null=True)),
                ('refund_status', models.CharField(blank=True, max_length=200, null=True)),
                ('refund_private_note', models.TextField(null=True)),
                ('acct_activities', models.TextField(null=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('ref', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('channel', models.CharField(blank=True, max_length=200, null=True)),
                ('card_type', models.CharField(blank=True, max_length=200, null=True)),
                ('bank', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(blank=True, max_length=200, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('message', models.CharField(blank=True, max_length=250, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-date_created',),
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=9)),
                ('new_price', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('mfgDate', models.DateField(blank=True, default=None, null=True)),
                ('expDate', models.DateField(blank=True, default=None, null=True)),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ('out_of_stock', models.BooleanField(default=False, null=True)),
                ('active', models.BooleanField(default=True, null=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='homePage.brand')),
                ('category', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='homePage.category')),
            ],
        ),
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ptd_review_id', models.CharField(max_length=200, null=True)),
                ('cus_name', models.CharField(max_length=200, null=True)),
                ('transaction_id', models.CharField(max_length=200, null=True)),
                ('order_date', models.DateTimeField(blank=True, null=True)),
                ('ptd_id', models.CharField(max_length=200, null=True)),
                ('product_name', models.CharField(max_length=200, null=True)),
                ('product_image', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WishList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_id', models.CharField(max_length=200, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.product')),
            ],
        ),
        migrations.CreateModel(
            name='Video_item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', embed_video.fields.EmbedVideoField()),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='homePage.product')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_name', models.CharField(blank=True, max_length=200, null=True)),
                ('store_address', models.CharField(blank=True, max_length=256, null=True)),
                ('city', models.CharField(max_length=200, null=True)),
                ('LGA', models.CharField(max_length=200, null=True)),
                ('state', models.CharField(max_length=200, null=True)),
                ('email', models.EmailField(max_length=200, null=True)),
                ('mobile', models.CharField(max_length=15, null=True)),
                ('altMobile', models.CharField(blank=True, default='', max_length=15)),
                ('verified', models.BooleanField(default=False, null=True)),
                ('active', models.BooleanField(default=True, null=True)),
                ('user_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Slide_image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slide_ptd_image', models.ImageField(upload_to='')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='homePage.product')),
            ],
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_type', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(max_length=200, null=True)),
                ('address', models.CharField(max_length=200, null=True)),
                ('city', models.CharField(max_length=200, null=True)),
                ('state', models.CharField(max_length=200, null=True)),
                ('zipcode', models.CharField(blank=True, max_length=200, null=True)),
                ('mobile', models.CharField(max_length=15, null=True)),
                ('altMobile', models.CharField(blank=True, max_length=15, null=True)),
                ('optional_note', models.TextField(blank=True, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.order')),
            ],
        ),
        migrations.CreateModel(
            name='RecentViewItems',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.product')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='homePage.store'),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(blank=True, default=0, null=True)),
                ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('line_total', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('store_name', models.CharField(blank=True, max_length=256, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('refundAmt', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.product')),
            ],
        ),
        migrations.CreateModel(
            name='CustomerAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_type', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(max_length=200, null=True)),
                ('address', models.CharField(max_length=200, null=True)),
                ('city', models.CharField(max_length=200, null=True)),
                ('state', models.CharField(max_length=200, null=True)),
                ('zipcode', models.CharField(blank=True, max_length=200, null=True)),
                ('mobile', models.CharField(max_length=15, null=True)),
                ('altMobile', models.CharField(blank=True, max_length=15, null=True)),
                ('default', models.BooleanField(default=False, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(blank=True, default='', max_length=200)),
                ('comment', models.CharField(blank=True, default='', max_length=256)),
                ('rate', models.FloatField(default=1, max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.customer')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='homePage.product')),
            ],
        ),
    ]
