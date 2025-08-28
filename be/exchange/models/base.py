"""
Base models for exchange app
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from banking.models.base import TimestampedModel


class ExchangeBaseModel(TimestampedModel):
    """Base model for exchange entities"""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True
        
    def get_audit_fields(self) -> dict:
        """Get audit fields for logging"""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }