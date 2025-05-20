import google.generativeai as genai
from langchain.llms.base import LLM
from typing import Optional, List, Any
import asyncio


genai.configure(api_key="AIzaSyD5xpx54iRKW2ljyK95gFepJ7irbzhK3W8")

class GeminiLLM(LLM):
    model_name: str = "gemini-2.0-flash"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        return asyncio.run(self._acall(prompt, stop, **kwargs))

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


# Generate email content dynamically based on provided values
def generate_email_content(product_name: str, quantity: int, price: float, vendor_name: str, 
                           company_name: str, shipping_address: str, city_state_zip: str, 
                           phone_number: Optional[str], contact_name: str, contact_title: str, contact_email: str):
    # Customize this prompt to generate the required email content with dynamic placeholders
    prompt = f"""
    Generate a personalized email to a vendor named {vendor_name} regarding a new purchase order from {company_name}. 
    The product is '{product_name}', with the following details:
    - Quantity: {quantity} units
    - Price per unit: ${price}
    The total amount for this purchase order is ${quantity * price}.
    
    Please ship the order to the following address:
    {company_name}
    {shipping_address}
    {city_state_zip}
    {phone_number if phone_number else "Phone number not provided."}

    Also, mention the following contact details:
    - Name: {contact_name}
    - Title: {contact_title}
    - Email: {contact_email}

    Request the vendor to ship the order as soon as possible and provide a tracking number once the shipment has been processed.
    
    Finish the email with the message: "Thank you for your continued partnership. We look forward to receiving the order."
    """

    llm = GeminiLLM()
    email_content = llm._call(prompt)
    print(email_content)
    return email_content