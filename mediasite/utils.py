from requests.compat import quote_plus


def odata_encode_str(s):
    """ String eq comparison in OData requires special characters
    to be escaped, like &. ALSO, single quotes need to be doubled up,
    so we do that before encoding.  """
    return quote_plus(s.replace("'", "''"))
