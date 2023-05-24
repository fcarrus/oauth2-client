# Example OAuth2 client for Ansible Automation Platform
# Ready to be deployed on Red Hat OpenShift
from flask import Flask, request, make_response
import os
import requests, json

app = Flask(__name__)

# Use the environment variables to get our parameters.

# This is where the OAuth2 service checks our credentials and asks us for permission to issue a token.
authorize_url = os.environ.get('AUTHORIZE_URL') or 'https://aap.example.com/api/o/authorize'

# This is where we get the token.
token_url = os.environ.get('TOKEN_URL') or "https://aap.example.com/api/o/token/"

# These are values we get from creating an Application on the AAP GUI.
client_id = os.environ.get('CLIENT_ID') or 'example-client-id'
client_secret = os.environ.get('CLIENT_SECRET') or 'example-secret'

# This is this app's endpoint where we get redirected from OAuth2 service.
callback_uri = os.environ.get('CALLBACK_URI') or "http://thisapp.example.com/authcallback"

# This is the URL where we use the token to get some data.
retrieve_data_uri = os.environ.get('DATA_URI') or "https://aap.example.com/api/v2/users/"

# The scope of the AAP token can be read, write or both. We use read only.
scope = os.environ.get('CLIENT_SCOPE') or 'read'

# Used for development only.
debug = os.environ.get('DEBUG') or False

@app.route('/')
def homepage():
    response = make_response()
    # Are we already logged in?
    access_token = request.cookies.get('access_token') or ''
    if access_token != '':
        # We are. Try to use the token to get the data we need
        api_call_headers = {'Authorization': 'Bearer ' + access_token}
        api_call_response = requests.get(retrieve_data_uri, headers=api_call_headers, verify=False)
        if api_call_response.status_code != 200:
            # Token's not valid. Clean up and go to the login page
            response.location = '/login'
            response.delete_cookie(key='access_token')
            response.status = 302
        else:
            # Token's valid, return the data to the browser
            # (Firefox renders it better)
            response.set_data(api_call_response.text)
            response.headers.add('Content-Type', 'application/json')
    else:
        # No we're not logged in. Clean up and go to the login page
        response.location = '/login'
        response.delete_cookie(key='access_token')
        response.status = 302
    return response

@app.route('/login')
def login():
    response = make_response()
    response.status = 302
    access_token = request.cookies.get('access_token') or ''
    # Are we already logged in?
    if access_token != '':
        # We are, go to homepage.
        response.location = '/'
    else:
        # We're not. Redirect to OAuth2 authentication service page providing the client_id and scope.
        # The OAuth2 will ask us to log in with our credentials and whether we agree on providing this app with a token
        #   so that it can make use of our privileges.
        response.location = '{}?response_type=code&client_id={}&redirect_uri={}&scope={}'.format(authorize_url, client_id, callback_uri, scope)
    return response

@app.route('/logout')
def logout():
    # Clean up and go to the login page.
    response = make_response("Logged out. <a href='/'>Go to Homepage</a>")
    response.delete_cookie(key='access_token')
    return response

@app.route('/authcallback')
def authcallback():
    # The OAuth2 service, after we successfully log in and confirm we want a token, 
    #   will redirect the browser to this page, appending a "code" parameter.
    # The parameter is an authorization code, to be used to retrieve our bearer token.
    # The authorization code usually lasts only 600 seconds, while the token is long-lasted,
    #   usually 1000 years or so (AAP's default values, can be changed in Settings)
    response = make_response('')
    # Did we get an error while logging in? (i.e. authentication failed or didn't authorize the token)
    error = request.args.get('error')
    if error is not None:
        # Yes we did, give warning and provide link to homepage.
        response.status = 401
        response.set_data("Unauthorized! <a href='/'>Go to Homepage</a>")
    else:
        # We didn't get an error, login was successful.
        # But did we get a code?
        authorization_code = request.args.get('code') or ''
        response.status = 302
        if authorization_code != '':
            # Yes we did, try to use it to get a Token
            data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': callback_uri}
            access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(client_id, client_secret))
            tokens = json.loads(access_token_response.text)
            # Was the token request successful?
            if 'access_token' in tokens:
                # We have the token, let's use it as a browser session cookie
                # This is probably not the best security practice: we should store this token 
                #   on the server, and provide the browser with just a reference,
                #   so that the token cannot be stolen from the user's computer.
                response.location = '/'
                response.set_cookie(key='access_token', value=tokens['access_token'])
            else:
                # We didn't get a token, something was wrong.
                # Issue a warning and print the error.
                response.set_data('Error while calling {}:{} code={}'.format(token_url, access_token_response.text, authorization_code))
                response.status = 500
            return response
        else:
            response.location = '/login'
    return response


if __name__ == '__main__':
    port = os.environ.get('FLASK_PORT') or 8080
    port = int(port)
    # Print the environment variable so that we can check they're good.
    # We also print the client_id and secret, that's very bad security practice.
    print("AUTHORIZE_URL='{}'\nTOKEN_URL='{}'\nCLIENT_ID='{}'\nCLIENT_SECRET='{}'\nCALLBACK_URI='{}'\nDATA_URI='{}'\nCLIENT_SCOPE='{}'\n".format(
        authorize_url, token_url, client_id, client_secret, callback_uri, retrieve_data_uri, scope)) 

    app.run(debug=debug, port=port, host='0.0.0.0')
