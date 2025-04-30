"""
URL configuration for electronics_inventory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from inventory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('add-component/', views.add_component, name='add_component'),
    path('edit-component/<int:pk>/', views.edit_component, name='edit_component'),
    path('delete-component/<int:pk>/', views.delete_component, name='delete_component'),
    path('request-component/<int:pk>/', views.request_component, name='request_component'),
    path('update-request/<int:pk>/', views.update_request, name='update_request'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('direct-issue-component/', views.direct_issue_component, name='direct_issue_component'),
    path('search-students/', views.search_students, name='search_students'),
    path('search-components/', views.search_components, name='search_components'),
    path('scan-barcode/', views.scan_barcode, name='scan_barcode'),
    path('generate-barcode/<int:pk>/', views.generate_barcode, name='generate_barcode'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/logout.html'), name='logout'),
     path('users/<int:user_id>/dashboard/', views.user_dashboard, name='user_dashboard'),
    
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
