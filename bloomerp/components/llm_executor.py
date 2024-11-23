from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from bloomerp.utils.llm import BloomerpOpenAI
from bloomerp.models import ApplicationField
from django.contrib.auth.decorators import login_required

@login_required
@route('llm_executor')
def llm_executor(request:HttpRequest) -> HttpResponse:
    '''
    Component to execute LLM queries.
    '''

    query_type = request.GET.get('llm_query_type', 'sql')
    query = request.GET.get('llm_query', None)

    llm_query_types = ['sql', 'document_template']

    if not query:
        return HttpResponse('No llm query provided')

    if query_type not in llm_query_types:
        return HttpResponse('Invalid llm query type, must be one of: ' + ', '.join(llm_query_types))

    # Init the OpenAI class
    openai = BloomerpOpenAI()

    # Check if the key is valid
    if not openai.is_valid_key():
        return HttpResponse('Invalid OpenAI key')


    if query_type == 'sql':
        db_tables_and_columns = ApplicationField.get_db_tables_and_columns()
        sql_query = openai.create_sql_query(query, db_tables_and_columns)
        return HttpResponse(sql_query)
    
    elif query_type == 'document_template':
        
        return HttpResponse('Document template AI is not implemented yet')

    context = {}
    return render(request, 'components/llm_executor.html', context)