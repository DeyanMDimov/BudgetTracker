from Budget import models
from Budget.models import account, category, transaction
from datetime import datetime, timedelta



def convertCSVToData(dataRows, old):
    rows = []
                
    for r in dataRows:
        rows.append(r)
        
    rows.pop(0)

    if old:
        for r in rows:
            if r[0] != "":
                r0 = r[0]
                r1 = r[1]
                r2 = r[2]
                r3 = r[3]
                r4 = r[4]
                r5 = r[5]
                r6 = r[6]
                r7 = r[7]
                r8 = r[8]
                r9 = r[9]
                
                # selected_accounts = account.objects.filter(name = r8)
                # for sa in selected_accounts:
                #     print(sa.name)
                #     print("Printed Account Name Once - " + str(selected_accounts.count()))

                # selected_account = selected_accounts[0]
                try:
                    selected_account = account.objects.get(name = r8)    
                except account.MultipleObjectsReturned:
                    print("MultipleObjects Rerturned")
                except account.DoesNotExist:
                    print("No accounts found")
                except:
                    print("otherexception")
                
                
                try:
                    selected_cat = category.objects.get(name = r5) 
                except category.MultipleObjectsReturned:
                    print("MultipleObjects Rerturned")
                except category.DoesNotExist:
                    if(r5 == "Work - Not Reimburse"):
                        selected_cat = category.objects.get(name = "Not Reimbursed")
                    else:
                        print("No category found - " + r5)
                        selected_cat = category.objects.get(name = "Undefined")
                except:
                    print("otherexception")
                
                tx_is_confirmed = True if selected_cat.name != "Undefined" else False
                
                transaction.objects.create(
                    date = datetime.strptime(r[0], '%m/%d/%y').date(),
                    description = transformDescription(r[1]),
                    amount = r[2],
                    type = r[3],
                    account = selected_account,
                    original_description = r[9],
                    category = selected_cat,
                    spreadsheetThemeCategory = r[4] + " " + r[5],
                    labels = r[6],
                    notes = r[7],
                    confirmed = tx_is_confirmed
                )
    else:
        for r in rows:
            if r[0] != "":
                csv_date = r[0]
                csv_description = r[1]
                csv_og_description = r[2]
                csv_amount = r[3]
                csv_type = r[4]
                csv_category = r[5]
                csv_account = r[6]
                
                selected_account = setAccount(csv_account)
                
                
                tx_date = csv_date
                #tx_og_desc = csv_og_description
                tx_amt = csv_amount
                tx_desc = transformDescription(csv_description)
                tx_type = csv_type
                tx_category = transformCategory(csv_category, tx_desc)

                transaction.objects.create(
                    date = datetime.strptime(tx_date, '%m/%d/%y').date(),
                    description = tx_desc,
                    amount = tx_amt,
                    type = tx_type,
                    account = selected_account,
                    original_description = csv_og_description,
                    category = tx_category,
                    spreadsheetThemeCategory = tx_category.name + " " + tx_category.theme.name,
                    labels = "",
                    notes = ""
                )
            


def transformDescription(csv_desc):
    result_desc = csv_desc
    if "VENMO" in csv_desc:
        if "CASHOUT" in csv_desc:
            result_desc = "Venmo Cashout"
        elif "PAYMENT" in csv_desc:
            result_desc = "Venmo"
    elif "ARMORY" in csv_desc:
        if "PAYROLL" in csv_desc:
            result_desc = "Armory Payroll"
        elif "Expensify" in csv_desc:
            result_desc = "Armory Expensify"
    elif "FANDUEL" in csv_desc:
        result_desc = "FanDuel"
    elif "DRAFTKINGS" in csv_desc:
        result_desc = "DraftKings"
    elif "Zelle Transaction" in csv_desc:
        result_desc = "Zelle"
    elif "MEN'S HEALTH LASALLE" in csv_desc:
        result_desc = "Men's Health LaSalle"
    elif "CAPITAL ONE" in csv_desc:
        if "MOBILE PMT" in csv_desc or "ONLINE PMT" in csv_desc or "CRCARDPMT" in csv_desc or "MOBILE payment" in csv_desc or "AUTOPAY payment" in csv_desc or "ONLINE payment" in csv_desc:
            result_desc = "Capital One Credit Card Payment"
    elif "CHASE" in csv_desc:
        if "CREDIT CRD EPAY" in csv_desc or "Chase Epay" in csv_desc or "CRD AUTOPAY" in csv_desc or "Payment Thank You - Web" in csv_desc:
            result_desc = "Chase Credit Card Payment"
    elif "COMED" in csv_desc:
        if "UTIL_BIL" in csv_desc or "PAYMENT" in csv_desc:
            result_desc = "ComEd Utility Bill"
    elif "PEOPLES GAS" in csv_desc:
        if "PAYMENTMEMO" in csv_desc:
            result_desc = "People's Gas Utility Bill"
    elif "25 N Bishop" in csv_desc or "Rockwell" in csv_desc:
        if "WEB PMTSMEMO" in csv_desc:
            result_desc = "25 N Bishop Rent Payment"
    
    return result_desc

def transformCategory(csv_cat, csv_desc):
    result_category = None
    
    if csv_cat == "Alcohol & Bars":
        result_category = category.objects.get(name = "Bars & Clubs")
    elif csv_cat == "Mortgage & Rent":
        result_category = category.objects.get(name = "Rent")
    elif csv_cat == "Newspapers & Magazines":
        result_category = category.objects.get(name = "Print Media")
    elif csv_cat == "Food Delivery-old":
        result_category = category.objects.get(name = "Food Delivery")
    elif csv_cat == "Performance":
        result_category = category.objects.get(name = "Mental Performance")
    elif csv_cat == "Ride Share":
        result_category = category.objects.get(name = "Ride Share & Taxi")
    elif csv_cat == "Online Subscriptions":
        if "Youtube" in csv_desc: 
            result_category = category.objects.get(name = "TV/Video Subscription")
        else:
            try: 
                result_category = category.objects.get(name = csv_cat)
            except:
                result_category = category.objects.get(name = "Undefined")    
    else:
        try: 
            result_category = category.objects.get(name = csv_cat)
        except:
            result_category = category.objects.get(name = "Undefined")

    if csv_desc == "Payment Thank You - Web":
        result_category = category.objects.get(name = "Credit Card Payment")
    
    
    return result_category
            
def setAccount(csv_account):
    selected_account = None
    print(csv_account)
    if(csv_account == "Quicksilver"):
        selected_account = account.objects.get(name = "CAPITAL ONE - Credit Card")
    elif(csv_account == "Chase Card"):
        selected_account = account.objects.get(name = "CHASE - Credit Card")
    elif(csv_account == "Premier Savings 4094"):
        selected_account = account.objects.get(name = "HUNTINGTON - Savings Account")
    elif(csv_account == "TCF FREE CHECKING"):
        selected_account = account.objects.get(name = "TCF Bank - Checking Account")
    elif(csv_account == "TCF CLASSIC SAVINGS"):
        selected_account = account.objects.get(name = "TCF Bank - Savings Account")
    elif(csv_account == "TCF POWER SAVINGS"):
        selected_account = account.objects.get(name = "TCF Bank - Savings Account")
    elif(csv_account == "HUNTINGTON - Checking Account"):
        selected_account = account.objects.get(name = "HUNTINGTON - Checking Account")
    else:
        print(csv_account)
        selected_account = account.objects.get(name = csv_account)
    
    return selected_account



    

   
