# Deliver It API Documentation

## Overview
Deliver It is a comprehensive delivery and logistics management system that provides APIs for managing suppliers, customers, drivers, inventory, and orders.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Rate Limiting
- Anonymous users: 100 requests per day
- Authenticated users: 1000 requests per day

## API Endpoints

### 1. Authentication & User Management
#### Base URL: `/api/users/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/token/refresh/` | POST | Refresh access token | - | `{"refresh": "your_refresh_token"}` | `{"access": "new_access_token"}` |
| `/logout/` | POST | Logout user | `Authorization: Bearer <token>` | `{"refresh": "your_refresh_token"}` | `{"detail": "Logout successful"}` |

### 2. Account Management
#### Base URL: `/api/account/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/request-otp/` | POST | Request OTP for password reset | - | `{"email": "user@example.com"}` | `{"detail": "OTP sent"}` |
| `/verify-otp/` | POST | Verify OTP | - | `{"email": "user@example.com", "otp": "123456"}` | `{"detail": "OTP verified"}` |
| `/reset-password/` | POST | Reset password with OTP | - | `{"email": "user@example.com", "otp": "123456", "new_password": "newpass"}` | `{"detail": "Password reset successful"}` |
| `/change-password/` | POST | Change password (authenticated) | `Authorization: Bearer <token>` | `{"old_password": "oldpass", "new_password": "newpass"}` | `{"detail": "Password changed successfully"}` |

