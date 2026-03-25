from django.db import models


class Node(models.Model):
    AXIOM = 'axiom'
    THEOREM = 'theorem'
    NODE_TYPE_CHOICES = [
        (AXIOM, 'Аксиома'),
        (THEOREM, 'Теорема'),
    ]

    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    node_type = models.CharField(max_length=10, choices=NODE_TYPE_CHOICES)
    level = models.PositiveIntegerField(
        help_text='0 — аксиома, 1..N — теорема (чем больше, тем сложнее)'
    )
    description = models.TextField(
        help_text='Markdown-текст с доказательством. Математика в формате $...$ и $$...$$'
    )

    class Meta:
        ordering = ['level', 'title']

    def __str__(self):
        return self.title


class Edge(models.Model):
    from_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing')
    to_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming')

    class Meta:
        unique_together = ('from_node', 'to_node')

    def __str__(self):
        return f'{self.from_node} → {self.to_node}'
