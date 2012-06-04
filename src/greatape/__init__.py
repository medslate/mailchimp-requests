#-*- coding: utf-8 -*-

import datetime
import urllib2
from urllib import quote_plus

try:
    from functools import partial
except ImportError:
    def partial(func, *args, **keywords):
        def newfunc(*fargs, **fkeywords):
            newkeywords = keywords.copy()
            newkeywords.update(fkeywords)
            return func(*(args + fargs), **newkeywords)
        newfunc.func = func
        newfunc.args = args
        newfunc.keywords = keywords
        return newfunc

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError('Ape requires either Python >2.6 or simplejson')


class MailChimpError(Exception):
    pass


class MailChimp(object):
    base_url = "%s://%s.api.mailchimp.com/1.3/?method=%s"

    def __init__(self, api_key, ssl=True, debug=False, **kwargs):
        self.data_center = api_key.rsplit('-', 1)[-1]
        self.api_key = api_key
        self.ssl = ssl
        self.debug = debug
        self.defaults = kwargs or {}
        self.prefix = ''

    def __getattr__(self, name, *args, **keywords):
        return partial(self, method=name, *args, **keywords)

    def list(self, id):
        chimp = MailChimp(self.api_key, self.ssl, self.debug, **self.defaults)
        chimp.defaults['id'] = id
        chimp.prefix = 'list'
        return chimp

    def __call__(self, params_dict=None, **kwargs):
        method = self.prefix + kwargs.pop('method')

        if params_dict is None:
            params_dict = {}
        params_dict.update({
            'apikey': self.api_key,
        })

        params = self._serialize(params_dict)
        if self.ssl:
            protocol = 'https'
        else:
            protocol = 'http'

        url = self.base_url % (protocol, self.data_center, method)

        if self.debug:
            print 'URL:', url
            print 'POST data:', params
        req = urllib2.Request(url, params)
        try:
            handle = urllib2.urlopen(req)
            res = handle.read()
            if self.debug:
                print 'Response : ', res
            response = json.loads(res)
            try:
                if 'error' in response:
                    raise MailChimpError(response['error'])
            except TypeError: # the response was boolean
                pass

            return response
        except urllib2.HTTPError, e:
            if e.code == 304:
                return []
            else:
                raise MailChimpError()

    def _serialize(self, params, key=None):
        """Replicates PHP's (incorrect) serialization to query parameters to
        accommodate the "array-based" parameters of MailChimp API methods.
        """
        pairs = []
        try:
            items = params.items()
        except AttributeError:
            items = [(str(i), n) for i, n in enumerate(params)]
        for name, value in items:
            name = quote_plus(name)
            if key is not None:
                name = '%s[%s]' % (key, name)
            if isinstance(value, (list, dict)):
                pairs.append(self._serialize(value, name))
            elif value is not None:
                if isinstance(value, (bool, datetime.datetime, datetime.date, int)):
                    value = str(value).lower()
                elif isinstance(value, unicode):
                    value = value.encode('utf-8')
                pairs.append('%s=%s' % (name, quote_plus(value)))
        return '&'.join(pairs)


class MailChimpSTS(MailChimp):
    base_url = "%s://%s.sts.mailchimp.com/1.0/%s.json/"

__all__ = ["MailChimp", "MailChimpError", "MailChimpSTS"]
