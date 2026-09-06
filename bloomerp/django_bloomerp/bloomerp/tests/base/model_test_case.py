from typing import Type

from django.test import TestCase
from django.db import models

class BloomerpModelTestCase(TestCase):
    model : Type[models.Model]
    
    