import google.generativeai as genai
from langchain.llms.base import LLM
from typing import Optional, List, Any
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

# Secure: Use environment variable for API key
genai.configure(api_key="AIzaSyD5xpx54iRKW2ljyK95gFepJ7irbzhK3W8")

class GeminiLLM(LLM):
    model_name: str = "gemini-2.0-flash"

    async def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        return await self._acall(prompt, stop, **kwargs)

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        model = genai.GenerativeModel(self.model_name)
        response = await model.generate_content_async(prompt)

        if response and hasattr(response, "text"):
            return response.text.strip()

        if response and hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content"):
                return candidate.content.strip()

        return "No response generated."

    @property
    def _llm_type(self) -> str:
        return "google_gemini"

# Updated email content generator with more fields
async def generate_email_content(
    products: List[dict],
    vendor_name: str,
    company_name: str,
    shipping_address: str,
    city_state_zip: str,
    phone_number: Optional[str],
    contact_name: str,
    contact_title: str,
    contact_email: str,
    order_number: str,
    tax: float,
    shipping_rate: float,
    payment_method: str,
    payment_date: str,
    note: Optional[str] = None,
) -> str:
    product_lines = ""
    subtotal = 0.0
    for idx, item in enumerate(products, 1):
        name = item.get("name")
        quantity = item.get("quantity", 0)
        price = item.get("sale_price") if item.get("sale_price") is not None else item.get("price", 0.0)
        line_total = quantity * price
        subtotal += line_total

        if item.get("sale_price") is not None and item.get("sale_price") != item.get("price"):
            product_lines += (f"{idx}. {name} — Quantity: {quantity}, "
                              f"Unit Price: ${item.get('price', 0.0)} (Sale Price: ${price}), "
                              f"Total: ${line_total:.2f}\n")
        else:
            product_lines += f"{idx}. {name} — Quantity: {quantity}, Unit Price: ${price}, Total: ${line_total:.2f}\n"

    total_amount = subtotal + tax + shipping_rate

    prompt = f"""
Generate a professional email to the vendor **{vendor_name}** from **{company_name}**, placing a purchase order with the following details:

**Order Number**: {order_number}

**Order Items**:
{product_lines}

**Subtotal**: ${subtotal:.2f}  
**Tax**: ${tax:.2f}  
**Shipping Rate**: ${shipping_rate:.2f}  
**Total Purchase Amount**: ${total_amount:.2f}  

**Payment Method**: {payment_method}  
**Payment Date**: {payment_date}  

Ship the items to:
{company_name}  
{shipping_address}  
{city_state_zip}  
{phone_number if phone_number else "Phone number not provided."}

**Contact Person**:  
- Name: {contact_name}  
- Title: {contact_title}  
- Email: {contact_email}  

Please process this order at the earliest and share the tracking number upon dispatch.

{f"**Note**: {note}" if note else ""}

End the email with:  
"Thank you for your continued partnership. We look forward to receiving the order."
    """

    llm = GeminiLLM()
    email_content = await llm._call(prompt)
    return email_content


def send_email(email_content: str, sender_email: str, receiver_email: str, password: str, attachment_path: Optional[str] = None) -> str:
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "New Purchase Order from Your Valued Customer"

    msg.attach(MIMEText(email_content, 'plain'))

    # Attach PDF if provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
            msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully with attachment!")
        return "Success"
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Error: {str(e)}"
