import sys
import math
import datetime

from tqdm import tqdm


def get_date(s):
    return datetime.datetime.strptime(s, '%Y/%m/%d').date().isoformat()


def get_transactions(group):
    transactions = []
    for t in group[1:]:
        t = [x for x in t.split('  ') if x]

        account = t[0]
        try:
            value = float(t[1].split()[0].replace(',', '.'))
        except IndexError as err:
            print(f'ERROR: {err} for entry {group}\n Account/Amount pair {t} could not be splitted, '
                  f'possibly due to less then two spaces separation')
            sys.exit(1)
        date = [x.replace(';', '').replace('date:', '').strip()
                for x in t[2:] if x not in [';']]

        if date:
            try:
                date = get_date(date[0]).isoformat()
            except Exception as e:
                date = get_date(group[0].split()[0])
        else:
            date = get_date(group[0].split()[0])

        transactions.append({
            'account': account,
            'date': date,
            'value': value
        })
    return transactions


def check_sum(doc, abs_tol=0.001):
    return math.isclose(
        sum([t['value'] for t in doc['transactions']]), 0, abs_tol=abs_tol)


def parse(group):
    doc = {}

    header_line = group[0].split()
    
    # get group date
    doc['group_date'] = get_date(header_line[0])
    # get subject
    # remove everything except group subject
    # TODO: implement parsing of transaction status and invoice number
    doc['subject'] = ' '.join([x for x in header_line[1:] if not x in ['*', '!'] and not x.startswith('(')])
    doc['transactions'] = get_transactions(group)

    # check total sum of all transactions is equal zero
    if not check_sum(doc):
        raise ArithmeticError('Transactions do not sum to zero', group)
    return doc


def read_file(in_file):
    with open(in_file, 'r') as in_file:
        lines = in_file.readlines()

    # remove newline at EOL
    # remove comments
    # remove global definition of year
    lines = [l.replace('\n', '') for l in lines if not l[0] in [';', 'Y']]

    # get transaction groups
    groups = []
    group = []
    for l in lines:
        if not l:
            groups.append(group)
            group = []
        else:
            group.append(l)
    groups = [g for g in groups if g]

    transactions = []
    for group in tqdm(groups):
        transactions.append(parse(group))

    return transactions
