# apps/web/finance/urls.py
from django.urls import path
from apps.web.finance.views import (
    FeeHeadListView,
    FeeInvoiceCreateView, FeeInvoiceDetailView, FeeInvoiceListView,
    FeeStructureCreateView, FeeStructureDetailView, FeeStructureListView,
    FinanceOverviewView, RecordPaymentView,
    StudentFeeAccountListView, StudentFeeView,
)

urlpatterns = [
    path("",                                        FinanceOverviewView.as_view(),      name="finance_overview"),
    path("fee-heads/",                              FeeHeadListView.as_view(),          name="fee_head_list"),
    path("fee-structures/",                         FeeStructureListView.as_view(),     name="fee_structure_list"),
    path("fee-structures/add/",                     FeeStructureCreateView.as_view(),   name="fee_structure_create"),
    path("fee-structures/<uuid:structure_id>/",     FeeStructureDetailView.as_view(),   name="fee_structure_detail"),
    path("accounts/",                               StudentFeeAccountListView.as_view(), name="fee_account_list"),
    path("invoices/",                               FeeInvoiceListView.as_view(),       name="invoice_list"),
    path("invoices/issue/",                         FeeInvoiceCreateView.as_view(),     name="invoice_create"),
    path("invoices/<uuid:invoice_id>/",             FeeInvoiceDetailView.as_view(),     name="invoice_detail"),
    path("invoices/<uuid:invoice_id>/pay/",         RecordPaymentView.as_view(),        name="record_payment"),
    path("my-fees/",                                StudentFeeView.as_view(),           name="my_fees"),
]
