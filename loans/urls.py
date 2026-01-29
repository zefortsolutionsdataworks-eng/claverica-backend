from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    # Loan Products
    path('products/', views.LoanProductListView.as_view(), name='product_list'),
    path('products/<uuid:pk>/', views.LoanProductDetailView.as_view(), name='product_detail'),
    
    # Loan Applications
    path('apply/', views.ApplyForLoanView.as_view(), name='apply'),
    path('', views.LoanListView.as_view(), name='loan_list'),
    path('<uuid:pk>/', views.LoanDetailView.as_view(), name='loan_detail'),
    
    # Loan Management
    path('<uuid:pk>/approve/', views.ApproveLoanView.as_view(), name='approve_loan'),
    path('<uuid:pk>/reject/', views.RejectLoanView.as_view(), name='reject_loan'),
    path('<uuid:pk>/disburse/', views.DisburseLoanView.as_view(), name='disburse_loan'),
    
    # Repayments
    path('repay/', views.RepayLoanView.as_view(), name='repay'),
    path('<uuid:pk>/repayments/', views.LoanRepaymentListView.as_view(), name='repayment_list'),
    
    # Credit Score
    path('credit-score/', views.CreditScoreView.as_view(), name='credit_score'),
]
