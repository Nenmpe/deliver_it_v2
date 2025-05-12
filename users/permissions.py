from rest_framework import permissions

class IsSupplier(permissions.BasePermission):
    """
    Allows access only to authenticated users who are suppliers.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_supplier)


class IsCustomer(permissions.BasePermission):
    """
    Allows access only to authenticated users who are customers.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_customer)
    

class IsDriver(permissions.BasePermission):
    """
    Allows access only to authenticated users who are drivers.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_driver)