from django.db import models


class Node(models.Model):
    AXIOM = 'axiom'
    THEOREM = 'theorem'
    NODE_TYPE_CHOICES = [
        (AXIOM, 'Аксиома'),
        (THEOREM, 'Теорема'),
    ]

    slug = models.SlugField(max_length=100, unique=True)
    title_en = models.CharField(max_length=200, null=True, blank=True)
    title_ru = models.CharField(max_length=200, null=True, blank=True)
    node_type = models.CharField(max_length=10, choices=NODE_TYPE_CHOICES)
    level = models.PositiveIntegerField(
        help_text='0 — аксиома, 1..N — теорема (чем больше, тем сложнее)'
    )
    description_en = models.TextField(null=True, blank=True)
    description_ru = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['level', 'slug']

    def __str__(self):
        return self.title_en or self.title_ru or self.slug


class Edge(models.Model):
    from_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing')
    to_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming')

    class Meta:
        unique_together = ('from_node', 'to_node')

    def __str__(self):
        return f'{self.from_node} → {self.to_node}'
