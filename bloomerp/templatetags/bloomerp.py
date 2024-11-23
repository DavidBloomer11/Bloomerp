from django import template
from django.db.models.manager import Manager
from django.db.models import Model
from bloomerp.utils.models import model_name_plural_underline, get_model_dashboard_view_url, get_list_view_url
from django.urls import reverse 
from django.contrib.contenttypes.models import ContentType
from bloomerp.models import Link, Widget
from django.utils.safestring import mark_safe
import uuid
from bloomerp.models import Bookmark, User

register = template.Library()

@register.filter(name='get_field_value')
def get_field_value(obj:Model, field_name:str):
    """
    Custom template filter to get the value of a field by its name.
    
    Example usage:
    {{ object|get_field_value:field_name }}

    """
    if '.' in field_name:
        attributes = field_name.split('.')
        value = obj
        for attribute in attributes:
            try:
                value = getattr(value, attribute)
            except Exception as e:
                return e
        return value
    try:
        return getattr(obj, field_name)
    except Exception as e:
        return e

from django.contrib.contenttypes.models import ContentType
@register.filter(name='get_foreign_key_value')
def get_foreign_key_value(obj:Model,field_name):
    '''
    
    '''

    try:
        resp = ''

        value = getattr(obj, field_name)
        if isinstance(value, Manager):
            qs = value.all()

            if not qs:
                return 'None'

            content_type_id = ContentType.objects.get_for_model(qs.model).pk
      

            resp += f'<a href="/simple-list-view/?content_type_id={content_type_id}&field_name={obj._meta.model_name}&field_value={obj.pk}">'
            for item in qs[:2]:
                resp+= item.__str__() + ', '
            resp += '... </a>'
            return resp
        else:
            try:
                return f'<a href="{value.get_absolute_url()}">{value}</a>'
            except:
                return value
    except Exception as e:
        return e

@register.filter(name='get_dict_value')
def get_dict_value(dictionary:dict, key:str):
    '''
    Returns the value of a key in a dictionary.

    Example usage:
    {{ dictionary|get_dict_value:key }}
    '''

    return dictionary.get(key)

@register.filter
def model_name(obj:Model):
    '''
    Returns the model name of an object.

    Example usage:
    {{ object|model_name }}
    
    '''
    return obj._meta.model_name

@register.filter
def model_name_plural(obj:Model):
    '''
    Returns the model verbose name of an object.

    Example usage:
    {{ object|model_name_plural }}
    
    '''
    return obj._meta.verbose_name_plural

@register.filter
def model_dashboard_url(content_type:ContentType):
    '''
    Returns the model app dashboard URL of an object.

    Example usage:
    {{ object|model_app_dashboard_url }}
    
    '''
    return reverse(get_model_dashboard_view_url(content_type.model_class()))

@register.filter
def model_name_plural_from_content_type(content_type:ContentType):
    '''
    Returns the model verbose name of an object.

    Example usage:
    {{ object|model_name_plural }}
    
    '''
    return content_type.model_class()._meta.verbose_name_plural

@register.filter
def length(obj) -> int:
    '''
    Returns the length of an object.

    Example usage:
    {{ object|length }}
    
    '''
    return len(obj)

@register.filter
def percentage(value, arg):
    try:
        value = int(value) / int(arg)
        return value*100
    except (ValueError, ZeroDivisionError):
        return None
    
@register.filter
def get_link_by_id(id:int):
    '''
    Returns the link object with the given id.

    Example usage:
    {{ id|get_link }}

    or 

    {% with id|get_link as link %}
    {% if link %}
    {{ link.name }}
    {% endif %}
    {% endwith %}

    '''
    try:
        return Link.objects.get(pk=id)
    except:
        return None
    
@register.filter
def get_widget_by_id(id:int):
    '''
    Returns the widget object with the given id.

    Example usage:
    {{ id|get_widget }}

    or 

    {% with id|get_widget as widget %}
    {% if widget %}
    {{ widget.name }}
    {% endif %}
    {% endwith %}

    '''
    try:
        return Widget.objects.get(pk=id)
    except:
        return None
    

@register.inclusion_tag('snippets/breadcrumb.html')
def breadcrumb(title:str, model:Model):
    '''
    Returns a breadcrumb navigation.

    Example usage:
    {% breadcrumb links %}
    '''
    list_view_url = get_list_view_url(model)
    model_name_plural = model._meta.verbose_name_plural.title()

    return {
        'title' : title,
        'list_view_url' : list_view_url,
        'model_name_plural' : model_name_plural	
    }
    
@register.inclusion_tag('snippets/workspace_item.html')
def workspace_item(item:dict):
    '''
    Returns a workspace item.

    Example usage:
    {% workspace_item item %}
    '''
    # generate random id for each item
    item['id'] = uuid.uuid4()

    return {'item': item}


@register.simple_tag(name='render_link')
def render_link(link_id:int):
    '''
    Returns a link object.

    Example usage:
    {% render_link link_id %}
    '''
    try:
        link = Link.objects.get(pk=link_id)
        if link.is_external_url():
            return mark_safe(f'<a link-id="{link.pk}" class="pointer text-primary link-item" href="https://{link.url}" target="_blank">{link.name}</a>')
        elif link.is_absolute_url:
            return mark_safe(f'<a link-id="{link.pk}" class="pointer text-primary link-item" hx-get="{link.url}" hx-target="#main-content" hx-push-url="true">{link.name}</a>')
        elif not link.requires_args():
            return mark_safe(f'<a link-id="{link.pk}" class="pointer text-primary link-item" hx-get="{reverse(link.url)}" hx-target="#main-content" hx-push-url="true">{link.name}</a>')
        else:
            return mark_safe("<p>Link requires arguments</p>")
    except:
        return mark_safe("<p>Link not found</p>")

@register.inclusion_tag('components/bookmark.html')
def render_bookmark(object:Model, user:User, size:int, target:str):
    '''
    Returns a bookmark object.

    Example usage:
    {% render_bookmark object user size target %}
    '''
    # Get the content_type_id and object_id from the request
    content_type_id = ContentType.objects.get_for_model(object).pk
    
    # Check if the bookmark allready exists
    bookmarked = Bookmark.objects.filter(user=user, content_type_id=content_type_id, object_id=object.pk).exists()

    return {
        'bookmarked': bookmarked,
        'content_type_id': content_type_id,
        'object_id': object.pk,
        'target' : target,
        'size': size
    }
