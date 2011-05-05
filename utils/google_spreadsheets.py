# Note: I tried installing gdata using pip, but it didn't work for me
# out of the box. I ended up using apt-get install python-gdata and
# everything worked smoothly.

import gdata.spreadsheet.service


def make_hierarchical_dict(d, sep=u":"):
    """
    Given a flat dict d, each key in d is broken up by the separator
    sep, and a hierarchical dict is returned.
    """
    assert type(d) == dict
    assert type(sep) == unicode

    result = {}
    for key, value in d.items():
        path = key.split(sep)
        curr_dict = result
        for i, directory in enumerate(path):
            if i == (len(path) - 1):
                assert directory not in curr_dict
                curr_dict[directory] = value
            else:
                if directory in curr_dict:
                    assert type(curr_dict[directory]) == dict
                else:
                    curr_dict[directory] = {}
                curr_dict = curr_dict[directory]
    return result


class GoogleSpreadsheet(object):
    """
    This is a simple wrapper around the Google Docs API. There are two
    useful methods provided by this wrapper: keys and __getitem__.
    """
    def __init__(self, client, spreadsheet):
        self._client = client
        self._spreadsheet = spreadsheet
        self._load_worksheets()

    def _key(self):
        return self._spreadsheet.id.text.rsplit('/', 1)[-1]

    def _load_worksheets(self):
        self._worksheets = {}
        worksheets_feed = self._client.GetWorksheetsFeed(self._key())
        for ws in worksheets_feed.entry:
            ws_title = ws.title.text
            self._worksheets[ws_title] = ws

    def keys(self):
        """
        Return a list containing the names of the worksheets in this
        spreadsheet.
        """
        return self._worksheets.keys()

    def __getitem__(self, title):
        """
        Iterate over all the rows in the worksheet with this title in
        this spreadsheet. If x is a GoogleSpreadsheet object, then
        x['Sheet1'] will iterate over all the rows in 'Sheet1'
        returning a dict for each row.
        """
        ws = self._worksheets[title]
        wksht_id = ws.id.text.rsplit('/', 1)[-1]
        for entry in self._client.GetListFeed(self._key(), wksht_id).entry:
            d = dict(zip(
                entry.custom.keys(),
                [value.text for value in entry.custom.values()]
                ))
            yield make_hierarchical_dict(d)


class GoogleSpreadsheetsClient(object):
    """
    This is a simple wrapper around the Google Docs API. The class is
    intended to be used as follows:

    from local_config_file import email, password
    spreadsheets = GoogleSpreadsheetsClient(email, password)
    for spreadshseet_title in spreadsheets.keys():
        spreadsheet = spreadsheets[spreadsheet_title]
        for worksheet_title in spreadhseet.keys():
            for row_dict in spreadsheet[worksheet_title]:
                print row_dict
    """
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._connect()
        self._load_spreadsheets()

    def _connect(self):
        self._client = gdata.spreadsheet.service.SpreadsheetsService()
        self._client.email = self._email
        self._client.password = self._password
        self._client.ProgrammaticLogin()

    def _load_spreadsheets(self):
        self._spreadsheets = {}
        spreadsheets_feed = self._client.GetSpreadsheetsFeed()
        for ss in spreadsheets_feed.entry:
            ss_title = ss.title.text
            wrapped_ss = GoogleSpreadsheet(self._client, ss)
            self._spreadsheets[ss_title] = wrapped_ss

    def keys(self):
        """
        Return a list of titles of all the spreadsheets available to
        this user.
        """
        return self._spreadsheets.keys()

    def __getitem__(self, title):
        """
        Return the GoogleSpreadsheet object with this title.
        """
        return self._spreadsheets[title]
