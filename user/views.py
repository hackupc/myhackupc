import random
import string

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import TemplateView

from app.utils import reverse
from applications import models as a_models
from user import forms, models, tokens, providers
from user.forms import SetPasswordForm, PasswordResetForm
from user.mixins import HaveSponsorPermissionMixin, IsHackerMixin
from user.models import User
from user.verification import check_recaptcha, check_client_ip, reset_tries


APPLICATION_TYPE = {
    'hacker': 'H',
    'volunteer': 'V',
    'mentor': 'M',
}


@check_client_ip
def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('root'))
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        next_ = request.GET.get('next', '/')
        if form.is_valid() and request.client_req_is_valid:
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = auth.authenticate(email=email, password=password)
            if user and user.is_active:
                auth.login(request, user)
                reset_tries(request)
                resp = HttpResponseRedirect(next_)
                c_domain = getattr(settings, 'LOGGED_IN_COOKIE_DOMAIN', getattr(settings, 'HACKATHON_DOMAIN', None))
                c_key = getattr(settings, 'LOGGED_IN_COOKIE_KEY', None)
                if c_domain and c_key:
                    try:
                        resp.set_cookie(c_key, 'biene', domain=c_domain, max_age=settings.SESSION_COOKIE_AGE)
                    except Exception:
                        # We don't care if this is not set, we are being cool here!
                        pass
                return resp
            else:
                form.add_error(None, 'Incorrect username or password. Please try again.')

        if not request.client_req_is_valid:
            form.add_error(None, 'Too many login attempts. Please try again in 5 minutes.')
    else:
        form = forms.LoginForm()

    return render(request, 'login.html', {'form': form})


@check_recaptcha
def signup(request, u_type):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('root'))
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST, type=u_type)
        if form.is_valid() and request.recaptcha_is_valid:
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            name = form.cleaned_data['name']

            if models.User.objects.filter(email=email).first() is not None:
                form.add_error(None, 'An account with this email already exists')
            else:
                models.User.objects.create_user(email=email, password=password, name=name, u_type=u_type)
                user = auth.authenticate(email=email, password=password)
                auth.login(request, user)
                next_url = request.GET.get('next', reverse('root'))
                return HttpResponseRedirect(next_url)
        if not request.recaptcha_is_valid:
            form.add_error(None, 'Invalid reCAPTCHA. Please try again.')
    else:
        form = forms.RegisterForm()

    return render(request, 'signup.html', {'form': form, 'app_type': APPLICATION_TYPE.get(u_type, 'H')})


class Logout(View):
    def get(self, request):
        auth.logout(request)
        messages.success(request, 'Successfully logged out!')
        next_url = request.GET.get('next', reverse('account_login'))
        resp = HttpResponseRedirect(next_url)
        c_domain = getattr(settings, 'LOGGED_IN_COOKIE_DOMAIN', None) or getattr(settings, 'HACKATHON_DOMAIN', None)
        c_key = getattr(settings, 'LOGGED_IN_COOKIE_KEY', None)
        if c_domain and c_key:
            try:
                resp.delete_cookie(c_key, domain=c_domain)
            except Exception:
                # We don't care if this is not deleted, we are being cool here!
                pass
        return resp


def activate(request, uid, token):
    try:
        uid = force_text(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
        if request.user.is_authenticated and request.user != user:
            messages.warning(request, "Trying to verify wrong user. Log out please!")
            return redirect('root')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.warning(request, "This user no longer exists. Please sign up again!")
        return redirect('root')

    if tokens.account_activation_token.check_token(user, token):
        messages.success(request, "Email verified!")

        user.email_verified = True
        user.save()
        auth.login(request, user)
    else:
        messages.error(request, "Email verification url has expired. Log in so we can send it again!")
    return redirect('root')


def password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST, )
        if form.is_valid():
            email = form.cleaned_data.get('email')
            user = User.objects.get(email=email)
            msg = tokens.generate_pw_reset_email(user, request)
            msg.send()
            return HttpResponseRedirect(reverse('password_reset_done'))
        else:
            return TemplateResponse(request, 'password_reset_form.html', {'form': form})
    else:
        form = PasswordResetForm()
    context = {
        'form': form,
    }

    return TemplateResponse(request, 'password_reset_form.html', context)


