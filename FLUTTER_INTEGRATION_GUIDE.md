# Bazari Crypto Wallet - Flutter Integration Guide

## Overview

This comprehensive guide provides everything the Flutter team needs to integrate with the Bazari Crypto Wallet API. The system includes user authentication, wallet management, crypto transactions, admin functionality, and real-time market data.

**Base URL**: `https://bazari.aygroup.app/api`

## 🔑 Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```dart
headers: {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer YOUR_TOKEN_HERE',
}
```

### Token Types
- **User Token**: 30-day expiry for regular users
- **Admin Token**: 8-hour expiry for admin users

---

## 📱 User Features & Endpoints

### 1. User Registration
**Automatic Wallet Generation**: Every new user automatically gets BTC, USDT, and ETH wallets created.

**Endpoint**: `POST /register`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> registerUser({
  required String username,
  required String email,
  required String password,
  String? firstName,
  String? lastName,
  String? phone,
}) async {
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/register'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'email': email,
      'password': password,
      'first_name': firstName ?? '',
      'last_name': lastName ?? '',
      'phone': phone ?? '',
    }),
  );

  if (response.statusCode == 201) {
    final data = jsonDecode(response.body);
    // Store token for future requests
    await storeToken(data['token']);
    return data;
  } else {
    throw Exception('Registration failed: ${response.body}');
  }
}
```

**Response Example**:
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
    "created_at": "2024-01-15T10:30:00"
  },
  "wallets": [
    {
      "id": 1,
      "currency": "BTC",
      "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "balance": 0.0,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "currency": "USDT",
      "address": "0x742d35Cc6634C0532925a3b8D8A8d5D4F7d6c8c9",
      "balance": 0.0,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 3,
      "currency": "ETH",
      "address": "0x8ba1f109551bD432803012645Hac136c593a6924",
      "balance": 0.0,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### 2. User Login

**Endpoint**: `POST /login`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> loginUser({
  required String username,
  required String password,
}) async {
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    await storeToken(data['token']);
    return data;
  } else if (response.statusCode == 403) {
    final error = jsonDecode(response.body);
    throw Exception('Account blocked: ${error['blocked_reason']}');
  } else {
    throw Exception('Login failed: ${response.body}');
  }
}
```

**Error Handling for Blocked Users**:
```json
{
  "message": "Account is blocked. Please contact support.",
  "blocked_reason": "Suspicious activity detected",
  "blocked_at": "2024-01-15T14:30:00"
}
```

### 3. Get User Profile

**Endpoint**: `GET /profile`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getUserProfile() async {
  final token = await getStoredToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/profile'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get profile: ${response.body}');
  }
}
```

### 4. Update User Profile

**Endpoint**: `PUT /profile`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> updateUserProfile({
  String? firstName,
  String? lastName,
  String? phone,
  bool? fingerprintEnabled,
}) async {
  final token = await getStoredToken();
  final body = <String, dynamic>{};
  
  if (firstName != null) body['first_name'] = firstName;
  if (lastName != null) body['last_name'] = lastName;
  if (phone != null) body['phone'] = phone;
  if (fingerprintEnabled != null) body['fingerprint_enabled'] = fingerprintEnabled;

  final response = await http.put(
    Uri.parse('https://bazari.aygroup.app/api/profile'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
    body: jsonEncode(body),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to update profile: ${response.body}');
  }
}
```

---

## 💰 Wallet Management

### 5. Get User Wallets

**Endpoint**: `GET /wallets`

**Dart Implementation**:
```dart
Future<List<Map<String, dynamic>>> getUserWallets() async {
  final token = await getStoredToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/wallets'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    final List<dynamic> wallets = jsonDecode(response.body);
    return wallets.cast<Map<String, dynamic>>();
  } else {
    throw Exception('Failed to get wallets: ${response.body}');
  }
}
```

**Response Example**:
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
  },
  {
    "id": 3,
    "user_id": 1,
    "currency": "ETH",
    "address": "0x8ba1f109551bD432803012645Hac136c593a6924",
    "balance": 2.75000000,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 6. Get Wallet Balance

**Endpoint**: `GET /wallets/{wallet_id}/balance`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getWalletBalance(int walletId) async {
  final token = await getStoredToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/wallets/$walletId/balance'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get balance: ${response.body}');
  }
}
```

---

## 🔄 Transaction Management

### 7. Send Cryptocurrency

**Endpoint**: `POST /transactions/send`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> sendCrypto({
  required String currency,
  required String toAddress,
  required double amount,
}) async {
  final token = await getStoredToken();
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/transactions/send'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
    body: jsonEncode({
      'currency': currency,
      'to_address': toAddress,
      'amount': amount,
    }),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    final error = jsonDecode(response.body);
    throw Exception('Send failed: ${error['message']}');
  }
}
```

**Response Example**:
```json
{
  "message": "Transaction sent successfully",
  "transaction": {
    "id": 2,
    "user_id": 1,
    "from_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "to_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "currency": "BTC",
    "amount": 0.001,
    "fee": 0.00001,
    "tx_hash": "0x9876543210fedcba...",
    "status": "pending",
    "transaction_type": "send",
    "created_at": "2024-01-15T15:00:00"
  },
  "remaining_balance": 0.00399000
}
```

### 8. Get Transaction History

**Endpoint**: `GET /wallets/{wallet_id}/transactions`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getTransactionHistory({
  required int walletId,
  int page = 1,
  int perPage = 20,
}) async {
  final token = await getStoredToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/wallets/$walletId/transactions?page=$page&per_page=$perPage'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get transactions: ${response.body}');
  }
}
```

