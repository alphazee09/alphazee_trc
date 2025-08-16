from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, Wallet, Transaction, KYCRecord, CryptoPrices, db
import jwt
from datetime import datetime, timedelta
from functools import wraps
import requests
import secrets
import base64

user_bp = Blueprint('user', __name__)

SECRET_KEY = 'alphazee09_secret_key_2024'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            if current_user.is_blocked:
                return jsonify({
                    'message': 'Account is blocked. Please contact support.',
                    'blocked_reason': current_user.blocked_reason
                }), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        password_hash = generate_password_hash(data['password'])
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create default wallets for BTC and USDT
        btc_wallet = Wallet(user_id=user.id, currency='BTC')
        btc_wallet.generate_address('BTC')
        
        usdt_wallet = Wallet(user_id=user.id, currency='USDT')
        usdt_wallet.generate_address('USDT')
        
        db.session.add(btc_wallet)
        db.session.add(usdt_wallet)
        db.session.commit()
        
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            # Check if user is blocked
            if user.is_blocked:
                return jsonify({
                    'message': 'Account is blocked. Please contact support.',
                    'blocked_reason': user.blocked_reason,
                    'blocked_at': user.blocked_at.isoformat() if user.blocked_at else None
                }), 403
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict()), 200

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.json
        
        current_user.first_name = data.get('first_name', current_user.first_name)
        current_user.last_name = data.get('last_name', current_user.last_name)
        current_user.phone = data.get('phone', current_user.phone)
        current_user.profile_image = data.get('profile_image', current_user.profile_image)
        current_user.fingerprint_enabled = data.get('fingerprint_enabled', current_user.fingerprint_enabled)
        current_user.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Profile update failed: {str(e)}'}), 500

@user_bp.route('/wallets', methods=['GET'])
@token_required
def get_wallets(current_user):
    wallets = Wallet.query.filter_by(user_id=current_user.id).all()
    return jsonify([wallet.to_dict() for wallet in wallets]), 200

@user_bp.route('/wallets/<string:currency>', methods=['GET'])
@token_required
def get_wallet_by_currency(current_user, currency):
    wallet = Wallet.query.filter_by(user_id=current_user.id, currency=currency.upper()).first()
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    return jsonify(wallet.to_dict()), 200

@user_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    return jsonify([tx.to_dict() for tx in transactions]), 200

@user_bp.route('/transactions/<string:currency>', methods=['GET'])
@token_required
def get_transactions_by_currency(current_user, currency):
    transactions = Transaction.query.filter_by(user_id=current_user.id, currency=currency.upper()).order_by(Transaction.created_at.desc()).all()
    return jsonify([tx.to_dict() for tx in transactions]), 200

@user_bp.route('/send', methods=['POST'])
@token_required
def send_crypto(current_user):
    try:
        data = request.json
        currency = data['currency'].upper()
        amount = float(data['amount'])
        to_address = data['to_address']
        
        # Check if user is verified for sending
        if not current_user.is_verified:
            return jsonify({'message': 'KYC verification required to send crypto'}), 403
        
        wallet = Wallet.query.filter_by(user_id=current_user.id, currency=currency).first()
        if not wallet:
            return jsonify({'message': 'Wallet not found'}), 404
        
        if wallet.balance < amount:
            return jsonify({'message': 'Insufficient balance'}), 400
        
        # Create transaction
        transaction = Transaction(
            user_id=current_user.id,
            from_wallet_id=wallet.id,
            from_address=wallet.address,
            to_address=to_address,
            currency=currency,
            amount=amount,
            fee=0.001 if currency == 'BTC' else 0.01,
            transaction_type='send',
            status='confirmed'
        )
        
        transaction.generate_tx_hash()
        transaction.generate_blockchain_data()
        transaction.confirmed_at = datetime.datetime.utcnow()
        
        # Update wallet balance
        wallet.balance -= amount
        wallet.balance -= transaction.fee
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction sent successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Send failed: {str(e)}'}), 500

