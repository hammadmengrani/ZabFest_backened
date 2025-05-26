from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = "mongodb+srv://hammadmengrani05:zgHTJ7ug0qfsJsQH@zabfest.brf4gwu.mongodb.net/"
DB_NAME = "marketplace"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Store collection
store_collection = db["stores"]

# Image generation collection
image_generation_collection = db["generated_images"]

cluster_results_collection = db["cluster_results"]

# Email generation collection
email_generation_collection = db["generated_emails"]

product_collection = db["products"]

user_collection = db["user_data"]
chat_collection = db["chats"]


# Helpers
def store_helper(store) -> dict:
    return {
        "id": str(store["_id"]),
        "store_name": store["store_name"],
        "owner_name": store["owner_name"],
        "email": store["email"],
        "category": store.get("category", []),
        "created_at": store.get("created_at"),
    }


def image_helper(image) -> dict:
    return {
        "id": str(image["_id"]),
        "email": image["email"],
        "prompt": image["prompt"],
        "image_url": image["image_url"],  # base64 string
        "created_at": image.get("created_at"),
    }

# Helper for Cluster Results
def cluster_helper(cluster) -> dict:
    return {
        "cluster_id": str(cluster["_id"]),  # Convert MongoDB ObjectId to string
        "keywords": cluster["keywords"],
        "created_at": cluster.get("created_at"),
    }

def email_helper(email_doc) -> dict:
    return {
        "id": str(email_doc["_id"]),
        "email": email_doc["email"],
        "brand": email_doc["brand"],
        "generated_email": email_doc["generated_email"],
        "attachment": email_doc.get("attachment", "N/A"),
        "created_at": email_doc.get("created_at"),
    }

def product_helper(product) -> dict:
    return {
        "id": str(product["_id"]),
        "title": product["title"],
        "short_description": product.get("short_description"),
        "description": product["description"],
        "category": product.get("category", []),
        "price": product["price"],
        "sale_price": product.get("sale_price"),
        "stock": product["stock"],
        "sku": product["sku"],
        "image_url": product.get("image_url"),
        "multi_images": product.get("multi_images", []),  # Multi-images list added
        "published": product["published"],
        "variations": product.get("variations", []),
        "brand": product.get("brand")  # Brand name added
    }

def user_helper(user) -> dict:
    return {
        "id": str(user.get("_id", "")),
        "email": user.get("email", ""),
        "question": user.get("question", ""),
        "answer": user.get("answer", ""),
        "date": user.get("date", ""),
        "time": user.get("time", ""),
        "chat_id": user.get("chat_id", ""),
        "prompt":user.get("prompt", []),
        "is_delete": False,
    }