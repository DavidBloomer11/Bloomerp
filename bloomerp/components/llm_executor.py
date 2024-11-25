from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from bloomerp.utils.llm import BloomerpOpenAI
from bloomerp.models import ApplicationField
from django.contrib.auth.decorators import login_required
from django.conf import settings

@login_required
@route('llm_executor')
def llm_executor(request:HttpRequest) -> HttpResponse:
    '''
    Component to execute LLM queries.
    '''
    query_type = request.GET.get('llm_query_type', None)
    query = request.GET.get('llm_query', None)
    llm_query_types = ['sql', 'document_template', 'tiny_mce_content']
    
    if not query:
        return HttpResponse('No llm query provided')

    if query_type not in llm_query_types:
        return HttpResponse('Invalid llm query type, must be one of: ' + ', '.join(llm_query_types))

    # Get the OpenAI key from the settings
    openai_key = settings.BLOOMERP_SETTINGS.get('OPENAI_API_KEY', None)
    if not openai_key:
        return HttpResponse('OpenAI key not found in settings')

    # Init the OpenAI class
    openai = BloomerpOpenAI(openai_key)

    # Check if the key is valid
    if not openai.is_valid_key():
        return HttpResponse('Invalid OpenAI key')


    if query_type == 'sql':
        db_tables_and_columns = ApplicationField.get_db_tables_and_columns()
        sql_query = openai.create_sql_query(query, db_tables_and_columns)
        return HttpResponse(sql_query)
    
    elif query_type == 'document_template':
        return HttpResponse('Document template AI is not implemented yet')
    elif query_type == 'tiny_mce_content':
        tiny_mce_content = openai.create_tiny_mce_content(query)
        return HttpResponse(tiny_mce_content)
