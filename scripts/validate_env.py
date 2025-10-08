#!/usr/bin/env python3
"""
Environment Variables Validation Script
Validates that all required environment variables are set and meet security requirements.
"""
import os
import sys
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def validate_required_vars() -> Tuple[List[str], List[str]]:
    """
    Validate required environment variables.

    Returns:
        Tuple of (missing_vars, present_vars)
    """
    required_vars = [
        # Supabase
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_KEY",

        # AI APIs
        "ANTHROPIC_API_KEY",
        "GOOGLE_GEMINI_API_KEY",
        "OPENAI_API_KEY",

        # Security
        "JWT_SECRET",
        "WEBHOOK_SECRET",

        # Application
        "ENVIRONMENT",
        "LOG_LEVEL",
        "ALLOWED_ORIGINS",
    ]

    missing = []
    present = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing.append(var)
        else:
            present.append(var)

    return missing, present


def validate_optional_vars() -> Dict[str, str]:
    """
    Check optional environment variables.

    Returns:
        Dictionary of optional var name to status
    """
    optional_vars = {
        "REDIS_URL": os.getenv("REDIS_URL"),
        "PORT": os.getenv("PORT"),
        "HOST": os.getenv("HOST"),
        "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"),
    }

    return {k: "Set" if v else "Using default" for k, v in optional_vars.items()}


def validate_security_requirements() -> List[Tuple[str, bool, str]]:
    """
    Validate security-specific requirements.

    Returns:
        List of (requirement_name, passes, message) tuples
    """
    checks = []

    # JWT Secret length
    jwt_secret = os.getenv("JWT_SECRET", "")
    jwt_ok = len(jwt_secret) >= 32
    checks.append((
        "JWT_SECRET length >= 32 chars",
        jwt_ok,
        f"Current length: {len(jwt_secret)}" if jwt_secret else "Not set"
    ))

    # JWT Secret strength (not default)
    jwt_strong = jwt_secret not in [
        "your_jwt_secret_key_minimum_32_characters",
        "change_this_to_a_secure_random_string",
        "",
    ]
    checks.append((
        "JWT_SECRET is not default value",
        jwt_strong,
        "Using custom secret" if jwt_strong else "Using default/weak secret"
    ))

    # Webhook Secret length
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    webhook_ok = len(webhook_secret) >= 32
    checks.append((
        "WEBHOOK_SECRET length >= 32 chars",
        webhook_ok,
        f"Current length: {len(webhook_secret)}" if webhook_secret else "Not set"
    ))

    # Webhook Secret strength (not default)
    webhook_strong = webhook_secret not in [
        "default-webhook-secret-change-in-production",
        "change_this_to_a_secure_random_string",
        "",
    ]
    checks.append((
        "WEBHOOK_SECRET is not default value",
        webhook_strong,
        "Using custom secret" if webhook_strong else "Using default/weak secret"
    ))

    # Environment setting
    environment = os.getenv("ENVIRONMENT", "development")
    env_ok = environment in ["development", "production", "staging"]
    checks.append((
        "ENVIRONMENT is valid",
        env_ok,
        f"Current: {environment}"
    ))

    # HTTPS in production
    if environment == "production":
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        https_ok = "https://" in allowed_origins or allowed_origins == "*"
        checks.append((
            "ALLOWED_ORIGINS uses HTTPS in production",
            https_ok,
            f"Current: {allowed_origins[:50]}..."
        ))

    return checks


