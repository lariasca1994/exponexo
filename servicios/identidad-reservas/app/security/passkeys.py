import json
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import get_settings
from app.security.encryption import decrypt_secret, encrypt_secret


def create_passkey_registration_options(
    user_id: str,
    email: str,
    name: str,
    existing_credential_ids: list[str],
) -> tuple[dict[str, Any], str]:
    settings = get_settings()
    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred_id))
        for cred_id in existing_credential_ids
    ]
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user_id.encode("utf-8"),
        user_name=email,
        user_display_name=name,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    challenge_token = encrypt_secret(
        json.dumps({"user_id": user_id, "challenge": bytes_to_base64url(options.challenge)})
    )
    return json.loads(options_to_json(options)), challenge_token


def complete_passkey_registration(
    user_id: str,
    challenge_token: str,
    credential_payload: dict[str, Any],
) -> tuple[str, str, int]:
    settings = get_settings()
    challenge_data = json.loads(decrypt_secret(challenge_token))
    if challenge_data.get("user_id") != user_id:
        raise ValueError("El desafío WebAuthn no corresponde al usuario actual.")

    expected_challenge = base64url_to_bytes(challenge_data["challenge"])
    verification = verify_registration_response(
        credential=credential_payload,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin_url,
    )
    cred_id_b64 = bytes_to_base64url(verification.credential_id)
    pub_key_b64 = bytes_to_base64url(verification.credential_public_key)
    return cred_id_b64, pub_key_b64, verification.sign_count


def create_passkey_authentication_options(
    user_id: str,
    credential_ids: list[str],
) -> tuple[dict[str, Any], str]:
    settings = get_settings()
    allow_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred_id))
        for cred_id in credential_ids
    ]
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    challenge_token = encrypt_secret(
        json.dumps({"user_id": user_id, "challenge": bytes_to_base64url(options.challenge)})
    )
    return json.loads(options_to_json(options)), challenge_token


def complete_passkey_authentication(
    expected_user_id: str,
    challenge_token: str,
    credential_payload: dict[str, Any],
    credential_public_key_b64: str,
    current_sign_count: int,
) -> int:
    settings = get_settings()
    challenge_data = json.loads(decrypt_secret(challenge_token))
    if challenge_data.get("user_id") != expected_user_id:
        raise ValueError("El desafío WebAuthn no coincide con el usuario.")

    expected_challenge = base64url_to_bytes(challenge_data["challenge"])
    verification = verify_authentication_response(
        credential=credential_payload,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin_url,
        credential_public_key=base64url_to_bytes(credential_public_key_b64),
        credential_current_sign_count=current_sign_count,
    )
    return verification.new_sign_count
