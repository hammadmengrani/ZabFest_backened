import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from database.db import cluster_results_collection
from datetime import datetime
import asyncio  # For running async code

async def get_trending_clusters(n_clusters=5):
    df = pd.read_csv(r"D:\Zab Fest Projext\backened\models\data.csv")
    df.dropna(axis=1, how='all', inplace=True)
    df_cleaned = df[['category_name_1']].dropna()
    df_cleaned['category_name_1'] = df_cleaned['category_name_1'].str.lower().str.replace(r'[^a-z\s]', '', regex=True)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df_cleaned['category_name_1'])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df_cleaned['Cluster'] = kmeans.fit_predict(X)

    def get_top_keywords(cluster, n_top_keywords=5):
        cluster_indices = df_cleaned[df_cleaned['Cluster'] == cluster].index
        X_dense = X.toarray()
        cluster_indices = cluster_indices[cluster_indices < X_dense.shape[0]]
        cluster_matrix = X_dense[cluster_indices]
        word_sums = cluster_matrix.sum(axis=0)
        top_indices = word_sums.argsort()[-n_top_keywords:][::-1]
        top_words = [vectorizer.get_feature_names_out()[i] for i in top_indices]
        return top_words

    results = []
    for i in range(n_clusters):
        try:
            top_keywords = get_top_keywords(i)

            cluster_document = {
                "keywords": top_keywords,
                "created_at": datetime.utcnow()
            }

            # ✅ Asynchronous insert
            await cluster_results_collection.insert_one(cluster_document)
            print(f"Cluster {i} stored successfully in the database.")

            results.append({
                "cluster": i,
                "keywords": top_keywords,
            })
        except Exception as e:
            print(f"Error in Cluster {i}: {e}")
            results.append({
                "cluster": i,
                "keywords": [],
                "error": str(e)
            })

    return results

# Run the async function
if __name__ == "__main__":
    asyncio.run(get_trending_clusters())
