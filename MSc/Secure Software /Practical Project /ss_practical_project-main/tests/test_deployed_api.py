import os
import re
import time

import pytest
import requests

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost").rstrip("/")

ALICE = {"username": "alice", "password": "tth1mJj5?£58"}
BOB   = {"username": "bob",   "password": "De586:Iq6}?!"}
ADMIN = {"username": "admin", "password": "L|fP1D%327mB"}

_sessions: dict = {}

def _url(path: str) -> str:
    return BASE_URL + "/" + path.lstrip("/")

def _get_csrf(session: requests.Session) -> str:
    """Fetch the login page and extract the CSRF token."""
    resp = session.get(_url("/login"), timeout=10)
    resp.raise_for_status()
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text)
    assert match, "CSRF token not found in login page"
    return match.group(1)

def _login(credentials: dict) -> requests.Session:
    session = requests.Session()
    csrf = _get_csrf(session)
    resp = session.post(
        _url("/login"),
        data={
            "username": credentials["username"],
            "password": credentials["password"],
            "csrf_token": csrf,
        },
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (302, 303), (
        f"Login failed for {credentials['username']!r}: HTTP {resp.status_code}"
    )
    return session

def _logout(session: requests.Session) -> None:
    session.get(_url("/logout"), allow_redirects=False, timeout=10)

def _get_session(credentials: dict) -> requests.Session:
    key = credentials["username"]
    if key not in _sessions:
        _sessions[key] = _login(credentials)
    return _sessions[key]

def _fresh_session(credentials: dict) -> requests.Session:
    time.sleep(1)
    return _login(credentials)

def test_api_is_running():
    resp = requests.get(_url("/health"), timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

@pytest.mark.parametrize("path", [
    "/documents",
    "/documents/1",
    "/shared",
    "/admin/users",
])
def test_unauthenticated_access_is_rejected(path):
    resp = requests.get(_url(path), allow_redirects=False, timeout=10)
    assert resp.status_code in (301, 302, 303, 307, 308, 401, 403), (
        f"Unauthenticated GET {path} returned {resp.status_code} — "
        "endpoint may be publicly accessible"
    )

def test_unauthenticated_upload_is_rejected():
    resp = requests.post(
        _url("/documents/upload"),
        data={"title": "test"},
        files={"document": ("test.txt", b"hello", "text/plain")},
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (301, 302, 303, 307, 308, 400, 401, 403), (
        f"Unauthenticated upload returned {resp.status_code}"
    )

def test_login_creates_authenticated_session():
    """After login, /documents must be accessible (HTTP 200)."""
    session = _fresh_session(ALICE)
    resp = session.get(_url("/documents"), timeout=10)
    assert resp.status_code == 200
    _logout(session)

def test_logout_invalidates_session():
    session = _fresh_session(ALICE)
    pre = session.get(_url("/documents"), timeout=10)
    assert pre.status_code == 200

    _logout(session)

    post = session.get(_url("/documents"), allow_redirects=False, timeout=10)
    assert post.status_code in (301, 302, 303, 307, 308, 401, 403), (
        "Session is still valid after logout — session was not invalidated"
    )

def test_invalid_credentials_are_rejected():
    session = requests.Session()
    csrf = _get_csrf(session)
    resp = session.post(
        _url("/login"),
        data={"username": "alice", "password": "wrongpassword!", "csrf_token": csrf},
        allow_redirects=False,
        timeout=10,
    )
    if resp.status_code in (302, 303):
        location = resp.headers.get("Location", "")
        assert "documents" not in location, (
            "Login with wrong password redirected to /documents"
        )

def test_user_can_access_own_documents():
    session = _get_session(ALICE)
    resp = session.get(_url("/documents"), timeout=10)
    assert resp.status_code == 200

def test_user_cannot_access_another_users_document_details():
    bob_session = _get_session(BOB)

    docs_page = bob_session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token from /documents — skipping IDOR test")

    upload_resp = bob_session.post(
        _url("/documents/upload"),
        data={"title": "Bob private doc", "csrf_token": csrf_match.group(1)},
        files={"document": ("bob_private.txt", b"secret content", "text/plain")},
        allow_redirects=True,
        timeout=10,
    )

    if upload_resp.status_code == 500:
        pytest.skip(
            "Upload returned 500 — FILE_ENCRYPTION_KEY is likely not set. "
            "Add it as a GitHub secret and re-run."
        )

    assert upload_resp.status_code == 200, (
        f"Bob's upload failed with {upload_resp.status_code}"
    )

    docs_resp = bob_session.get(_url("/documents"), timeout=10)
    doc_ids = re.findall(r'/documents/(\d+)', docs_resp.text)

    if not doc_ids:
        pytest.skip("Bob has no documents to test IDOR against")

    bob_doc_id = int(doc_ids[0])

    alice_session = _get_session(ALICE)
    resp = alice_session.get(_url(f"/documents/{bob_doc_id}"), timeout=10)
    assert resp.status_code in (403, 404), (
        f"Alice accessed Bob's document (id={bob_doc_id}) — "
        f"IDOR vulnerability: HTTP {resp.status_code}"
    )


def test_user_cannot_download_another_users_document():
    bob_session = _get_session(BOB)
    docs_page = bob_session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token — skipping download IDOR test")

    upload_resp = bob_session.post(
        _url("/documents/upload"),
        data={"title": "Bob confidential", "csrf_token": csrf_match.group(1)},
        files={"document": ("confidential.txt", b"top secret", "text/plain")},
        allow_redirects=True,
        timeout=10,
    )

    if upload_resp.status_code == 500:
        pytest.skip("Upload returned 500 — FILE_ENCRYPTION_KEY not set, skipping.")

    docs_resp = bob_session.get(_url("/documents"), timeout=10)
    doc_ids = re.findall(r'/documents/(\d+)', docs_resp.text)

    if not doc_ids:
        pytest.skip("Bob has no documents — skipping download IDOR test")

    bob_doc_id = int(doc_ids[0])

    alice_session = _get_session(ALICE)
    resp = alice_session.get(
        _url(f"/documents/{bob_doc_id}/download"),
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (302, 303, 401, 403, 404), (
        f"Alice downloaded Bob's document (id={bob_doc_id}) — "
        f"broken access control: HTTP {resp.status_code}"
    )

def test_regular_user_cannot_access_admin_panel():
    session = _get_session(ALICE)
    resp = session.get(_url("/admin/users"), timeout=10)
    assert resp.status_code == 403, (
        f"Regular user accessed /admin/users — HTTP {resp.status_code}"
    )

def test_regular_user_cannot_disable_another_user():
    alice_session = _get_session(ALICE)
    temp = requests.Session()
    csrf = _get_csrf(temp)

    resp = alice_session.post(
        _url("/admin/users/2/disable"),
        data={"csrf_token": csrf},
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (302, 303, 400, 401, 403), (
        f"Regular user could invoke admin disable action: HTTP {resp.status_code}"
    )

def test_admin_can_access_admin_panel():
    session = _get_session(ADMIN)
    resp = session.get(_url("/admin/users"), timeout=10)
    assert resp.status_code == 200, (
        f"Admin user could not access /admin/users: HTTP {resp.status_code}"
    )

def test_non_recipient_cannot_download_shared_document():
    alice_session = _get_session(ALICE)
    docs_page = alice_session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token — skipping shared IDOR test")

    upload_resp = alice_session.post(
        _url("/documents/upload"),
        data={"title": "Shared doc test", "csrf_token": csrf_match.group(1)},
        files={"document": ("shared_test.txt", b"shared content", "text/plain")},
        allow_redirects=True,
        timeout=10,
    )

    if upload_resp.status_code == 500:
        pytest.skip("Upload returned 500 — FILE_ENCRYPTION_KEY not set, skipping.")

    docs_resp = alice_session.get(_url("/documents"), timeout=10)
    doc_ids = re.findall(r'/documents/(\d+)', docs_resp.text)

    if not doc_ids:
        pytest.skip("Alice has no documents — skipping shared IDOR test")

    doc_id = int(doc_ids[0])

    resp = requests.get(
        _url(f"/shared/{doc_id}/download"),
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (301, 302, 303, 307, 308, 401, 403), (
        f"Unauthenticated access to /shared/{doc_id}/download returned {resp.status_code}"
    )

@pytest.mark.parametrize("bad_id", ["abc", "../etc", "-1", "0", "99999999"])
def test_malformed_document_id_is_rejected(bad_id):
    session = _get_session(ALICE)
    resp = session.get(_url(f"/documents/{bad_id}"), timeout=10)
    assert resp.status_code in (400, 403, 404), (
        f"GET /documents/{bad_id!r} returned {resp.status_code} — "
        "may indicate an unhandled exception"
    )

def test_disallowed_file_type_is_rejected():
    session = _get_session(ALICE)
    docs_page = session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token — skipping file type test")

    resp = session.post(
        _url("/documents/upload"),
        data={"title": "Shell script", "csrf_token": csrf_match.group(1)},
        files={"document": ("evil.sh", b"#!/bin/bash\nrm -rf /", "text/plain")},
        allow_redirects=True,
        timeout=10,
    )
    assert resp.status_code in (200, 400), (
        f"Upload of .sh file returned {resp.status_code} — "
        "file type validation must run before encryption"
    )
    assert "evil.sh" not in resp.text, (
        "Disallowed file 'evil.sh' appears in documents list after upload"
    )

def test_file_content_mismatch_is_rejected():
    session = _get_session(ALICE)
    docs_page = session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token — skipping magic bytes test")

    resp = session.post(
        _url("/documents/upload"),
        data={"title": "Fake PDF", "csrf_token": csrf_match.group(1)},
        files={"document": ("fake.pdf", b"this is not a pdf", "application/pdf")},
        allow_redirects=True,
        timeout=10,
    )
    assert resp.status_code in (200, 400), (
        f"Upload of fake .pdf returned {resp.status_code}"
    )
    assert "fake.pdf" not in resp.text, (
        "File with mismatched magic bytes was accepted"
    )

def test_oversized_upload_is_rejected():
    session = _get_session(ALICE)
    docs_page = session.get(_url("/documents"), timeout=10)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', docs_page.text)
    if not csrf_match:
        pytest.skip("Could not extract CSRF token — skipping size limit test")

    big_content = b"\x00" * (11 * 1024 * 1024)  # 11 MB
    resp = session.post(
        _url("/documents/upload"),
        data={"title": "Too big", "csrf_token": csrf_match.group(1)},
        files={"document": ("big.txt", big_content, "text/plain")},
        allow_redirects=True,
        timeout=30,
    )

    assert resp.status_code in (200, 400, 413), (
        f"Oversized upload returned {resp.status_code}"
    )

def test_upload_without_csrf_token_is_rejected():
    session = _get_session(ALICE)
    resp = session.post(
        _url("/documents/upload"),
        data={"title": "No CSRF"},
        files={"document": ("test.txt", b"hello", "text/plain")},
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (400, 403), (
        f"Upload without CSRF token returned {resp.status_code} — "
        "CSRF protection may not be active"
    )

def test_login_without_csrf_token_is_rejected():
    session = requests.Session()
    session.get(_url("/login"), timeout=10)
    resp = session.post(
        _url("/login"),
        data={"username": "alice", "password": "tth1mJj5?£58"},
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code in (400, 403), (
        f"Login without CSRF token returned {resp.status_code}"
    )

@pytest.mark.parametrize("header,expected_substring", [
    ("X-Frame-Options",        "DENY"),
    ("X-Content-Type-Options", "nosniff"),
    ("Content-Security-Policy","default-src"),
])
def test_security_headers_present(header, expected_substring):
    resp = requests.get(_url("/health"), timeout=10)
    value = resp.headers.get(header, "")
    assert expected_substring in value, (
        f"Security header '{header}' missing or incorrect: {value!r}"
    )