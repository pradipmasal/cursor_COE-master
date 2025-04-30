from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group, Permission
from .models import Component, IssueRequest, UserProfile

# Unregister the default UserAdmin and GroupAdmin
admin.site.unregister(User)
admin.site.unregister(Group)

# Create a custom UserAdmin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active', 'is_superuser'),
        }),
    )

# Create a custom GroupAdmin
class CustomGroupAdmin(GroupAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

# Register the custom UserAdmin and GroupAdmin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_admin', 'get_email', 'get_date_joined', 'get_last_login')
    list_filter = ('is_admin',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'get_date_joined', 'get_last_login')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_date_joined(self, obj):
        return obj.user.date_joined
    get_date_joined.short_description = 'Date Joined'
    
    def get_last_login(self, obj):
        return obj.user.last_login
    get_last_login.short_description = 'Last Login'

@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'quantity', 'available', 'created_at', 'updated_at')
    list_filter = ('available', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Inventory Details', {
            'fields': ('quantity', 'available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(IssueRequest)
class IssueRequestAdmin(admin.ModelAdmin):
    list_display = ('component', 'student', 'quantity', 'status', 'request_date', 'issue_date', 'return_deadline', 'return_date', 'admin')
    list_filter = ('status', 'request_date', 'issue_date', 'return_deadline', 'return_date')
    search_fields = ('component__name', 'student__username', 'notes', 'rejection_reason')
    date_hierarchy = 'request_date'
    readonly_fields = ('request_date', 'issue_date', 'return_date', 'return_deadline')
    fieldsets = (
        ('Request Information', {
            'fields': ('component', 'student', 'quantity', 'status')
        }),
        ('Dates', {
            'fields': ('request_date', 'issue_date', 'return_deadline', 'return_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'rejection_reason', 'admin')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('component', 'student', 'admin')
