import uuid 
import strawberry
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import bcrypt
from database.db import user_collection, user_helper, chat_collection, product_helper,product_collection, store_collection, store_helper, image_generation_collection, image_helper,cluster_results_collection,email_generation_collection,email_helper
from models.generatedImage import generate_image
from gemini import get_trending_products_from_gemini
from mail import generate_email_content, send_email
import random
import string
from models.po import add_name_only
from models.GPT import ask_gemini, genrate_chat_topic


@strawberry.type
class QuestionResponse:
    id: str
    email: str
    question: str
    answer: str
    date: str   
    time: str
    chat_id: str  
    is_delete:bool
    prompt: str  

@strawberry.type
class Chat:
    chat_id: str
    email: str
    topic: str

@strawberry.input
class ProductInput:
    name: str
    quantity: int
    price: float
    sale_price: float


@strawberry.type
class StoreType:
    id: str
    store_name: str
    owner_name: str
    email: str
    category: List[str]
    created_at: Optional[datetime] = None

@strawberry.type
class StoreDashboardType:
    store_name: str
    owner_name: str
    email: str
    category: List[str]

# image generation input
@strawberry.input
class ImagePromptInput:
    prompt: Optional[str] = None
    product_name: Optional[str] = None
    mode: Optional[str] = None  # Add this line


# Image Data Type for image generation
@strawberry.type
class GeneratedImageType:
    id: str
    email: str
    image_url: str
    prompt: str
    # created_at: datetime
    
# Cluster Result Type    
@strawberry.type
class ClusterResult:
    keywords: List[str]
    trending_products: Optional[str] = None
    error: Optional[str] = None


#email generation
@strawberry.type
class GeneratedEmailType:
    id: str
    email: str
    brand: str
    generated_email: str
    attachment: Optional[str] = "N/A"
    created_at: Optional[datetime] = None


@strawberry.type
class ProductType:
    id: str
    title: str
    short_description: Optional[str]
    description: str
    category: Optional[List[str]]
    price: int
    sale_price: Optional[int]
    stock: int
    sku: str
    image_url: Optional[str]
    published: bool
    variations: Optional[List[str]]
    multi_images: Optional[List[str]]  
    brand: Optional[str]  # ✅ Add this line



