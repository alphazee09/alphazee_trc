# Alphazee09 Crypto Wallet API Documentation

## Overview

This documentation covers all available API endpoints for the Alphazee09 Crypto Wallet application. The API provides both user and admin functionality with comprehensive authentication and security features.

**Base URL:** `https://zmhqivcm6ly1.manus.space/api`

## Authentication

### Headers Required
```
Content-Type: application/json
Authorization: Bearer <token>
```

### Token Types
- **User Token**: For regular user operations (30-day expiry)
- **Admin Token**: For admin operations (8-hour expiry)

---

## User Authentication Endpoints

### 1. User Registration
**POST** `/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "string (required)",
  "email": "string (required)", 
  "password": "string (required)",
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "phone": "string (optional)"
}
```

**Response (201 - Success):**
```json
{
  "message": "User registered successfully",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "profile_image": null,
    "fingerprint_enabled": false,
    "is_verified": false,
    "is_blocked": false,
    "blocked_at": null,
    "blocked_reason": null,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

**Error Responses:**
```json
// 400 - Username exists
{
  "message": "Username already exists"
}

// 400 - Email exists  
{
  "message": "Email already exists"
}

// 500 - Server error
{
  "message": "Registration failed: <error_details>"
}
```

### 2. User Login
**POST** `/login`

Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response (200 - Success):**
```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "profile_image": null,
    "fingerprint_enabled": false,
    "is_verified": false,
    "is_blocked": false,
    "blocked_at": null,
    "blocked_reason": null,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

**Error Responses:**
```json
// 401 - Invalid credentials
{
  "message": "Invalid credentials"
}

// 403 - Account blocked
{
  "message": "Account is blocked. Please contact support.",
  "blocked_reason": "Suspicious activity detected",
  "blocked_at": "2024-01-15T14:30:00"
}
```

### 3. Get User Profile
**GET** `/profile`

Get current user's profile information.

**Headers:** Authorization: Bearer `<user_token>`

**Response (200 - Success):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "profile_image": null,
  "fingerprint_enabled": false,
  "is_verified": false,
  "is_blocked": false,
  "blocked_at": null,
  "blocked_reason": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### 4. Update User Profile
**PUT** `/profile`

Update user profile information.

**Headers:** Authorization: Bearer `<user_token>`

**Request Body:**
```json
{
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "phone": "+1987654321",
  "fingerprint_enabled": true
}
```

**Response (200 - Success):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John Updated",
    "last_name": "Doe Updated",
    "phone": "+1987654321",
    "profile_image": null,
    "fingerprint_enabled": true,
    "is_verified": false,
    "is_blocked": false,
    "blocked_at": null,
    "blocked_reason": null,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T14:45:00"
  }
}
```

---

## Wallet Management Endpoints

### 5. Get User Wallets
**GET** `/wallets`

Get all wallets for the authenticated user.

**Headers:** Authorization: Bearer `<user_token>`

**Response (200 - Success):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "currency": "BTC",
    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "balance": 0.00500000,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": 2,
    "user_id": 1,
    "currency": "USDT",
    "address": "0x742d35Cc6634C0532925a3b8D8A8d5D4F7d6c8c9",
    "balance": 100.50000000,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 6. Get Wallet Balance
**GET** `/wallets/{wallet_id}/balance`

Get balance for a specific wallet.

**Headers:** Authorization: Bearer `<user_token>`

**Response (200 - Success):**
```json
{
  "wallet_id": 1,
  "currency": "BTC",
  "balance": 0.00500000,
  "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
  "last_updated": "2024-01-15T14:30:00"
}
```

### 7. Get Transaction History
**GET** `/wallets/{wallet_id}/transactions`

Get transaction history for a specific wallet.

**Headers:** Authorization: Bearer `<user_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response (200 - Success):**
```json
{
  "transactions": [
    {
      "id": 1,
      "user_id": 1,
      "from_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
      "to_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "currency": "BTC",
      "amount": 0.00500000,
      "fee": 0.00001000,
      "tx_hash": "0x1234567890abcdef...",
      "block_number": 17500000,
      "block_hash": "0xabcdef1234567890...",
      "gas_used": null,
      "gas_price": null,
      "contract_address": null,
      "token_id": null,
      "status": "confirmed",
      "transaction_type": "receive",
      "created_at": "2024-01-15T14:30:00",
      "confirmed_at": "2024-01-15T14:35:00"
    }
  ],
  "total": 10,
  "pages": 1,
  "current_page": 1,
  "per_page": 20,
  "has_next": false,
  "has_prev": false
}
```