### 3. Supplier Management
#### Base URL: `/api/supplier/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/signup/` | POST | Register new supplier | - | ```json
{
    "email": "supplier@example.com",
    "password": "pass123",
    "password2": "pass123",
    "fullname": "Supplier Name",
    "contact_no": "1234567890",
    "address": "Supplier Address",
    "is_supplier": true,
    "terms_accepted": true,
    "company_name": "Company Name",
    "pan_no": "123456",
    "latitude": 27.7172,
    "longitude": 85.3240
}
``` | ```json
{
    "detail": "Supplier account created successfully. Please log in."
}
``` |
| `/signin/` | POST | Supplier login | - | ```json
{
    "email": "supplier@example.com",
    "password": "pass123"
}
``` | ```json
{
    "access": "access_token",
    "refresh": "refresh_token",
    "user": {
        "id": 1,
        "email": "supplier@example.com",
        "fullname": "Supplier Name",
        "is_supplier": true,
        "is_customer": false,
        "is_driver": false,
        "Supplier": {
            "uid": "uuid",
            "company_name": "Company Name",
            "pan_no": "123456",
            "company_location": {
                "type": "Point",
                "coordinates": [85.3240, 27.7172]
            }
        }
    }
}
``` |
| `/customers/` | GET | List all customers | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Customers retrieved successfully",
    "data": [
        {
            "uid": "customer_uuid",
            "email": "customer@example.com",
            "fullname": "Customer Name",
            "contact_no": "1234567890",
            "address": "Customer Address",
            "country": "Country Name",
            "state": "State Name",
            "city": "City Name"
        }
    ]
}
``` |
| `/drivers/` | GET | List all drivers | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Drivers retrieved successfully",
    "data": [
        {
            "uid": "driver_uuid",
            "email": "driver@example.com",
            "fullname": "Driver Name",
            "contact_no": "1234567890",
            "address": "Driver Address",
            "vehicle_type": "two-wheel",
            "driving_license_no": "DL123456",
            "vehicle_speed": "40.00",
            "location": {
                "type": "Point",
                "coordinates": [85.3240, 27.7172]
            },
            "status": "available"
        }
    ]
}
``` |

### 4. Customer Management
#### Base URL: `/api/customer/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/signup/` | POST | Register new customer | - | ```json
{
    "email": "customer@example.com",
    "password": "pass123",
    "password2": "pass123",
    "fullname": "Customer Name",
    "contact_no": "1234567890",
    "address": "Customer Address",
    "is_customer": true,
    "terms_accepted": true,
    "country": "Country Name",
    "state": "State Name",
    "city": "City Name",
    "postal_code": "12345"
}
``` | ```json
{
    "detail": "Customer account created successfully. Please log in."
}
``` |
| `/signin/` | POST | Customer login | - | ```json
{
    "email": "customer@example.com",
    "password": "pass123"
}
``` | ```json
{
    "access": "access_token",
    "refresh": "refresh_token",
    "user": {
        "id": 1,
        "email": "customer@example.com",
        "fullname": "Customer Name",
        "is_supplier": false,
        "is_customer": true,
        "is_driver": false,
        "Customer": {
            "uid": "uuid",
            "country": "Country Name",
            "state": "State Name",
            "city": "City Name",
            "postal_code": "12345"
        }
    }
}
``` |

### 5. Driver Management
#### Base URL: `/api/driver/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/signup/` | POST | Register new driver | - | ```json
{
    "email": "driver@example.com",
    "password": "pass123",
    "password2": "pass123",
    "fullname": "Driver Name",
    "contact_no": "1234567890",
    "address": "Driver Address",
    "is_driver": true,
    "terms_accepted": true,
    "driving_license_no": "DL123456",
    "vehicle_type": "two-wheel",
    "number_plate_no": "ABC123",
    "vehicle_speed": 40.00,
    "status": "offline",
    "latitude": 27.7172,
    "longitude": 85.3240
}
``` | ```json
{
    "detail": "Driver account created successfully. Please log in."
}
``` |
| `/signin/` | POST | Driver login | - | ```json
{
    "email": "driver@example.com",
    "password": "pass123"
}
``` | ```json
{
    "access": "access_token",
    "refresh": "refresh_token",
    "user": {
        "id": 1,
        "email": "driver@example.com",
        "fullname": "Driver Name",
        "is_supplier": false,
        "is_customer": false,
        "is_driver": true,
        "Driver": {
            "uid": "uuid",
            "driving_license_no": "DL123456",
            "vehicle_type": "two-wheel",
            "number_plate_no": "ABC123",
            "vehicle_speed": 40.00,
            "location": {
                "type": "Point",
                "coordinates": [85.3240, 27.7172]
            },
            "status": "offline",
            "last_updated": "2024-03-14T12:00:00Z"
        }
    }
}
``` |

### 6. Inventory Management
#### Base URL: `/api/inventory/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/items/` | GET | List all items | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Items retrieved successfully",
    "data": [
        {
            "uid": "item_uuid",
            "name": "Item Name",
            "description": "Item Description",
            "price": "100.00",
            "quantity": 10,
            "supplier": "supplier_uuid"
        }
    ]
}
``` |
| `/items/` | POST | Create new item | `Authorization: Bearer <token>` | ```json
{
    "name": "Item Name",
    "description": "Item Description",
    "price": 100.00,
    "quantity": 10
}
``` | ```json
{
    "status": "success",
    "message": "Item created successfully",
    "data": {
        "uid": "item_uuid",
        "name": "Item Name",
        "description": "Item Description",
        "price": "100.00",
        "quantity": 10,
        "supplier": "supplier_uuid"
    }
}
``` |
| `/items/{uid}/` | GET | Get item details | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Item retrieved successfully",
    "data": {
        "uid": "item_uuid",
        "name": "Item Name",
        "description": "Item Description",
        "price": "100.00",
        "quantity": 10,
        "supplier": "supplier_uuid"
    }
}
``` |
| `/items/{uid}/` | PUT | Update item | `Authorization: Bearer <token>` | ```json
{
    "name": "Updated Name",
    "description": "Updated Description",
    "price": 150.00,
    "quantity": 15
}
``` | ```json
{
    "status": "success",
    "message": "Item updated successfully",
    "data": {
        "uid": "item_uuid",
        "name": "Updated Name",
        "description": "Updated Description",
        "price": "150.00",
        "quantity": 15,
        "supplier": "supplier_uuid"
    }
}
``` |
| `/items/{uid}/` | DELETE | Delete item | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Item deleted successfully",
    "data": null
}
``` |

### 7. Order Management
#### Base URL: `/api/delivery/`

