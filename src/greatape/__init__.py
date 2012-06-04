#-*- coding: utf-8 -*-

import datetime
import logging
import threading
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
        raise ImportError("Ape requires either Python >2.6 or simplejson")

import requests

from greatape.exceptions import MailChimpError, MailChimpConnectionError, \
    MailChimpServiceError, MailChimpAPIError


logger = logging.getLogger("greatape")

DEFAULT_TIMEOUT = 30


class MailChimp(object):
    base_url = "%(protocol)s://%(data_center)s.api.mailchimp.com/1.3/?method=%(method)s"

    def __init__(self, api_key, ssl=True, keep_alive=True, timeout=DEFAULT_TIMEOUT, **kwargs):
        self.data_center = api_key.rsplit("-", 1)[-1]
        self.api_key = api_key
        self.ssl = ssl
        self.keep_alive = keep_alive
        self.timeout = timeout
        self.defaults = kwargs or {}
        self.prefix = ""
        self._thread = threading.local()

    def __getattr__(self, name, *args, **keywords):
        return partial(self, method=name, *args, **keywords)

    def list(self, id):
        chimp = MailChimp(self.api_key, self.ssl, **self.defaults)
        chimp.defaults["id"] = id
        chimp.prefix = "list"
        return chimp

    def build_method_url(self, method):
        if self.ssl:
            protocol = "https"
        else:
            protocol = "http"
        return self.base_url % {
            "protocol": protocol,
            "data_center": self.data_center,
            "method": method
        }

    def serialize_params(self, params_dict):
        if params_dict is None:
            params_dict = {}
        params_dict.update({
            "apikey": self.api_key,
        })
        return self._serialize(params_dict)

    def get_http_session(self):
        if not self.keep_alive:
            return requests

        if hasattr(self._thread, "session"):
            if self._thread.use_count < 100:
                self._thread.use_count += 1
                return self._thread.session

        self._thread.session = requests.session()
        self._thread.use_count = 1
        return self._thread.session

    def call_api(self, url, data):
        logger.debug(u"Calling API using url: %s", url)
        logger.debug(u"Serialized POST data is: %s", data)

        try:
            response = self.get_http_session().post(url, data=data, timeout=self.timeout)
            logger.debug(
                u"Response (%s): %s",
                response.status_code, response.content
            )
            response.raise_for_status()
        except (requests.Timeout, requests.ConnectionError), e:
            logger.error("Connecting to %s failed: %s.", url, e)
            raise MailChimpConnectionError(
                "Connecting to %s failed: %s." % (url, e)
            )
        except requests.HTTPError, e:
            logger.exception(
                "HTTP error while accessing MailChimp API %s: %s.",
                url, e.response.status_code
            )
            if e.response.status_code == 304: # TODO: why this special case?
                return []
            else:
                message = "HTTP error while accessing MailChimp API %s: %s." % (
                    url, e.response.status_code
                )
                mailchimp_error = MailChimpServiceError(message)
                mailchimp_error.exception = e
                raise mailchimp_error
        except requests.RequestException, e:
            logger.exception(
                "Error while accessing MailChimp API %s: %s.", url, e
            )
            raise MailChimpError(str(e))

        data = json.loads(response.text)
        if not isinstance(data, bool):
            if "error" in data:
                logger.error("MailChimp API error: %s.", data["error"])
                raise MailChimpAPIError(data["error"])

        return data

    def __call__(self, params_dict=None, **kwargs):
        method = self.prefix + kwargs.pop("method")
        url = self.build_method_url(method)
        data = self.serialize_params(params_dict)
        return self.call_api(url, data)

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
                name = "%s[%s]" % (key, name)
            if isinstance(value, (list, dict)):
                pairs.append(self._serialize(value, name))
            elif value is not None:
                if isinstance(value, (bool, datetime.datetime, datetime.date, int)):
                    value = str(value).lower()
                elif isinstance(value, unicode):
                    value = value.encode("utf-8")
                pairs.append("%s=%s" % (name, quote_plus(value)))
        return "&".join(pairs)


class MailChimpSTS(MailChimp):
    base_url = "%s://%s.sts.mailchimp.com/1.0/%s.json/"

__all__ = ["MailChimp", "MailChimpError", "MailChimpAPIError", "MailChimpSTS"]
