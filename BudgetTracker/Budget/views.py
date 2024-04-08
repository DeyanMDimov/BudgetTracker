from django.shortcuts import render
from Budget.models import category, theme, account, transaction, travelTrip, equalPaySplit
from Budget import importLogic
from django.forms.models import model_to_dict
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import connection
from django.http import JsonResponse
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ExpressionWrapper, Sum, Q, Count
import json
import csv
import os
import time



def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value

def pretty_print_response(response):
  print(json.dumps(response, indent=2, sort_keys=True, default=str))



# Create your views here.
def index(request):
    return render (request, 'base.html')


def importTx(request):
    existingThemes = theme.objects.all()
    existingCategories = category.objects.all().order_by('theme__name', 'name')
    existingAccounts = account.objects.all().order_by('name')
    responseMessage = ""
    if request.method == 'GET':
       
        
        if 'addTheme' in request.GET:
            themeToAdd = request.GET['addTheme']
            try:
                existingTheme = theme.objects.get(name = themeToAdd)
                responseMessage = "Theme - \"" + themeToAdd + "\" not added - already exists."
            except:
                theme.objects.create(
                    name = themeToAdd
                )
                responseMessage = "Theme - \"" + themeToAdd + "\" successfully added."
                #return render(request, 'importTx.html', {"addAction": responseMessage, "existingThemes": existingThemes, "existingCategories": existingCategories})
            
            
            #return render(request, 'importTx.html', {"addAction": responseMessage, "existingThemes": existingThemes})
        
        elif 'addCategory' in request.GET:
            categoryToAdd = request.GET['addCategory']
            parentThemeName = request.GET['existingTheme']
            for cat in category.objects.all():
                themeOfCat = cat.getTheme()
                print(cat.name, themeOfCat)
            try:
                existingCategory = category.objects.get(name = categoryToAdd)
                responseMessage = "Category - \"" + categoryToAdd + "\" not added - already exists."
            except: 
                parentTheme = theme.objects.get(name = parentThemeName)
                category.objects.create(
                    name = categoryToAdd,
                    theme = parentTheme
                )
                responseMessage = "Category - \"" + categoryToAdd + "\" successfully added to theme \"" + parentThemeName + "\"."
                #return render(request, 'importTx.html', {"addAction": responseMessage, "existingThemes": existingThemes, "existingCategories": existingCategories})

            

        elif 'addAccount' in request.GET:
            accountToAdd = request.GET['addAccount']
            try:
                existingAccount = account.objects.get(name = accountToAdd)
                responseMessage = "Account - \"" + accountToAdd + "\" not added - already exists."
            except:
                account.objects.create(
                    name = accountToAdd
                )
                responseMessage = "Account - \"" + accountToAdd + "\" successfully added."

        elif 'loadOldTx' in request.GET:
            # try:
                file = open("static/sorted-transactions-2012-2019.csv")
                csvreader = csv.reader(file)
                
                importLogic.convertCSVToData(csvreader, True)
                

                # rows = []
                
                # for r in csvreader:
                #     rows.append(r)
                    
                # rows.pop(0)

                # for r in rows:
                #     r0 = r[0]
                #     r1 = r[1]
                #     r2 = r[2]
                #     r3 = r[3]
                #     r4 = r[4]
                #     r5 = r[5]
                #     r6 = r[6]
                #     r7 = r[7]
                #     r8 = r[8]
                #     r9 = r[9]
                   
                #     # selected_accounts = account.objects.filter(name = r8)
                #     # for sa in selected_accounts:
                #     #     print(sa.name)
                #     #     print("Printed Account Name Once - " + str(selected_accounts.count()))

                #     # selected_account = selected_accounts[0]
                #     try:
                #         selected_account = account.objects.get(name = r8)    
                #     except account.MultipleObjectsReturned:
                #         print("MultipleObjects Rerturned")
                #     except account.DoesNotExist:
                #         print("No accounts found")
                #     except:
                #         print("otherexception")
                    
                    
                #     try:
                #         selected_cat = category.objects.get(name = r5) 
                #     except category.MultipleObjectsReturned:
                #         print("MultipleObjects Rerturned")
                #     except category.DoesNotExist:
                #         print("No category found - " + r5)
                #         selected_cat = category.objects.get(name = "Undefined")
                #     except:
                #         print("otherexception")
                    
                    
                #     transaction.objects.create(
                #         date = datetime.strptime(r[0], '%m/%d/%y').date(),
                #         description = r[1],
                #         amount = r[2],
                #         type = r[3],
                #         account = selected_account,
                #         original_description = r[9],
                #         category = selected_cat,
                #         spreadsheetThemeCategory = r[4] + " " + r[5],
                #         labels = r[6],
                #         notes = r[7]
                #     )    
                

                file.close()
                responseMessage = "Successfully loaded transactions."
            # except Exception as e:
            #     responseMessage="Failed to load Txs - " + str(e)

        elif 'loadNewTx' in request.GET:
            file = open("static/PublicTX.csv")
            csvreader = csv.reader(file)
                
            importLogic.convertCSVToData(csvreader, False)
            file.close()
            responseMessage = "Successfully loaded transactions."
        elif 'deleteAllTx' in request.GET:
            allTx = transaction.objects.all()
            for tx in allTx:
                tx.account = None
                tx.category = None
            allTx.delete()    
            responseMessage = "Successfully deleted all transactions."
        
        trips = travelTrip.objects.all()
        print(str(len(trips)))
        return render(request, 'importTx.html', {"addAction": responseMessage, "existingThemes": existingThemes, "existingCategories": existingCategories, "existingAccounts": existingAccounts, "trips": trips})        
    else:
        pass
    
    

    

    return render(request, 'importTx.html', { "existingThemes": existingThemes, "existingCategories": existingCategories, "existingAccounts": existingAccounts})

