"""加密工具模块

提供数据加密、解密和安全相关功能。
"""

import base64
import hashlib
import hmac
import secrets
import uuid
from typing import Optional, Union, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from ..core import get_logger, get_config

logger = get_logger(__name__)


class CryptoError(Exception):
    """加密相关异常"""
    pass


class SymmetricCrypto:
    """对称加密工具类
    
    使用Fernet进行对称加密，基于AES 128位加密。
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """初始化对称加密器
        
        Args:
            key: 加密密钥，如果为None则从配置中获取
        """
        if key is None:
            config = get_config()
            key_str = getattr(config, 'ENCRYPTION_KEY', None)
            if key_str:
                key = key_str.encode('utf-8')
            else:
                # 生成新密钥
                key = Fernet.generate_key()
                logger.warning("未配置加密密钥，使用临时生成的密钥")
        
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        # 如果密钥不是标准Fernet格式，使用PBKDF2派生
        if len(key) != 44 or not self._is_valid_fernet_key(key):
            key = self._derive_key(key)
        
        self.fernet = Fernet(key)
    
    def _is_valid_fernet_key(self, key: bytes) -> bool:
        """检查是否为有效的Fernet密钥
        
        Args:
            key: 密钥
            
        Returns:
            bool: 是否有效
        """
        try:
            Fernet(key)
            return True
        except Exception:
            return False
    
    def _derive_key(self, password: bytes, salt: Optional[bytes] = None) -> bytes:
        """从密码派生Fernet密钥
        
        Args:
            password: 密码
            salt: 盐值，如果为None则使用固定盐值
            
        Returns:
            bytes: 派生的密钥
        """
        if salt is None:
            # 使用固定盐值以确保相同密码生成相同密钥
            salt = b'tk_bi_demo_salt_'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据（Base64编码）
            
        Raises:
            CryptoError: 加密失败
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        
        except Exception as e:
            logger.error(f"数据加密失败: {str(e)}")
            raise CryptoError(f"加密失败: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            
        Returns:
            str: 解密后的数据
            
        Raises:
            CryptoError: 解密失败
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        
        except Exception as e:
            logger.error(f"数据解密失败: {str(e)}")
            raise CryptoError(f"解密失败: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any], fields: Optional[list] = None) -> Dict[str, Any]:
        """加密字典中的指定字段
        
        Args:
            data: 要加密的字典
            fields: 要加密的字段列表，如果为None则加密所有字符串字段
            
        Returns:
            Dict[str, Any]: 加密后的字典
        """
        result = data.copy()
        
        if fields is None:
            # 加密所有字符串字段
            fields = [k for k, v in data.items() if isinstance(v, str)]
        
        for field in fields:
            if field in result and result[field] is not None:
                try:
                    result[field] = self.encrypt(str(result[field]))
                except CryptoError:
                    logger.warning(f"字段 '{field}' 加密失败，保持原值")
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], fields: list) -> Dict[str, Any]:
        """解密字典中的指定字段
        
        Args:
            data: 要解密的字典
            fields: 要解密的字段列表
            
        Returns:
            Dict[str, Any]: 解密后的字典
        """
        result = data.copy()
        
        for field in fields:
            if field in result and result[field] is not None:
                try:
                    result[field] = self.decrypt(result[field])
                except CryptoError:
                    logger.warning(f"字段 '{field}' 解密失败，保持原值")
        
        return result


class HashUtils:
    """哈希工具类
    
    提供各种哈希算法。
    """
    
    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        """计算MD5哈希
        
        Args:
            data: 要哈希的数据
            
        Returns:
            str: MD5哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()
    
    @staticmethod
    def sha1(data: Union[str, bytes]) -> str:
        """计算SHA1哈希
        
        Args:
            data: 要哈希的数据
            
        Returns:
            str: SHA1哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha1(data).hexdigest()
    
    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        """计算SHA256哈希
        
        Args:
            data: 要哈希的数据
            
        Returns:
            str: SHA256哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha512(data: Union[str, bytes]) -> str:
        """计算SHA512哈希
        
        Args:
            data: 要哈希的数据
            
        Returns:
            str: SHA512哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()
    
    @staticmethod
    def hmac_sha256(data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """计算HMAC-SHA256
        
        Args:
            data: 要哈希的数据
            key: 密钥
            
        Returns:
            str: HMAC-SHA256值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def password_hash(password: str, salt: Optional[str] = None) -> tuple:
        """生成密码哈希
        
        Args:
            password: 密码
            salt: 盐值，如果为None则自动生成
            
        Returns:
            tuple: (哈希值, 盐值)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=100000,
            backend=default_backend()
        )
        
        hash_bytes = kdf.derive(password_bytes)
        hash_hex = hash_bytes.hex()
        
        return hash_hex, salt
    
    @staticmethod
    def verify_password(password: str, hash_value: str, salt: str) -> bool:
        """验证密码
        
        Args:
            password: 密码
            hash_value: 哈希值
            salt: 盐值
            
        Returns:
            bool: 密码是否正确
        """
        try:
            computed_hash, _ = HashUtils.password_hash(password, salt)
            return secrets.compare_digest(computed_hash, hash_value)
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False


class TokenGenerator:
    """令牌生成器
    
    提供各种令牌生成功能。
    """
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """生成随机令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            str: 随机令牌（十六进制）
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_url_safe_token(length: int = 32) -> str:
        """生成URL安全的令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            str: URL安全令牌
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID
        
        Returns:
            str: UUID字符串
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """生成短ID
        
        Args:
            length: ID长度
            
        Returns:
            str: 短ID
        """
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_api_key(prefix: str = "tk", length: int = 32) -> str:
        """生成API密钥
        
        Args:
            prefix: 前缀
            length: 密钥长度
            
        Returns:
            str: API密钥
        """
        token = secrets.token_hex(length)
        return f"{prefix}_{token}"
    
    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID
        
        Returns:
            str: 会话ID
        """
        return secrets.token_urlsafe(32)


