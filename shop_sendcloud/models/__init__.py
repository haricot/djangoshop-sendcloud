# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from shop.money.fields import MoneyField
from shop.models.address import BaseShippingAddress, BaseBillingAddress, CountryField
from shop.models.customer import BaseCustomer


class Customer(BaseCustomer):
    """
    Default materialized model for Customer, adding a customer's number and salutation.

    If this model is materialized, then also register the corresponding serializer class
    :class:`shop.serializers.defaults.customer.CustomerSerializer`.
    """
    SALUTATION = [('mrs', _("Mrs.")), ('mr', _("Mr.")), ('na', _("(n/a)"))]

    number = models.PositiveIntegerField(
        _("Customer Number"),
        null=True,
        default=None,
        unique=True,
    )

    salutation = models.CharField(
        _("Salutation"),
        max_length=5,
        choices=SALUTATION,
    )

    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        null=True,
    )

    def get_number(self):
        return self.number

    def get_or_assign_number(self):
        if self.number is None:
            aggr = Customer.objects.filter(number__isnull=False).aggregate(models.Max('number'))
            self.number = (aggr['number__max'] or 0) + 1
            self.save()
        return self.get_number()

    @classmethod
    def reorder_form_fields(self, field_order):
        field_order.insert(0, 'salutation')
        field_order.append('phone_number')
        return field_order

    def as_text(self):
        template = get_template('shop_sendcloud/customer.txt')
        return template.render({'customer': self})


class AddressModelMixin(models.Model):
    name = models.CharField(
        _("Full name"),
        max_length=1024,
    )

    company_name = models.CharField(
        _("Company name"),
        max_length=1024,
        blank=True,
        null=True,
    )

    address = models.CharField(
        _("Address line"),
        max_length=1024,
    )

    house_number = models.CharField(
        _("House number"),
        max_length=12,
    )

    postal_code = models.CharField(
        _("ZIP / Postal code"),
        max_length=12,
    )

    city = models.CharField(
        _("City"),
        max_length=1024,
    )

    country = CountryField(_("Country"))

    class Meta:
        abstract = True


class ShippingAddress(BaseShippingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")

    def as_text(self):
        template = get_template('shop_sendcloud/address.txt')
        return template.render({'address': self})


class BillingAddress(BaseBillingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Billing Address")
        verbose_name_plural = _("Billing Addresses")

    def as_text(self):
        template = get_template('shop_sendcloud/address.txt')
        return template.render({'address': self})


class ShippingMethod(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    name = models.CharField(
        max_length=255,
    )

    carrier = models.CharField(
        max_length=32,
    )

    min_weight = models.DecimalField(
        max_digits=6,
        decimal_places=3,
    )

    max_weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
    )

    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
    )

    class Meta:
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")


class ShippingDestination(models.Model):
    shipping_method = models.ForeignKey(
        ShippingMethod,
        related_name='destinations',
    )

    country = models.CharField(max_length=3)

    price = MoneyField(currency='EUR')

    class Meta:
        verbose_name = _("Shipping Destination")
        verbose_name_plural = _("Shipping Destination")
        unique_together = ['country', 'shipping_method']
