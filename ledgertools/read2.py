import re
import sys
import math
import pendulum

from tqdm import tqdm

# regex copied from https://github.com/Tagirijus/ledger-parse
PAT_TRANSACTION_DATA = re.compile(r'(?P<year>\d{4})[/|-](?P<month>\d{2})[/|-](?P<day>\d{2})(?:=(?P<year_aux>\d{4})[/|-](?P<month_aux>\d{2})[/|-](?P<day_aux>\d{2}))? (?P<state>[\*|!])?[ ]?(\((?P<code>[^\)].+)\) )?(?P<payee>.+)')
PAT_COMMENT = re.compile(r';(.+)')
PAT_TAG = re.compile('(?:\s|^)(\S+):([^,]+)?(?:,|$)')

class Ledger():
    """Holds all transactions
    """
    def __init__(self, raw_transactions=None):
        self._transactions = []
        if raw_transactions is not None:
            self._transactions = self._import_raw_transactions(raw_transactions)

    @property
    def transactions(self):
        return {}

    def _parse_tags(self, string):
        tags = {}
        # split string in parts
        for part in string.split(','):
            # search for tag pattern in part
            re_tag = PAT_TAG.search(part)
            if re_tag is not None:
                # add found tags to dict
                tags[re_tag.groups()[0]] = re_tag.groups()[1]
        return tags

    def _parse_comments(self, string):
        re_comment = PAT_COMMENT.search(string)
        if re_comment is not None:
            # set comment if found
            return re_comment.groups()[0].strip()
        else:
            return None

    def _remove_comment(self, string):
        comments = self._parse_comments(string)
        if comments is not None:
            return string.replace(comments, '').replace(' ; ', '')
        else:
            return string

    def _parse_header(self, string):
        re_header = PAT_TRANSACTION_DATA.match(string)
        if re_header is not None:
            t_primary_date = pendulum.Date(int(re_header.group('year')),
                                           int(re_header.group('month')),
                                           int(re_header.group('day'))) or None
            t_status = re_header.group('state') or None
            t_code = re_header.group('code') or None
            t_description = self._remove_comment(re_header.group('payee')) or None
            t_comment = None
            t_tags = {}
            # check for comment in header
            t_comment = self._parse_comments(re_header.string)
            # check comment for tags
            if t_comment is not None:
                t_tags = self._parse_tags(t_comment)
                # remove tags from comment string
                for tag, value in t_tags.items():
                    t_comment = t_comment.replace(f'{tag}:{value}', '')
                # remove artefacts from comment
                t_comment = t_comment.replace(' , ', '')

            return dict(primary_date=t_primary_date,
                        status=t_status,
                        code=t_code,
                        description=t_description,
                        comment=t_comment,
                        tags=t_tags)
        else:
            return None

    def _parse_posting(self, string):
        return string

    def _import_raw_transactions(self, raw_transactions):
        for transaction in raw_transactions:
            t = Transaction()
            posting_tags = {}
            for line in transaction:
                # find header line
                header = self._parse_header(line)
                if header is not None:
                    t.header = header
                    continue

                # find comment lines in postings
                if line.startswith(';'):
                    posting_comments = self._parse_comments(line)                
                    if posting_comments is not None:
                        # merge dicts
                        posting_tags = {**posting_tags, **self._parse_tags(posting_comments)}
                        continue

                # find postings
                print(self._parse_posting(line))





class Transaction():
    """Represents a transaction and contains at least two postings
    """
    def __init__(self):
        self._header = dict(primary_date=None,
                            status=None,
                            code=None,
                            description=None,
                            comment=None,
                            tags={})
        self._postings = []

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        self._header = header


class Posting():
    """Represents a single posting
    """
    def __init__(self):
        pass


def read_file(in_file):
    with open(in_file, 'r') as in_file:
        lines = in_file.readlines()[:17]

    # remove newline at EOL
    # remove global comments
    # strip whitespace
    lines = [l.replace('\n', '').strip() for l in lines if not l[0].strip() in [';']]

    for line in lines:
        print(line)

    transactions = []
    group = []
    for line in lines:
       if not line.strip():  # .strip handles lines with only spaces as chars
           transactions.append(group)
           group = []
       else:
           group.append(line)
    transactions = [g for g in transactions if g]

    ledger = Ledger(transactions)

    return ledger.transactions
