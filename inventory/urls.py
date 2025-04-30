from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('add-component/', views.add_component, name='add_component'),
    path('edit-component/<int:pk>/', views.edit_component, name='edit_component'),
    path('delete-component/<int:pk>/', views.delete_component, name='delete_component'),
    path('request-component/<int:pk>/', views.request_component, name='request_component'),
    path('update-request/<int:pk>/', views.update_request, name='update_request'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('direct-issue-component/', views.direct_issue_component, name='direct_issue_component'),
    path('scan-barcode/', views.scan_barcode, name='scan_barcode'),
    path('generate-barcode/<int:pk>/', views.generate_barcode, name='generate_barcode'),
    path('users/<int:user_id>/dashboard/', views.user_dashboard, name='user_dashboard'),

    
    # API endpoints
    path('api/search-students/', views.search_students, name='search_students'),
    path('api/search-components/', views.search_components, name='search_components'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='inventory/password_reset_form.html',
             email_template_name='inventory/password_reset_email.html',
             subject_template_name='inventory/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='inventory/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='inventory/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='inventory/password_reset_complete.html'
         ),
         name='password_reset_complete'),
] 