@user_bp.route('/admin/send', methods=['POST'])
def admin_send():
    try:
        data = request.json
        admin_key = data.get('admin_key')
        
        if admin_key != 'alphazee09_admin_2024':
            return jsonify({'message': 'Unauthorized'}), 401
        
        user_id = data['user_id']
        currency = data['currency'].upper()
        amount = float(data['amount'])
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        wallet = Wallet.query.filter_by(user_id=user_id, currency=currency).first()
        if not wallet:
            return jsonify({'message': 'Wallet not found'}), 404
        
        # Create receive transaction
        transaction = Transaction(
            user_id=user_id,
            to_wallet_id=wallet.id,
            from_address='0x' + secrets.token_hex(20),  # Admin address
            to_address=wallet.address,
            currency=currency,
            amount=amount,
            fee=0,
            transaction_type='receive',
            status='confirmed'
        )
        
        transaction.generate_tx_hash()
        transaction.generate_blockchain_data()
        transaction.confirmed_at = datetime.datetime.utcnow()
        
        # Update wallet balance
        wallet.balance += amount
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Crypto sent successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Admin send failed: {str(e)}'}), 500

@user_bp.route('/kyc', methods=['POST'])
@token_required
def submit_kyc(current_user):
    try:
        data = request.json
        
        # Check if user already has pending or approved KYC
        existing_kyc = KYCRecord.query.filter_by(user_id=current_user.id).filter(
            KYCRecord.status.in_(['pending', 'approved'])
        ).first()
        
        if existing_kyc:
            return jsonify({'message': 'KYC already submitted or approved'}), 400
        
        kyc_record = KYCRecord(
            user_id=current_user.id,
            document_type=data['document_type'],
            document_number=data['document_number'],
            document_front=data['document_front'],
            document_back=data.get('document_back'),
            selfie_image=data['selfie_image']
        )
        
        db.session.add(kyc_record)
        db.session.commit()
        
        return jsonify({
            'message': 'KYC submitted successfully',
            'kyc': kyc_record.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'KYC submission failed: {str(e)}'}), 500

@user_bp.route('/kyc/status', methods=['GET'])
@token_required
def get_kyc_status(current_user):
    kyc_record = KYCRecord.query.filter_by(user_id=current_user.id).order_by(KYCRecord.submitted_at.desc()).first()
    
    if not kyc_record:
        return jsonify({'status': 'not_submitted'}), 200
    
    return jsonify(kyc_record.to_dict()), 200

@user_bp.route('/admin/kyc/approve', methods=['POST'])
def approve_kyc():
    try:
        data = request.json
        admin_key = data.get('admin_key')
        
        if admin_key != 'alphazee09_admin_2024':
            return jsonify({'message': 'Unauthorized'}), 401
        
        kyc_id = data['kyc_id']
        kyc_record = KYCRecord.query.get(kyc_id)
        
        if not kyc_record:
            return jsonify({'message': 'KYC record not found'}), 404
        
        kyc_record.status = 'approved'
        kyc_record.reviewed_at = datetime.datetime.utcnow()
        kyc_record.reviewer_notes = data.get('notes', 'Approved by admin')
        
        # Update user verification status
        user = User.query.get(kyc_record.user_id)
        user.is_verified = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'KYC approved successfully',
            'kyc': kyc_record.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'KYC approval failed: {str(e)}'}), 500

