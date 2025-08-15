from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, Wallet, Transaction, KYCRecord, CryptoPrices, db
import jwt
import datetime
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
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
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
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
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