def viewTx(request):
    if request.method == "GET":
        if 'date_filter_start' in request.GET and 'date_filter_end' in request.GET:
            date_start_string = request.GET['date_filter_start']
            date_end_string =  request.GET['date_filter_end']
            
            print (date_end_string)
            print (date_start_string)
            txs = transaction.objects.filter(date__gte=date_start_string, date__lte=date_end_string).order_by('-date')
        
        elif 'daterange' in request.GET:
            if request.GET['daterange'] == "YTD":
                today = datetime.today()
                firstOfTheYear = datetime(year = today.year, month = 1, day = 1)
                txs = transaction.objects.filter(date__gte=firstOfTheYear).order_by('-date')
            elif request.GET['daterange'] == "180days":
                today = datetime.today()
                resultStartDate = datetime.now() + timedelta(-180)
                txs = transaction.objects.filter(date__gte=resultStartDate).order_by('-date')
        else:
            defaultStartDate = datetime.now() + timedelta(-200)
            txs = transaction.objects.filter(date__gte=defaultStartDate).order_by('-date')
            
            #txs = transaction.objects.filter(description__icontains="zelle")

    #txs = transaction.objects.all().order_by('-date')
    #txs = transaction.objects.filter(description = "Venmo").order_by('-date')

    
    numberOfTransactions = len(txs)
    

    existingThemes = theme.objects.all().order_by('name')
    existingCategories = category.objects.all().order_by('name')

    existingTrips = travelTrip.objects.all()

    accts_default_order = account.objects.all()

    accts = []
    accts.append(accts_default_order[0])
    accts.append(accts_default_order[1])
    accts.append(accts_default_order[2])

    # print(accts)
    # themeCatDict = {}
    # for t in existingThemes:
    #     listOfCats = []
    #     for c in existingCategories.filter(theme == t):
    #         listOfCats.append(c)
    #     themeCatDict.append({t : listOfCats})

    

    return render(request, 'viewTx.html', {"transactions": txs, "themes": existingThemes, "cats": existingCategories, "accts": accts, "tx_count": numberOfTransactions, "trips": existingTrips})

