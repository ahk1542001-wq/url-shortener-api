import re
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator

RESERVED_CODES = {"api", "static", "health", "docs", "openapi", "u", "admin", "tree"}


class ShortenRequest(BaseModel):
    url: str
    custom_code: Optional[str] = None
    title: Optional[str] = None
    show_on_tree: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or fewer")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 3 or len(v) > 20:
            raise ValueError("Custom code must be 3-20 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError(
                "Custom code must contain only letters, numbers, and hyphens"
            )
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved code and cannot be used")
        return v


class EditLinkRequest(BaseModel):
    original_url: str
    title: Optional[str] = None
    show_on_tree: bool = False

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or fewer")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        value = v.strip()
        if len(value) < 3 or len(value) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError(
                "Username must contain only letters, numbers, hyphens, and underscores"
            )
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 5 or len(v) > 128:
            raise ValueError("Password must be 5-128 characters")
        return v


class UpdateAdminUserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        value = v.strip()
        if len(value) < 3 or len(value) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError(
                "Username must contain only letters, numbers, hyphens, and underscores"
            )
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if len(v) < 5 or len(v) > 128:
            raise ValueError("Password must be 5-128 characters")
        return v

    @model_validator(mode="after")
    def require_change(self):
        if self.username is None and self.password is None and self.is_active is None:
            raise ValueError("Provide at least one user change")
        return self


class CreateProfileRequest(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError("Username must contain only letters, numbers, and hyphens")
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved name and cannot be used")
        return v.lower()


class SocialLink(BaseModel):
    platform: str
    url: str
    title: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if len(v) < 1 or len(v) > 20:
            raise ValueError("Platform name must be 1-20 characters")
        if not re.match(r"^[a-z-]+$", v):
            raise ValueError(
                "Platform name must contain only lowercase letters and hyphens"
            )
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class UpdateProfileRequest(BaseModel):
    username: str
    bio: Optional[str] = None
    social_links: Optional[List[SocialLink]] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, and hyphens (e.g. my-name-123, digital-creator)"
            )
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved name and cannot be used")
        return v.lower()

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "<" in v or ">" in v:
                raise ValueError("HTML is not allowed in bio")
            if len(v) > 500:
                raise ValueError("Bio must be 500 characters or fewer")
        return v


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    already_exists: bool = False


class AnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: str
    last_accessed: str
