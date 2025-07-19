from datetime import datetime as dt, timezone as tz

import msal
from flask import session, redirect, request
from flask_login import LoginManager, login_user, logout_user
from msal import ConfidentialClientApplication

from flask_azure_sso.exc import AzureException, LoginFailedError
from flask_azure_sso.user.azure_user import AzureUser

login_manager = LoginManager()


class AzureClient(object):
    """
    Client to interface with Azure Single Sign On
    """

    def __init__(self, app=None):
        self._tenant_id = None
        self._client_id = None
        self._client_secret = None
        self._redirect_uri = None
        self._authority_url = None
        self._scopes = []
        self._post_logout_url = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._tenant_id = app.config.get('AZURE_TENANT_ID')
        self._client_id = app.config.get('AZURE_CLIENT_ID')
        self._client_secret = app.config.get('AZURE_CLIENT_SECRET')
        self._redirect_uri = app.config.get('AZURE_CLIENT_REDIRECT_URI')
        self._authority_url = app.config.get('AZURE_CLIENT_AUTHORITY', f'https://login.microsoftonline.com/{self._tenant_id}')
        self._scopes = app.config.get('AZURE_CLIENT_SCOPES', ['User.Read'])
        self._post_logout_url = app.config.get('AZURE_CLIENT_POST_LOGOUT_URL', '/')
        login_manager.init_app(app)  # This enables the use of flask-login login_required decorator

    def _build_msal_app(self, cache=None):
        """
        Build an MSAL Confidential Client Application object.

        :return: the MSAL Confidential Client Application object.
        :rtype: msal ConfidentialClientApplication
        """
        return ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=self._client_secret,
            authority=self._authority_url,
            token_cache=cache,
        )

    @staticmethod
    def _is_token_valid_():
        """
        Check if token is valid (has not expired).

        :return: True if token is valid (has not expired)., False otherwise.
        :rtype: bool
        """
        user_data = session.get('user', None)

        if user_data is None:
            raise LoginFailedError('User is not logged in!')

        return dt.fromtimestamp(user_data.get('expires_at'), tz=tz.utc)

    def login(self):
        """
        Login to Azure Single Sign On by initiating the Auth Code Flow.

        :return: redirects the application to Azure Single Sign On.
        :rtype: flask.redirect
        """
        session['origin_url'] = request.url
        cache = msal.SerializableTokenCache()
        code_flow = self._build_msal_app(cache=cache).initiate_auth_code_flow(
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
        )

        session['flow'] = code_flow
        session['cache'] = cache.serialize()

        return redirect(code_flow.authorization_url())

    def callback(self):
        """
        Callback method for Azure Single Sign On. This method is called from your redirect_uri to handle
         the application level authorization settings.

        :return: redirect to the index of the application
        :rtype: flask.redirect
        """

        serialized_cache = session.get('cache', None)

        cache = msal.SerializableTokenCache()
        if serialized_cache:
            cache.deserialize(serialized_cache)

        auth_response = self._build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            auth_code_flow=session.get('flow'),
            auth_response=request.args
        )

        if "error" in auth_response:
            raise AzureException('Authorization failed!')

        id_token_claims = auth_response.get('id_token_claims', None)

        if id_token_claims is None:
            raise AzureException('No id_token_claims!')

        session['user'] = {
            "name": id_token_claims.get("name"),
            "email": id_token_claims.get("preferred_username"),
            "oid": id_token_claims.get("oid"),
            "roles": id_token_claims.get("roles", []),
            "groups": id_token_claims.get("groups", []),
            "access_token": auth_response.get("access_token"),
            "refresh_token": auth_response.get("refresh_token"),
            "expires_at": id_token_claims.get("expires_at"),
            "scopes": id_token_claims.get("scopes", self._scopes),
        }

        login_user(AzureUser(session['user']))
        session['cache'] = cache.serialize()
        origin_url = session.get('origin_url', request.base_url)
        origin_url = origin_url.replace('http://', 'https://')
        return redirect(origin_url)

    def logout(self):
        if session.get('user', None) is not None:
            logout_user()
            session.clear()
        return redirect(f'{self._authority_url}/oauth2/v2.0/logout?post_logout_redirect_uri={self._post_logout_url}')

    def refresh_token(self): ...
