import os
import math

class CheckFailed(Exception):
    '''raise this when there's at least one check does not pass'''

def valid_accounts():
    try:
        with open('.valid_accounts', 'r') as infile:
            lines = infile.readlines()
        return [line.rstrip() for line in lines]
    except:
        print('No ".valid_accounts" file found!')
        return []

def transaction_checks():
    return [check_sum_is_zero, check_valid_accounts]

def check_sum_is_zero(transaction, abs_tol=0.001):
    sum_of_postings = sum([p.amount for p in transaction.postings])
    return math.isclose(sum_of_postings, 0, abs_tol=abs_tol), f'Sum of postings is off by {sum_of_postings:.2f}'

def check_valid_accounts(transaction):
    invalid_accounts = []
    for posting in transaction.postings:
        if posting.account not in valid_accounts():
            invalid_accounts.append(posting.account)
    return len(invalid_accounts) < 1, f'Invalid account names: {invalid_accounts}'
