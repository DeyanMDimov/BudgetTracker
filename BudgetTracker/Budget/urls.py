from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('importData/', views.importTx, name='importTx'),
    path('viewTx/', views.viewTx, name="viewTx"),
    path('viewSummary/', views.viewSummary, name="viewSummary"),
    path('cleanse/', views.cleanseForPublic, name="cleanseForPublic"),
    path('equalPay/', views.equalPay, name="equalPay"),
    path('ajax/confirmTx/', views.confirmTx, name="confirmTx"),
    path('ajax/getCats/', views.getCorrectCategories, name="getCorrectCategories"),
    path('ajax/getTx/', views.getTxDetailsForEdit, name="getTxDetails"),
    path('ajax/submitTxChanges/', views.saveTxChanges, name="saveTxChanges"),
    path('ajax/submitTxSplit/', views.saveTxSplit, name="saveTxSplit"),
    path('ajax/deleteTx/', views.deleteTx, name="deleteTx"),
    path('ajax/getOptionsForNewTx/', views.getOptionsForNewTx, name="setupNewTx"),
    path('ajax/saveNewTx/', views.saveNewTx, name="saveNewTx"),
    path('ajax/setEqualPayPromo/', views.setEqualPayPromo, name="setEqualPayPromo"),
    
    
    #path('ajax/connectToLink/', views.create_link_token, name="getLinkToken"),
    #path('fullTeamStats/', views.fullTeamStats, name="fullTeamStats")
]