def viewSummary(request):

    
   
    yearToDisplay = 2024
    if 'yearSummary' in request.GET:
        yearToDisplay = request.GET['yearSummary']
    
    themeTotals = {}
    existingCategories = category.objects.all().order_by('theme__name', 'name')
    categoryThemePairs = {}
    overallTotals = {}
    overallTotals['total'] = 0

    for i in range(12):
        overallTotals[i+1] = 0

    transactionsForTheYear = transaction.objects.filter(date__year = yearToDisplay)

    for t in theme.objects.all().order_by('name'):
        theme_debit_transactions = transactionsForTheYear.filter(type = 'debit', category__theme__name = t.name)
        theme_credit_transactions = transactionsForTheYear.filter(type = 'credit', category__theme__name = t.name)

        total_debit_amt = sum(tx.amount for tx in theme_debit_transactions)
        total_credit_amt = sum(tx.amount for tx in theme_credit_transactions)  
       
        totalForYear = total_credit_amt - total_debit_amt
        individualThemeTotals = {}
        individualThemeTotals['id'] = t.id
        individualThemeTotals['total'] = round(totalForYear, 2)

        overallTotals['total'] += round(totalForYear, 2)

        for i in range(12):

            if(totalForYear != 0):
                theme_debit_month_transactions = theme_debit_transactions.filter(date__month = i+1)
                theme_credit_month_transactions = theme_credit_transactions.filter(date__month = i+1)

                total_debit_amt = sum(tx.amount for tx in theme_debit_month_transactions)
                total_credit_amt = sum(tx.amount for tx in theme_credit_month_transactions) 
            
                totalForMonth = total_credit_amt - total_debit_amt
                
                individualThemeTotals[i+1] = round(totalForMonth, 2)

                overallTotals[i+1] += round(totalForMonth, 2)
                #print("Month " + str(i) + ":" + str(overallTotals[i+1]))
            else:
                individualThemeTotals[i+1] = 0

        for cat in category.objects.filter(theme = t):
            categoryThemePairs[cat.name] = t.name

            category_debit_transactions = theme_debit_transactions.filter(category__name = cat.name)
            category_credit_transactions = theme_credit_transactions.filter(category__name = cat.name)

            total_debit_amt = sum(tx.amount for tx in category_debit_transactions)
            total_credit_amt = sum(tx.amount for tx in category_credit_transactions) 

            totalForCatForYear = total_credit_amt - total_debit_amt
            individualCatTotals = {}
            individualCatTotals['total'] = round(totalForCatForYear, 2)

            for i in range(12):
                if(totalForCatForYear != 0):
                    category_debit_month_transactions = category_debit_transactions.filter(date__month = i+1)
                    category_credit_month_transactions = category_credit_transactions.filter(date__month = i+1)

                    total_debit_amt = sum(tx.amount for tx in category_debit_month_transactions)
                    total_credit_amt = sum(tx.amount for tx in category_credit_month_transactions) 
                
                    totalForCatForMonth = total_credit_amt - total_debit_amt
                    individualCatTotals[i+1] = round(totalForCatForMonth, 2)
                else:
                    individualCatTotals[i+1] = 0
            
            individualThemeTotals[cat.name] = individualCatTotals
        
        themeTotals[t.name] =  individualThemeTotals

    themeTotals['overall'] = overallTotals   

    
   

    #return render(request, 'viewSummary.html', {'existingThemes': theme.objects.all().order_by('name'), 'themeTotals': themeTotals})
    return render(request, 'viewSummary.html', {'existingThemes': themeTotals, 'existingCategories': existingCategories, 'categoryThemePairs': categoryThemePairs, 'yearSelected': yearToDisplay})