@user_bp.route('/crypto/prices', methods=['GET'])
def get_crypto_prices():
    try:
        # Fetch from CoinGecko API
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': 'bitcoin,tether,ethereum,binancecoin,cardano,solana,polkadot,dogecoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Map to our format
        crypto_mapping = {
            'bitcoin': {'symbol': 'BTC', 'name': 'Bitcoin'},
            'tether': {'symbol': 'USDT', 'name': 'Tether'},
            'ethereum': {'symbol': 'ETH', 'name': 'Ethereum'},
            'binancecoin': {'symbol': 'BNB', 'name': 'Binance Coin'},
            'cardano': {'symbol': 'ADA', 'name': 'Cardano'},
            'solana': {'symbol': 'SOL', 'name': 'Solana'},
            'polkadot': {'symbol': 'DOT', 'name': 'Polkadot'},
            'dogecoin': {'symbol': 'DOGE', 'name': 'Dogecoin'}
        }
        
        prices = []
        for coin_id, coin_data in data.items():
            if coin_id in crypto_mapping:
                crypto_info = crypto_mapping[coin_id]
                prices.append({
                    'symbol': crypto_info['symbol'],
                    'name': crypto_info['name'],
                    'price_usd': coin_data['usd'],
                    'change_24h': coin_data.get('usd_24h_change', 0),
                    'market_cap': coin_data.get('usd_market_cap'),
                    'volume_24h': coin_data.get('usd_24h_vol')
                })
        
        return jsonify(prices), 200
        
    except Exception as e:
        # Fallback data if API fails
        fallback_prices = [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'price_usd': 43250.50, 'change_24h': 2.45, 'market_cap': 847000000000, 'volume_24h': 15000000000},
            {'symbol': 'USDT', 'name': 'Tether', 'price_usd': 1.00, 'change_24h': 0.01, 'market_cap': 95000000000, 'volume_24h': 25000000000},
            {'symbol': 'ETH', 'name': 'Ethereum', 'price_usd': 2650.75, 'change_24h': 1.85, 'market_cap': 318000000000, 'volume_24h': 8000000000},
            {'symbol': 'BNB', 'name': 'Binance Coin', 'price_usd': 315.20, 'change_24h': -0.75, 'market_cap': 47000000000, 'volume_24h': 1200000000},
            {'symbol': 'ADA', 'name': 'Cardano', 'price_usd': 0.485, 'change_24h': 3.25, 'market_cap': 17000000000, 'volume_24h': 450000000},
            {'symbol': 'SOL', 'name': 'Solana', 'price_usd': 98.45, 'change_24h': 4.15, 'market_cap': 42000000000, 'volume_24h': 1800000000},
            {'symbol': 'DOT', 'name': 'Polkadot', 'price_usd': 7.25, 'change_24h': -1.25, 'market_cap': 9500000000, 'volume_24h': 180000000},
            {'symbol': 'DOGE', 'name': 'Dogecoin', 'price_usd': 0.085, 'change_24h': 5.85, 'market_cap': 12000000000, 'volume_24h': 650000000}
        ]
        return jsonify(fallback_prices), 200

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())