### 9. Get Transaction Details

**Endpoint**: `GET /transactions/{transaction_id}`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getTransactionDetails(int transactionId) async {
  final token = await getStoredToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/transactions/$transactionId'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get transaction: ${response.body}');
  }
}
```

---

## 📊 Market Data

### 10. Get Crypto Prices

**Endpoint**: `GET /crypto/prices`

**Dart Implementation**:
```dart
Future<List<Map<String, dynamic>>> getCryptoPrices() async {
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/crypto/prices'),
    headers: {'Content-Type': 'application/json'},
  );

  if (response.statusCode == 200) {
    final List<dynamic> prices = jsonDecode(response.body);
    return prices.cast<Map<String, dynamic>>();
  } else {
    throw Exception('Failed to get prices: ${response.body}');
  }
}
```

**Response Example**:
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
  },
  {
    "id": 3,
    "symbol": "ETH",
    "name": "Ethereum",
    "price_usd": 3200.75,
    "change_24h": 1.8,
    "market_cap": 380000000000,
    "volume_24h": 15000000000,
    "updated_at": "2024-01-15T15:00:00"
  }
]
```

### 11. Get Specific Crypto Price

**Endpoint**: `GET /crypto/price/{symbol}`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getCryptoPrice(String symbol) async {
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/crypto/price/$symbol'),
    headers: {'Content-Type': 'application/json'},
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get price for $symbol: ${response.body}');
  }
}
```

---

## 🔐 Admin Features & Endpoints

### 12. Admin Login

**Endpoint**: `POST /admin/login`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> adminLogin({
  required String username,
  required String password,
}) async {
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/admin/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    await storeAdminToken(data['token']);
    return data;
  } else {
    throw Exception('Admin login failed: ${response.body}');
  }
}
```

### 13. Admin Dashboard

**Endpoint**: `GET /admin/dashboard`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getAdminDashboard() async {
  final token = await getStoredAdminToken();
  final response = await http.get(
    Uri.parse('https://bazari.aygroup.app/api/admin/dashboard'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get dashboard: ${response.body}');
  }
}
```

**Response Example**:
```json
{
  "user_stats": {
    "total_users": 150,
    "active_users": 145,
    "blocked_users": 5,
    "verified_users": 120
  },
  "wallet_stats": {
    "total_wallets": 450,
    "btc_wallets": 150,
    "usdt_wallets": 150,
    "eth_wallets": 150
  },
  "balance_stats": {
    "btc_total": 5.75000000,
    "usdt_total": 15000.00000000,
    "eth_total": 125.50000000
  },
  "transaction_stats": {
    "total_transactions": 500,
    "pending_transactions": 5,
    "confirmed_transactions": 495
  }
}
```

### 14. Get All Users (Admin)

**Endpoint**: `GET /admin/users`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getAdminUsers({
  int page = 1,
  int perPage = 20,
  String search = '',
  String status = '',
}) async {
  final token = await getStoredAdminToken();
  final queryParams = <String, String>{
    'page': page.toString(),
    'per_page': perPage.toString(),
  };
  
  if (search.isNotEmpty) queryParams['search'] = search;
  if (status.isNotEmpty) queryParams['status'] = status;

  final uri = Uri.parse('https://bazari.aygroup.app/api/admin/users')
      .replace(queryParameters: queryParams);

  final response = await http.get(
    uri,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get users: ${response.body}');
  }
}
```

### 15. Block/Unblock User

**Block User**: `POST /admin/users/{user_id}/block`
**Unblock User**: `POST /admin/users/{user_id}/unblock`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> blockUser({
  required int userId,
  required String reason,
}) async {
  final token = await getStoredAdminToken();
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/admin/users/$userId/block'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
    body: jsonEncode({'reason': reason}),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to block user: ${response.body}');
  }
}