---

## Transaction Endpoints

### 8. Send Cryptocurrency
**POST** `/transactions/send`

Send cryptocurrency to another address.

**Headers:** Authorization: Bearer `<user_token>`

**Request Body:**
```json
{
  "currency": "BTC",
  "to_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  "amount": 0.001
}
```

**Response (200 - Success):**
```json
{
  "message": "Transaction sent successfully",
  "transaction": {
    "id": 2,
    "user_id": 1,
    "from_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "to_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "currency": "BTC",
    "amount": 0.00100000,
    "fee": 0.00001000,
    "tx_hash": "0x9876543210fedcba...",
    "block_number": 17500001,
    "block_hash": "0xfedcba0987654321...",
    "gas_used": null,
    "gas_price": null,
    "contract_address": null,
    "token_id": null,
    "status": "pending",
    "transaction_type": "send",
    "created_at": "2024-01-15T15:00:00",
    "confirmed_at": null
  },
  "remaining_balance": 0.00399000
}
```

**Error Responses:**
```json
// 400 - Insufficient balance
{
  "message": "Insufficient balance"
}

// 404 - Wallet not found
{
  "message": "Wallet not found for currency BTC"
}
```

### 9. Get Transaction Details
**GET** `/transactions/{transaction_id}`

Get detailed information about a specific transaction.

**Headers:** Authorization: Bearer `<user_token>`

**Response (200 - Success):**
```json
{
  "id": 1,
  "user_id": 1,
  "from_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  "to_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
  "currency": "BTC",
  "amount": 0.00500000,
  "fee": 0.00001000,
  "tx_hash": "0x1234567890abcdef...",
  "block_number": 17500000,
  "block_hash": "0xabcdef1234567890...",
  "gas_used": null,
  "gas_price": null,
  "contract_address": null,
  "token_id": null,
  "status": "confirmed",
  "transaction_type": "receive",
  "created_at": "2024-01-15T14:30:00",
  "confirmed_at": "2024-01-15T14:35:00"
}
```

---

## Market Data Endpoints

### 10. Get Crypto Prices
**GET** `/crypto/prices`

Get current prices for all supported cryptocurrencies.

**Response (200 - Success):**
```json
[
  {
    "id": 1,
    "symbol": "BTC",
    "name": "Bitcoin",
    "price_usd": 45000.50,
    "change_24h": 2.5,
    "market_cap": 850000000000,
    "volume_24h": 25000000000,
    "updated_at": "2024-01-15T15:00:00"
  },
  {
    "id": 2,
    "symbol": "USDT",
    "name": "Tether",
    "price_usd": 1.00,
    "change_24h": 0.1,
    "market_cap": 95000000000,
    "volume_24h": 45000000000,
    "updated_at": "2024-01-15T15:00:00"
  }
]
```

### 11. Get Specific Crypto Price
**GET** `/crypto/price/{symbol}`

Get current price for a specific cryptocurrency.

**Response (200 - Success):**
```json
{
  "id": 1,
  "symbol": "BTC",
  "name": "Bitcoin",
  "price_usd": 45000.50,
  "change_24h": 2.5,
  "market_cap": 850000000000,
  "volume_24h": 25000000000,
  "updated_at": "2024-01-15T15:00:00"
}
```

---

## Admin Authentication Endpoints

### 12. Admin Registration
**POST** `/admin/register`

Register a new admin account.

