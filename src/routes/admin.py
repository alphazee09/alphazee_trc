from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import Admin, User, Wallet, Transaction, AdminAction, db
import jwt
from datetime import datetime, timedelta
from functools import wraps
import secrets
from decimal import Decimal

admin_bp = Blueprint('admin', __name__)

SECRET_KEY = 'alphazee09_admin_secret_key_2024'

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Admin token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_admin = Admin.query.get(data['admin_id'])
            if not current_admin or not current_admin.is_active:
                return jsonify({'message': 'Admin not found or inactive'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Admin token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Admin token is invalid'}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated

def log_admin_action(admin_id, action_type, target_user_id=None, action_details=None):
    """Log admin actions for audit trail"""
    action = AdminAction(
        admin_id=admin_id,
        action_type=action_type,
        target_user_id=target_user_id,
        action_details=action_details
    )
    db.session.add(action)
    db.session.commit()

# Admin Authentication Routes

@admin_bp.route('/admin/register', methods=['POST'])
def admin_register():
    """Register a new admin (Super admin only functionality)"""
    try:
        data = request.json
        
        # Check if admin with username or email already exists
        if Admin.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Admin username already exists'}), 400
        
        if Admin.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Admin email already exists'}), 400
        
        password_hash = generate_password_hash(data['password'])
        
        admin = Admin(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', 'admin')
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin registered successfully',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Admin registration failed: {str(e)}'}), 500

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.json
        admin = Admin.query.filter_by(username=data['username']).first()
        
        if admin and check_password_hash(admin.password_hash, data['password']):
            if not admin.is_active:
                return jsonify({'message': 'Admin account is deactivated'}), 403
            
            # Update last login time
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            token = jwt.encode({
                'admin_id': admin.id,
                'role': admin.role,
                'exp': datetime.utcnow() + timedelta(hours=8)  # 8 hour session
            }, SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'message': 'Admin login successful',
                'token': token,
                'admin': admin.to_dict()
            }), 200
        else:
            return jsonify({'message': 'Invalid admin credentials'}), 401
            
    except Exception as e:
        return jsonify({'message': f'Admin login failed: {str(e)}'}), 500

@admin_bp.route('/admin/profile', methods=['GET'])
@admin_token_required
def admin_profile(current_admin):
    """Get admin profile"""
    return jsonify({
        'admin': current_admin.to_dict()
    }), 200

# User Management Routes

