from decimal import Decimal
from django.db import models


class TomanPriceField(models.DecimalField):
    def get_internal_type(self):
        return "TextField"

    def db_type(self, connection):
        return "text"

    def from_db_value(self, value, expression, connection):
        return Decimal(value) if value is not None else None

    def get_db_converters(self, connection):
        return [self.from_db_value]


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = TomanPriceField(max_digits=50, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="تصویر اصلی (اختیاری)")

    def __str__(self):
        return f"{self.name} - {self.category.name}"

    def get_main_image(self):
        """برگرداندن اولین عکس یا تصویر اصلی"""
        first_image = self.images.first()
        if first_image:
            return first_image.image
        return self.image


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/", verbose_name="عکس")
    order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "عکس محصول"
        verbose_name_plural = "عکس‌های محصول"

    def __str__(self):
        return f"{self.product.name} - تصویر {self.order + 1}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر",
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="شماره تماس")
    address = models.TextField(blank=True, verbose_name="نشانی")
    city = models.CharField(max_length=100, blank=True, verbose_name="شهر")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="کد پستی")

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران"

    def __str__(self):
        return f"پروفایل {self.user.username}"