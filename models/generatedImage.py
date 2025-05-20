from langchain.prompts import PromptTemplate
import openai
from datetime import datetime
from models.api_token import API_TOEKN

# Set your OpenAI API key
client = openai.OpenAI(api_key=API_TOEKN)

# LangChain template for marketing-style image prompt
marketing_prompt_template = PromptTemplate.from_template(
    "Create a high-quality, visually stunning marketing image for a product called '{product_name}'. "
    "The image should showcase the product in an appealing, modern, and engaging setting, emphasizing its benefits and desirability."
)

def generate_image(mode: str = "product_name", input_text: str = ""):
    """
    mode: 'product_name' or 'custom_prompt'
    input_text: product name or custom prompt depending on mode
    """
    try:
        if mode == "product_name":
            if not input_text:
                raise ValueError("Product name required for 'product_name' mode.")
            prompt = marketing_prompt_template.format(product_name=input_text)

        elif mode == "custom_prompt":
            if not input_text:
                raise ValueError("Custom prompt required for 'custom_prompt' mode.")
            prompt = input_text

        else:
            raise ValueError("Invalid mode. Use 'product_name' or 'custom_prompt'.")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        image_url = response.data[0].url
        print("✅ Image generated successfully!")
        return {
            "image_url": image_url,
            "created_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print("❌ Error generating image:", str(e))
        return None
