from google.generativeai import GenerativeModel, configure
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Step 1: Configure Gemini
configure(api_key="AIzaSyD5xpx54iRKW2ljyK95gFepJ7irbzhK3W8")

# Step 2: Define Gemini LLM
class GeminiLLM(LLM):
    model_name: str = "gemini-2.0-flash"

    def _call(self, prompt: str, stop: list = None, **kwargs) -> str:
        model = GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text

    @property
    def _llm_type(self) -> str:
        return "google_gemini"

# Step 3: LangChain Prompt
template = """
You are a professional market analyst in Pakistan, reporting current product trends based on latest consumer behavior, market demand, and social media activity. 

Based on the following keywords: {keywords}, provide a detailed list of **top trending products** in Pakistan **right now**. 

For each product, include:
1. **Product Name**
2. **Short Description**
3. **Why it's trending (e.g. demand, seasonal relevance, influencer marketing, etc.)**
4. **A user review summary (2-3 lines based on online reviews)**
5. **Average rating (out of 5 stars)**
6. **Google Trend Values for 2024-2025 in axis x and y to plot line chart based on 12 months**
7. **Google Trend for 2024-2025 based on region only in pakistan**
8. **Product cost**
9. **Selling cost**
10. **Shipping cost**
11. **Tax cost**
12. **Discount cost. this cost should be less than 25% of the product cost**
13. **Product quantity: min: 1, max:100 make it random from given min and max**



List at least 8 products and rating should be atleast 4.5. Keep the tone informative, realistic, and current. Do not include any introduction or disclaimer. Start directly with the product list.
data format will be in JSON format.
Make sure to include the following keys in the JSON response:
- product_name
- short_description
- trending_reason
- user_review_summary
- average_rating
- google_trend
- google_trend_region
- product_cost
- shipping_cost
- discount_cost
- tax_cost
- product_quantity

Only product title in product name.
"""


prompt = PromptTemplate(
    input_variables=["keywords"],
    template=template
)

llm = GeminiLLM()
llm_chain = LLMChain(llm=llm, prompt=prompt)

# ✅ Clean callable function
def get_trending_products_from_gemini(keyword: str) -> str:
    response = llm_chain.run({"keywords": keyword})
    return response
