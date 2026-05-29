from django.db import models

from .constants import CallStatus


class Call(models.Model):
    """Modelo representativo de um Chamado no banco de dados SQLite."""
    title: str = models.CharField(max_length=150, verbose_name="Título")
    description: str = models.TextField(verbose_name="Descrição")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    status: str = models.CharField(
        max_length=20,
        choices=[
            (CallStatus.PENDING, "Pendente"),
            (CallStatus.RESOLVED, "Resolvido"),
        ],
        default=CallStatus.PENDING,
        verbose_name="Status",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"

    def __str__(self) -> str:
        return f"#{self.id} — {self.title}"
