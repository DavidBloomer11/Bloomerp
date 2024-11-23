from bloomerp.models import (
    DocumentTemplate,
    File)
from bloomerp.utils.pdf import generate_pdf
from django.db.models import Model
from django.core.files.base import ContentFile
from django.template import engines
from django.template.loader import render_to_string

class DocumentController:
    def __init__(self) -> None:
        pass

    def create_document(
            self,
            template:DocumentTemplate, 
            instance:Model, 
            free_variables: dict=None
        ):
        ''' Creates a document for a particular template, using the model variable and the free variables:
            - Template : The document template
            - Instance : The model instance
            - Free variables : A dictionary of free variables

        '''
        data = {}

        data['object'] = instance
    	
        #Add free variable data
        data.update(free_variables)

        #Create metadata variable
        meta_data = {}
        meta_data['document_template'] = template.pk

        meta_data['signed'] = False
        
        #Format HTML       
        django_engine = engines["django"]
        temp = django_engine.from_string(template.template)
        formatted_html = temp.render(data)        

        document_bytes = generate_pdf(
            html_content=formatted_html,
            css_content=template.styling.styling,
        )
    
        content_file = ContentFile(document_bytes)
        
        file_object = File()
        
        #Save the file
        file_object.file.save(template.name + ' ' + str(instance) + '.pdf', content_file)

        file_object.name = template.name + ' ' + str(instance)
        file_object.content_object = instance

        #Save metadata
        file_object.meta = meta_data

        file_object.save()
        
    def create_preview_document(
            self,
            template:DocumentTemplate,
            data:dict
        ) -> ContentFile:
        ''' Creates a preview document for a particular template, using the model variable and the free variables:
            - Template : The document template
            - Data : A dictionary of free variables
        '''
        #Format HTML
        django_engine = engines["django"]
        temp = django_engine.from_string(template.template)
        formatted_html = temp.render(data)
        
        document_bytes = generate_pdf(
            html_content=formatted_html,
            css_content=template.styling.styling,
        )

        content_file = ContentFile(document_bytes)

        return content_file



    def send_signature_request(
            self,
            requested_by:int,
            file_id: int,
            requested_for = None,
            requested_for_email = None,
        ):
        '''
        Sends a signature request to someone.
        '''
        #Get file
        file = File.objects.get(pk=int(file_id))
        '''
        if requested_for_email:
            #Email given
            signature_request = SignatureRequest(
                requested_by=User.objects.get(pk=int(requested_by)),
                requested_for_email=requested_for_email,
                file = file
            )
            email = requested_for_email
        else:
            #User given
            requested_for_user = User.objects.get(pk=int(requested_for))

            signature_request = SignatureRequest(
                requested_by=User.objects.get(pk=int(requested_by)),
                requested_for=requested_for_user,
                file = File.objects.get(pk=int(file_id))
            )
            email = requested_for_user.email
        signature_request.save()
        
        #Send notification
        NotificationController.create_notification_from_signature_request(signature_request)
        '''

    def sign_pdf(self, pdf_file : File, signature_bytes):
        '''
        Function that will sign a pdf file, using signature bytes.
        '''
        file_path = pdf_file.file.path

        meta_data = {
            'signed' : True
        }
        '''
        handler = PdfHandler(file_path)

        #Sign the actual document and retreive the bytes
        document_bytes = handler.sign_pdf(
            signature_path=None,
            signature_bytes= signature_bytes
        )
        content_file = ContentFile(document_bytes)
        
        signed_file_obj = File()

        #Save the file
        signed_file_obj.file.save(pdf_file.name + '- signed' '.pdf', content_file)

        signed_file_obj.name = pdf_file.name + ' - signed'
        signed_file_obj.content_object = pdf_file.content_object
        
        signed_file_obj.meta = {'signed':True}
        signed_file_obj.save()
        
        pdf_file.meta = {'signed_file_id':signed_file_obj.pk}
        pdf_file.save()

        return signed_file_obj
        '''

        
         


        


        