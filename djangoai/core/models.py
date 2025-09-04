from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Ticket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='open')  # open/closed
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
