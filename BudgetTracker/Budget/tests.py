from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from Budget import reconcileLogic
from Budget.models import account, transaction


CHASE_CSV = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
03/02/2024,03/03/2024,TARGET 00012345,Shopping,Sale,-54.20,
03/02/2024,03/04/2024,STARBUCKS,Food & Drink,Sale,-6.75,
03/05/2024,03/05/2024,Payment Thank You - Web,,Payment,500.00,
03/07/2024,03/08/2024,AMAZON MKTPL,Shopping,Return,12.99,
03/09/2024,03/10/2024,WHOLEFDS,Groceries,Sale,-88.10,
"""

CAPITAL_ONE_CSV = """Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit
2024-03-02,2024-03-03,1234,SHELL OIL,Gas/Automotive,41.50,
2024-03-04,2024-03-04,1234,CAPITAL ONE MOBILE PYMT,Payment/Credit,,300.00
2024-03-06,2024-03-07,1234,UBER TRIP,Other Travel,"1,012.25",
"""

IMPORT_FILE_CSV = """Date,Description,Original Description,Amount,Transaction Type,Category,Account Name,Labels,Notes
03/02/24,Target,TARGET 00012345,54.20,debit,Shopping,Chase Card,,
03/03/24,Shell,SHELL OIL,41.50,debit,Gas & Fuel,Quicksilver,,
03/05/24,Chase Credit Card Payment,Payment Thank You - Web,500.00,credit,Credit Card Payment,Chase Card,,
"""


class ParseStatementTests(SimpleTestCase):

    def test_chase_signed_amounts(self):
        result = reconcileLogic.parseStatementCSV(CHASE_CSV)
        rows = result['rows']
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0], {
            'date': date(2024, 3, 2), 'description': 'TARGET 00012345',
            'amount': Decimal('54.20'), 'type': 'debit', 'account': None,
        })
        self.assertEqual((rows[2]['type'], rows[2]['amount']), ('credit', Decimal('500.00')))
        self.assertEqual((rows[3]['type'], rows[3]['amount']), ('credit', Decimal('12.99')))
        self.assertFalse(result['hasAccountColumn'])
        self.assertIn('negative amounts as charges', result['formatDescription'])

        totals = reconcileLogic.summarize(rows)
        self.assertEqual(totals['debits'], Decimal('149.05'))
        self.assertEqual(totals['credits'], Decimal('512.99'))

    def test_positive_charges_when_most_amounts_are_positive(self):
        csvText = "Trans. Date,Post Date,Description,Amount,Category\n" \
                  "03/01/2024,03/02/2024,GROCERY,25.00,Supermarkets\n" \
                  "03/03/2024,03/03/2024,RESTAURANT,40.00,Restaurants\n" \
                  "03/04/2024,03/04/2024,PAYMENT,-65.00,Payments\n"
        rows = reconcileLogic.parseStatementCSV(csvText)['rows']
        self.assertEqual([r['type'] for r in rows], ['debit', 'debit', 'credit'])
        self.assertEqual(rows[2]['amount'], Decimal('65.00'))

    def test_capital_one_debit_credit_columns(self):
        result = reconcileLogic.parseStatementCSV(CAPITAL_ONE_CSV)
        rows = result['rows']
        self.assertEqual([(r['date'], r['type'], r['amount']) for r in rows], [
            (date(2024, 3, 2), 'debit', Decimal('41.50')),
            (date(2024, 3, 4), 'credit', Decimal('300.00')),
            (date(2024, 3, 6), 'debit', Decimal('1012.25')),
        ])
        self.assertEqual(result['formatDescription'], "Separate Debit and Credit columns.")

    def test_tracker_import_file_with_accounts(self):
        result = reconcileLogic.parseStatementCSV(IMPORT_FILE_CSV)
        self.assertTrue(result['hasAccountColumn'])
        self.assertEqual([r['account'] for r in result['rows']], ['Chase Card', 'Quicksilver', 'Chase Card'])
        self.assertEqual([r['type'] for r in result['rows']], ['debit', 'debit', 'credit'])

    def test_tracker_import_file_without_recognisable_headers(self):
        csvText = "When,What,Raw,How much,Kind,Cat,Acct\n" \
                  "03/02/24,Target,TARGET,54.20,debit,Shopping,Chase Card\n"
        result = reconcileLogic.parseStatementCSV(csvText)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['amount'], Decimal('54.20'))
        self.assertEqual(result['rows'][0]['account'], 'Chase Card')

    def test_unreadable_rows_are_skipped_and_reported(self):
        csvText = CHASE_CSV + ",,Total,,,-148.05,\n"
        result = reconcileLogic.parseStatementCSV(csvText)
        self.assertEqual(len(result['rows']), 5)
        self.assertEqual(result['skippedCount'], 1)

    def test_unrecognised_file(self):
        with self.assertRaises(reconcileLogic.StatementParseError):
            reconcileLogic.parseStatementCSV("foo,bar\n1,2\n")
        with self.assertRaises(reconcileLogic.StatementParseError):
            reconcileLogic.parseStatementCSV("")

    def test_parse_amount_formats(self):
        self.assertEqual(reconcileLogic.parseAmount('$1,234.56'), Decimal('1234.56'))
        self.assertEqual(reconcileLogic.parseAmount('(12.00)'), Decimal('-12.00'))
        self.assertIsNone(reconcileLogic.parseAmount('  '))
        with self.assertRaises(ValueError):
            reconcileLogic.parseAmount('abc')


def row(day, amount, txType, description='x'):
    return {'date': date(2024, 3, day), 'description': description, 'amount': Decimal(amount), 'type': txType}


class CompareTests(SimpleTestCase):

    def test_split_transaction_still_matches(self):
        statement = [row(2, '100.00', 'debit'), row(5, '500.00', 'credit')]
        tracker = [row(2, '60.00', 'debit'), row(2, '40.00', 'debit'), row(5, '500.00', 'credit')]

        result = reconcileLogic.compare(statement, tracker)

        self.assertTrue(result['allMatch'])
        self.assertEqual(result['mismatchedDayCount'], 0)
        self.assertEqual((result['statementCount'], result['trackerCount']), (2, 3))

    def test_missing_and_wrong_transactions_are_flagged(self):
        statement = [row(2, '100.00', 'debit'), row(3, '20.00', 'debit'), row(5, '500.00', 'credit')]
        tracker = [row(2, '100.00', 'debit'), row(5, '450.00', 'credit')]

        result = reconcileLogic.compare(statement, tracker)

        self.assertFalse(result['allMatch'])
        charges, credits, net = result['totals']
        self.assertEqual(charges['difference'], Decimal('-20.00'))
        self.assertEqual(credits['difference'], Decimal('-50.00'))
        self.assertEqual(net['statement'], Decimal('-380.00'))
        self.assertEqual(net['tracker'], Decimal('-350.00'))
        self.assertEqual(net['difference'], Decimal('30.00'))
        self.assertEqual([(d['date'].day, d['matches']) for d in result['days']], [(2, True), (3, False), (5, False)])
        self.assertEqual(result['days'][1]['netDifference'], Decimal('-20.00'))


class ReconcileViewTests(TestCase):

    def setUp(self):
        self.chase = account.objects.create(name='CHASE - Credit Card')
        self.capOne = account.objects.create(name='CAPITAL ONE - Credit Card')

    def addTx(self, acct, day, amount, txType, description='x'):
        return transaction.objects.create(
            date=date(2024, 3, day), description=description, amount=Decimal(amount), type=txType,
            account=acct, original_description=description,
        )

    def post(self, csvText=None, **fields):
        data = dict(fields)
        if csvText is not None:
            data['statement_file'] = SimpleUploadedFile('statement.csv', csvText.encode('utf-8'), content_type='text/csv')
        return self.client.post('/reconcile/', data)

    def test_get_renders_form(self):
        response = self.client.get('/reconcile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Statement CSV')

    def test_chase_statement_matches_split_transactions(self):
        self.addTx(self.chase, 2, '30.00', 'debit', 'Target - groceries')
        self.addTx(self.chase, 2, '24.20', 'debit', 'Target - household')  # split of the 54.20 charge
        self.addTx(self.chase, 2, '6.75', 'debit')
        self.addTx(self.chase, 5, '500.00', 'credit')
        self.addTx(self.chase, 7, '12.99', 'credit')
        self.addTx(self.chase, 9, '88.10', 'debit')
        self.addTx(self.capOne, 9, '999.00', 'debit')   # other account, must be ignored
        self.addTx(self.chase, 20, '15.00', 'debit')    # outside the statement's date range

        response = self.post(CHASE_CSV, account=self.chase.id)

        self.assertEqual(response.status_code, 200)
        comparison = response.context['comparison']
        self.assertTrue(comparison['allMatch'], comparison['totals'])
        self.assertEqual(response.context['startDate'], '2024-03-02')
        self.assertEqual(response.context['endDate'], '2024-03-09')
        self.assertContains(response, 'Totals match')

    def test_mismatch_is_reported(self):
        self.addTx(self.chase, 2, '54.20', 'debit')
        self.addTx(self.chase, 5, '500.00', 'credit')

        response = self.post(CHASE_CSV, account=self.chase.id)

        comparison = response.context['comparison']
        self.assertFalse(comparison['allMatch'])
        self.assertEqual(comparison['mismatchedDayCount'], 3)
        self.assertContains(response, "Totals don't match")

    def test_statement_without_account_column_requires_an_account(self):
        response = self.post(CHASE_CSV)
        self.assertIn('errors', response.context)
        self.assertNotIn('comparison', response.context)

    def test_import_file_rows_are_filtered_to_the_chosen_account(self):
        self.addTx(self.chase, 2, '54.20', 'debit')
        self.addTx(self.chase, 5, '500.00', 'credit')

        response = self.post(IMPORT_FILE_CSV, account=self.chase.id)

        self.assertTrue(response.context['comparison']['allMatch'])
        self.assertIn('1 statement row(s) for other accounts were ignored.', response.context['notes'])

    def test_explicit_date_range_limits_both_sides(self):
        self.addTx(self.chase, 2, '54.20', 'debit')
        self.addTx(self.chase, 2, '6.75', 'debit')

        response = self.post(CHASE_CSV, account=self.chase.id, start_date='2024-03-01', end_date='2024-03-03')

        self.assertTrue(response.context['comparison']['allMatch'])
        self.assertIn('3 statement row(s) dated outside the selected range were ignored.', response.context['notes'])

    def test_tracker_totals_without_a_statement(self):
        self.addTx(self.chase, 2, '54.20', 'debit')
        self.addTx(self.chase, 5, '500.00', 'credit')

        response = self.post(account=self.chase.id, start_date='2024-03-01', end_date='2024-03-31')

        totals = response.context['trackerTotals']
        self.assertEqual(totals['debits'], Decimal('54.20'))
        self.assertEqual(totals['credits'], Decimal('500.00'))
        self.assertEqual(totals['count'], 2)

    def test_no_statement_and_no_dates_is_an_error(self):
        response = self.post(account=self.chase.id)
        self.assertIn('errors', response.context)