| Endpoint | Method | Description | Headers | Request Body | Response |
|----------|--------|-------------|---------|--------------|-----------|
| `/orders/` | GET | List all orders | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Orders retrieved successfully",
    "data": [
        {
            "order_id": "order_uuid",
            "supplier": "supplier_uuid",
            "item": "item_uuid",
            "qty": 2,
            "price": "200.00",
            "customer": "customer_uuid",
            "delivery_date": "2024-03-15T12:00:00Z",
            "instruction": "Handle with care",
            "driver": "driver_uuid",
            "estimated_time": "00:30:00",
            "total_distance_km": 5.5,
            "path_coords": [[85.3240, 27.7172], [85.3250, 27.7182]]
        }
    ]
}
``` |
| `/orders/` | POST | Create new order | `Authorization: Bearer <token>` | ```json
{
    "supplier": "supplier_uuid",
    "item": "item_uuid",
    "qty": 2,
    "delivery_date": "2024-03-15T12:00:00Z",
    "instruction": "Handle with care",
    "latitude": 27.7172,
    "longitude": 85.3240
}
``` | ```json
{
    "status": "success",
    "message": "Order created successfully",
    "data": {
        "order_id": "order_uuid",
        "supplier": "supplier_uuid",
        "item": "item_uuid",
        "qty": 2,
        "price": "200.00",
        "customer": "customer_uuid",
        "delivery_date": "2024-03-15T12:00:00Z",
        "instruction": "Handle with care",
        "driver": "driver_uuid",
        "estimated_time": "00:30:00",
        "total_distance_km": 5.5,
        "path_coords": [[85.3240, 27.7172], [85.3250, 27.7182]]
    }
}
``` |
| `/orders/{uid}/` | GET | Get order details | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Order retrieved successfully",
    "data": {
        "order_id": "order_uuid",
        "supplier": "supplier_uuid",
        "item": "item_uuid",
        "qty": 2,
        "price": "200.00",
        "customer": "customer_uuid",
        "delivery_date": "2024-03-15T12:00:00Z",
        "instruction": "Handle with care",
        "driver": "driver_uuid",
        "estimated_time": "00:30:00",
        "total_distance_km": 5.5,
        "path_coords": [[85.3240, 27.7172], [85.3250, 27.7182]]
    }
}
``` |
| `/orders/{uid}/` | PUT | Update order status | `Authorization: Bearer <token>` | ```json
{
    "status": "in_progress"
}
``` | ```json
{
    "status": "success",
    "message": "Order updated successfully",
    "data": {
        "order_id": "order_uuid",
        "status": "in_progress"
    }
}
``` |
| `/orders/{uid}/` | DELETE | Cancel order | `Authorization: Bearer <token>` | - | ```json
{
    "status": "success",
    "message": "Order cancelled successfully",
    "data": null
}
``` |

## Error Responses
All endpoints may return the following error responses:

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| 400 | Bad Request - Invalid input data | ```json
{
    "status": "error",
    "message": "Invalid input data",
    "errors": {
        "field_name": ["Error message"]
    }
}
``` |
| 401 | Unauthorized - Invalid or missing token | ```json
{
    "detail": "Authentication credentials were not provided."
}
``` |
| 403 | Forbidden - Insufficient permissions | ```json
{
    "detail": "You do not have permission to perform this action."
}
``` |
| 404 | Not Found - Resource doesn't exist | ```json
{
    "detail": "Not found."
}
``` |
| 429 | Too Many Requests - Rate limit exceeded | ```json
{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
``` |

## Notes
- All timestamps are in UTC
- All monetary values are in the base currency unit
- Geographic coordinates use the WGS84 coordinate system
- File uploads should use multipart/form-data
- Maximum request size: 10MB

## Best Practices
1. Always include the Authorization header for authenticated requests
2. Handle rate limiting by implementing exponential backoff
3. Validate all input data before sending requests
4. Implement proper error handling for all API responses
5. Use HTTPS for all API requests in production
6. Keep tokens secure and never expose them in client-side code
7. Implement proper token refresh mechanism
8. Handle network errors and timeouts appropriately

## Support
For API support or to report issues, please contact the development team at support@deliverit.com 