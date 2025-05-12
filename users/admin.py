from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

admin.site.site_header = "DeliverIt Admin"
admin.site.site_title = "DeliverIt Admin Portal"

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'fullname', 'is_supplier', 'is_customer', 'is_driver', 'is_staff')
    list_filter = ('is_supplier', 'is_customer', 'is_driver', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('fullname', 'contact_no', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'is_supplier', 'is_customer', 'is_driver')}),
        ('Other', {'fields': ('terms_accepted',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'fullname', 'terms_accepted'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, UserAdmin)