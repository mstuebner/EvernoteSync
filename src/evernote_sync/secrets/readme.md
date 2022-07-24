Place all the secret information in one file per key, named like the attribute holding ONLY 
the value. Files used in evernote_file_upload.py:

- consumer_key
- consumer_secret
- token_production
- token_sandbox

See also: https://pydantic-docs.helpmanual.io/usage/settings/#secret-support

# How to get those tokens?

- Request API consumer key and secret (https://dev.evernote.com/key.php)
- Create files consumer_key and consumer_secret, paste the information and add them to gitignore
- Initially the access is granted to sandbox only. When your script is done the production access 
  needs to be activated by Evernote team. Activation must be requested (https://dev.evernote.com/support/glossary.php#k) 
- Run evernote_oauth.py to get the tokens you need.