class SignatureUtils:
    """签名工具类
    
    提供数据签名和验证功能。
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """初始化签名工具
        
        Args:
            secret_key: 签名密钥，如果为None则从配置中获取
        """
        if secret_key is None:
            config = get_config()
            secret_key = getattr(config, 'SECRET_KEY', 'default_secret_key')
        
        self.secret_key = secret_key.encode('utf-8')
    
    def sign(self, data: Union[str, Dict[str, Any]]) -> str:
        """对数据进行签名
        
        Args:
            data: 要签名的数据
            
        Returns:
            str: 签名值
        """
        if isinstance(data, dict):
            # 对字典进行排序后序列化
            import json
            data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        return HashUtils.hmac_sha256(data, self.secret_key)
    
    def verify(self, data: Union[str, Dict[str, Any]], signature: str) -> bool:
        """验证数据签名
        
        Args:
            data: 原始数据
            signature: 签名值
            
        Returns:
            bool: 签名是否有效
        """
        try:
            computed_signature = self.sign(data)
            return secrets.compare_digest(computed_signature, signature)
        except Exception as e:
            logger.error(f"签名验证失败: {str(e)}")
            return False
    
    def create_signed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建带签名的数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 带签名的数据
        """
        signature = self.sign(data)
        return {
            "data": data,
            "signature": signature,
            "timestamp": int(time.time())
        }
    
    def verify_signed_data(self, signed_data: Dict[str, Any], max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """验证带签名的数据
        
        Args:
            signed_data: 带签名的数据
            max_age: 最大有效期（秒），如果为None则不检查时间
            
        Returns:
            Optional[Dict[str, Any]]: 验证成功返回原始数据，失败返回None
        """
        try:
            data = signed_data.get("data")
            signature = signed_data.get("signature")
            timestamp = signed_data.get("timestamp")
            
            if not data or not signature:
                return None
            
            # 验证签名
            if not self.verify(data, signature):
                return None
            
            # 检查时间有效性
            if max_age is not None and timestamp:
                import time
                current_time = int(time.time())
                if current_time - timestamp > max_age:
                    logger.warning("签名数据已过期")
                    return None
            
            return data
        
        except Exception as e:
            logger.error(f"签名数据验证失败: {str(e)}")
            return None


# 全局实例
_symmetric_crypto = None
_signature_utils = None


def get_symmetric_crypto() -> SymmetricCrypto:
    """获取对称加密器实例
    
    Returns:
        SymmetricCrypto: 对称加密器
    """
    global _symmetric_crypto
    if _symmetric_crypto is None:
        _symmetric_crypto = SymmetricCrypto()
    return _symmetric_crypto


def get_signature_utils() -> SignatureUtils:
    """获取签名工具实例
    
    Returns:
        SignatureUtils: 签名工具
    """
    global _signature_utils
    if _signature_utils is None:
        _signature_utils = SignatureUtils()
    return _signature_utils


# 便捷函数
def encrypt(data: Union[str, bytes]) -> str:
    """加密数据"""
    return get_symmetric_crypto().encrypt(data)


def decrypt(encrypted_data: str) -> str:
    """解密数据"""
    return get_symmetric_crypto().decrypt(encrypted_data)


def hash_password(password: str) -> tuple:
    """哈希密码"""
    return HashUtils.password_hash(password)


def verify_password(password: str, hash_value: str, salt: str) -> bool:
    """验证密码"""
    return HashUtils.verify_password(password, hash_value, salt)


def generate_token(length: int = 32) -> str:
    """生成随机令牌"""
    return TokenGenerator.generate_random_token(length)


def generate_api_key(prefix: str = "tk") -> str:
    """生成API密钥"""
    return TokenGenerator.generate_api_key(prefix)


def sign_data(data: Union[str, Dict[str, Any]]) -> str:
    """签名数据"""
    return get_signature_utils().sign(data)


def verify_signature(data: Union[str, Dict[str, Any]], signature: str) -> bool:
    """验证签名"""
    return get_signature_utils().verify(data, signature)


# 导入time模块
import time