def password_reset_confirm(request, uid, token):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    try:
        uid = force_text(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return TemplateResponse(request, 'password_reset_confirm.html', {'validlink': False})

    if tokens.password_reset_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                form.save(user)
                return HttpResponseRedirect(reverse('password_reset_complete'))
        form = SetPasswordForm()
    else:
        return TemplateResponse(request, 'password_reset_confirm.html', {'validlink': False})

    return TemplateResponse(request, 'password_reset_confirm.html', {'validlink': True, 'form': form})


def password_reset_complete(request):
    return TemplateResponse(request, 'password_reset_complete.html', None)


def password_reset_done(request):
    return TemplateResponse(request, 'password_reset_done.html', None)


@login_required
def verify_email_required(request):
    if request.user.email_verified:
        messages.warning(request, "Your email has already been verified")
        return HttpResponseRedirect(reverse('root'))
    return TemplateResponse(request, 'verify_email_required.html', None)


@login_required
def set_password(request):
    if request.user.has_usable_password():
        return HttpResponseRedirect(reverse('root'))
    if request.method == 'GET':
        return TemplateResponse(request, 'callback.html', {'form': SetPasswordForm(), 'email': request.user.email})
    else:
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            form.save(user)
            auth.login(request, user)
            messages.success(request, 'Password correctly set')
            return HttpResponseRedirect(reverse('root'))
        return TemplateResponse(request, 'callback.html', {'form': form, 'email': request.user.email})


@login_required
def send_email_verification(request):
    if request.user.email_verified:
        messages.warning(request, "Your email has already been verified")
        return HttpResponseRedirect(reverse('root'))
    msg = tokens.generate_verify_email(request.user)
    msg.send()
    messages.success(request, "Verification email successfully sent")
    return HttpResponseRedirect(reverse('root'))


def callback(request, provider=None):
    if not provider:
        messages.error(request, 'Invalid URL')
        return HttpResponseRedirect(reverse('root'))
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('root'))
    code = request.GET.get('code', '')
    if not code:
        messages.error(request, 'Invalid URL')
        return HttpResponseRedirect(reverse('root'))
    try:
        access_token = providers.auth_mlh(code, request)
        mlhuser = providers.get_mlh_user(access_token)
    except ValueError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(reverse('root'))

    user = User.objects.filter(mlh_id=mlhuser.get('id', -1)).first()
    if user:
        auth.login(request, user)
    elif User.objects.filter(email=mlhuser.get('email', None)).first():
        messages.error(request, 'An account with this email already exists. Sign in using your password.')
    else:
        user = User.objects.create_mlhuser(
            email=mlhuser.get('email', None),
            name=mlhuser.get('first_name', '') + ' ' + mlhuser.get('last_name', None),
            mlh_id=mlhuser.get('id', None),
        )
        auth.login(request, user)

        # Save extra info
        draft = a_models.DraftApplication()
        draft.user = user
        mlhdiet = mlhuser.get('dietary_restrictions', '')
        diet = mlhdiet if mlhdiet in dict(a_models.DIETS).keys() else 'Others'
        draft.save_dict({
            'degree': mlhuser.get('major', ''),
            'university': mlhuser.get('school', {}).get('name', ''),
            'phone_number': mlhuser.get('phone_number', ''),
            'tshirt_size': [k for k, v in a_models.TSHIRT_SIZES if v == mlhuser.get('shirt_size', '')][0],
            'diet': mlhdiet,
            'other_diet': mlhdiet if diet == 'Others' else '',
        })
        draft.save()
    return HttpResponseRedirect(reverse('root'))


class SponsorRegister(HaveSponsorPermissionMixin, TemplateView):
    template_name = 'signup.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SponsorRegister, self).get_context_data(**kwargs)
        form = forms.RegisterSponsorForm()
        context.update({'form': form, 'is_sposnor_form': True})
        return context

    def post(self, request, *args, **kwargs):
        form = forms.RegisterSponsorForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            n_max = form.cleaned_data['n_max']
            password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            if models.User.objects.filter(email=email).first() is not None:
                messages.error(request, 'An account with this email already exists')
            else:
                user = models.User.objects.create_sponsor(email=email, password=password, name=name, n_max=n_max)
                msg = tokens.generate_sponsor_link_email(user, request)
                msg.send()
                messages.success(request, "Sponsor link email successfully sent")
                return HttpResponseRedirect(reverse('sponsor_user_list'))
        context = self.get_context_data()
        context.update({'form': form})
        return TemplateResponse(request, self.template_name, context)


class UserProfile(IsHackerMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserProfile, self).get_context_data(**kwargs)
        form = forms.ProfileForm(initial={
            'name': self.request.user.name,
            'email': self.request.user.email,
            'type': self.request.user.type if self.request.user.can_change_type() else 'H',
            'non_change_type': self.request.user.get_type_display(),
        }, type_active=self.request.user.can_change_type())
        context.update({'form': form})
        return context

    def post(self, request, *args, **kwargs):
        form = forms.ProfileForm(request.POST, type_active=request.user.can_change_type())
        if form.is_valid():
            name = form.cleaned_data['name']
            request.user.name = name
            if request.user.can_change_type():
                type = form.cleaned_data['type']
                request.user.type = type
            request.user.save()
            messages.success(request, "Profile saved successfully")
            c = self.get_context_data()
        else:
            c = self.get_context_data()
            c.update({'form': form})
        return render(request, self.template_name, c)


class DeleteAccount(IsHackerMixin, TemplateView):
    template_name = 'confirm_delete.html'

    def post(self, request, *args, **kwargs):
        request.user.delete()
        messages.success(request, "User deleted successfully")
        return HttpResponseRedirect(reverse('root'))