@strawberry.type
class Mutation:

    @strawberry.mutation
    async def register_store(
        self,
        store_name: str,
        owner_name: str,
        email: str,
        password: str,
        category: List[str]  # <-- replaced 'niches' with 'category'
    ) -> StoreType:
        # Check if store already exists
        existing = await store_collection.find_one({"email": email})
        if existing:
            raise Exception("Store with this email already exists.")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create the new store document
        new_store = {
            "store_name": store_name,
            "owner_name": owner_name,
            "email": email,
            "password": hashed_password,
            "category": category,
            "created_at": datetime.utcnow(),
        }

        # Insert the store document into the database
        result = await store_collection.insert_one(new_store)
        created_store = await store_collection.find_one({"_id": result.inserted_id})

        return StoreType(**store_helper(created_store))

    @strawberry.mutation
    async def login_store(self, email: str, password: str) -> Optional[StoreDashboardType]:
        store = await store_collection.find_one({"email": email})
        if not store:
            raise Exception("Store not found with this email.")

        stored_password = store["password"]
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            raise Exception("Invalid password.")

        return StoreDashboardType(
            store_name=store["store_name"],
            owner_name=store["owner_name"],
            email=store["email"],
            category=store.get("category", [])
        )

    @strawberry.mutation
    async def generate_and_store_image(
        self,
        email: str,
        input: ImagePromptInput,
    ) -> GeneratedImageType:

        if not input.prompt and not input.product_name:
            raise Exception("Either 'prompt' or 'product_name' must be provided.")

        mode = input.mode if input.mode in ["product_name", "custom_prompt"] else "product_name"
        input_text = input.product_name if mode == "product_name" else input.prompt

        result = generate_image(mode=mode, input_text=input_text)

        if result:
            image_url = result.get("image_url")
            if not image_url:
                raise Exception("Image URL not returned from generation function.")

            image_document = {
                "email": email,
                "prompt": input_text,
                "image_url": image_url,
                "created_at": result.get("created_at"),
            }

            image_result = await image_generation_collection.insert_one(image_document)
            generated_image = await image_generation_collection.find_one({"_id": image_result.inserted_id})
            image_help = image_helper(generated_image)

            return GeneratedImageType(
                id=image_help["id"],
                email=image_help["email"],
                prompt=image_help["prompt"],
                image_url=image_help["image_url"],
            )
        else:
            raise Exception("Failed to generate the image.")


    @strawberry.mutation
    async def generate_send_store_email(
        self,
        email: str,  # receiver email
        brand: str,
        products: List[ProductInput],
        vendor_name: str,
        company_name: str,
        shipping_address: str,
        city_state_zip: str,
        tax: float,
        shipping_rate: float,
        payment_method: str,
        payment_date: str,
        note: Optional[str] = None,
        phone_number: Optional[str] = None,
        contact_name: str = "",
        contact_title: str = "",
        contact_email: str = "",
    ) -> GeneratedEmailType:

        SENDER_EMAIL = "hammadmengrani05@gmail.com"
        SENDER_PASSWORD = "aotb wakh kpsq twuf"

        # Generate order number
        order_number = ''.join(random.choices(string.digits, k=10))

        product_dicts = [product.__dict__ for product in products]

        # Generate email content asynchronously
        email_content = await generate_email_content(
            products=product_dicts,
            vendor_name=vendor_name,
            company_name=company_name,
            shipping_address=shipping_address,
            city_state_zip=city_state_zip,
            phone_number=phone_number,
            contact_name=contact_name,
            contact_title=contact_title,
            contact_email=contact_email,
            order_number=order_number,
            tax=tax,
            shipping_rate=shipping_rate,
            payment_method=payment_method,
            payment_date=payment_date,
            note=note,
        )

        # Generate PDF in memory using po.py function
        pdf_stream = add_name_only(
            name=vendor_name,
            title=contact_title,
            phone=phone_number or "",
            email=contact_email or "",
            address=shipping_address,
            date=payment_date,
            po_number=order_number,
            products=product_dicts,
            tax=f"{tax:.2f}",
            shipping=f"{shipping_rate:.2f}",
            payment_method=payment_method,
            payment_date=payment_date,
            notes=note or "",
        )

        # Define a fixed output PDF filename (relative or absolute path)
        output_pdf_path = "purchase_order.pdf"

        # Write the in-memory PDF bytes to disk
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_stream.read())

        # Send email with PDF attachment (pass the file path)
        send_result = send_email(
            email_content=email_content,
            sender_email=SENDER_EMAIL,
            receiver_email=email,
            password=SENDER_PASSWORD,
            attachment_path=output_pdf_path,
        )

        if send_result.startswith("Error"):
            raise Exception(send_result)

        # Save email generation record to DB
        email_doc = {
            "email": email,
            "brand": brand,
            "generated_email": email_content,
            "attachment": output_pdf_path,
            "created_at": datetime.utcnow(),
        }

        result = await email_generation_collection.insert_one(email_doc)
        saved_email = await email_generation_collection.find_one({"_id": result.inserted_id})

        return GeneratedEmailType(**email_helper(saved_email))


    @strawberry.mutation
    async def add_product(
        self,
        title: str,
        short_description: Optional[str],
        description: str,
        price: int,
        sale_price: Optional[int] = None,
        stock: int = 0,
        sku: str = "",
        image_url: Optional[str] = None,
        published: bool = True,
        variations: Optional[List[str]] = None,
        multi_images: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        brand: Optional[str] = None,  # ✅ Add this line
    ) -> ProductType:
        new_product = {
            "title": title,
            "short_description": short_description,
            "description": description,
            "price": price,
            "sale_price": sale_price,
            "stock": stock,
            "sku": sku,
            "image_url": image_url,
            "published": published,
            "variations": variations or [],
            "multi_images": multi_images or [],
            "category": category or [],
            "brand": brand  # ✅ Add this line
        }
        result = await product_collection.insert_one(new_product)
        product = await product_collection.find_one({"_id": result.inserted_id})
        return ProductType(**product_helper(product))
    
    @strawberry.mutation
    async def ask_gemini(self, email: str, question: str, chat_id: str) -> QuestionResponse:
        now = datetime.now()
        answer = ""
        if chat_id == "new":
            chat_id = f"{str(uuid.uuid4())}"
            topic = await genrate_chat_topic(question)
            await chat_collection.insert_one({
                "email": email, 
                "chat_id": chat_id,
                "createdAt": now,
                "is_delete":False,
                "topic": topic  # ✅ Default topic
            })
        message_count = await user_collection.find({"chat_id": chat_id}).to_list()
        if len(message_count) >= 100:
            return QuestionResponse(id="", email=email, question=question, answer="⚠️ Chat limit reached. Start a new chat.", date="", time="", chat_id=chat_id)
        
        # Gemini se response lein
        answer = await ask_gemini(question)

        # Check if the answer is a dictionary and extract the result
        if isinstance(answer, dict) and 'result' in answer:
            answer = answer['result']  # Return only the 'result' field

        new_entry = await user_collection.insert_one({
            "email": email,
            "question": question,
            "answer": answer,
            "createdAt": now,
            "chat_id": chat_id,
            "prompt": "",
            "is_delete": False,
        })
        created_question = await user_collection.find_one({"_id": new_entry.inserted_id})
        return QuestionResponse(**user_helper(created_question)) 





