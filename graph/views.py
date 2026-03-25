from django.shortcuts import render
from django.http import JsonResponse
from .models import Node, Edge


def index(request):
    return render(request, 'graph/index.html')


def graph_data(request):
    nodes = [
        {
            'id': node.pk,
            'slug': node.slug,
            'title': {'en': node.title_en, 'ru': node.title_ru},
            'description': {'en': node.description_en, 'ru': node.description_ru},
            'node_type': node.node_type,
            'level': node.level,
        }
        for node in Node.objects.all()
    ]
    edges = [
        {
            'source': edge.from_node_id,
            'target': edge.to_node_id,
        }
        for edge in Edge.objects.all()
    ]
    return JsonResponse({'nodes': nodes, 'edges': edges})
