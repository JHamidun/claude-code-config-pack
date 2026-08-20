---
name: pinecone
description: "Pinecone vector DB (PINECONE_API_KEY): semantic search, RAG; индексы company-<name>-bot и др. Триггеры: «векторная база», «семантический поиск»."
---

# Pinecone Vector Database Skill

## Overview

Expert skill for using Pinecone - the leading vector database for AI applications, semantic search, and RAG systems.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: PINECONE_API_KEY
PINECONE_API_KEY=os.getenv('PINECONE_API_KEY')
```

## Существующие индексы

| Индекс | Описание |
|--------|----------|
| `company-tm-bot` | Company TM бот |
| `company-plus-bot` | Company Plus бот |
| `agent-dev` | Разработка агентов |
| `chatbot-data` | Данные чатбота |
| `test-index` | Тестовый |

**Параметры:** Dimension 3072 (OpenAI text-embedding-3-large), Metric cosine, Serverless AWS us-east-1

## When to Use Pinecone

**Best for:**
- Semantic search
- RAG (Retrieval Augmented Generation)
- Recommendation systems
- Similarity matching
- Knowledge base indexing
- Document search
- Image/audio similarity

**Advantages:**
- Serverless infrastructure
- Integrated embedding models
- Real-time updates
- Metadata filtering
- Hybrid search (semantic + keyword)
- Scales to billions of vectors

## Dependencies

```bash
pip install pinecone
```

## Basic Usage

### Setup Client

```python
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
```

### Create Serverless Index

```python
def create_index(name: str, dimension: int = 3072, metric: str = "cosine"):
    """
    Create a new serverless index.

    Args:
        name: Index name
        dimension: Vector dimension (3072 — канон живых индексов, text-embedding-3-large;
                   1536 для text-embedding-3-small, 768 for many others)
        metric: "cosine", "euclidean", or "dotproduct"
    """
    from pinecone import ServerlessSpec

    pc.create_index(
        name=name,
        dimension=dimension,
        metric=metric,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    return pc.Index(name)

# Usage (3072 = канон живых индексов проекта)
index = create_index("my-knowledge-base", dimension=3072)
```

### Create Index with Integrated Embeddings

```python
def create_index_with_embeddings(name: str, embed_model: str = "multilingual-e5-large"):
    """
    Create index with integrated embedding model.

    Models:
        - multilingual-e5-large (1024 dim, 100+ languages)
        - llama-text-embed-v2 (1024 dim)
        - pinecone-sparse-english-v0 (sparse)
    """
    from pinecone import ServerlessSpec

    pc.create_index(
        name=name,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        embedding={
            "model": embed_model,
            "field_map": {"text": "text"}
        }
    )

    return pc.Index(name)
```

### Upsert Vectors

```python
def upsert_vectors(index_name: str, vectors: list):
    """
    Upsert vectors with metadata.

    vectors format:
        [{"id": "doc1", "values": [...], "metadata": {...}}, ...]
    """
    index = pc.Index(index_name)

    index.upsert(
        vectors=vectors,
        namespace="default"
    )

    return len(vectors)

# Example with embeddings
import openai

def embed_and_upsert(index_name: str, texts: list, ids: list, metadata: list = None):
    """Embed texts and upsert to Pinecone."""

    # Get embeddings from OpenAI
    client = openai.OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    vectors = []
    for i, embedding in enumerate(response.data):
        vectors.append({
            "id": ids[i],
            "values": embedding.embedding,
            "metadata": metadata[i] if metadata else {"text": texts[i]}
        })

    index = pc.Index(index_name)
    index.upsert(vectors=vectors)

    return len(vectors)
```

### Query (Semantic Search)

```python
def query_index(index_name: str, query_vector: list, top_k: int = 10,
                filter: dict = None, include_metadata: bool = True):
    """
    Query index for similar vectors.

    Args:
        query_vector: Query embedding
        top_k: Number of results
        filter: Metadata filter
        include_metadata: Include metadata in results
    """
    index = pc.Index(index_name)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        filter=filter,
        include_metadata=include_metadata,
        namespace="default"
    )

    return results.matches

# Example with text query
def search_similar(index_name: str, query_text: str, top_k: int = 10):
    """Search for similar documents by text."""

    # Get query embedding
    client = openai.OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query_text]
    )
    query_vector = response.data[0].embedding

    return query_index(index_name, query_vector, top_k)
```

### Query with Integrated Embeddings

```python
def search_text(index_name: str, query: str, top_k: int = 10):
    """
    Search using integrated embeddings (no external embedding needed).

    Works with indexes created with embedding parameter.
    """
    index = pc.Index(index_name)

    results = index.query(
        data=query,  # Text query, not vector
        top_k=top_k,
        include_metadata=True
    )

    return results.matches
