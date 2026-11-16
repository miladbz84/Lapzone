from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from store.models import Category, Product


@override_settings(SECURE_SSL_REDIRECT=False)
class StoreSecurityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test laptops")
        self.product = Product.objects.create(
            category=self.category,
            name="Test laptop",
            description="A product used only in the test database.",
            price=Decimal("1250000.00"),
            stock=5,
        )

    def test_state_changing_cart_and_logout_routes_reject_get(self):
        for route in (
            reverse("add_to_cart", args=[self.product.pk]),
            reverse("remove_from_cart", args=[self.product.pk]),
            reverse("update_cart_quantity", args=[self.product.pk]),
            reverse("logout"),
        ):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 405)

    def test_add_to_cart_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("add_to_cart", args=[self.product.pk]), {"quantity": "1"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_cart_and_checkout_use_current_database_price(self):
        session = self.client.session
        session["cart"] = {
            str(self.product.pk): {
                "name": "Forged name",
                "price": "1",
                "quantity": 2,
                "image": "",
            }
        }
        session.save()

        cart_response = self.client.get(reverse("cart"))
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.context["cart_items"][0]["price"], self.product.price)
        self.assertEqual(cart_response.context["cart_items"][0]["name"], self.product.name)
        self.assertEqual(cart_response.context["total"], Decimal("2500000.00"))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)]["price"], "1")

        checkout_response = self.client.get(reverse("checkout"))
        self.assertEqual(checkout_response.status_code, 200)
        self.assertEqual(checkout_response.context["total"], Decimal("2500000.00"))

    def test_registration_uses_configured_password_validators(self):
        response = self.client.post(reverse("register"), {
            "username": "weak-password-user",
            "email": "weak@example.test",
            "password1": "123",
            "password2": "123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="weak-password-user").exists())

    def test_registration_rejects_missing_password(self):
        self.client.post(reverse("register"), {
            "username": "no-password-user",
            "email": "no-password@example.test",
            "password1": "",
            "password2": "",
        })
        self.assertFalse(User.objects.filter(username="no-password-user").exists())

    def test_profile_get_does_not_create_a_profile_record(self):
        user = User.objects.create_user(username="profile-test-user", password="ValidTestPass!842")
        self.client.force_login(user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(hasattr(user, "profile"))

    def test_store_static_css_is_discoverable(self):
        self.assertIsNotNone(finders.find("style.css"))


class ProductAdminActionTests(TestCase):
    def test_move_to_category_action_intermediate_form_and_submission(self):
        source = Category.objects.create(name="Source category")
        destination = Category.objects.create(name="Destination category")
        first = Product.objects.create(
            category=source, name="First admin test product", description="Test",
            price=Decimal("10.00"), stock=2,
        )
        second = Product.objects.create(
            category=source, name="Second admin test product", description="Test",
            price=Decimal("20.00"), stock=3,
        )
        admin_user = User.objects.create_superuser(
            username="action-admin", email="admin@example.test", password="SafeAdminTest!842"
        )
        self.client.force_login(admin_user)
        changelist = reverse("admin:store_product_changelist")
        selected = [str(first.pk), str(second.pk)]

        form_response = self.client.post(changelist, {
            "action": "move_to_category",
            ACTION_CHECKBOX_NAME: selected,
            "index": "0",
            "select_across": "0",
        })
        self.assertEqual(form_response.status_code, 200)
        self.assertTemplateUsed(form_response, "admin/store/product/move_to_category.html")
        self.assertContains(form_response, "Destination category")

        result = self.client.post(changelist, {
            "action": "move_to_category",
            ACTION_CHECKBOX_NAME: selected,
            "category": str(destination.pk),
            "select_across": "0",
        })
        self.assertEqual(result.status_code, 302)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.category_id, destination.pk)
        self.assertEqual(second.category_id, destination.pk)