**Request Body:**
```json
{
  "username": "admin_user",
  "email": "admin@example.com",
  "password": "secureAdminPass123",
  "first_name": "Admin",
  "last_name": "User",
  "role": "admin"
}
```

**Response (201 - Success):**
```json
{
  "message": "Admin registered successfully",
  "admin": {
    "id": 1,
    "username": "admin_user",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "is_active": true,
    "last_login": null,
    "created_at": "2024-01-15T16:00:00",
    "updated_at": "2024-01-15T16:00:00"
  }
}
```

### 13. Admin Login
**POST** `/admin/login`

Authenticate admin and receive access token.

**Request Body:**
```json
{
  "username": "admin_user",
  "password": "secureAdminPass123"
}
```

**Response (200 - Success):**
```json
{
  "message": "Admin login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "admin": {
    "id": 1,
    "username": "admin_user",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "is_active": true,
    "last_login": "2024-01-15T16:15:00",
    "created_at": "2024-01-15T16:00:00",
    "updated_at": "2024-01-15T16:15:00"
  }
}
```

### 14. Admin Profile
**GET** `/admin/profile`

Get current admin's profile information.

**Headers:** Authorization: Bearer `<admin_token>`

**Response (200 - Success):**
```json
{
  "admin": {
    "id": 1,
    "username": "admin_user",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "is_active": true,
    "last_login": "2024-01-15T16:15:00",
    "created_at": "2024-01-15T16:00:00",
    "updated_at": "2024-01-15T16:15:00"
  }
}
```

---

## Admin User Management Endpoints

### 15. Get All Users
**GET** `/admin/users`

Get all users with pagination and filtering.

**Headers:** Authorization: Bearer `<admin_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `search` (optional): Search in username, email, first_name, last_name
- `status` (optional): Filter by status (active, blocked, verified, unverified)

**Response (200 - Success):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "profile_image": null,
      "fingerprint_enabled": false,
      "is_verified": false,
      "is_blocked": false,
      "blocked_at": null,
      "blocked_reason": null,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 50,
  "pages": 3,
  "current_page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

### 16. Get User Details
**GET** `/admin/users/{user_id}`

Get detailed information about a specific user.

**Headers:** Authorization: Bearer `<admin_token>`

**Response (200 - Success):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "profile_image": null,
    "fingerprint_enabled": false,
    "is_verified": false,
    "is_blocked": false,
    "blocked_at": null,
    "blocked_reason": null,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  "wallets": [
    {
      "id": 1,
      "user_id": 1,
      "currency": "BTC",
      "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "balance": 0.00500000,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "recent_transactions": [
    {
      "id": 1,
      "user_id": 1,
      "from_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
      "to_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "currency": "BTC",
      "amount": 0.00500000,
      "fee": 0.00001000,
      "tx_hash": "0x1234567890abcdef...",
      "status": "confirmed",
      "transaction_type": "receive",
      "created_at": "2024-01-15T14:30:00"
    }
  ]
}
```

### 17. Block User
**POST** `/admin/users/{user_id}/block`

Block a user account.

**Headers:** Authorization: Bearer `<admin_token>`

**Request Body:**
```json
{
  "reason": "Suspicious activity detected"
}
```

**Response (200 - Success):**
```json
{
  "message": "User blocked successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "profile_image": null,
    "fingerprint_enabled": false,
    "is_verified": false,
    "is_blocked": true,
    "blocked_at": "2024-01-15T16:30:00",
    "blocked_reason": "Suspicious activity detected",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T16:30:00"
  }
}
```

### 18. Unblock User
**POST** `/admin/users/{user_id}/unblock`

Unblock a user account.

**Headers:** Authorization: Bearer `<admin_token>`

**Response (200 - Success):**
```json
{
  "message": "User unblocked successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "profile_image": null,
    "fingerprint_enabled": false,
    "is_verified": false,
    "is_blocked": false,
    "blocked_at": null,
    "blocked_reason": null,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T16:35:00"
  }
}
```

