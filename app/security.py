"""Authentification locale et règles d'accès aux documents."""

from dataclasses import dataclass
from hashlib import pbkdf2_hmac, sha256
import hmac
import secrets
from time import time


SESSION_COOKIE = 'novalys_session'
PBKDF2_ITERATIONS = 310_000


@dataclass(frozen=True)
class User:
    username: str
    private_folder: str


@dataclass(frozen=True)
class _Credential:
    user: User
    salt: bytes
    digest: bytes


def _password_digest(password: str, salt: bytes) -> bytes:
    return pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS
    )


class Authenticator:
    """Petit magasin de comptes et de sessions, adapté à l'API locale.

    Les mots de passe viennent de la configuration et ne sont jamais stockés
    en clair. Les sessions restent en mémoire : redémarrer l'API les invalide.
    """

    def __init__(self, password_user_a: str, password_user_b: str,
                 session_ttl: int):
        self.session_ttl = session_ttl
        self._credentials = {
            'user_a': self._credential(User('user_a', 'A'), password_user_a),
            'user_b': self._credential(User('user_b', 'B'), password_user_b),
        }
        self._sessions: dict[str, tuple[User, float]] = {}

    @staticmethod
    def _credential(user: User, password: str) -> _Credential:
        salt = secrets.token_bytes(16)
        return _Credential(user, salt, _password_digest(password, salt))

    def authenticate(self, username: str, password: str) -> User | None:
        credential = self._credentials.get(username)
        if credential is None:
            # Keep the timing of an unknown account close to a known account.
            _password_digest(password, b'novalys-unknown-user')
            return None
        candidate = _password_digest(password, credential.salt)
        if not hmac.compare_digest(candidate, credential.digest):
            return None
        return credential.user

    def create_session(self, user: User) -> str:
        self._purge_expired()
        token = secrets.token_urlsafe(32)
        self._sessions[sha256(token.encode('ascii')).hexdigest()] = (
            user, time() + self.session_ttl
        )
        return token

    def user_from_token(self, token: str | None) -> User | None:
        if not token:
            return None
        key = sha256(token.encode('ascii', errors='ignore')).hexdigest()
        session = self._sessions.get(key)
        if session is None:
            return None
        user, expires_at = session
        if expires_at <= time():
            self._sessions.pop(key, None)
            return None
        return user

    def revoke(self, token: str | None) -> None:
        if token:
            key = sha256(token.encode('ascii', errors='ignore')).hexdigest()
            self._sessions.pop(key, None)

    def _purge_expired(self) -> None:
        now = time()
        for key, (_, expires_at) in list(self._sessions.items()):
            if expires_at <= now:
                self._sessions.pop(key, None)

BASELINE_MODE = 'baseline'

# Les utilisateurs de démonstration ont chacun un périmètre privé. Aucun rôle
# transmis par le client n'est accepté comme identité.
TARGET_ACCESS = {
    'user_a': frozenset({'public', 'A'}),
    'user_b': frozenset({'public', 'B'}),
}

SYSTEM_PROMPT = '''Tu es l'assistant documentaire de Novalys, entreprise fictive.
Réponds directement à la question en français, à partir des extraits fournis.
Indique les références des extraits utilisés entre crochets à la fin de ta réponse.
Si les extraits ne permettent pas de répondre, dis-le clairement.
Ne complète pas les faits avec des connaissances externes.'''