# Admin functionality for adding crypto to user wallets
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key or admin_key != 'alphazee09_admin_2024':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/admin/users', methods=['GET'])
@admin_required
def admin_get_all_users():
    """Get all users for admin panel"""
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            user_data = user.to_dict()
            # Add wallet information
            wallets = Wallet.query.filter_by(user_id=user.id).all()
            user_data['wallets'] = []
            
            for wallet in wallets:
                user_data['wallets'].append({
                    'id': wallet.id,
                    'currency': wallet.currency,
                    'address': wallet.address,
                    'balance': float(wallet.balance)
                })
            
            users_data.append(user_data)
        
        return jsonify({
            'message': 'Users retrieved successfully',
            'users': users_data,
            'total_users': len(users_data)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error retrieving users: {str(e)}'}), 500

@user_bp.route('/admin/users/<int:user_id>/add-crypto', methods=['POST'])
@admin_required
def admin_add_crypto_to_user(user_id):
    """Add cryptocurrency to a specific user's wallet"""
    try:
        data = request.json
        currency = data.get('currency', '').upper()
        amount = float(data.get('amount', 0))
        
        if not currency or amount <= 0:
            return jsonify({'message': 'Valid currency and amount required'}), 400
        
        if currency not in ['BTC', 'USDT', 'ETH']:
            return jsonify({'message': 'Unsupported currency. Use BTC, USDT, or ETH'}), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Find or create wallet for this currency
        wallet = Wallet.query.filter_by(user_id=user_id, currency=currency).first()
        
        if not wallet:
            # Create new wallet if it doesn't exist
            if currency == 'BTC':
                address = f"1{secrets.token_hex(16)[:25]}"
            elif currency == 'ETH' or currency == 'USDT':
                address = f"0x{secrets.token_hex(20)}"
            else:
                address = f"{currency.lower()}_{secrets.token_hex(16)}"
            
            private_key = secrets.token_hex(32)
            
            wallet = Wallet(
                user_id=user_id,
                currency=currency,
                address=address,
                private_key=private_key,
                balance=0.0
            )
            db.session.add(wallet)
        
        # Add the amount to wallet balance
        old_balance = float(wallet.balance)
        wallet.balance = float(wallet.balance) + amount
        
        # Create a transaction record for this admin addition
        transaction = Transaction(
            user_id=user_id,
            to_wallet_id=wallet.id,
            transaction_type='receive',
            currency=currency,
            amount=amount,
            fee=0.0,
            to_address=wallet.address,
            from_address='ADMIN_DEPOSIT',
            tx_hash=f"admin_{secrets.token_hex(32)}",
            block_number=secrets.randbelow(1000000) + 800000,
            block_hash=f"0x{secrets.token_hex(32)}",
            gas_used=21000 if currency in ['ETH', 'USDT'] else None,
            gas_price=20000000000 if currency in ['ETH', 'USDT'] else None,
            contract_address='0xa0b86a33e6ba3b936f1e5b6b7b8b5c6d8e9f0a1b' if currency == 'USDT' else None,
            status='confirmed',
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully added {amount} {currency} to user {user.username}',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'wallet': {
                'currency': currency,
                'address': wallet.address,
                'old_balance': old_balance,
                'new_balance': float(wallet.balance),
                'amount_added': amount
            },
            'transaction': {
                'id': transaction.id,
                'tx_hash': transaction.tx_hash,
                'block_number': transaction.block_number,
                'status': transaction.status
            }
        }), 200
        
    except ValueError:
        return jsonify({'message': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding crypto: {str(e)}'}), 500

@user_bp.route('/admin/users/<int:user_id>/wallets', methods=['GET'])
@admin_required
def admin_get_user_wallets(user_id):
    """Get all wallets for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        wallets_data = []
        
        for wallet in wallets:
            wallets_data.append({
                'id': wallet.id,
                'currency': wallet.currency,
                'address': wallet.address,
                'balance': float(wallet.balance),
                'created_at': wallet.created_at.isoformat() if wallet.created_at else None
            })
        
        return jsonify({
            'message': 'User wallets retrieved successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'wallets': wallets_data,
            'total_wallets': len(wallets_data)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error retrieving wallets: {str(e)}'}), 500

@user_bp.route('/admin/transactions', methods=['GET'])
@admin_required
def admin_get_all_transactions():
    """Get all transactions for admin monitoring"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        transactions = Transaction.query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        transactions_data = []
        for transaction in transactions.items:
            user = User.query.get(transaction.user_id)
            wallet = None
            if transaction.to_wallet_id:
                wallet = Wallet.query.get(transaction.to_wallet_id)
            elif transaction.from_wallet_id:
                wallet = Wallet.query.get(transaction.from_wallet_id)
            
            transactions_data.append({
                'id': transaction.id,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                } if user else None,
                'wallet_currency': wallet.currency if wallet else transaction.currency,
                'transaction_type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'fee': float(transaction.fee) if transaction.fee else 0,
                'to_address': transaction.to_address,
                'from_address': transaction.from_address,
                'tx_hash': transaction.tx_hash,
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'confirmed_at': transaction.confirmed_at.isoformat() if transaction.confirmed_at else None
            })
        
        return jsonify({
            'message': 'Transactions retrieved successfully',
            'transactions': transactions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': transactions.total,
                'pages': transactions.pages,
                'has_next': transactions.has_next,
                'has_prev': transactions.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error retrieving transactions: {str(e)}'}), 500

@user_bp.route('/admin/send-crypto', methods=['POST'])
@admin_required
def admin_send_crypto_to_user():
    """Send cryptocurrency from admin to any user"""
    try:
        data = request.json
        username = data.get('username')
        currency = data.get('currency', '').upper()
        amount = float(data.get('amount', 0))
        note = data.get('note', 'Admin transfer')
        
        if not username or not currency or amount <= 0:
            return jsonify({'message': 'Username, currency, and amount are required'}), 400
        
        if currency not in ['BTC', 'USDT', 'ETH']:
            return jsonify({'message': 'Unsupported currency. Use BTC, USDT, or ETH'}), 400
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': f'User {username} not found'}), 404
        
        # Find or create wallet
        wallet = Wallet.query.filter_by(user_id=user.id, currency=currency).first()
        
        if not wallet:
            # Create new wallet
            if currency == 'BTC':
                address = f"1{secrets.token_hex(16)[:25]}"
            elif currency == 'ETH' or currency == 'USDT':
                address = f"0x{secrets.token_hex(20)}"
            else:
                address = f"{currency.lower()}_{secrets.token_hex(16)}"
            
            private_key = secrets.token_hex(32)
            
            wallet = Wallet(
                user_id=user.id,
                currency=currency,
                address=address,
                private_key=private_key,
                balance=0.0
            )
            db.session.add(wallet)
        
        # Add amount to wallet
        old_balance = float(wallet.balance)
        wallet.balance = float(wallet.balance) + amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            to_wallet_id=wallet.id,
            transaction_type='receive',
            currency=currency,
            amount=amount,
            fee=0.0,
            to_address=wallet.address,
            from_address='ADMIN_SEND',
            tx_hash=f"admin_send_{secrets.token_hex(32)}",
            block_number=secrets.randbelow(1000000) + 800000,
            block_hash=f"0x{secrets.token_hex(32)}",
            gas_used=21000 if currency in ['ETH', 'USDT'] else None,
            gas_price=20000000000 if currency in ['ETH', 'USDT'] else None,
            contract_address='0xa0b86a33e6ba3b936f1e5b6b7b8b5c6d8e9f0a1b' if currency == 'USDT' else None,
            status='confirmed',
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully sent {amount} {currency} to {username}',
            'recipient': {
                'username': user.username,
                'email': user.email
            },
            'transfer_details': {
                'currency': currency,
                'amount': amount,
                'old_balance': old_balance,
                'new_balance': float(wallet.balance),
                'wallet_address': wallet.address,
                'note': note
            },
            'transaction': {
                'tx_hash': transaction.tx_hash,
                'block_number': transaction.block_number,
                'status': transaction.status,
                'timestamp': transaction.created_at.isoformat()
            }
        }), 200
        
    except ValueError:
        return jsonify({'message': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error sending crypto: {str(e)}'}), 500

@user_bp.route('/admin/stats', methods=['GET'])
@admin_required
def admin_get_stats():
    """Get admin dashboard statistics"""
    try:
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        total_wallets = Wallet.query.count()
        total_transactions = Transaction.query.count()
        
        # Get wallet balances by currency
        wallet_stats = db.session.query(
            Wallet.currency,
            db.func.count(Wallet.id).label('wallet_count'),
            db.func.sum(Wallet.balance).label('total_balance')
        ).group_by(Wallet.currency).all()
        
        currency_stats = []
        for stat in wallet_stats:
            currency_stats.append({
                'currency': stat.currency,
                'wallet_count': stat.wallet_count,
                'total_balance': float(stat.total_balance) if stat.total_balance else 0
            })
        
        # Recent transactions
        recent_transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).limit(10).all()
        
        recent_tx_data = []
        for tx in recent_transactions:
            user = User.query.get(tx.user_id)
            wallet = None
            if tx.to_wallet_id:
                wallet = Wallet.query.get(tx.to_wallet_id)
            elif tx.from_wallet_id:
                wallet = Wallet.query.get(tx.from_wallet_id)
            
            recent_tx_data.append({
                'id': tx.id,
                'username': user.username if user else 'Unknown',
                'currency': wallet.currency if wallet else tx.currency,
                'type': tx.transaction_type,
                'amount': float(tx.amount),
                'status': tx.status,
                'created_at': tx.created_at.isoformat() if tx.created_at else None
            })
        
        return jsonify({
            'message': 'Admin statistics retrieved successfully',
            'stats': {
                'total_users': total_users,
                'verified_users': verified_users,
                'total_wallets': total_wallets,
                'total_transactions': total_transactions,
                'verification_rate': round((verified_users / total_users * 100), 2) if total_users > 0 else 0
            },
            'currency_stats': currency_stats,
            'recent_transactions': recent_tx_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error retrieving stats: {str(e)}'}), 500