---

## Admin Wallet Management Endpoints

### 19. Get All Wallets
**GET** `/admin/wallets`

Get all user wallet addresses with pagination and filtering.

**Headers:** Authorization: Bearer `<admin_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50)
- `currency` (optional): Filter by currency (BTC, USDT, ETH)
- `user_id` (optional): Filter by specific user ID

**Response (200 - Success):**
```json
{
  "wallets": [
    {
      "id": 1,
      "user_id": 1,
      "currency": "BTC",
      "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "balance": 0.00500000,
      "created_at": "2024-01-15T10:30:00",
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "is_blocked": false
      }
    }
  ],
  "total": 100,
  "pages": 2,
  "current_page": 1,
  "per_page": 50,
  "has_next": true,
  "has_prev": false
}
```

### 20. Get User Wallets
**GET** `/admin/users/{user_id}/wallets`

Get specific user's wallet addresses.

**Headers:** Authorization: Bearer `<admin_token>`

**Response (200 - Success):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_blocked": false
  },
  "wallets": [
    {
      "id": 1,
      "user_id": 1,
      "currency": "BTC",
      "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "balance": 0.00500000,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "user_id": 1,
      "currency": "USDT",
      "address": "0x742d35Cc6634C0532925a3b8D8A8d5D4F7d6c8c9",
      "balance": 100.50000000,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

---

## Admin Crypto Transfer Endpoints

### 21. Send Crypto to User
**POST** `/admin/send-crypto`

Admin sends cryptocurrency to a specific user.

**Headers:** Authorization: Bearer `<admin_token>`

**Request Body:**
```json
{
  "user_id": 1,
  "currency": "BTC",
  "amount": 0.01,
  "note": "Promotional bonus"
}
```

**Response (200 - Success):**
```json
{
  "message": "Successfully sent 0.01 BTC to user john_doe",
  "transaction": {
    "id": 10,
    "user_id": 1,
    "from_address": "ADMIN_WALLET",
    "to_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "currency": "BTC",
    "amount": 0.01000000,
    "fee": 0.00000000,
    "tx_hash": "0xadmin123456789...",
    "block_number": 17500010,
    "block_hash": "0xadmin987654321...",
    "status": "confirmed",
    "transaction_type": "receive",
    "created_at": "2024-01-15T17:00:00",
    "confirmed_at": "2024-01-15T17:00:00"
  },
  "updated_balance": 0.01500000
}
```

**Error Responses:**
```json
// 404 - User not found
{
  "message": "User not found"
}

// 400 - User blocked
{
  "message": "Cannot send crypto to blocked user"
}

// 404 - Wallet not found
{
  "message": "User does not have a BTC wallet"
}
```

### 22. Get Admin Crypto Transfers
**GET** `/admin/crypto-transfers`

Get all crypto transfers made by the admin.

**Headers:** Authorization: Bearer `<admin_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response (200 - Success):**
```json
{
  "transfers": [
    {
      "id": 5,
      "admin_id": 1,
      "action_type": "send_crypto",
      "target_user_id": 1,
      "action_details": {
        "currency": "BTC",
        "amount": "0.01",
        "note": "Promotional bonus",
        "transaction_id": 10
      },
      "created_at": "2024-01-15T17:00:00",
      "target_user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
      }
    }
  ],
  "total": 25,
  "pages": 2,
  "current_page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## Admin Analytics Endpoints

### 23. Admin Dashboard
**GET** `/admin/dashboard`

Get comprehensive dashboard statistics.

**Headers:** Authorization: Bearer `<admin_token>`

**Response (200 - Success):**
```json
{
  "user_stats": {
    "total_users": 150,
    "active_users": 145,
    "blocked_users": 5,
    "verified_users": 120
  },
  "wallet_stats": {
    "total_wallets": 300,
    "btc_wallets": 150,
    "usdt_wallets": 150,
    "eth_wallets": 0
  },
  "balance_stats": {
    "btc_total": 5.75000000,
    "usdt_total": 15000.00000000,
    "eth_total": 0.00000000
  },
  "transaction_stats": {
    "total_transactions": 500,
    "pending_transactions": 5,
    "confirmed_transactions": 495
  },
  "recent_actions": [
    {
      "id": 1,
      "admin_id": 1,
      "action_type": "block_user",
      "target_user_id": 5,
      "action_details": {
        "reason": "Suspicious activity"
      },
      "created_at": "2024-01-15T16:30:00"
    }
  ]
}
```

### 24. Get Admin Actions
**GET** `/admin/actions`

Get admin action history.

**Headers:** Authorization: Bearer `<admin_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `action_type` (optional): Filter by action type