def equalPay(request):
    defaultStartDate = datetime.now() + timedelta(-1500)
    txs = transaction.objects.filter(date__gte=defaultStartDate, description="Amazon").order_by('-date')
    numberOfTransactions = len(txs)
    existingThemes = theme.objects.all()
    existingTrips = travelTrip.objects.all()
    accts_default_order = account.objects.all()
    accts = []
    accts.append(accts_default_order[6])
    accts.append(accts_default_order[2])
    accts.append(accts_default_order[0])
    accts.append(accts_default_order[1])
    accts.append(accts_default_order[5])
    accts.append(accts_default_order[3])
    accts.append(accts_default_order[4])
    existingCategories = category.objects.all().order_by('name')
    return render(request, 'equalPay.html', {"transactions": txs, "themes": existingThemes, "cats": existingCategories, "accts": accts, "tx_count": numberOfTransactions, "trips": existingTrips})

def confirmTx(request):
    confirmTxId = request.GET.get('tx_id')
    tx = transaction.objects.get(transactionId = confirmTxId)
    tx.confirmed = True
    tx.save()
    print("Transaction with ID: " + str(tx.transactionId) + " confirmed.")

    return render(request, 'viewTx.html', {'response': "success"})

def getCorrectCategories(request):
    themesString = request.GET.get('theme')
    print(themesString)
    themesArray = themesString.split(',')

    themeToGetStr = themesArray[0]
    themeToGet = theme.objects.get(name = themeToGetStr)
    cats = category.objects.filter(theme = themeToGet).order_by('name')
    listOfCategories = []
    for c in cats:
        listOfCategories.append([c.name, c.id])
    
    return JsonResponse({'categories': listOfCategories}, status="200")

def getTxDetailsForEdit(request):
    tx_id = request.GET.get('tx_id')
    tx = transaction.objects.get(transactionId = tx_id)
    tx.confirmed = False
    tx.save()
    tx_dict = model_to_dict(tx)
    tx_dict['theme'] = tx.category.theme.name
    tx_dict['category'] = tx.category.name
    tx_dict['account'] = tx.account.name
    tx_dict['sub_flag'] = tx.is_subscription
    tx_dict['trip_flag'] = tx.part_of_travel_trip
    if tx.travel_trip != None:
        tx_dict['trip_name'] = tx.travel_trip.name
    else:
        tx_dict['trip_name'] = ""
    themes = theme.objects.all()
    cats = category.objects.filter(theme = tx.category.theme)
    themesList = []
    catsList = []
    for t in themes:
        themesList.append(t.name)
    for c in cats:
        catsList.append(c.name)
    trips = travelTrip.objects.all()
    tripsList = []
    for trip in trips:
        tripsList.append(trip.name)
    

    return JsonResponse({'tx': tx_dict, 'themes': themesList, 'cats': catsList, 'trips': tripsList}, status="200")

def saveTxChanges(request):
    tx_id = request.GET.get('tx_id')
    tx_date = str(request.GET.get('tx_date'))
    tx_desc = request.GET.get('tx_desc')
    tx_amt = request.GET.get('tx_amt')
    tx_type = request.GET.get('tx_type')
    tx_category = request.GET.get('tx_category')
    tx_labels = request.GET.get('tx_labels')
    tx_notes = request.GET.get('tx_notes')


    tx_trip_flag = True if request.GET.get('tx_trip_flag') == 'true' else False
    tx_trip_name = request.GET.get('tx_trip_name')
    tx_is_sub = True if request.GET.get('tx_subs_flag') == 'true' else False
    #tx_account = request.GET.get('')
    #tx_og_desc = request.GET.get('')
                
    tx = transaction.objects.get(transactionId = tx_id)
    tx.confirmed = True
    print(tx_date)
    tx.date = datetime.strptime(tx_date, '%m/%d/%Y').date()
    tx.description = tx_desc
    tx.amount = tx_amt
    tx.type = tx_type
    tx.category = category.objects.get(name = tx_category)
    tx.labels = tx_labels
    tx.notes = tx_notes
    tx.part_of_travel_trip = tx_trip_flag
    tx.is_subscription = tx_is_sub
    tx.save()

    print(tx_trip_flag)

    if tx_trip_flag:
        try:
            existingTrip = travelTrip.objects.get(name = tx_trip_name)
            tx.travel_trip = existingTrip
            tx.save()
        except ObjectDoesNotExist:
            newTrip = travelTrip.objects.create(name = tx_trip_name)
            tx.travel_trip = newTrip
            tx.save()
    else:
        tx.travel_trip = None
        tx.save()

    return JsonResponse({}, status="200")

