# Bloomerp API

The Bloomerp API leverages Django REST Framework to automatically generate RESTful endpoints for all models defined within your application. This integration allows for seamless CRUD (Create, Read, Update, Delete) operations on your models without the need for extensive manual setup.

## How It Works with Models

When you define a model in your Bloomerp application, the `generate_serializer` and `generate_model_viewset_class` functions in `bloomerp/utils/api.py` dynamically create corresponding serializers and viewsets. These are then registered with the router to expose API endpoints.

## Example: Creating a Model and Its API

### 1. Define the Model

Create a new model in your Django app that inherits from `BloomerpModel`.

```python
# sales/models.py
from django.db import models
from bloomerp.models import BloomerpModel

class Category(BloomerpModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    string_search_fields = ['name', 'description']
    allow_string_search = True
```

### 2. Accessing the API Endpoints

After setting up the models, the following API endpoints will become automaticaly available:

- **List Categories**: `GET /api/categories/`
- **Create Category**: `POST /api/categories/`
- **Retrieve Category**: `GET /api/categories/{id}/`
- **Update Category**: `PUT /api/categories/{id}/`
- **Partial Update**: `PATCH /api/categories/{id}/`
- **Delete Category**: `DELETE /api/categories/{id}/`

### 3. Example Requests

- **Create a New Category**

    ```sh
    POST /api/categories/
    Content-Type: application/json

    {
        "name": "Electronics",
        "description": "Devices and gadgets."
    }
    ```

- **Retrieve a Category**

    ```sh
    GET /api/categories/1/
    ```

- **Update a Category**

    ```sh
    PUT /api/categories/1/
    Content-Type: application/json

    {
        "name": "Electronics and Gadgets",
        "description": "Updated description."
    }
    ```

## Authentication and Permissions

Bloomerp integrates with Django's authentication system. Ensure that appropriate permissions are set for your API endpoints to secure access.

## Django Rest Framework

Bloomerp utilizes Django Rest Framework to construct it's APIs. For more information, refer to [django-rest-framework](https://www.django-rest-framework.org/).



