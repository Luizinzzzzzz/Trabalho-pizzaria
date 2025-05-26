# models.py
from django.db import models
from django.utils import timezone
import json

class Sabor(models.Model):
    nome = models.CharField(max_length=100)
    ingredientes = models.TextField()  # JSON string
    preco_pequena = models.DecimalField(max_digits=8, decimal_places=2)
    preco_media = models.DecimalField(max_digits=8, decimal_places=2)
    preco_grande = models.DecimalField(max_digits=8, decimal_places=2)
    preco_familia = models.DecimalField(max_digits=8, decimal_places=2)
    ativo = models.BooleanField(default=True)
    
    def get_ingredientes(self):
        return json.loads(self.ingredientes) if self.ingredientes else []
    
    def set_ingredientes(self, lista):
        self.ingredientes = json.dumps(lista)
    
    def get_preco(self, tamanho):
        precos = {
            'Pequena': self.preco_pequena,
            'Média': self.preco_media,
            'Grande': self.preco_grande,
            'Família': self.preco_familia
        }
        return precos.get(tamanho, self.preco_media)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name_plural = "Sabores"

class Adicional(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"
    
    class Meta:
        verbose_name_plural = "Adicionais"

class Pedido(models.Model):
    TAMANHOS = [
        ('Pequena', 'Pequena'),
        ('Média', 'Média'),
        ('Grande', 'Grande'),
        ('Família', 'Família'),
    ]
    
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Em preparo', 'Em preparo'),
        ('Saiu para entrega', 'Saiu para entrega'),
        ('Entregue', 'Entregue'),
        ('Cancelado', 'Cancelado'),
    ]
    
    numero = models.AutoField(primary_key=True)
    cliente_nome = models.CharField(max_length=200)
    cliente_telefone = models.CharField(max_length=20)
    sabor = models.ForeignKey(Sabor, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=20, choices=TAMANHOS, default='Média')
    adicionais = models.ManyToManyField(Adicional, blank=True)
    observacoes = models.TextField(blank=True)
    data_hora = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def calcular_tempo_preparo(self):
        """Calcula o tempo estimado de preparo em minutos"""
        tempo_base = {
            'Pequena': 15,
            'Média': 20,
            'Grande': 25,
            'Família': 30
        }
        tempo = tempo_base.get(self.tamanho, 20)
        tempo += self.adicionais.count() * 2
        return tempo
    
    def calcular_valor_total(self):
        """Calcula o valor total do pedido"""
        valor_base = self.sabor.get_preco(self.tamanho)
        valor_adicionais = sum(adicional.preco for adicional in self.adicionais.all())
        self.valor_total = valor_base + valor_adicionais
        return self.valor_total
    
    def save(self, *args, **kwargs):
        if not self.valor_total:
            super().save(*args, **kwargs)  # Salva primeiro para ter o ID
            self.calcular_valor_total()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pedido #{self.numero} - {self.cliente_nome} - {self.sabor.nome}"
    
    class Meta:
        ordering = ['-data_hora']

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Pedido, Sabor, Adicional
import json

def home(request):
    """Página inicial com dashboard"""
    pedidos_pendentes = Pedido.objects.filter(status__in=['Pendente', 'Em preparo']).order_by('data_hora')
    pedidos_hoje = Pedido.objects.filter(data_hora__date=timezone.now().date())
    
    # Estatísticas
    total_pedidos_hoje = pedidos_hoje.count()
    faturamento_hoje = pedidos_hoje.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    pedidos_fila = pedidos_pendentes.count()
    
    context = {
        'pedidos_pendentes': pedidos_pendentes,
        'total_pedidos_hoje': total_pedidos_hoje,
        'faturamento_hoje': faturamento_hoje,
        'pedidos_fila': pedidos_fila,
    }
    
    return render(request, 'pizzaria/home.html', context)

