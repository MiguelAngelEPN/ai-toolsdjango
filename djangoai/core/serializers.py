from rest_framework import serializers
from .models import Customer, Ticket, Payment

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'balance']

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'customer', 'subject', 'description', 'status', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'customer', 'amount', 'created_at']
