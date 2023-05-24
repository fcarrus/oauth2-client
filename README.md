# oauth2-client

This example app makes use of OAuth2 authentication.

It was developed to demonstrate the OAuth2 integration with Ansible Automation Platform.

It allows you to log in to AAP and create a token, in order to give this app the same permission as your user, but without knowing your credentials.

## How to use it

* Log in to Ansible Automation Platform and `Add` a new application from the `Applications` menu
  * Give it a name like "oauth2-client"
  * Choose an Organization
  * Select `Authorization code` from the Grant Type menu
  * Type in the `Redirect URIs`: this is the URL(s) where this application will be exposed (i.e. an OpenShift Route). It must end with `/authcallback`
  * Select `Confidential` in the Client Type menu
  * Make note of the Client ID and Client Secret.
* Open the deploy.yaml in a text editor and go to the `env` section of the container
  * In the AUTHORIZE_URL, TOKEN_URL and DATA_URI replace the FQDN with your AAP Controller FQDN
  * In the CLIENT_ID and CLIENT_SECRET replace the values with the ones from AAP's Application.
  * In the CALLBACK_URI use the same URL as the `Redirect URI` in AAP's Application.
* Save and apply the deploy.yaml file in a namespace of your choice with `$ oc -n mynamespace apply -f deploy.yaml`

Now point your browser to this app Route's address and it will redirect you to the AAP Controller asking you to Log In and then to authorize your user. After accepting, a token will be created and this app will use it to retrieve the content from the DATA_URI resource (list of all AAP's users).

To remove the token created, head to the Applications menu, select the Application and in the Tokens tab select and delete them.
