from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.views.decorators.http import require_POST
from .forms import ProfileUserForm, UserProfileForm
from .models import Category, Product, UserProfile


# صفحه اصلی
def home(request):
    categories = Category.objects.prefetch_related("products__images")
    font_sizes = [22 - i for i in range(len(categories))]
    brand_list = [
        "HP",
        "Dell",
        "Lenovo",
        "Asus",
        "Apple",
        "Acer",
        "Microsoft Surface",
        "MSI",
    ]
    return render(request, "home.html", {
        "categories": categories,
        "font_sizes": font_sizes,
        "brand_list": brand_list,
    })


# جزئیات محصول
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('images'), pk=pk)
    return render(request, "product_detail.html", {"product": product})


# افزودن به سبد خرید
@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # دریافت تعداد از فرم
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "تعداد واردشده معتبر نیست.")
        return redirect("product_detail", pk=pk)
    
    # بررسی موجودی
    if quantity <= 0:
        messages.error(request, "تعداد باید بیشتر از صفر باشد.")
        return redirect("product_detail", pk=pk)
    
    if quantity > product.stock:
        messages.error(request, f"موجودی این محصول {product.stock} عدد است.")
        return redirect("product_detail", pk=pk)
    
    cart = request.session.get("cart", {})
    cart_key = str(pk)
    if cart_key in cart:
        try:
            previous = cart[cart_key]
            previous_quantity = int(previous.get("quantity", 0)) if isinstance(previous, dict) else 0
        except (AttributeError, TypeError, ValueError):
            previous_quantity = 0
    else:
        previous_quantity = 0
    new_quantity = previous_quantity + quantity
    if new_quantity > product.stock:
        messages.error(request, f"موجودی کافی نیست. موجودی: {product.stock} عدد")
        return redirect("product_detail", pk=pk)
    main_image = product.get_main_image()
    cart[cart_key] = {
        "name": product.name,
        "price": str(product.price),
        "quantity": new_quantity,
        "image": main_image.url if main_image else "",
    }
    request.session["cart"] = cart
    messages.success(request, f"{quantity} عدد {product.name} به سبد خرید اضافه شد.")
    return redirect("cart")


# به‌روزرسانی تعداد در سبد خرید
@require_POST
def update_cart_quantity(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "تعداد واردشده معتبر نیست.")
        return redirect("cart")

    if quantity <= 0:
        messages.error(request, "تعداد باید بیشتر از صفر باشد.")
        return redirect("cart")

    if quantity > product.stock:
        messages.error(request, f"موجودی این محصول {product.stock} عدد است.")
        return redirect("cart")

    cart = request.session.get("cart", {})
    if str(pk) in cart:
        item = cart[str(pk)]
        if not isinstance(item, dict):
            item = {}
        item["quantity"] = quantity
        cart[str(pk)] = item
        request.session["cart"] = cart
        messages.success(request, f"تعداد {product.name} به‌روزرسانی شد.")
    else:
        messages.error(request, "محصولی با این مشخصات در سبد خرید نیست.")
    
    return redirect("cart")


# حذف از سبد خرید
@require_POST
def remove_from_cart(request, pk):
    cart = request.session.get("cart", {})
    product = get_object_or_404(Product, pk=pk)
    if str(pk) in cart:
        del cart[str(pk)]
        request.session["cart"] = cart
        messages.success(request, f"{product.name} از سبد خرید حذف شد.")
    else:
        messages.error(request, "محصولی با این مشخصات در سبد خرید نیست.")
    return redirect("cart")


# نمایش سبد خرید
def cart_view(request):
    cart = request.session.get("cart", {})
    # دریافت اطلاعات محصولات برای بررسی موجودی
    cart_items = []
    total = Decimal("0")
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            quantity = int(item.get("quantity", 1))
            price = product.price
            if quantity <= 0 or quantity > product.stock:
                raise ValueError("Invalid cart quantity")
            line_total = price * quantity
            main_image = product.get_main_image()
            image = main_image.url if main_image else ""
            cart_items.append({
                "id": product_id,
                "product": product,
                "name": product.name,
                "price": price,
                "quantity": quantity,
                "line_total": line_total,
                "image": image,
            })
            total += line_total
        except (Product.DoesNotExist, ValueError, InvalidOperation, KeyError, TypeError, AttributeError):
            # Ignore invalid or unavailable session entries without mutating on GET.
            continue

    return render(request, "cart.html", {"cart_items": cart_items, "total": total})