def saveTxSplit(request):
    tx_id = request.POST.get('original_tx_id')
    txs = request.POST.get('split_txs')
    split_txs = json.loads(txs)

    original_tx = transaction.objects.get(transactionId = tx_id)
    original_amount = original_tx.amount if original_tx.type == "debit" else original_tx.amount*-1

    new_amt_total = 0 
    for tx in split_txs:
        print(tx['tx_type'], " ", tx['tx_amt'])
        if tx['tx_type'] == "debit":
            new_amt_total += Decimal(tx['tx_amt'])
        else:
            new_amt_total -= Decimal(tx['tx_amt'])

    if new_amt_total != original_amount:
        return JsonResponse({'Message': 'Transaction totals don\'t match.'}, status="400")
    
    ids_created = dict()
    split_count_for_response = 0
    for tx in split_txs:
        if(tx['tx_new'] == False):
            original_tx.date = datetime.strptime(tx['tx_date'], '%m/%d/%Y').date()
            original_tx.description = tx['tx_desc']
            original_tx.amount = tx['tx_amt']
            original_tx.type = tx['tx_type']
            original_tx.category = category.objects.get(name = tx['tx_category'])
            original_tx.labels = tx['tx_labels']
            original_tx.notes = tx['tx_notes']
            original_tx.confirmed = True
            original_tx.save()

        else:
            new_tx = transaction.objects.create(
                date = datetime.strptime(tx['tx_date'], '%m/%d/%Y').date(),
                description = tx['tx_desc'],
                amount = tx['tx_amt'],
                type = tx['tx_type'],
                category = category.objects.get(name = tx['tx_category']),
                labels = tx['tx_labels'],
                notes = tx['tx_notes'],
                account = account.objects.get(name = tx['tx_account']),
                original_description = original_tx.original_description,
                confirmed = True,
                spreadsheetThemeCategory = category.objects.get(name = tx['tx_category']).theme.name + " " + tx['tx_category']
            )
            #ids_created.append({"split"+str(split_count_for_response) : new_tx.transactionId})
            element_page_id = tx['page_id']
            #print(element_page_id + " " + str(tx['tx_amt']))
            print(new_tx.pk)
            ids_created[element_page_id] =  str(new_tx.pk)
            split_count_for_response += 1

    print(ids_created)

    return JsonResponse(ids_created, status="200")

def deleteTx(request):
    tx_id = request.GET.get('tx_id')

    tx = transaction.objects.get(transactionId = tx_id)

    tx.delete()
    return JsonResponse({}, status="200")

def getOptionsForNewTx(request):
    #tx_id = request.GET.get('tx_id')
    #tx = transaction.objects.get(transactionId = tx_id)
    #tx.confirmed = False
    #tx.save()
    # tx_dict = model_to_dict(tx)
    # tx_dict['theme'] = tx.category.theme.name
    # tx_dict['category'] = tx.category.name
    # tx_dict['account'] = tx.account.name
    themes = theme.objects.all().order_by('name')
    cats = category.objects.filter(theme = themes[0])
    accts = account.objects.all().order_by('name')
    themesList = list(theme.name for theme in themes)

    catsList = []
    acctsList = []
    # for t in themes:
    #     themesList.append(t.name)
    for c in cats:
        catsList.append(c.name)
    
    for acc in accts:
        acctsList.append(acc.name)
    trips = travelTrip.objects.all()
    tripsList = []
    for trip in trips:
        tripsList.append(trip.name)

    return JsonResponse({'themes': themesList, 'cats': catsList, 'accts': acctsList, 'trips': tripsList}, status="200")

