# flask-azure-sso
Flask plugin for Azure SSO

This plugin is not production ready. Use at your own risk!

Plans:
1. Make the plugin work
2. Make the plugin secure
3. Add in some default routes to make it easier to integrate into other applications

Goals:
This plugin is meant to ease SSO integrations when utilizing Azure Entra-ID within a flask application.
Ideally this means having the inclusion within code be as simple as calling init_app and letting the app 
configuration or environment be used to pull the necessary settings.