def novo_pedido(request):
    """Página para criar novo pedido"""
    if request.method == 'POST':
        try:
            # Dados do cliente
            cliente_nome = request.POST.get('cliente_nome')
            cliente_telefone = request.POST.get('cliente_telefone')
            
            # Dados da pizza
            sabor_id = request.POST.get('sabor')
            tamanho = request.POST.get('tamanho')
            observacoes = request.POST.get('observacoes', '')
            
            # Adicionais (podem ser múltiplos)
            adicionais_ids = request.POST.getlist('adicionais')
            
            # Validações
            if not all([cliente_nome, cliente_telefone, sabor_id, tamanho]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos!')
                return redirect('novo_pedido')
            
            # Cria o pedido
            sabor = get_object_or_404(Sabor, id=sabor_id, ativo=True)
            pedido = Pedido.objects.create(
                cliente_nome=cliente_nome,
                cliente_telefone=cliente_telefone,
                sabor=sabor,
                tamanho=tamanho,
                observacoes=observacoes
            )
            
            # Adiciona os adicionais
            if adicionais_ids:
                adicionais = Adicional.objects.filter(id__in=adicionais_ids, ativo=True)
                pedido.adicionais.set(adicionais)
            
            # Calcula o valor total
            pedido.calcular_valor_total()
            pedido.save()
            
            messages.success(request, f'Pedido #{pedido.numero} criado com sucesso! Valor: R$ {pedido.valor_total:.2f}')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar pedido: {str(e)}')
    
    # GET - Exibe o formulário
    sabores = Sabor.objects.filter(ativo=True)
    adicionais = Adicional.objects.filter(ativo=True)
    
    context = {
        'sabores': sabores,
        'adicionais': adicionais,
        'tamanhos': Pedido.TAMANHOS,
    }
    
    return render(request, 'pizzaria/novo_pedido.html', context)

def fila_pedidos(request):
    """Visualiza a fila de pedidos"""
    pedidos = Pedido.objects.filter(status__in=['Pendente', 'Em preparo', 'Saiu para entrega']).order_by('data_hora')
    
    context = {
        'pedidos': pedidos,
    }
    
    return render(request, 'pizzaria/fila_pedidos.html', context)

def atualizar_status_pedido(request, pedido_id):
    """Atualiza o status de um pedido via AJAX"""
    if request.method == 'POST':
        try:
            pedido = get_object_or_404(Pedido, numero=pedido_id)
            novo_status = request.POST.get('status')
            
            if novo_status in dict(Pedido.STATUS_CHOICES):
                pedido.status = novo_status
                pedido.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Status do pedido #{pedido.numero} atualizado para {novo_status}',
                    'novo_status': novo_status
                })
            else:
                return JsonResponse({'success': False, 'message': 'Status inválido'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

def buscar_pedidos(request):
    """API para buscar pedidos"""
    termo = request.GET.get('q', '')
    
    if termo:
        pedidos = Pedido.objects.filter(
            Q(numero__icontains=termo) |
            Q(cliente_nome__icontains=termo) |
            Q(cliente_telefone__icontains=termo) |
            Q(sabor__nome__icontains=termo)
        ).order_by('-data_hora')[:20]
    else:
        pedidos = Pedido.objects.all().order_by('-data_hora')[:20]
    
    pedidos_data = []
    for pedido in pedidos:
        adicionais = [adicional.nome for adicional in pedido.adicionais.all()]
        
        pedidos_data.append({
            'numero': pedido.numero,
            'cliente': pedido.cliente_nome,
            'telefone': pedido.cliente_telefone,
            'sabor': pedido.sabor.nome,
            'tamanho': pedido.tamanho,
            'adicionais': adicionais,
            'valor_total': str(pedido.valor_total),
            'status': pedido.status,
            'data_hora': pedido.data_hora.strftime('%d/%m/%Y %H:%M'),
            'tempo_preparo': pedido.calcular_tempo_preparo()
        })
    
    return JsonResponse({
        'pedidos': pedidos_data,
        'total': len(pedidos_data)
    })

def detalhes_pedido(request, pedido_id):
    """Exibe detalhes de um pedido específico"""
    pedido = get_object_or_404(Pedido, numero=pedido_id)
    
    context = {
        'pedido': pedido,
        'tempo_preparo': pedido.calcular_tempo_preparo(),
        'ingredientes': pedido.sabor.get_ingredientes(),
    }
    
    return render(request, 'pizzaria/detalhes_pedido.html', context)

def cardapio(request):
    """Gerencia o cardápio"""
    sabores = Sabor.objects.filter(ativo=True)
    adicionais = Adicional.objects.filter(ativo=True)
    
    context = {
        'sabores': sabores,
        'adicionais': adicionais,
    }
    
    return render(request, 'pizzaria/cardapio.html', context)

def relatorio_vendas(request):
    """Gera relatório de vendas"""
    # Período padrão: últimos 7 dias
    data_fim = timezone.now()
    data_inicio = data_fim - timedelta(days=7)
    
    # Se há parâmetros de data, usa eles
    if request.GET.get('data_inicio'):
        try:
            data_inicio = timezone.datetime.strptime(request.GET.get('data_inicio'), '%Y-%m-%d')
            data_inicio = timezone.make_aware(data_inicio)
        except:
            pass
    
    if request.GET.get('data_fim'):
        try:
            data_fim = timezone.datetime.strptime(request.GET.get('data_fim'), '%Y-%m-%d')
            data_fim = timezone.make_aware(data_fim.replace(hour=23, minute=59, second=59))
        except:
            pass
    
    # Filtra pedidos do período
    pedidos = Pedido.objects.filter(
        data_hora__range=(data_inicio, data_fim),
        status='Entregue'
    )
    
    # Estatísticas gerais
    total_pedidos = pedidos.count()
    faturamento_total = pedidos.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    
    # Sabores mais vendidos
    sabores_populares = pedidos.values('sabor__nome').annotate(
        quantidade=Count('sabor')
    ).order_by('-quantidade')[:5]
    
    # Tamanhos mais vendidos
    tamanhos_populares = pedidos.values('tamanho').annotate(
        quantidade=Count('tamanho')
    ).order_by('-quantidade')
    
    # Adicionais mais pedidos
    adicionais_populares = Adicional.objects.filter(
        pedido__in=pedidos
    ).annotate(
        quantidade=Count('pedido')
    ).order_by('-quantidade')[:5]
    
    context = {
        'data_inicio': data_inicio.date(),
        'data_fim': data_fim.date(),
        'total_pedidos': total_pedidos,
        'faturamento_total': faturamento_total,
        'sabores_populares': sabores_populares,
        'tamanhos_populares': tamanhos_populares,
        'adicionais_populares': adicionais_populares,
    }
    
    return render(request, 'pizzaria/relatorio.html', context)

def get_preco_sabor(request, sabor_id):
    """API para obter preços de um sabor"""
    try:
        sabor = get_object_or_404(Sabor, id=sabor_id, ativo=True)
        precos = {
            'Pequena': str(sabor.preco_pequena),
            'Média': str(sabor.preco_media),
            'Grande': str(sabor.preco_grande),
            'Família': str(sabor.preco_familia),
        }
        
        return JsonResponse({
            'success': True,
            'precos': precos,
            'ingredientes': sabor.get_ingredientes()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# urls.py
from django.urls import path
from . import views

app_name = 'pizzaria'

urlpatterns = [
    path('', views.home, name='home'),
    path('novo-pedido/', views.novo_pedido, name='novo_pedido'),
    path('fila/', views.fila_pedidos, name='fila_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    path('cardapio/', views.cardapio, name='cardapio'),
    path('relatorio/', views.relatorio_vendas, name='relatorio_vendas'),
    
    # APIs
    path('api/pedidos/', views.buscar_pedidos, name='buscar_pedidos'),
    path('api/pedido/<int:pedido_id>/status/', views.atualizar_status_pedido, name='atualizar_status'),
    path('api/sabor/<int:sabor_id>/precos/', views.get_preco_sabor, name='get_preco_sabor'),
]