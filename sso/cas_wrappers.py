from urllib import parse as urllib_parse

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.http.response import JsonResponse
from django.shortcuts import render

from django_cas_ng import views as baseviews
from django_cas_ng.models import ProxyGrantingTicket, SessionTicket
from django_cas_ng.signals import cas_user_logout
from django_cas_ng.utils import (
    get_cas_client,
    get_protocol,
    get_redirect_url,
)

import json

# from rest_framework_jwt.settings import api_settings

# jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
# jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class APILoginView(baseviews.LoginView):
    def successful_login(self, request: HttpRequest, next_page: str) -> HttpResponse:
        """
        This method is called on successful login.
        Overriden to render a page that send JWT token via postMessage
        if the page receive a message from one of the whitelisted origin.
        """
        user = request.user
        # payload = jwt_payload_handler(user)
        # token = jwt_encode_handler(payload)

        data = {
            # "token": token,
            "cors_origin_regex_whitelist": settings.CORS_ALLOWED_ORIGINS,
            "next_page": next_page,
        }

        return JsonResponse(json.dump(user))


class APILogoutView(baseviews.LogoutView):
    def get(self, request: HttpRequest) -> HttpResponse:
        """

        "django.middleware.security.SecurityMiddleware",

            :param request:
            :return:
        """
        next_page = settings.SUCCESS_SSO_AUTH_REDIRECT

        # try to find the ticket matching current session for logout signal
        try:
            st = SessionTicket.objects.get(session_key=request.session.session_key)
            ticket = st.ticket
        except SessionTicket.DoesNotExist:
            ticket = None
        # send logout signal
        cas_user_logout.send(
            sender="manual",
            user=request.user,
            session=request.session,
            ticket=ticket,
        )

        # clean current session ProxyGrantingTicket and SessionTicket
        ProxyGrantingTicket.objects.filter(
            session_key=request.session.session_key
        ).delete()
        SessionTicket.objects.filter(session_key=request.session.session_key).delete()
        auth_logout(request)

        next_page = next_page or get_redirect_url(request)
        if settings.CAS_LOGOUT_COMPLETELY:
            client = get_cas_client(request=request)
            return HttpResponseRedirect(client.get_logout_url(next_page))

        # This is in most cases pointless if not CAS_RENEW is set. The user will
        # simply be logged in again on next request requiring authorization.
        return HttpResponseRedirect(next_page)
