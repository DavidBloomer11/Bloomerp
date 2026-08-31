from bloomerp.router import router
from bloomerp.views.generic.markdown import MarkdownView

@router.route(
    "test-view"
)
class TestView(MarkdownView):
    markdown_file = "test.md"
    
    
    
    
    
    
    
    