Future<Map<String, dynamic>> unblockUser(int userId) async {
  final token = await getStoredAdminToken();
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/admin/users/$userId/unblock'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to unblock user: ${response.body}');
  }
}
```

### 16. Admin Send Crypto

**Endpoint**: `POST /admin/send-crypto`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> adminSendCrypto({
  required int userId,
  required String currency,
  required double amount,
  String note = '',
}) async {
  final token = await getStoredAdminToken();
  final response = await http.post(
    Uri.parse('https://bazari.aygroup.app/api/admin/send-crypto'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
    body: jsonEncode({
      'user_id': userId,
      'currency': currency,
      'amount': amount,
      'note': note,
    }),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to send crypto: ${response.body}');
  }
}
```

### 17. View All Wallets (Admin)

**Endpoint**: `GET /admin/wallets`

**Dart Implementation**:
```dart
Future<Map<String, dynamic>> getAdminWallets({
  int page = 1,
  int perPage = 50,
  String currency = '',
  int? userId,
}) async {
  final token = await getStoredAdminToken();
  final queryParams = <String, String>{
    'page': page.toString(),
    'per_page': perPage.toString(),
  };
  
  if (currency.isNotEmpty) queryParams['currency'] = currency;
  if (userId != null) queryParams['user_id'] = userId.toString();

  final uri = Uri.parse('https://bazari.aygroup.app/api/admin/wallets')
      .replace(queryParameters: queryParams);

  final response = await http.get(
    uri,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to get wallets: ${response.body}');
  }
}
```

---

## 🛠 Utility Functions

### Token Management

```dart
import 'package:shared_preferences/shared_preferences.dart';

class TokenManager {
  static const String _userTokenKey = 'user_token';
  static const String _adminTokenKey = 'admin_token';

  static Future<void> storeToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userTokenKey, token);
  }

  static Future<void> storeAdminToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_adminTokenKey, token);
  }

  static Future<String?> getStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userTokenKey);
  }

  static Future<String?> getStoredAdminToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_adminTokenKey);
  }

  static Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userTokenKey);
    await prefs.remove(_adminTokenKey);
  }
}
```

### Error Handling

```dart
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => 'ApiException: $message';
}

class ApiService {
  static void handleError(http.Response response) {
    switch (response.statusCode) {
      case 401:
        throw ApiException('Unauthorized - Please login again', statusCode: 401);
      case 403:
        final body = jsonDecode(response.body);
        if (body.containsKey('blocked_reason')) {
          throw ApiException('Account blocked: ${body['blocked_reason']}', statusCode: 403);
        }
        throw ApiException('Forbidden', statusCode: 403);
      case 404:
        throw ApiException('Resource not found', statusCode: 404);
      case 500:
        throw ApiException('Server error - Please try again later', statusCode: 500);
      default:
        throw ApiException('Request failed: ${response.body}', statusCode: response.statusCode);
    }
  }
}
```

