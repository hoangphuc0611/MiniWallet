from django.contrib import admin
from api.models import Customer,Wallet,Withdrawal,Deposit


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    pass
@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    pass
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    pass