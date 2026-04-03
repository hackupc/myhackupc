from user.views.authentication import (
    login, signup, Logout, activate,
    password_reset, password_reset_confirm, password_reset_complete, password_reset_done,
    verify_email_required, set_password, send_email_verification,
    callback, SponsorRegister,
)
from user.views.profile import UserProfile, DeleteAccount

__all__ = [
    'login', 'signup', 'Logout', 'activate',
    'password_reset', 'password_reset_confirm', 'password_reset_complete', 'password_reset_done',
    'verify_email_required', 'set_password', 'send_email_verification',
    'callback', 'SponsorRegister',
    'UserProfile', 'DeleteAccount',
]
