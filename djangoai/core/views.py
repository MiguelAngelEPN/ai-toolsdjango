from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Customer, Ticket, Payment
from .serializers import CustomerSerializer, TicketSerializer, PaymentSerializer

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from openai import OpenAI
import json
from decimal import Decimal, InvalidOperation
import re
# Cliente OpenAI apuntando a OLLAMA local
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
#-----------------validador de decimales-------
def to_decimal(x):
    try:
        if isinstance(x, Decimal):
            return x
        if isinstance(x, (int, float)):
            return Decimal(str(x))
        if isinstance(x, str):
            # elimina todo lo que no sea dígito, punto o signo menos
            cleaned = re.sub(r'[^0-9\.\-]', '', x)
            if cleaned == '' or cleaned == '-' or cleaned == '.':
                return None
            return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return None
    return None

#----------------------------------------
@api_view(['GET'])
def get_balance(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    return Response({'customer_id': customer.id, 'name': customer.name, 'balance': str(customer.balance)})


@api_view(['POST'])
def create_ticket(request):
    """
    body: { "customer_id": 1, "subject": "X", "description": "Y" }
    """
    cid = request.data.get('customer_id')
    subject = request.data.get('subject')
    description = request.data.get('description', '')
    if not cid or not subject:
        return Response({'error': 'customer_id y subject son requeridos'}, status=400)
    customer = get_object_or_404(Customer, pk=cid)
    ticket = Ticket.objects.create(customer=customer, subject=subject, description=description)
    return Response(TicketSerializer(ticket).data, status=201)


@api_view(['POST'])
def register_payment(request):
    """
    body: { "customer_id": 1, "amount": 50.00 }
    """
    cid = request.data.get('customer_id')
    amount = request.data.get('amount')
    if not cid or not amount:
        return Response({'error': 'customer_id y amount son requeridos'}, status=400)
    customer = get_object_or_404(Customer, pk=cid)
    # registra pago y actualiza saldo
    payment = Payment.objects.create(customer=customer, amount=amount)
    customer.balance = customer.balance - float(amount)
    customer.save(update_fields=['balance'])
    return Response({
        'payment': PaymentSerializer(payment).data,
        'new_balance': str(customer.balance)
    }, status=201)


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer



#----- INTEGRACIÓN CON OLLAMA VIA SDK OPENAI  -----
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": "Consulta el saldo de un cliente por ID.",
            "parameters": {
                "type": "object",
                "properties": { "customer_id": { "type": "integer" } },
                "required": ["customer_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Crea un ticket para un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "subject": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["customer_id","subject"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_payment",
            "description": "Registra un pago y descuenta del saldo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "amount": {"type": "number"}
                },
                "required": ["customer_id","amount"]
            },
        },
    },
]

# --- Implementación real de cada herramienta ---
def tool_check_balance(customer_id: int):
    c = get_object_or_404(Customer, pk=customer_id)
    return {"customer_id": c.id, "name": c.name, "balance": float(c.balance)}

def tool_create_ticket(customer_id: int, subject: str, description: str = ""):
    customer = get_object_or_404(Customer, pk=customer_id)
    ticket = Ticket.objects.create(customer=customer, subject=subject, description=description)
    return {"id": ticket.id, "customer": customer.id, "subject": ticket.subject, "status": ticket.status}

def tool_register_payment(customer_id: int, amount):
    # amount puede venir como int/float/str -> pásalo a Decimal
    amount_dec = to_decimal(amount)
    if amount_dec is None:
        raise ValueError("amount inválido")

    customer = get_object_or_404(Customer, pk=customer_id)

    # Crea el pago con Decimal
    payment = Payment.objects.create(customer=customer, amount=amount_dec)

    # Actualiza saldo con Decimal
    customer.balance = (customer.balance or Decimal('0')) - amount_dec
    customer.save(update_fields=['balance'])

    # Para JSON simple, devuelve números primitivos
    return {
        "payment_id": payment.id,
        "new_balance": float(customer.balance),
    }



# --- Tabla de despacho nombre->función
DISPATCH = {
    "check_balance": tool_check_balance,
    "create_ticket": tool_create_ticket,
    "register_payment": tool_register_payment,
}

# Endpoint del asistente: el front le manda { "text": "..." }
@api_view(['POST'])
@csrf_exempt
def assistant(request):
    """
    Body:
    { "text": "Consulta el saldo del cliente 1 y registra un pago de 50" }
    """
    user_text = request.data.get("text", "")
    if not user_text:
        return Response({"error": "Falta 'text' en el body"}, status=400)

    # 1) Primer turno: el modelo decide si necesita llamar tools
    messages = [
        {"role": "system", "content":
         "Eres un agente de soporte para una pyme. "
         "Puedes CONSULTAR saldo, CREAR tickets y REGISTRAR pagos usando herramientas. "
         "Si te faltan datos (ID cliente, monto, asunto), pídelos. Responde en español."},
        {"role": "user", "content": user_text},
    ]

    # Uso del modelo de Ollama qwen2.5
    resp = client.chat.completions.create(
        model="qwen2.5",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = resp.choices[0].message

    tool_messages = []
    if getattr(msg, "tool_calls", None):
        # 2) Ejecutar cada tool pedida por el modelo y adjuntar los resultados
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            result = DISPATCH[name](**args)
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": json.dumps(result),
            })

        # 3) Segundo turno: devolvemos resultados de tools al modelo para que redacte la respuesta final
        messages.append({"role": "assistant", "tool_calls": msg.tool_calls})
        messages.extend(tool_messages)

        final = client.chat.completions.create(
            model="qwen2.5",
            messages=messages
        )
        answer = final.choices[0].message.content
        return Response({
            "answer": answer,
            "tool_results": [json.loads(t["content"]) for t in tool_messages]
        })

    # Si el modelo no llamó herramientas, regresamos su respuesta directa
    return Response({"answer": msg.content})