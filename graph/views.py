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
            'title': node.title,
            'node_type': node.node_type,
            'level': node.level,
            'description': node.description,
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
