from django.db import models

# Create your models here.
class account(models.Model):
    name = models.CharField(max_length = 100, null = True, blank = True)
    displayName = models.CharField(max_length = 100, null = True, blank = True)

class theme(models.Model):
    name = models.CharField(max_length = 50, null = True, blank = True)
    

class category(models.Model):
    name = models.CharField(max_length = 50, null = True, blank = True)    
    theme = models.ForeignKey(theme, on_delete=models.CASCADE)

    def getTheme(self):
        return self.theme.name

class travelTrip(models.Model):
    name = models.CharField(max_length = 100, null = True, blank = True)
    startDate = models.DateField(null = True, blank = True)
    endDate = models.DateField(null = True, blank = True)
    totalSpent = models.DecimalField(decimal_places = 2, max_digits = 8, null = True, blank = True)
    

class transaction(models.Model):
    transactionId = models.AutoField(primary_key = True)
    date = models.DateField()
    description = models.CharField(max_length = 100)
    amount = models.DecimalField(decimal_places = 2, max_digits = 6)
    type = models.CharField(max_length=6)
    account = models.ForeignKey(account, on_delete=models.CASCADE, null = True, blank = True)
    original_description = models.CharField(max_length = 100)
    category = models.ForeignKey(category, on_delete=models.CASCADE, null = True, blank = True)
    spreadsheetThemeCategory = models.CharField(max_length = 100, null = True)
    labels = models.CharField(max_length=50, null = True, blank = True)
    notes = models.CharField(max_length = 350, null = True, blank = True)
    confirmed = models.BooleanField(default = False)
    part_of_travel_trip = models.BooleanField(default = False)
    travel_trip = models.ForeignKey(travelTrip, on_delete = models.CASCADE, null = True, blank = True)
    is_subscription = models.BooleanField(default = False)
    has_equalPaySplit = models.BooleanField(default = False)

    def displayDate(self):
        return self.date.strftime('%m/%d/%Y')

    def getThemeTotal(self, themeName, startDate, endDate):
        pass

    def getCatTotal(self, catName, themeName, startDate, endDate):
        pass


 
class equalPaySplit(models.Model):
    transactionSplit = models.ForeignKey(transaction, on_delete=models.CASCADE)
    split_length_months = models.SmallIntegerField(null = True, blank = True)

  