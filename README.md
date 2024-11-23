# bloomerp
Bloomerp is an open source Business Management Software framework that let's you create a fully functioning business management applications by just defining the database models. 
In it's core, it uses the popular Python framework Django and HTMX to provide a robust and quick application.

## Features
Bloomerp is comprised of various features.
- Intuitive CRUD views with integrated access controll provided by Django
- List views that offer advanced filtering capabilities
- Intuitive PDF generation system for model objects that let's you easily define templates like contracts, 
- Intuitive dashboarding capabilities based on SQL queries
- Integration with LLMs to create SQL queries
- Bulk upload's for models
- REST Api's for all models using django-rest-framework
- Intuitive file system UI including folder structures
- Bookmarking system to track bookmarked objects for users
- Comment system that let's you comment on certain objects

## Getting started
You can start using the Bloomerp framework in a few simple steps:
1. Install Django and the Bloomerp framework
2. Setup project by defining settings in your Django application
3. Start defining your models

### Install Django, Bloomerp, and start a project
First, start by installing Django.
```sh
pip install django
```
Next, you need to install the Bloomerp framework.
```sh
pip install bloomerp
```

### Setup project
Once you have installed the necessary dependencies, it's time to start creating our new project. 

For the purpose of this tutorial let's imagine building a sales application. The data needs to be tracked are products, sales and customers. We'll start by creating our Django project.

Creating the Django project.
```sh
django-admin startproject core
```

Creating the Django app.
```sh
django-admin startapp sales
```

Once we have done the above, we have to go into core/settings.py to setup a few things.


```python
#settings.py
from bloomerp.config import BLOOMERP_APPS, BLOOMERP_MIDDLEWARE, BLOOMERP_USER_MODEL
from bloomerp.models import User

# Setup installed apps
INSTALLED_APPS = [
    ...
    'sales'
    # Any other installed app
]
INSTALLED_APPS += BLOOMERP_APPS

# Setup middleware
MIDDLEWARE = [
    ...
]
MIDDLEWARE += BLOOMERP_MIDDLEWARE

# Setup user
AUTH_USER_MODEL = BLOOMERP_USER_MODEL

# Setup crispy (Bloomerp uses django-crispy-forms)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Setup Bloomerp settings
BLOOMERP_SETTINGS = {
    "globals" : {
        "organization_name": "FooBar",
    },
    "BASE_URL": "", # The base url of the application
    "ROUTERS" : [
        ...
        # More on routers later, we can leave it blank for now.
    ],
}

```

Once we have got our settings configured, we can go ahead and make our migrations.
```sh
python manage.py migrate
```

### Create your models
Let's start defining some basic models for our sales application. As was noted before, we'll have to define three basic models for this example.
```python
from django.db import models
from bloomerp.models import BloomerpModel
from bloomerp.models.fields import BloomerpFileField
from django.utils import timezone

class Customer(BloomerpModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

class Product(BloomerpModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = BloomerpFileField(allowed_extensions=['.jpg', '.jpeg', '.png'])
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Order(BloomerpModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    date = models.DateField(default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='pending')
```

Now that we have our models defined, we first have to make the neccessary migrations:

```sh
python manage.py makemigrations sales
python manage.py migrate sales
```

Additionally, we want to store the application fields that will be used throughout the application. Note that we have to run this command every time we update our data models in order to make sure the application runs smoothly. For that, we can use the following command:
```sh
python manage.py save_application_fields
```

Let's also create a superuser to login.
```sh
python manage.py createsuperuser
```

Finally, we are ready to startup our server.
```sh
python manage.py runserver
```


## Roadmap
Although significant effort has been made to make Bloomerp to work as it does today, it still remains a work-in-progress project. The following list comprises of things that are expected to be done in the future:

- Write more tests to make the application more robust for errors
- ...
