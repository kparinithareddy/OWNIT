import pytest
import jwt
from datetime import datetime, timezone, timedelta
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.exceptions import UnauthorizedException, ValidationException
from app.services.document_service import validate_magic_bytes, sanitize_filename
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse


def test_password_hashing_security():
    password = "SuperSecretPassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)

    # 1. Must not be plaintext
    assert h1 != password
    # 2. Must use unique salts (bcrypt)
    assert h1 != h2
    # 3. Must verify successfully
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True
    # 4. Must reject wrong password
    assert verify_password("WrongPassword!", h1) is False


def test_jwt_expiration_security():
    # Create expired token (-10 minutes)
    expired_token = create_access_token(
        data={"sub": "user123", "username": "testuser"},
        expires_delta=timedelta(minutes=-10)
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        decode_access_token(expired_token)

    assert "expired" in exc_info.value.message.lower()


def test_magic_bytes_file_upload_validation():
    # Valid PDF magic bytes
    valid_pdf_bytes = b"%PDF-1.4\n%..."
    assert validate_magic_bytes(valid_pdf_bytes, ".pdf") is True

    # Malicious script claiming to be PDF
    fake_pdf_bytes = b"<?php echo 'malicious code'; ?>"
    assert validate_magic_bytes(fake_pdf_bytes, ".pdf") is False

    # Valid PNG magic bytes
    valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
    assert validate_magic_bytes(valid_png_bytes, ".png") is True

    # Malicious executable claiming to be PNG
    fake_png_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
    assert validate_magic_bytes(fake_png_bytes, ".png") is False

    # Valid JPEG magic bytes
    valid_jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    assert validate_magic_bytes(valid_jpeg_bytes, ".jpg") is True
    assert validate_magic_bytes(valid_jpeg_bytes, ".jpeg") is True


def test_filename_header_sanitization():
    # Attempt HTTP response splitting / header injection
    malicious_filename = "document\r\nSet-Cookie: session=hijacked\r\n.pdf"
    clean_name = sanitize_filename(malicious_filename)

    assert "\r" not in clean_name
    assert "\n" not in clean_name
    assert '"' not in clean_name
    assert "\\" not in clean_name
    assert "/" not in clean_name

    # Directory traversal in filename
    traversal_name = "../../../etc/passwd"
    clean_traversal = sanitize_filename(traversal_name)
    assert ".." not in clean_traversal
    assert "/" not in clean_traversal
