"""
Base models for portfolio app
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from banking.models.base import TimestampedModel