def saveNewTx(request):
    tx_id = request.GET.get('tx_id')
    tx_date = str(request.GET.get('tx_date'))
    tx_desc = request.GET.get('tx_desc')
    tx_amt = request.GET.get('tx_amt')
    tx_type = request.GET.get('tx_type')
    tx_category = request.GET.get('tx_category')
    tx_labels = request.GET.get('tx_labels')
    tx_notes = request.GET.get('tx_notes')
    tx_account = request.GET.get('acct')
    tx_og_desc = request.GET.get('o_desc')
    tx_trip_flag = request.GET.get('trip_flag')
    tx_trip_name = request.GET.get('trip_name')
    tx_subs_flag = request.GET.get('subs_flag')

    print("tx_id: " + str(tx_id))
    print("tx_date: " + str(tx_date))
    print("tx_desc: " + str(tx_desc))
    print("tx_amt: "  + str(tx_amt))
    print("tx_type: "  + str(tx_type))
    print("tx_category: "  + str(tx_category))
    print("tx_labels: "  + str(tx_labels))
    print("tx_notes: "  + str(tx_notes))
    print("tx_account: "  + str(tx_account))
    print("tx_og_desc: "  + str(tx_og_desc))

    part_of_travel_trip = True if (tx_trip_flag == 'true' or tx_trip_flag == 'True') else False
    
    is_subscription = True if (tx_subs_flag == 'true' or tx_subs_flag == 'True') else False

    problems = []

    try:
        inputted_date = datetime.strptime(tx_date, '%m/%d/%Y')
    except Exception as e:
        try:
            inputted_date = datetime.strptime(tx_date, '%m/%d/%y')
        except Exception as ee:
            problems.append('date_col')
    try:
        inputted_amt = float(tx_amt)
    except:
        problems.append('amount_col')
    
    if len(problems) > 0:
        return JsonResponse({'problems': problems}, status="400")
        
    new_tx = transaction.objects.create(
                date = datetime.strptime(tx_date, '%m/%d/%Y').date(),
                description = tx_desc,
                amount = tx_amt,
                type = tx_type,
                category = category.objects.get(name = tx_category),
                labels = tx_labels,
                notes = tx_notes,
                account = account.objects.get(name = tx_account),
                original_description = tx_og_desc,
                part_of_travel_trip = part_of_travel_trip,
                is_subscription = is_subscription,
                confirmed = True,
                spreadsheetThemeCategory = category.objects.get(name = tx_category).theme.name + " " + tx_category
            )
    
    if part_of_travel_trip:
        try:
            existingTrip = travelTrip.objects.get(name = tx_trip_name)
            new_tx.travel_trip = existingTrip
            new_tx.save()
        except ObjectDoesNotExist:
            newTrip = travelTrip.objects.create(name = tx_trip_name)
            new_tx.travel_trip = newTrip
            new_tx.save()
    
    id_created = str(new_tx.pk)

    return JsonResponse({'created_id': id_created}, status="200")

def setEqualPayPromo(request):
    tx_id = request.GET.get('tx_id')
    hasSplit = request.GET.get('tx_has_equal_pay_split')
    splitDuration = request.GET.get('split_duration')


    singleTransaction = transaction.objects.get(transactionId = tx_id)
    if hasSplit:
        singleTransaction.has_equalPaySplit = True

        equalPaySplit.objects.create(
            transactionSplit = singleTransaction,
            split_length_months = splitDuration
        )
    
    #equalPaySplit.

def cleanseForPublic (request):
    

    
    category.objects.filter(name = "Student Loans").delete()
    category.objects.filter(name = "Credit Card Rewards").delete()

    
    
    defaultStartDate = datetime.now() + timedelta(-180)
    txs = transaction.objects.filter(date__gte=defaultStartDate).order_by('-date')
    numberOfTransactions = len(txs)
    

    existingThemes = theme.objects.all()
    existingCategories = category.objects.all().order_by('name')

    existingTrips = travelTrip.objects.all()

    accts_default_order = account.objects.all()

    accts = []
  

    return render(request, 'viewTx.html', {"transactions": txs, "themes": existingThemes, "cats": existingCategories, "accts": accts, "tx_count": numberOfTransactions, "trips": existingTrips})