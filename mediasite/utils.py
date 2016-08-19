from requests.compat import quote_plus


def odata_encode_str(s):
    """ String eq comparison in OData requires special characters
    to be escaped, like &. """
    return quote_plus(s)
