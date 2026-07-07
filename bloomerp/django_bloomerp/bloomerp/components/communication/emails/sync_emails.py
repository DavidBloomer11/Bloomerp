from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from typing import TYPE_CHECKING
from bloomerp.celery.utils import is_celery_available
from bloomerp.communication.emails.actions import sync_emails_for_folder
from bloomerp.router import router
from bloomerp.utils.async_utils import run_async_or_sync
from bloomerp.utils.requests import render_blank_form
from django import forms
from django.urls import reverse

if TYPE_CHECKING:
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder


class SyncEmailsForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Start Date",
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="End Date",
    )
    


@router.register(
    path="components/communication/sync_emails/<str:folder>",
    url_name="components_sync_emails"
)
@login_required
def sync_emails(request: HttpRequest, folder: "str | InboxFolder") -> HttpResponse:
    from bloomerp.communication.utils.resolver import resolve_item
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
    
    folder = resolve_item(folder, target=InboxFolder)
    
    text = "Synchronize your emails starting from the specified date range. Please select the start and end dates for synchronization."
    if not is_celery_available():
        text += " Note: Celery is not available in the current environment. Email synchronization may not work as expected." 
    
    btn_text = "Sync Emails"
    btn_args = {
        "bloomerp-close-modal" : "bloomerp-general-use-modal",
    }
    
    if request.method == "GET":
        return render_blank_form(
            request=request,
            form=SyncEmailsForm(),
            url=reverse(
                "components_sync_emails",
                args=[folder.id],
            ),
            text=text,
            submit_label=btn_text,
            button_attrs=btn_args
        )
    if request.method == "POST":
        form = SyncEmailsForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")
            # Implement the logic to sync emails based on the provided dates
            ran_async, result = run_async_or_sync(
                sync_emails_for_folder,
                folder=folder,
                from_date=start_date,
                to_date=end_date
            )
            if ran_async:
                pass
            
            return HttpResponse(f"Synced {result} emails from {start_date} to {end_date}")
        else:
            return render_blank_form(
                request=request,
                form=form,
                url=reverse(
                    "components_sync_emails",
                    args=[folder.id],
                ),
                text=text,
                submit_label=btn_text,
                button_attrs=btn_args
            )
            
    
    
