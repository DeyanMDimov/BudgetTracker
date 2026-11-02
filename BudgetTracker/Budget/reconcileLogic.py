"""Compare a credit card / bank statement CSV against the transactions stored in the tracker.

Transactions get split, so the two sides are compared by totals (overall and per day)
rather than row by row.

Every row, from either side, is normalised to a dict:
    {'date': date, 'description': str, 'amount': Decimal (positive), 'type': 'debit' | 'credit', ...}
"""
import csv
import io
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

from Budget.importLogic import CSV_ACCOUNT_ALIASES


DATE_FORMATS = ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%m-%d-%Y', '%m-%d-%y', '%Y/%m/%d')

# Header names to look for, most specific first. Matching ignores case and surrounding spaces.
DATE_HEADERS = ('transaction date', 'trans. date', 'trans date', 'date', 'posted date', 'post date', 'posting date')
DESCRIPTION_HEADERS = ('description', 'payee', 'merchant', 'name', 'original description')
AMOUNT_HEADERS = ('amount', 'transaction amount')
DEBIT_HEADERS = ('debit', 'debit amount', 'withdrawal', 'withdrawals')
CREDIT_HEADERS = ('credit', 'credit amount', 'deposit', 'deposits')
TYPE_HEADERS = ('transaction type', 'type')
ACCOUNT_HEADERS = ('account name', 'account')

# Column layout of the file the "Load New Transactions" import reads (static/PublicTX.csv).
IMPORT_LAYOUT = {'date': 0, 'description': 1, 'amount': 3, 'type': 4, 'account': 6}

ZERO = Decimal('0')
MAX_SKIPPED_EXAMPLES = 5


class StatementParseError(Exception):
    pass


def decodeUpload(rawBytes):
    try:
        return rawBytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        return rawBytes.decode('latin-1')


def parseDate(value):
    value = (value or '').strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parseAmount(value):
    """'$1,234.56' -> Decimal('1234.56'), '(12.00)' -> Decimal('-12.00'), '' -> None.
    Raises ValueError for anything else that isn't a number."""
    value = (value or '').strip().replace('$', '').replace(',', '').replace(' ', '')
    if value == '':
        return None
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1]
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError(value)
    return -amount if negative else amount


def _findColumn(headers, candidates):
    for candidate in candidates:
        if candidate in headers:
            return headers.index(candidate)
    return None


def _cell(row, index):
    if index is None or index >= len(row):
        return ''
    return row[index].strip()


def _isDebitCreditColumn(dataRows, index):
    values = {_cell(r, index).lower() for r in dataRows} - {''}
    return len(values) > 0 and values <= {'debit', 'credit'}


def parseStatementCSV(text):
    """Parse a statement CSV and work out how it represents charges vs. credits.

    Supported layouts (detected from the header row):
      * separate Debit / Credit columns (e.g. Capital One)
      * an Amount column plus a Type column holding 'debit' / 'credit' (the tracker's own import file)
      * a single signed Amount column (e.g. Chase, where charges are negative)

    Returns a dict with:
      rows               - normalised rows
      formatDescription  - human readable explanation of how the file was read
      hasAccountColumn   - whether rows carry an account name
      skippedCount       - rows that had content but no readable date / amount
      skippedExamples    - a few of those rows, for display
    """
    allRows = [r for r in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in r)]
    if not allRows:
        raise StatementParseError("The file is empty.")

    headers = [h.strip().lower() for h in allRows[0]]
    dataRows = allRows[1:]
    cols = {
        'date': _findColumn(headers, DATE_HEADERS),
        'description': _findColumn(headers, DESCRIPTION_HEADERS),
        'amount': _findColumn(headers, AMOUNT_HEADERS),
        'debit': _findColumn(headers, DEBIT_HEADERS),
        'credit': _findColumn(headers, CREDIT_HEADERS),
        'type': _findColumn(headers, TYPE_HEADERS),
        'account': _findColumn(headers, ACCOUNT_HEADERS),
    }

    if cols['date'] is not None and cols['debit'] is not None and cols['credit'] is not None:
        mode = 'debitCredit'
        formatDescription = "Separate Debit and Credit columns."
    elif cols['date'] is not None and cols['amount'] is not None:
        if cols['type'] is not None and _isDebitCreditColumn(dataRows, cols['type']):
            mode = 'typed'
            formatDescription = "Amount column with a debit/credit Type column."
        else:
            mode = 'signed'
            formatDescription = None  # filled in once the sign convention is known
    elif len(allRows[0]) >= 7 and _isDebitCreditColumn(allRows[1:] or allRows, IMPORT_LAYOUT['type']):
        # No recognisable headers - fall back to the tracker's own import file layout.
        mode = 'typed'
        cols = dict(cols, debit=None, credit=None, **IMPORT_LAYOUT)
        formatDescription = "Tracker import file layout (date, description, original description, amount, type, category, account)."
        if parseDate(_cell(allRows[0], IMPORT_LAYOUT['date'])) is not None:
            dataRows = allRows  # first row is data, not a header
    else:
        raise StatementParseError(
            "Couldn't find a date column and an amount column in this file. "
            "Expected headers like 'Transaction Date' and 'Amount', or 'Debit' and 'Credit'."
        )

    parsed = []
    skipped = []
    for row in dataRows:
        txDate = parseDate(_cell(row, cols['date']))
        try:
            if mode == 'debitCredit':
                debit = parseAmount(_cell(row, cols['debit']))
                credit = parseAmount(_cell(row, cols['credit']))
                if debit:
                    amount, txType = abs(debit), 'debit'
                elif credit:
                    amount, txType = abs(credit), 'credit'
                elif debit is not None or credit is not None:
                    amount, txType = ZERO, 'debit'
                else:
                    amount, txType = None, None
            elif mode == 'typed':
                amount = parseAmount(_cell(row, cols['amount']))
                amount = abs(amount) if amount is not None else None
                txType = _cell(row, cols['type']).lower()
            else:
                amount = parseAmount(_cell(row, cols['amount']))
                txType = None  # decided below, once the sign convention is known
        except ValueError:
            amount = None

        if txDate is None or amount is None or txType not in ('debit', 'credit', None):
            skipped.append(row)
            continue

        parsed.append({
            'date': txDate,
            'description': _cell(row, cols['description']),
            'amount': amount,
            'type': txType,
            'account': _cell(row, cols['account']) or None,
        })

    if mode == 'signed':
        # Card issuers disagree on the sign of a purchase (Chase: negative, Discover/Amex: positive).
        # Purchases vastly outnumber payments and refunds on a card statement, so go with the majority.
        negatives = sum(1 for r in parsed if r['amount'] < 0)
        positives = sum(1 for r in parsed if r['amount'] > 0)
        chargesAreNegative = negatives >= positives
        for r in parsed:
            isCharge = (r['amount'] <= 0) if chargesAreNegative else (r['amount'] >= 0)
            r['type'] = 'debit' if isCharge else 'credit'
            r['amount'] = abs(r['amount'])
        formatDescription = (
            "Single signed Amount column - read %s amounts as charges and %s amounts as credits "
            "(most rows were %s)." % (
                ('negative', 'positive', 'negative') if chargesAreNegative else ('positive', 'negative', 'positive')
            )
        )

    if not parsed:
        raise StatementParseError("No transactions with a readable date and amount were found in the file.")

    return {
        'rows': parsed,
        'formatDescription': formatDescription,
        'hasAccountColumn': cols['account'] is not None and any(r['account'] for r in parsed),
        'skippedCount': len(skipped),
        'skippedExamples': [', '.join(r) for r in skipped[:MAX_SKIPPED_EXAMPLES]],
    }