# ثبت‌نام
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not email or not password1:
            messages.error(request, "نام کاربری، ایمیل و رمز عبور را کامل وارد کنید.")
        elif password1 != password2:
            messages.error(request, "رمز عبور و تکرار آن یکسان نیستند.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "این نام کاربری قبلاً ثبت شده است.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "این ایمیل قبلاً ثبت شده است.")
        else:
            candidate = User(username=username, email=email)
            try:
                validate_password(password1, user=candidate)
            except ValidationError as error:
                for validation_error in error.messages:
                    messages.error(request, str(validation_error))
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                login(request, user)  # بعد از ثبت‌نام لاگین می‌شود
                messages.success(request, "ثبت‌نام با موفقیت انجام شد.")
                return redirect("home")

    return render(request, "register.html")


# ورود
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        user_exists = User.objects.filter(username__iexact=username).first()

        if user_exists:
            user = authenticate(request, username=user_exists.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "خوش آمدید!")
                return redirect("home")
            messages.error(request, "نام کاربری یا رمز عبور اشتباه است.")
        else:
            email = request.POST.get("email", "").strip()
            password2 = request.POST.get("password2")
            if not username:
                messages.error(request, "نام کاربری را وارد کنید.")
            elif not email:
                messages.error(request, "برای ساخت حساب جدید، ایمیل را وارد کنید.")
            elif User.objects.filter(email__iexact=email).exists():
                messages.error(request, "این ایمیل قبلاً ثبت شده است.")
            elif not password:
                messages.error(request, "رمز عبور را وارد کنید.")
            elif password != password2:
                messages.error(request, "رمز عبور و تکرار آن یکسان نیستند.")
            else:
                candidate = User(username=username, email=email)
                try:
                    validate_password(password, user=candidate)
                except ValidationError as error:
                    for validation_error in error.messages:
                        messages.error(request, str(validation_error))
                else:
                    user = User.objects.create_user(username=username, email=email, password=password)
                    login(request, user)
                    messages.success(request, "ثبت‌نام با موفقیت انجام شد.")
                    return redirect("home")

    return render(request, "login.html")


# خروج
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "شما با موفقیت خارج شدید.")
    return redirect("home")


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # A GET must not create a database row; save the profile only on valid POST.
        profile = UserProfile(user=request.user)
    user_form = ProfileUserForm(instance=request.user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == "POST":
        user_form = ProfileUserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "اطلاعات پروفایل ذخیره شد.")
            return redirect("profile")

    return render(request, "profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })


@login_required
def password_change_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "گذرواژه با موفقیت تغییر کرد.")
        return redirect("profile")
    return render(request, "password_change.html", {"form": form})


# تسویه حساب
def checkout(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "سبد خرید شما خالی است.")
        return redirect("cart")

    cart_items = []
    total = Decimal("0")
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            quantity = int(item.get("quantity", 0))
            if quantity <= 0 or quantity > product.stock:
                raise ValueError("Invalid cart quantity")
            price = product.price
            main_image = product.get_main_image()
            line_total = price * quantity
            cart_items.append({
                "id": product.pk,
                "product": product,
                "name": product.name,
                "image": main_image.url if main_image else "",
                "price": price,
                "quantity": quantity,
                "line_total": line_total,
            })
        except (Product.DoesNotExist, ValueError, TypeError, AttributeError, InvalidOperation):
            messages.error(request, "یکی از اقلام سبد خرید نامعتبر است یا موجودی کافی ندارد.")
            return redirect("cart")
        total += line_total

    return render(request, "checkout.html", {"cart_items": cart_items, "total": total})


# درباره ما
def about_view(request):
    return render(request, "about.html")


# تماس با ما
def contact_view(request):
    return render(request, "contact.html")


# حریم خصوصی
def privacy_view(request):
    return render(request, "privacy.html")


# شرایط و قوانین
def terms_view(request):
    return render(request, "terms.html")


# دسته‌بندی محصولات
def category_view(request, category_name):
    try:
        category = Category.objects.prefetch_related("products__images").get(name=category_name)
        products = category.products.all()
        return render(request, "category.html", {"category": category, "products": products})
    except Category.DoesNotExist:
        messages.error(request, "دسته‌بندی مورد نظر یافت نشد.")
        return redirect("home")


# جستجو
def search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query)
        ).select_related('category').prefetch_related('images')
    
    return render(request, "search.html", {
        "query": query,
        "products": products,
        "results_count": products.count()
    })