@admin_bp.route('/admin/users', methods=['GET'])
@admin_token_required
def get_all_users(current_admin):
    """Get all users with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')  # active, blocked, verified, unverified
        
        query = User.query
        
        # Apply search filter
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.first_name.contains(search)) |
                (User.last_name.contains(search))
            )
        
        # Apply status filter
        if status == 'blocked':
            query = query.filter(User.is_blocked == True)
        elif status == 'active':
            query = query.filter(User.is_blocked == False)
        elif status == 'verified':
            query = query.filter(User.is_verified == True)
        elif status == 'unverified':
            query = query.filter(User.is_verified == False)
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Log admin action
        log_admin_action(current_admin.id, 'view_users', action_details={
            'page': page,
            'per_page': per_page,
            'search': search,
            'status': status
        })
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': users.has_next,
            'has_prev': users.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch users: {str(e)}'}), 500

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_token_required
def get_user_details(current_admin, user_id):
    """Get detailed user information"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get user's wallets
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        
        # Get user's recent transactions
        transactions = Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.created_at.desc()
        ).limit(10).all()
        
        # Log admin action
        log_admin_action(current_admin.id, 'view_user_details', target_user_id=user_id)
        
        return jsonify({
            'user': user.to_dict(),
            'wallets': [wallet.to_dict() for wallet in wallets],
            'recent_transactions': [tx.to_dict() for tx in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch user details: {str(e)}'}), 500

@admin_bp.route('/admin/users/<int:user_id>/block', methods=['POST'])
@admin_token_required
def block_user(current_admin, user_id):
    """Block a user"""
    try:
        data = request.json
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.is_blocked:
            return jsonify({'message': 'User is already blocked'}), 400
        
        reason = data.get('reason', 'No reason provided')
        
        user.is_blocked = True
        user.blocked_at = datetime.utcnow()
        user.blocked_by = current_admin.id
        user.blocked_reason = reason
        
        db.session.commit()
        
        # Log admin action
        log_admin_action(current_admin.id, 'block_user', target_user_id=user_id, 
                        action_details={'reason': reason})
        
        return jsonify({
            'message': 'User blocked successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to block user: {str(e)}'}), 500

@admin_bp.route('/admin/users/<int:user_id>/unblock', methods=['POST'])
@admin_token_required
def unblock_user(current_admin, user_id):
    """Unblock a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if not user.is_blocked:
            return jsonify({'message': 'User is not blocked'}), 400
        
        user.is_blocked = False
        user.blocked_at = None
        user.blocked_by = None
        user.blocked_reason = None
        
        db.session.commit()
        
        # Log admin action
        log_admin_action(current_admin.id, 'unblock_user', target_user_id=user_id)
        
        return jsonify({
            'message': 'User unblocked successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to unblock user: {str(e)}'}), 500

# Wallet Management Routes

@admin_bp.route('/admin/wallets', methods=['GET'])
@admin_token_required
def get_all_wallets(current_admin):
    """Get all user wallet addresses"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        currency = request.args.get('currency', '')
        user_id = request.args.get('user_id', type=int)
        
        query = db.session.query(Wallet, User).join(User, Wallet.user_id == User.id)
        
        # Apply filters
        if currency:
            query = query.filter(Wallet.currency == currency.upper())
        if user_id:
            query = query.filter(Wallet.user_id == user_id)
        
        wallets = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Log admin action
        log_admin_action(current_admin.id, 'view_wallets', action_details={
            'page': page,
            'per_page': per_page,
            'currency': currency,
            'user_id': user_id
        })
        
        wallet_data = []
        for wallet, user in wallets.items:
            wallet_dict = wallet.to_dict()
            wallet_dict['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_blocked': user.is_blocked
            }
            wallet_data.append(wallet_dict)
        
        return jsonify({
            'wallets': wallet_data,
            'total': wallets.total,
            'pages': wallets.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': wallets.has_next,
            'has_prev': wallets.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch wallets: {str(e)}'}), 500

@admin_bp.route('/admin/users/<int:user_id>/wallets', methods=['GET'])
@admin_token_required
def get_user_wallets(current_admin, user_id):
    """Get specific user's wallet addresses"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        
        # Log admin action
        log_admin_action(current_admin.id, 'view_user_wallets', target_user_id=user_id)
        
        return jsonify({
            'user': user.to_dict(),
            'wallets': [wallet.to_dict() for wallet in wallets]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch user wallets: {str(e)}'}), 500

# Crypto Sending Routes

@admin_bp.route('/admin/send-crypto', methods=['POST'])
@admin_token_required
def admin_send_crypto(current_admin):
    """Admin sends crypto to a specific user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['user_id', 'currency', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        user_id = data['user_id']
        currency = data['currency'].upper()
        amount = Decimal(str(data['amount']))
        note = data.get('note', '')
        
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if user is blocked
        if user.is_blocked:
            return jsonify({'message': 'Cannot send crypto to blocked user'}), 400
        
        # Find user's wallet for the specified currency
        wallet = Wallet.query.filter_by(user_id=user_id, currency=currency).first()
        if not wallet:
            return jsonify({'message': f'User does not have a {currency} wallet'}), 404
        
        # Update wallet balance
        wallet.balance += amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            to_wallet_id=wallet.id,
            from_address='ADMIN_WALLET',
            to_address=wallet.address,
            currency=currency,
            amount=amount,
            fee=0,  # No fee for admin transfers
            transaction_type='receive',
            status='confirmed'
        )
        
        # Generate transaction hash and blockchain data
        transaction.generate_tx_hash()
        transaction.generate_blockchain_data()
        transaction.confirmed_at = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        
        # Log admin action
        log_admin_action(current_admin.id, 'send_crypto', target_user_id=user_id, 
                        action_details={
                            'currency': currency,
                            'amount': str(amount),
                            'note': note,
                            'transaction_id': transaction.id
                        })
        
        return jsonify({
            'message': f'Successfully sent {amount} {currency} to user {user.username}',
            'transaction': transaction.to_dict(),
            'updated_balance': float(wallet.balance)
        }), 200
        
    except ValueError:
        return jsonify({'message': 'Invalid amount format'}), 400
    except Exception as e:
        return jsonify({'message': f'Failed to send crypto: {str(e)}'}), 500

@admin_bp.route('/admin/crypto-transfers', methods=['GET'])
@admin_token_required
def get_admin_crypto_transfers(current_admin):
    """Get all admin crypto transfers"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get admin crypto transfer actions
        actions = AdminAction.query.filter_by(
            admin_id=current_admin.id,
            action_type='send_crypto'
        ).order_by(AdminAction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        transfers = []
        for action in actions.items:
            transfer_data = action.to_dict()
            if action.target_user_id:
                user = User.query.get(action.target_user_id)
                if user:
                    transfer_data['target_user'] = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
            transfers.append(transfer_data)
        
        return jsonify({
            'transfers': transfers,
            'total': actions.total,
            'pages': actions.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': actions.has_next,
            'has_prev': actions.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch crypto transfers: {str(e)}'}), 500

# Admin Activity and Analytics Routes

@admin_bp.route('/admin/dashboard', methods=['GET'])
@admin_token_required
def admin_dashboard(current_admin):
    """Get admin dashboard statistics"""
    try:
        # Get user statistics
        total_users = User.query.count()
        blocked_users = User.query.filter_by(is_blocked=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()
        active_users = total_users - blocked_users
        
        # Get wallet statistics
        total_wallets = Wallet.query.count()
        btc_wallets = Wallet.query.filter_by(currency='BTC').count()
        usdt_wallets = Wallet.query.filter_by(currency='USDT').count()
        eth_wallets = Wallet.query.filter_by(currency='ETH').count()
        
        # Get total balances by currency
        btc_total = db.session.query(db.func.sum(Wallet.balance)).filter_by(currency='BTC').scalar() or 0
        usdt_total = db.session.query(db.func.sum(Wallet.balance)).filter_by(currency='USDT').scalar() or 0
        eth_total = db.session.query(db.func.sum(Wallet.balance)).filter_by(currency='ETH').scalar() or 0
        
        # Get transaction statistics
        total_transactions = Transaction.query.count()
        pending_transactions = Transaction.query.filter_by(status='pending').count()
        confirmed_transactions = Transaction.query.filter_by(status='confirmed').count()
        
        # Get recent admin actions
        recent_actions = AdminAction.query.order_by(
            AdminAction.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'user_stats': {
                'total_users': total_users,
                'active_users': active_users,
                'blocked_users': blocked_users,
                'verified_users': verified_users
            },
            'wallet_stats': {
                'total_wallets': total_wallets,
                'btc_wallets': btc_wallets,
                'usdt_wallets': usdt_wallets,
                'eth_wallets': eth_wallets
            },
            'balance_stats': {
                'btc_total': float(btc_total),
                'usdt_total': float(usdt_total),
                'eth_total': float(eth_total)
            },
            'transaction_stats': {
                'total_transactions': total_transactions,
                'pending_transactions': pending_transactions,
                'confirmed_transactions': confirmed_transactions
            },
            'recent_actions': [action.to_dict() for action in recent_actions]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch dashboard data: {str(e)}'}), 500

@admin_bp.route('/admin/actions', methods=['GET'])
@admin_token_required
def get_admin_actions(current_admin):
    """Get admin action history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        action_type = request.args.get('action_type', '')
        
        query = AdminAction.query.filter_by(admin_id=current_admin.id)
        
        if action_type:
            query = query.filter_by(action_type=action_type)
        
        actions = query.order_by(AdminAction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'actions': [action.to_dict() for action in actions.items],
            'total': actions.total,
            'pages': actions.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': actions.has_next,
            'has_prev': actions.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to fetch admin actions: {str(e)}'}), 500