def statementRowMatchesAccount(rowAccountName, acct):
    """Does an account name from a statement row refer to this account?"""
    if not rowAccountName:
        return False
    resolved = CSV_ACCOUNT_ALIASES.get(rowAccountName.strip(), rowAccountName.strip()).lower()
    return resolved in {(acct.name or '').lower(), (acct.displayName or '').lower()}


def trackerRows(transactions):
    return [{
        'id': tx.transactionId,
        'date': tx.date,
        'description': tx.description,
        'amount': tx.amount,
        'type': (tx.type or '').strip().lower(),
        'account': tx.account.name if tx.account else None,
        'category': tx.category.name if tx.category else None,
    } for tx in transactions]


def summarize(rows):
    debits = sum((r['amount'] for r in rows if r['type'] == 'debit'), ZERO)
    credits = sum((r['amount'] for r in rows if r['type'] == 'credit'), ZERO)
    return {'debits': debits, 'credits': credits, 'net': debits - credits, 'count': len(rows)}


def _compareLine(label, key, statementTotals, trackerTotals):
    difference = trackerTotals[key] - statementTotals[key]
    return {
        'label': label,
        'statement': statementTotals[key],
        'tracker': trackerTotals[key],
        'difference': difference,
        'matches': difference == 0,
    }


def compare(statementRows, trackerRowsList):
    """Totals for both sides plus a per-day breakdown.

    A day "matches" when its charges and its credits agree. Transaction counts are shown
    but never count as a mismatch, since splitting a transaction changes the count.
    """
    statementTotals = summarize(statementRows)
    trackerTotals = summarize(trackerRowsList)

    totals = [
        _compareLine('Charges (debits)', 'debits', statementTotals, trackerTotals),
        _compareLine('Payments & credits', 'credits', statementTotals, trackerTotals),
        _compareLine('Net (charges - credits)', 'net', statementTotals, trackerTotals),
    ]

    byDate = defaultdict(lambda: ([], []))
    for r in statementRows:
        byDate[r['date']][0].append(r)
    for r in trackerRowsList:
        byDate[r['date']][1].append(r)

    days = []
    for day in sorted(byDate):
        dayStatementRows, dayTrackerRows = byDate[day]
        s = summarize(dayStatementRows)
        t = summarize(dayTrackerRows)
        days.append({
            'date': day,
            'statement': s,
            'tracker': t,
            'netDifference': t['net'] - s['net'],
            'matches': s['debits'] == t['debits'] and s['credits'] == t['credits'],
            'statementRows': dayStatementRows,
            'trackerRows': dayTrackerRows,
        })

    return {
        'totals': totals,
        'statementCount': statementTotals['count'],
        'trackerCount': trackerTotals['count'],
        'allMatch': all(line['matches'] for line in totals),
        'days': days,
        'mismatchedDayCount': sum(1 for d in days if not d['matches']),
    }
