import re
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()


def _generate_username(base):
    """Return a unique username derived from `base`."""
    base = re.sub(r'[^\w]', '', base).lower()[:20] or 'user'
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{counter}'
        counter += 1
    return username


class NoSignupFormSocialAdapter(DefaultSocialAccountAdapter):
    """
    Bypass the /accounts/3rdparty/signup/ form entirely.
    New Google users are created and connected automatically.
    """

    def is_auto_signup_allowed(self, request, sociallogin):
        return True  # never show the intermediate signup form

    def pre_social_login(self, request, sociallogin):
        """
        Called right after Google returns but before allauth decides what to do.
        If this is a new user (not yet in the DB), create them instantly and
        connect the social account so allauth skips the signup page.
        """
        # Already connected to an existing user → nothing to do
        if sociallogin.is_existing:
            return

        # Try to find a user with the same email
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
        if not email:
            return

        try:
            existing_user = User.objects.get(email=email)
            # Connect this social account to the existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # Brand-new user — auto-create them right now
            extra = sociallogin.account.extra_data
            base = extra.get('name') or email.split('@')[0]
            username = _generate_username(base)

            user = User(
                username=username,
                email=email,
                first_name=extra.get('given_name', ''),
                last_name=extra.get('family_name', ''),
            )
            user.set_unusable_password()
            user.save()

            # Mark email verified immediately
            EmailAddress.objects.update_or_create(
                user=user,
                defaults={'email': email, 'primary': True, 'verified': True},
            )

            sociallogin.user = user
            sociallogin.save(request, connect=True)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            base = data.get('name') or data.get('email', '').split('@')[0]
            user.username = _generate_username(base)
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        EmailAddress.objects.update_or_create(
            user=user,
            defaults={'email': user.email, 'primary': True, 'verified': True},
        )
        return user