```

### Metadata Filtering

```python
def search_with_filter(index_name: str, query_vector: list, filters: dict):
    """
    Search with metadata filters.

    Filter examples:
        {"category": "tech"}
        {"price": {"$lt": 100}}
        {"tags": {"$in": ["python", "ai"]}}
        {"$and": [{"category": "tech"}, {"status": "active"}]}
    """
    index = pc.Index(index_name)

    results = index.query(
        vector=query_vector,
        top_k=10,
        filter=filters,
        include_metadata=True
    )

    return results.matches

# Filter operators:
# $eq - equal
# $ne - not equal
# $gt, $gte - greater than
# $lt, $lte - less than
# $in, $nin - in/not in array
# $and, $or - logical operators
```

### Hybrid Search (Semantic + Keyword)

```python
def hybrid_search(index_name: str, query: str, top_k: int = 10, alpha: float = 0.5):
    """
    Hybrid search combining semantic and keyword search.

    alpha: Weight for semantic (1.0 = all semantic, 0.0 = all keyword)
    """
    index = pc.Index(index_name)

    # Requires index with both dense and sparse embeddings
    results = index.query(
        data=query,
        top_k=top_k,
        include_metadata=True,
        sparse_vector=True  # Enable sparse matching
    )

    return results.matches
```

### Fetch Vectors by ID

```python
def fetch_by_ids(index_name: str, ids: list):
    """Fetch specific vectors by IDs."""

    index = pc.Index(index_name)

    results = index.fetch(ids=ids, namespace="default")

    return results.vectors
```

### Update Metadata

```python
def update_metadata(index_name: str, id: str, metadata: dict):
    """Update metadata for a vector."""

    index = pc.Index(index_name)

    index.update(
        id=id,
        set_metadata=metadata,
        namespace="default"
    )
```

### Delete Vectors

```python
def delete_vectors(index_name: str, ids: list = None, filter: dict = None,
                   delete_all: bool = False):
    """
    Delete vectors.

    Can delete by:
        - IDs
        - Metadata filter
        - All (delete_all=True)
    """
    index = pc.Index(index_name)

    if delete_all:
        index.delete(delete_all=True, namespace="default")
    elif filter:
        index.delete(filter=filter, namespace="default")
    elif ids:
        index.delete(ids=ids, namespace="default")
```

### Index Statistics

```python
def get_stats(index_name: str):
    """Get index statistics."""

    index = pc.Index(index_name)
    stats = index.describe_index_stats()

    return {
        "total_vector_count": stats.total_vector_count,
        "dimension": stats.dimension,
        "namespaces": stats.namespaces
    }
```

### List Indexes

```python
def list_indexes():
    """List all indexes."""

    return [index.name for index in pc.list_indexes()]
```

## Namespaces

Namespaces allow partitioning data within an index:

```python
# Upsert to specific namespace
index.upsert(vectors=vectors, namespace="documents")
index.upsert(vectors=vectors, namespace="images")

# Query specific namespace
results = index.query(vector=query, namespace="documents")

# Delete from namespace
index.delete(ids=ids, namespace="documents")
```

## Embedding Models

| Model | Dimensions | Languages |
|-------|------------|-----------|
| text-embedding-3-small (OpenAI) | 1536 | Multi |
| text-embedding-3-large (OpenAI) | 3072 | Multi |
| multilingual-e5-large (Pinecone) | 1024 | 100+ |
| llama-text-embed-v2 (Pinecone) | 1024 | English |

## API Pricing

| Tier | Price | Storage |
|------|-------|---------|
| Starter | Free | 100K vectors |
| Standard | $0.33/GB/hour | Unlimited |
| Enterprise | Custom | Custom |

## Quick Reference

| Task | Code |
|------|------|
| Create index | `pc.create_index(name, dimension, metric, spec)` |
| Get index | `pc.Index(name)` |
| Upsert | `index.upsert(vectors)` |
| Query | `index.query(vector, top_k)` |
| Fetch | `index.fetch(ids)` |
| Delete | `index.delete(ids)` |
| Stats | `index.describe_index_stats()` |

## Tips

1. **Dimension** - должен совпадать с моделью embeddings
2. **Namespaces** - для разделения данных в одном индексе
3. **Metadata** - храни текст для retrieval
4. **Batch upsert** - до 100 векторов за раз
5. **Integrated embeddings** - не нужен внешний API
6. **Hybrid search** - лучше для text retrieval
7. **Cosine** - лучший metric для normalized embeddings