# Query class to fetch stores by email
@strawberry.type
class Query:

    @strawberry.field
    async def get_questions(self, email: str, chat_id: str) -> List[QuestionResponse]:
        """Retrieve all questions for a specific user in a specific chat."""
        questions = []
        async for user in user_collection.find({"email": email, "chat_id": chat_id}):  # 🆕 Chat ID filter
            questions.append(QuestionResponse(**user_helper(user)))
        return questions

    @strawberry.field
    async def get_chats(self, email: str) -> List[Chat]:
        """Retrieve all chats for a user."""
        chats = []
        async for chat in chat_collection.find({"email": email,"is_delete":False}).sort({"createdAt":-1}):
            chats.append(Chat(chat_id=chat["chat_id"], email=chat["email"], topic=chat.get("topic", "Untitled Chat")))
        return chats

    @strawberry.field
    async def get_store_by_email(self, email: str) -> Optional[StoreType]:
        store = await store_collection.find_one({"email": email})
        if not store:
            return None
        return StoreType(**store_helper(store))
    
    @strawberry.field
    async def get_trending_products(self, email: str, keywords: list[str]) -> ClusterResult:
        try:
            keyword_str = ", ".join(keywords)
            trending_products = get_trending_products_from_gemini(keyword_str)

            return ClusterResult(
                keywords=keywords,
                trending_products=trending_products
            )

        except Exception as e:
            return ClusterResult(
                keywords=keywords,
                error=str(e)
            )


    @strawberry.field
    async def get_products(self) -> List[ProductType]:
        products = []
        async for product in product_collection.find():
            products.append(ProductType(**product_helper(product)))
        return products
    
    
    @strawberry.field
    async def get_products_by_brand(self, brand: str) -> List[ProductType]:
        products = []
        async for product in product_collection.find({"brand": brand}):
            products.append(ProductType(**product_helper(product)))
        return products
    

# Create the schema with both Query and Mutation
schema = strawberry.Schema(query=Query, mutation=Mutation)