### Complete API Service Class

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class BazariApiService {
  static const String baseUrl = 'https://bazari.aygroup.app/api';

  // User Authentication
  static Future<Map<String, dynamic>> register({
    required String username,
    required String email,
    required String password,
    String? firstName,
    String? lastName,
    String? phone,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'email': email,
        'password': password,
        'first_name': firstName ?? '',
        'last_name': lastName ?? '',
        'phone': phone ?? '',
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      await TokenManager.storeToken(data['token']);
      return data;
    } else {
      ApiService.handleError(response);
      throw ApiException('Registration failed');
    }
  }

  static Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await TokenManager.storeToken(data['token']);
      return data;
    } else {
      ApiService.handleError(response);
      throw ApiException('Login failed');
    }
  }

  // Wallet Operations
  static Future<List<Map<String, dynamic>>> getWallets() async {
    final token = await TokenManager.getStoredToken();
    if (token == null) throw ApiException('No token available');

    final response = await http.get(
      Uri.parse('$baseUrl/wallets'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final List<dynamic> wallets = jsonDecode(response.body);
      return wallets.cast<Map<String, dynamic>>();
    } else {
      ApiService.handleError(response);
      throw ApiException('Failed to get wallets');
    }
  }

  // Transaction Operations
  static Future<Map<String, dynamic>> sendCrypto({
    required String currency,
    required String toAddress,
    required double amount,
  }) async {
    final token = await TokenManager.getStoredToken();
    if (token == null) throw ApiException('No token available');

    final response = await http.post(
      Uri.parse('$baseUrl/transactions/send'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'currency': currency,
        'to_address': toAddress,
        'amount': amount,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      ApiService.handleError(response);
      throw ApiException('Failed to send crypto');
    }
  }

  // Market Data
  static Future<List<Map<String, dynamic>>> getCryptoPrices() async {
    final response = await http.get(
      Uri.parse('$baseUrl/crypto/prices'),
      headers: {'Content-Type': 'application/json'},
    );

    if (response.statusCode == 200) {
      final List<dynamic> prices = jsonDecode(response.body);
      return prices.cast<Map<String, dynamic>>();
    } else {
      ApiService.handleError(response);
      throw ApiException('Failed to get crypto prices');
    }
  }

  // Admin Operations
  static Future<Map<String, dynamic>> adminLogin({
    required String username,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/admin/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await TokenManager.storeAdminToken(data['token']);
      return data;
    } else {
      ApiService.handleError(response);
      throw ApiException('Admin login failed');
    }
  }

  static Future<Map<String, dynamic>> getAdminDashboard() async {
    final token = await TokenManager.getStoredAdminToken();
    if (token == null) throw ApiException('No admin token available');

    final response = await http.get(
      Uri.parse('$baseUrl/admin/dashboard'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      ApiService.handleError(response);
      throw ApiException('Failed to get admin dashboard');
    }
  }
}
```

---

## 📋 Data Models

### User Model
```dart
class User {
  final int id;
  final String username;
  final String email;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String? profileImage;
  final bool fingerprintEnabled;
  final bool isVerified;
  final bool isBlocked;
  final DateTime? blockedAt;
  final String? blockedReason;
  final DateTime createdAt;
  final DateTime updatedAt;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.firstName,
    this.lastName,
    this.phone,
    this.profileImage,
    required this.fingerprintEnabled,
    required this.isVerified,
    required this.isBlocked,
    this.blockedAt,
    this.blockedReason,
    required this.createdAt,
    required this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      phone: json['phone'],
      profileImage: json['profile_image'],
      fingerprintEnabled: json['fingerprint_enabled'] ?? false,
      isVerified: json['is_verified'] ?? false,
      isBlocked: json['is_blocked'] ?? false,
      blockedAt: json['blocked_at'] != null ? DateTime.parse(json['blocked_at']) : null,
      blockedReason: json['blocked_reason'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

### Wallet Model
```dart
class Wallet {
  final int id;
  final int userId;
  final String currency;
  final String address;
  final double balance;
  final DateTime createdAt;

  Wallet({
    required this.id,
    required this.userId,
    required this.currency,
    required this.address,
    required this.balance,
    required this.createdAt,
  });

  factory Wallet.fromJson(Map<String, dynamic> json) {
    return Wallet(
      id: json['id'],
      userId: json['user_id'],
      currency: json['currency'],
      address: json['address'],
      balance: (json['balance'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
```

### Transaction Model
```dart
class Transaction {
  final int id;
  final int userId;
  final String fromAddress;
  final String toAddress;
  final String currency;
  final double amount;
  final double fee;
  final String txHash;
  final int? blockNumber;
  final String? blockHash;
  final String status;
  final String transactionType;
  final DateTime createdAt;
  final DateTime? confirmedAt;

  Transaction({
    required this.id,
    required this.userId,
    required this.fromAddress,
    required this.toAddress,
    required this.currency,
    required this.amount,
    required this.fee,
    required this.txHash,
    this.blockNumber,
    this.blockHash,
    required this.status,
    required this.transactionType,
    required this.createdAt,
    this.confirmedAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      userId: json['user_id'],
      fromAddress: json['from_address'],
      toAddress: json['to_address'],
      currency: json['currency'],
      amount: (json['amount'] as num).toDouble(),
      fee: (json['fee'] as num).toDouble(),
      txHash: json['tx_hash'],
      blockNumber: json['block_number'],
      blockHash: json['block_hash'],
      status: json['status'],
      transactionType: json['transaction_type'],
      createdAt: DateTime.parse(json['created_at']),
      confirmedAt: json['confirmed_at'] != null ? DateTime.parse(json['confirmed_at']) : null,
    );
  }
}
```

### Crypto Price Model
```dart
class CryptoPrice {
  final int id;
  final String symbol;
  final String name;
  final double priceUsd;
  final double change24h;
  final double? marketCap;
  final double? volume24h;
  final DateTime updatedAt;

  CryptoPrice({
    required this.id,
    required this.symbol,
    required this.name,
    required this.priceUsd,
    required this.change24h,
    this.marketCap,
    this.volume24h,
    required this.updatedAt,
  });

  factory CryptoPrice.fromJson(Map<String, dynamic> json) {
    return CryptoPrice(
      id: json['id'],
      symbol: json['symbol'],
      name: json['name'],
      priceUsd: (json['price_usd'] as num).toDouble(),
      change24h: (json['change_24h'] as num).toDouble(),
      marketCap: json['market_cap'] != null ? (json['market_cap'] as num).toDouble() : null,
      volume24h: json['volume_24h'] != null ? (json['volume_24h'] as num).toDouble() : null,
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

---

## 🔒 Security Best Practices

### 1. Token Storage
```dart
// Use flutter_secure_storage for sensitive data
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureTokenManager {
  static const _storage = FlutterSecureStorage();
  static const String _userTokenKey = 'user_token';
  static const String _adminTokenKey = 'admin_token';

  static Future<void> storeToken(String token) async {
    await _storage.write(key: _userTokenKey, value: token);
  }

  static Future<String?> getToken() async {
    return await _storage.read(key: _userTokenKey);
  }

  static Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}
```

### 2. Network Security
```dart
import 'package:dio/dio.dart';
import 'package:dio_certificate_pinning/dio_certificate_pinning.dart';

class SecureHttpClient {
  static Dio createSecureClient() {
    final dio = Dio();
    
    // Add certificate pinning
    dio.interceptors.add(CertificatePinningInterceptor(
      allowedSHAFingerprints: ['YOUR_SERVER_CERTIFICATE_FINGERPRINT'],
    ));

    // Add request/response logging in debug mode
    if (kDebugMode) {
      dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
      ));
    }

    return dio;
  }
}
```

### 3. Input Validation
```dart
class ValidationUtils {
  static bool isValidEmail(String email) {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }

  static bool isValidPassword(String password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    return RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$').hasMatch(password);
  }

  static bool isValidCryptoAddress(String address, String currency) {
    switch (currency.toUpperCase()) {
      case 'BTC':
        return RegExp(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$').hasMatch(address);
      case 'ETH':
      case 'USDT':
        return RegExp(r'^0x[a-fA-F0-9]{40}$').hasMatch(address);
      default:
        return false;
    }
  }
}
```

---

## 🚀 Getting Started Checklist

### 1. Setup Dependencies
Add these to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  dio: ^5.3.2
  dio_certificate_pinning: ^6.0.0

dev_dependencies:
  json_annotation: ^4.8.1
  json_serializable: ^6.7.1
  build_runner: ^2.4.7
```

### 2. Initialize Services
```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize secure storage
  await SecureTokenManager.initialize();
  
  runApp(MyApp());
}
```

### 3. Test API Connection
```dart
Future<void> testApiConnection() async {
  try {
    final prices = await BazariApiService.getCryptoPrices();
    print('API Connection successful. Got ${prices.length} crypto prices.');
  } catch (e) {
    print('API Connection failed: $e');
  }
}
```

---

## 📞 Support & Resources

### Base URL
**Production**: `https://bazari.aygroup.app/api`

### Default Admin Credentials (for testing)
- **Username**: `admin`
- **Password**: `Admin123!`
- **Email**: `admin@alphazee09.com`

### Supported Cryptocurrencies
- **BTC** (Bitcoin)
- **USDT** (Tether)
- **ETH** (Ethereum)

### Rate Limits
- **User endpoints**: 100 requests per minute
- **Admin endpoints**: 200 requests per minute
- **Public endpoints**: 50 requests per minute

### Error Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden (Account blocked)
- **404**: Not Found
- **500**: Server Error

---

**Last Updated**: August 16, 2024  
**Base URL**: https://bazari.aygroup.app/api  
**Version**: 2.0.0  
**Features**: Complete wallet generation, admin management, crypto transactions