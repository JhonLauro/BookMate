"""
Custom email backend using Brevo API instead of SMTP.
This works on Render.com free tier which blocks SMTP ports.
"""
import os
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


class BrevoAPIBackend(BaseEmailBackend):
    """
    Email backend that uses Brevo's API to send emails.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        
        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY', '')
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of sent messages.
        """
        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        return num_sent
    
    def _send(self, email_message):
        """
        Send a single email message.
        """
        if not email_message.recipients():
            return False
        
        try:
            # Debug logging
            print(f"[Brevo Backend] Sending email:")
            print(f"  Subject: {email_message.subject}")
            print(f"  From: {email_message.from_email or settings.DEFAULT_FROM_EMAIL}")
            print(f"  To: {email_message.to}")
            print(f"  Content type: {email_message.content_subtype}")
            
            # Prepare sender
            from_email = email_message.from_email or settings.DEFAULT_FROM_EMAIL
            sender = {"email": from_email}
            
            # Extract name from "Name <email>" format if present
            if '<' in from_email:
                name_part = from_email.split('<')[0].strip()
                email_part = from_email.split('<')[1].replace('>', '').strip()
                sender = {"name": name_part, "email": email_part}
            
            # Prepare recipients
            to = [{"email": recipient} for recipient in email_message.to]
            
            # Django password reset sends plain text emails, convert to HTML for better rendering
            body_content = email_message.body
            
            # Prepare email based on content type
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject=email_message.subject,
            )
            
            # Set content based on type
            if email_message.content_subtype == 'html':
                send_smtp_email.html_content = body_content
            else:
                # For plain text, also set as text_content
                send_smtp_email.text_content = body_content
                # Also convert to simple HTML for better rendering
                send_smtp_email.html_content = body_content.replace('\n', '<br>')
            
            # Add CC if present
            if email_message.cc:
                send_smtp_email.cc = [{"email": recipient} for recipient in email_message.cc]
            
            # Add BCC if present
            if email_message.bcc:
                send_smtp_email.bcc = [{"email": recipient} for recipient in email_message.bcc]
            
            # Send email via Brevo API
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            print(f"  ✅ Brevo API Response: {api_response}")
            return True
            
        except ApiException as e:
            print(f"  ❌ Brevo API Error: {e}")
            if not self.fail_silently:
                raise
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if not self.fail_silently:
                raise
            return False
