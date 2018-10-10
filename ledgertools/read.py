import re
import sys
import math
import pendulum

from tqdm import tqdm
from ledgertools.checks import transaction_checks, CheckFailed


# regex copied from https://github.com/Tagirijus/ledger-parse
PAT_TRANSACTION_DATA = re.compile(r'(?P<year>\d{4})[/|-](?P<month>\d{2})[/|-](?P<day>\d{2})(?:=(?P<year_aux>\d{4})[/|-](?P<month_aux>\d{2})[/|-](?P<day_aux>\d{2}))? (?P<state>[\*|!])?[ ]?(\((?P<code>[^\)].+)\) )?(?P<payee>.+)')
PAT_COMMENT = re.compile(r';(.+)')
PAT_TAG = re.compile('(?:\s|^)(\S+):([^,]+)?(?:,|$)')

class Ledger():
    """Holds all transactions
    """
    def __init__(self, ledger_filename=None, raw_transactions=None):
        self._transactions = []
        if ledger_filename is not None:
            self._transactions = self.import_ledger_file(ledger_filename)
        if raw_transactions is not None:
            self._transactions = self._import_raw_transactions(raw_transactions)

    @property
    def json(self):
        return [t.json for t in self.transactions]

    @property
    def transactions(self):
        return self._transactions

    def run_checks(self, strict=True):
        n_checks_failed = 0
        for transaction in self._transactions:
            for check in transaction_checks():
                success, info = transaction.run_checks(check)
                if not success:
                    n_checks_failed += 1
                    print(f'{check.__name__} failed for transaction\n {transaction}{info}')
        if n_checks_failed > 0 and strict:
            raise CheckFailed(f'{n_checks_failed} checks failed')

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
                                           int(re_header.group('day')))
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
        parts = [p.strip() for p in string.split(' ') if p]

        account = parts[0]
        try:
            amount = float(parts[1].replace(',', '.'))
        except:
            print(string, parts)
            raise

        # check for tags
        tags = {}
        if len(parts) > 2 and parts[2] == ';':
            tags = self._parse_tags(' '.join(parts[2:]))
        # check for posting date
        secondary_date = None
        if 'date' in tags.keys():
            try:
                secondary_date = pendulum.parse(tags['date']).date()
                del tags['date']
            except:
                print(parts)
                raise
        return dict(account=account,
                    amount=amount,
                    tags=tags,
                    secondary_date=secondary_date)

    def _import_raw_transactions(self, raw_transactions):
        transactions = []
        for transaction in tqdm(raw_transactions):
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
                t.add_posting(Posting(**self._parse_posting(line), primary_date=t.header['primary_date']))
            transactions.append(t)

        return transactions

    def import_ledger_file(self, filename):
        with open(filename, 'r') as in_file:
            lines = in_file.readlines()

        # remove newline at EOL
        # remove global comments
        # strip whitespace
        lines = [l.replace('\n', '').strip() for l in lines if not l[0].strip() in [';', 'Y']]

        transactions = []
        group = []

        for line in lines:
            if not line.strip():  # .strip handles lines with only spaces as chars
               transactions.append(group)
               group = []
            else:
               group.append(line)
        # add last group
        transactions.append(group)
        transactions = [g for g in transactions if g]

        return self._import_raw_transactions(transactions)


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

    def __str__(self):
        header = f'{self.date} {self.status} ({self.code}) {self.description}'
        h_tags = ', '.join([f'{k}:{v}' for k,v in self.tags.items()])
        h_comment = self.comment
        postings = ''
        for posting in self._postings:
            postings += f'\t{posting.__repr__()}\n'
        return f'{header} [{h_tags}] | {h_comment}\n{postings}'

    @property
    def json(self):
        return dict(date=self.date,
                    status=self.status,
                    code=self.code,
                    description=self.description,
                    postings=[p.json for p in self.postings],
                    comment=self.comment)

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        self._header = header

    @property
    def date(self):
        try:
            self._header['primary_date'].isoformat()
        except:
            print(self.header)
            raise
        return self._header['primary_date'].isoformat()

    @property
    def status(self):
        return self._header['status']

    @property
    def code(self):
        return self._header['code']

    @property
    def description(self):
        return self._header['description']

    @property
    def comment(self):
        return self._header['comment']

    @property
    def tags(self):
        return self._header['tags']

    @property
    def postings(self):
        return self._postings

    def add_posting(self, posting):
        self._postings.append(posting)

    def run_checks(self, check):
        return check(self)


class Posting():
    """Represents a single posting
    """
    def __init__(self, account, amount, primary_date, tags={}, secondary_date=None):
        self._account = account
        self._amount = amount
        self._primary_date = primary_date
        self._tags = tags
        self._secondary_date = secondary_date

    def __repr__(self):
        return f'{self._account:<40}    {self._amount:10.2f}'

    @property
    def json(self):
        return dict(account=self.account,
                    date=self.date,
                    amount=self.amount,
                    tags=self.tags)

    @property
    def account(self):
        return self._account

    @property
    def amount(self):
        return self._amount

    @property
    def tags(self):
        return self._tags

    @property
    def date(self):
        if self._secondary_date is not None:
            return self._secondary_date.isoformat()
        else:
            return self._primary_date.isoformat()
    

def read_file(in_file, run_checks=False):
    ledger = Ledger(ledger_filename=in_file)
    if run_checks:
        ledger.run_checks(strict=False)
    return ledger.json