def validate_api_keys() -> List[Tuple[str, bool, str]]:
    """
    Validate API key formats (basic checks).

    Returns:
        List of (key_name, valid, message) tuples
    """
    checks = []

    # Supabase URL format
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_url_ok = supabase_url.startswith("https://") and ".supabase.co" in supabase_url
    checks.append((
        "SUPABASE_URL format",
        supabase_url_ok,
        "Valid Supabase URL" if supabase_url_ok else "Invalid format (should be https://xxx.supabase.co)"
    ))

    # Supabase keys (basic length check)
    supabase_key = os.getenv("SUPABASE_KEY", "")
    supabase_key_ok = len(supabase_key) > 100  # Supabase keys are long
    checks.append((
        "SUPABASE_KEY length",
        supabase_key_ok,
        f"{len(supabase_key)} chars" if supabase_key else "Not set"
    ))

    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    service_key_ok = len(supabase_service_key) > 100
    checks.append((
        "SUPABASE_SERVICE_KEY length",
        service_key_ok,
        f"{len(supabase_service_key)} chars" if supabase_service_key else "Not set"
    ))

    # Anthropic API key format
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_ok = anthropic_key.startswith("sk-ant-")
    checks.append((
        "ANTHROPIC_API_KEY format",
        anthropic_ok,
        "Valid format (sk-ant-...)" if anthropic_ok else "Invalid format"
    ))

    # OpenAI API key format
    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_ok = openai_key.startswith("sk-")
    checks.append((
        "OPENAI_API_KEY format",
        openai_ok,
        "Valid format (sk-...)" if openai_ok else "Invalid format"
    ))

    # Google Gemini API key (basic check)
    gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY", "")
    gemini_ok = len(gemini_key) > 20  # Basic length check
    checks.append((
        "GOOGLE_GEMINI_API_KEY length",
        gemini_ok,
        f"{len(gemini_key)} chars" if gemini_key else "Not set"
    ))

    return checks


def generate_secure_secret(length: int = 64) -> str:
    """Generate a secure random secret."""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main() -> int:
    """Main validation function."""
    print_header("🔍 ENVIRONMENT VARIABLES VALIDATION")

    # Load .env file if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_success("Loaded .env file")
    except ImportError:
        print_warning("python-dotenv not installed, reading from environment only")

    # Check required variables
    print_header("📋 Required Variables")
    missing, present = validate_required_vars()

    if present:
        print(f"\n{Colors.BOLD}Present ({len(present)}/{len(present) + len(missing)}):{Colors.END}")
        for var in present:
            value = os.getenv(var, "")
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print_success(f"{var}: {masked}")

    if missing:
        print(f"\n{Colors.BOLD}Missing ({len(missing)}):{Colors.END}")
        for var in missing:
            print_error(f"{var}: NOT SET")

    # Check optional variables
    print_header("⚙️  Optional Variables")
    optional = validate_optional_vars()
    for var, status in optional.items():
        if status == "Set":
            print_success(f"{var}: {status}")
        else:
            print_warning(f"{var}: {status}")

    # Security checks
    print_header("🔒 Security Requirements")
    security_checks = validate_security_requirements()
    security_passed = 0
    security_total = len(security_checks)

    for name, passes, message in security_checks:
        if passes:
            print_success(f"{name}: {message}")
            security_passed += 1
        else:
            print_error(f"{name}: {message}")

    # API key validation
    print_header("🔑 API Key Validation")
    api_checks = validate_api_keys()
    api_passed = 0
    api_total = len(api_checks)

    for name, valid, message in api_checks:
        if valid:
            print_success(f"{name}: {message}")
            api_passed += 1
        else:
            print_error(f"{name}: {message}")

    # Summary
    print_header("📊 Validation Summary")

    all_passed = len(missing) == 0 and security_passed == security_total and api_passed == api_total

    if all_passed:
        print_success(f"All checks passed! ✨")
        print_success(f"Required variables: {len(present)}/{len(present) + len(missing)}")
        print_success(f"Security checks: {security_passed}/{security_total}")
        print_success(f"API key checks: {api_passed}/{api_total}")
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Environment is ready for deployment!{Colors.END}\n")
        return 0
    else:
        print_error(f"Some checks failed!")
        print(f"Required variables: {len(present)}/{len(present) + len(missing)}")
        print(f"Security checks: {security_passed}/{security_total}")
        print(f"API key checks: {api_passed}/{api_total}")

        # Provide recommendations
        print_header("💡 Recommendations")

        if missing:
            print_warning(f"Set missing variables in .env file")

        if security_passed < security_total:
            print_warning("Generate secure secrets:")
            print(f"\n  JWT_SECRET={generate_secure_secret(64)}")
            print(f"  WEBHOOK_SECRET={generate_secure_secret(64)}\n")

        if api_passed < api_total:
            print_warning("Verify API keys are correctly copied from provider dashboards")

        print(f"\n{Colors.RED}{Colors.BOLD}✗ Environment validation failed. Fix issues before deployment.{Colors.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
