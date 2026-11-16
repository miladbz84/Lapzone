from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django import forms
from django.contrib import messages
from django.template.response import TemplateResponse
from .models import Product, Category, ProductImage

class MoveToCategoryInlineForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label="دسته‌بندی جدید")

def move_to_category(modeladmin, request, queryset):
    if 'category' in request.POST:
        form = MoveToCategoryInlineForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            count = queryset.update(category=category)
            messages.success(request, f"{count} محصول به دسته '{category.name}' منتقل شد.")
            return None
    else:
        form = MoveToCategoryInlineForm()

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": "انتقال محصولات به دسته دلخواه",
        "opts": modeladmin.model._meta,
        "form": form,
        "action_name": "move_to_category",
        "action_checkbox_name": ACTION_CHECKBOX_NAME,
        "selected_ids": queryset.values_list("pk", flat=True),
        "select_across": request.POST.get("select_across", "0"),
    }
    return TemplateResponse(
        request,
        "admin/store/product/move_to_category.html",
        context,
    )

move_to_category.short_description = "منتقل کردن محصولات انتخابی به دسته دلخواه"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'order')
    verbose_name = "عکس محصول"
    verbose_name_plural = "عکس‌های محصول"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock')
    actions = [move_to_category]
    inlines = [ProductImageInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'category', 'description')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'stock')
        }),
        ('تصویر اصلی (اختیاری - در صورت وجود عکس‌های دیگر استفاده نمی‌شود)', {
            'fields': ('image',)
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