**Response (200 - Success):**
```json
{
  "actions": [
    {
      "id": 1,
      "admin_id": 1,
      "action_type": "block_user",
      "target_user_id": 5,
      "action_details": {
        "reason": "Suspicious activity"
      },
      "created_at": "2024-01-15T16:30:00"
    },
    {
      "id": 2,
      "admin_id": 1,
      "action_type": "send_crypto",
      "target_user_id": 1,
      "action_details": {
        "currency": "BTC",
        "amount": "0.01",
        "note": "Promotional bonus"
      },
      "created_at": "2024-01-15T17:00:00"
    }
  ],
  "total": 50,
  "pages": 3,
  "current_page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## Error Handling

### Common Error Responses

**401 - Unauthorized:**
```json
{
  "message": "Token is missing"
}

{
  "message": "Token has expired"
}

{
  "message": "Token is invalid"
}
```

**403 - Forbidden:**
```json
{
  "message": "Account is blocked. Please contact support.",
  "blocked_reason": "Suspicious activity detected"
}

{
  "message": "Admin account is deactivated"
}
```

**404 - Not Found:**
```json
{
  "message": "User not found"
}

{
  "message": "Wallet not found"
}

{
  "message": "Transaction not found"
}
```

**500 - Internal Server Error:**
```json
{
  "message": "Internal server error"
}
```

---

## Rate Limiting

- **User endpoints**: 100 requests per minute per user
- **Admin endpoints**: 200 requests per minute per admin
- **Public endpoints** (prices): 50 requests per minute per IP

---

## Data Models

### User Model
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string", 
  "phone": "string",
  "profile_image": "string (base64)",
  "fingerprint_enabled": "boolean",
  "is_verified": "boolean",
  "is_blocked": "boolean",
  "blocked_at": "datetime",
  "blocked_reason": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Wallet Model
```json
{
  "id": "integer",
  "user_id": "integer",
  "currency": "string (BTC, USDT, ETH)",
  "address": "string",
  "balance": "decimal",
  "created_at": "datetime"
}
```

### Transaction Model
```json
{
  "id": "integer",
  "user_id": "integer",
  "from_address": "string",
  "to_address": "string",
  "currency": "string",
  "amount": "decimal",
  "fee": "decimal",
  "tx_hash": "string",
  "block_number": "integer",
  "block_hash": "string",
  "gas_used": "integer",
  "gas_price": "decimal",
  "contract_address": "string",
  "token_id": "string",
  "status": "string (pending, confirmed, failed)",
  "transaction_type": "string (send, receive)",
  "created_at": "datetime",
  "confirmed_at": "datetime"
}
```

### Admin Model
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string (admin, super_admin)",
  "is_active": "boolean",
  "last_login": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Security Notes

1. **Always use HTTPS** in production
2. **Store tokens securely** on the client side
3. **Implement proper token refresh** mechanisms
4. **Validate all input data** before sending requests
5. **Handle errors gracefully** in the mobile app
6. **Log security events** for audit purposes

---

## Support

For technical support or API questions, contact:
- **Email**: support@alphazee09.com
- **Documentation**: https://docs.alphazee09.com
- **Status Page**: https://status.alphazee09.com

---

**Last Updated**: January 15, 2024
**Version**: 2.0.0