OVERVIEW
========

``greatape`` is a minimalist client library for version 1.3 of the MailChimp
API.  It was very much inspired by Mike Verdone's `Twitter client library
<http://github.com/sixohsix/twitter>`_ in that it does a bit of mucky, dynamic
business with __getattr__ to avoid having to actually write code for all the
methods that the API provides.

``greatape`` is pretty darned easy to use.  Simple import the API object and 
instantiate it with your API key.



>>> from greatape import MailChimp
>>> mailchimp = MailChimp('<your api key>')
>>> mailchimp.ping()
u\"Everything's Chimpy!\"
>>> mailchimp.lists()
>>> mailchimp.listActivity({'id':'<LIST_ID>'})

You can now access any of the methods in the API by calling them on your
``MailChimp`` instance with the required parameters as keyword arguments.
Results will be returned as Python lists or dictionaries.  (Note that you do
not need to provide your API key as a parameter other than to the constructor.)
Refer to the `MailChimp API documentation <http://www.mailchimp.com/api/1.2/>`_
for a complete list of available methods.

>>> from greatape import MailChimpSTS
>>> mc_sts = MailChimpSTS('<your api key>')
>>> params={
            'message':{
                'subject':'<subject>',
                'html':'<html email text>',
                'text':'<plain email text>',
                'from_name':'<your Name>',
                'from_email':'<your email id>',
                'to_email':recipient_list,
            },
            'track_opens':config.get('track_opens',False),
            'track_clicks':config.get('track_clicks',False),
            'tags':config.get('tags',[]),
        }
>>> mc_sts.SendEmail(params)

``greatape`` defaults to using SSL and keep-alive to access the MailChimp API.
If this isn't what you want, pass ``ssl=False`` or ``keep_alive=False``
to the ``MailChimp`` constructor.

Logging uses the Python's ``logging`` module. Configure the ``greatape`` logger
and set it to DEBUG level to get info about all API calls and exchanged data.
