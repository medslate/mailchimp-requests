#-*- coding: utf-8 -*-

class MailChimpError(Exception):
    pass

class MailChimpConnectionError(MailChimpError):
    """Network connection error"""

class MailChimpServiceError(MailChimpError):
    """HTTP request error"""
    exception = None #: original exception

class MailChimpAPIError(MailChimpError):
    """API call error"""
