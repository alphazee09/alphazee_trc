from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
import hashlib

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.Text, nullable=True)
    fingerprint_enabled = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    blocked_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    wallets = db.relationship('Wallet', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    kyc_records = db.relationship('KYCRecord', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'fingerprint_enabled': self.fingerprint_enabled,
            'is_verified': self.is_verified,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'blocked_reason': self.blocked_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(50), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    admin_actions = db.relationship('AdminAction', backref='admin', lazy=True)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AdminAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # block_user, unblock_user, send_crypto, view_wallet
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action_details = db.Column(db.JSON, nullable=True)  # Store additional details about the action
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminAction {self.action_type} by Admin {self.admin_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'action_type': self.action_type,
            'target_user_id': self.target_user_id,
            'action_details': self.action_details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # BTC, USDT, etc.
    address = db.Column(db.String(255), unique=True, nullable=False)
    private_key = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(20, 8), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions_sent = db.relationship('Transaction', foreign_keys='Transaction.from_wallet_id', backref='from_wallet', lazy=True)
    transactions_received = db.relationship('Transaction', foreign_keys='Transaction.to_wallet_id', backref='to_wallet', lazy=True)

    def __repr__(self):
        return f'<Wallet {self.currency}:{self.address[:10]}...>'

    def generate_address(self, currency):
        if currency == 'BTC':
            # Generate Bitcoin-like address
            random_bytes = secrets.token_bytes(25)
            address = '1' + hashlib.sha256(random_bytes).hexdigest()[:33]
        elif currency in ['USDT', 'ETH']:
            # Generate Ethereum-like address for ETH and USDT ERC-20
            random_bytes = secrets.token_bytes(20)
            address = '0x' + random_bytes.hex()
        else:
            # Default Ethereum-like format for other tokens
            random_bytes = secrets.token_bytes(20)
            address = '0x' + random_bytes.hex()
        
        self.address = address
        self.private_key = secrets.token_hex(32)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'currency': self.currency,
            'address': self.address,
            'balance': float(self.balance),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    from_wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=True)
    to_wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=True)
    from_address = db.Column(db.String(255), nullable=False)
    to_address = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(20, 8), nullable=False)
    fee = db.Column(db.Numeric(20, 8), default=0.0)
    tx_hash = db.Column(db.String(255), unique=True, nullable=False)
    block_number = db.Column(db.Integer, nullable=True)
    block_hash = db.Column(db.String(255), nullable=True)
    gas_used = db.Column(db.Integer, nullable=True)
    gas_price = db.Column(db.Numeric(20, 8), nullable=True)
    contract_address = db.Column(db.String(255), nullable=True)
    token_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    transaction_type = db.Column(db.String(20), nullable=False)  # send, receive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Transaction {self.tx_hash[:10]}...>'

    def generate_tx_hash(self):
        random_data = f"{self.from_address}{self.to_address}{self.amount}{datetime.utcnow().timestamp()}"
        self.tx_hash = '0x' + hashlib.sha256(random_data.encode()).hexdigest()

    def generate_blockchain_data(self):
        # Generate realistic blockchain data
        self.block_number = secrets.randbelow(18000000) + 17000000  # Recent block numbers
        self.block_hash = '0x' + secrets.token_hex(32)
        
        if self.currency == 'USDT':
            self.gas_used = secrets.randbelow(50000) + 21000
            self.gas_price = secrets.randbelow(50) + 10
            self.contract_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7'  # USDT contract
            self.token_id = 'USDT'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'currency': self.currency,
            'amount': float(self.amount),
            'fee': float(self.fee),
            'tx_hash': self.tx_hash,
            'block_number': self.block_number,
            'block_hash': self.block_hash,
            'gas_used': self.gas_used,
            'gas_price': float(self.gas_price) if self.gas_price else None,
            'contract_address': self.contract_address,
            'token_id': self.token_id,
            'status': self.status,
            'transaction_type': self.transaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }

class KYCRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # passport, driver_license, national_id
    document_number = db.Column(db.String(100), nullable=False)
    document_front = db.Column(db.Text, nullable=False)  # Base64 encoded image
    document_back = db.Column(db.Text, nullable=True)  # Base64 encoded image
    selfie_image = db.Column(db.Text, nullable=False)  # Base64 encoded image
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<KYCRecord {self.user_id}:{self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_notes': self.reviewer_notes
        }

class CryptoPrices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    price_usd = db.Column(db.Numeric(20, 8), nullable=False)
    change_24h = db.Column(db.Numeric(10, 4), nullable=False)
    market_cap = db.Column(db.Numeric(20, 2), nullable=True)
    volume_24h = db.Column(db.Numeric(20, 2), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CryptoPrices {self.symbol}:${self.price_usd}>'

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'price_usd': float(self.price_usd),
            'change_24h': float(self.change_24h),
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'volume_24h': float(self.volume_24h) if self.volume_24h else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

