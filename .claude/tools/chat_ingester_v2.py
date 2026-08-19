#!/usr/bin/env python3
"""
Chat History Ingester V2 - улучшенная версия с:
- Multilingual embeddings (sentence-transformers)
- Извлечение кода отдельно
- Auto-tagging контента
- Дедупликация
- Knowledge extraction

Использование:
    python chat_ingester_v2.py scan
    python chat_ingester_v2.py ingest [--limit N] [--force]
    python chat_ingester_v2.py search "query" [--type code|error|learning]
    python chat_ingester_v2.py extract-knowledge
    python chat_ingester_v2.py dedupe
"""

import json
import sys
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional
from collections import defaultdict

# Справка печатается ДО тяжёлых импортов: chromadb тянет opentelemetry и на
# неполной установке падает трассировкой ещё на `--help`. Постороннему это
# выглядит как сломанный инструмент, хотя сломано окружение.
if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help")):
    print(__doc__)
    sys.exit(0)

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:  # ImportError и поломки транзитивных зависимостей
    print("ERROR: нужен chromadb (legacy-путь векторной памяти): pip install chromadb", file=sys.stderr)
    print(f"  {e}", file=sys.stderr)
    sys.exit(1)

# Try to use sentence-transformers for better embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    USE_CUSTOM_EMBEDDINGS = True
    print("[INFO] Using multilingual sentence-transformers")
except ImportError:
    USE_CUSTOM_EMBEDDINGS = False
    print("[INFO] Using ChromaDB default embeddings")

# Paths
CHATS_DIR = Path.home() / ".claude" / "projects"
MEMORY_DIR = Path.home() / ".claude" / "memory"
VECTOR_DB_PATH = MEMORY_DIR / "vector_db_v2"

# Config
CHUNK_SIZE = 800  # smaller chunks for better precision
OVERLAP = 100
MIN_CONTENT_LENGTH = 50
CODE_MIN_LENGTH = 30


def get_client():
    """Get ChromaDB client."""
    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(VECTOR_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )


def get_embedding_function():
    """Get custom embedding function if available."""
    if USE_CUSTOM_EMBEDDINGS:
        from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

        class MultilingualEmbedding(EmbeddingFunction):
            def __call__(self, input: Documents) -> Embeddings:
                return EMBEDDING_MODEL.encode(input).tolist()

            @staticmethod
            def name() -> str:
                return "multilingual-MiniLM-L12-v2"

        return MultilingualEmbedding()
    return None


def get_collection(client, name="chat_history_v2"):
    """Get or create collection."""
    ef = get_embedding_function()
    if ef:
        return client.get_or_create_collection(
            name=name,
            embedding_function=ef,
            metadata={"description": "Claude Code chat history with multilingual embeddings"}
        )
    return client.get_or_create_collection(
        name=name,
        metadata={"description": "Claude Code chat history"}
    )


def detect_content_type(text: str) -> str:
    """Detect content type: code, error, question, discussion, learning, decision."""
    text_lower = text.lower()

    # Check for code patterns
    code_patterns = [
        r'```[\w]*\n',  # Code blocks
        r'def \w+\(',   # Python functions
        r'function \w+\(',  # JS functions
        r'class \w+[:\(]',  # Classes
        r'import \w+',   # Imports
        r'from \w+ import',
        r'const \w+ =',  # JS/TS
        r'let \w+ =',
        r'async def',
        r'await ',
    ]
    for pattern in code_patterns:
        if re.search(pattern, text):
            return "code"

    # Check for errors
    error_patterns = [
        r'error:',
        r'exception:',
        r'traceback',
        r'failed',
        r'ошибка',
        r'не работает',
        r'сломалось',
        r'баг',
        r'\[error\]',
        r'api error',
    ]
    for pattern in error_patterns:
        if re.search(pattern, text_lower):
            return "error"

    # Check for questions
    if '?' in text and len(text) < 500:
        return "question"

    # Check for learnings/decisions
    learning_patterns = [
        r'важно:',
        r'запомни',
        r'нужно использовать',
        r'лучше использовать',
        r'правильный способ',
        r'решение:',
    ]
    for pattern in learning_patterns:
        if re.search(pattern, text_lower):
            return "learning"

    decision_patterns = [
        r'решил использовать',
        r'выбрал',
        r'буду использовать',
        r'архитектура:',
    ]
    for pattern in decision_patterns:
        if re.search(pattern, text_lower):
            return "decision"

    return "discussion"


def extract_code_blocks(text: str) -> list[dict]:
    """Extract code blocks with language detection."""
    code_blocks = []

    # Markdown code blocks
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    for lang, code in matches:
        if len(code.strip()) >= CODE_MIN_LENGTH:
            code_blocks.append({
                "language": lang or "unknown",
                "code": code.strip(),
                "type": "code_block"
            })

    # Inline code with context
    inline_pattern = r'`([^`]+)`'
    inline_matches = re.findall(inline_pattern, text)
    for code in inline_matches:
        if len(code) >= 20 and ' ' not in code:  # Likely a command or variable
            code_blocks.append({
                "language": "inline",
                "code": code,
                "type": "inline_code"
            })

    return code_blocks


def extract_errors(text: str) -> list[dict]:
    """Extract error messages and their context."""
    errors = []

    # Common error patterns
    patterns = [
        r'(Error|Exception|Traceback)[:\s]+([^\n]+(?:\n[^\n]+){0,5})',
        r'(API Error)[:\s]+(\{[^}]+\})',
        r'(ошибка|error)[:\s]+([^\n]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            error_type, error_text = match
            errors.append({
                "type": error_type,
                "message": error_text.strip()[:500]
            })

    return errors


def extract_topics(text: str) -> list[str]:
    """Extract main topics from text."""
    topics = set()

    # Tech keywords
    tech_keywords = [
        'python', 'javascript', 'typescript', 'react', 'fastapi', 'django',
        'telegram', 'bot', 'api', 'database', 'postgresql', 'mongodb', 'redis',
        'docker', 'kubernetes', 'aws', 'gcp', 'azure',
        'chromadb', 'vector', 'embedding', 'llm', 'gpt', 'claude',
        'authentication', 'oauth', 'jwt', 'webhook', 'websocket',
        'n8n', 'automation', 'workflow',
        'html', 'css', 'презентация', 'slides',
        'heygen', 'elevenlabs', 'deepgram', 'tts', 'stt',
    ]

    text_lower = text.lower()
    for keyword in tech_keywords:
        if keyword in text_lower:
            topics.add(keyword)

    return list(topics)[:10]  # Limit to 10 topics


def smart_chunk(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Smart chunking that respects sentence boundaries."""
    # Split by sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence.split())

        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    # Filter too small chunks
    return [c for c in chunks if len(c) >= MIN_CONTENT_LENGTH]


def compute_doc_id(content: str, source: str = "") -> str:
    """Generate unique document ID."""
    hash_input = f"{content[:200]}{source}"
    return f"v2_{hashlib.md5(hash_input.encode()).hexdigest()[:16]}"


def find_all_chats() -> list[Path]:
    """Find all JSONL chat files."""
    if not CHATS_DIR.exists():
        return []
    return list(CHATS_DIR.rglob("*.jsonl"))


def parse_chat_file(file_path: Path) -> Optional[dict]:
    """Parse a single chat JSONL file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        if not content.strip():
            return None

        raw_lines = []
        for line in content.strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    raw_lines.append(data)
                except json.JSONDecodeError:
                    continue

        if not raw_lines:
            return None

        # Extract text content - handle both formats
        texts = []
        roles = []
        timestamp = ""

        for line_data in raw_lines:
            # Get timestamp from first line with it
            if not timestamp and 'timestamp' in line_data:
                timestamp = line_data['timestamp']

            # Format 1: message is nested inside 'message' key
            msg = line_data.get('message', line_data)

            role = msg.get('role', 'unknown')
            msg_content = msg.get('content')

            if msg_content and isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text = item.get('text', '')
                        # Skip system messages and tool results
                        if text and not text.startswith('<ide_') and not text.startswith('<system'):
                            texts.append(text)
                            roles.append(role)
            elif msg_content and isinstance(msg_content, str):
                # Simple string content
                if not msg_content.startswith('<'):
                    texts.append(msg_content)
                    roles.append(role)

        if not texts:
            return None

        full_text = '\n\n'.join(texts)

        return {
            'file': str(file_path),
            'timestamp': timestamp,
            'date': timestamp[:10] if timestamp else '',
            'messages': texts,
            'roles': roles,
            'full_text': full_text,
            'message_count': len(texts),
            'code_blocks': extract_code_blocks(full_text),
            'errors': extract_errors(full_text),
            'topics': extract_topics(full_text)
        }
    except Exception as e:
        return None


def scan_chats():
    """Scan and report statistics."""
    files = find_all_chats()
    print(f"\n📂 Chat files found: {len(files)}")

    total_size = sum(f.stat().st_size for f in files if f.exists())
    print(f"💾 Total size: {total_size / 1024 / 1024:.1f} MB")

    # Sample analysis
    topic_counts = defaultdict(int)
    type_counts = defaultdict(int)
    code_count = 0
    error_count = 0

    for f in files[:200]:  # Sample
        parsed = parse_chat_file(f)
        if parsed:
            for topic in parsed['topics']:
                topic_counts[topic] += 1
            code_count += len(parsed['code_blocks'])
            error_count += len(parsed['errors'])
            content_type = detect_content_type(parsed['full_text'])
            type_counts[content_type] += 1

    print(f"\n📊 Sample analysis (200 files):")
    print(f"   Code blocks: {code_count}")
    print(f"   Errors found: {error_count}")

    print(f"\n🏷️  Top topics:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"   {topic}: {count}")

    print(f"\n📁 Content types:")
    for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {ctype}: {count}")

    # Check existing
    client = get_client()
    collection = get_collection(client)
    print(f"\n🗄️  Already in vector DB v2: {collection.count()}")


def ingest_chats(limit: int = None, force: bool = False):
    """Ingest chat history with smart processing."""
    files = find_all_chats()

    # Sort by modification time (newest first)
    files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

    if limit:
        files = files[:limit]

    client = get_client()
    collection = get_collection(client)

    # Get existing IDs
    existing_ids = set()
    if not force:
        try:
            result = collection.get()
            existing_ids = set(result['ids']) if result['ids'] else set()
        except:
            pass

    print(f"\n🚀 Ingesting {len(files)} chat files...")
    print(f"⏭️  Skipping {len(existing_ids)} existing documents")

    stats = {"ingested": 0, "skipped": 0, "code": 0, "errors": 0}

    for i, file_path in enumerate(files):
        if (i + 1) % 50 == 0:
            print(f"   Progress: {i + 1}/{len(files)} | Ingested: {stats['ingested']}")

        parsed = parse_chat_file(file_path)
        if not parsed or len(parsed['full_text']) < MIN_CONTENT_LENGTH:
            stats['skipped'] += 1
            continue

        # Chunk and process main content
        chunks = smart_chunk(parsed['full_text'])

        for j, chunk in enumerate(chunks):
            doc_id = compute_doc_id(chunk, parsed['file'])

            if doc_id in existing_ids:
                continue

            content_type = detect_content_type(chunk)
            topics = extract_topics(chunk)

            try:
                collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "type": content_type,
                        "source": "chat_history",
                        "file": parsed['file'][-100:],  # Last 100 chars
                        "date": parsed['date'],
                        "topics": ",".join(topics),
                        "chunk_index": j
                    }],
                    ids=[doc_id]
                )
                stats['ingested'] += 1
            except Exception as e:
                if stats['errors'] < 3:
                    print(f"[ERROR] {e}")
                stats['errors'] += 1

        # Index code blocks separately
        for k, code_block in enumerate(parsed['code_blocks']):
            if len(code_block['code']) < CODE_MIN_LENGTH:
                continue

            code_id = compute_doc_id(code_block['code'], f"code_{k}")
            if code_id in existing_ids:
                continue

            try:
                collection.add(
                    documents=[code_block['code']],
                    metadatas=[{
                        "type": "code",
                        "source": "code_extraction",
                        "language": code_block['language'],
                        "date": parsed['date'],
                        "file": parsed['file'][-100:]
                    }],
                    ids=[code_id]
                )
                stats['code'] += 1
            except:
                pass

    print(f"\n✅ Done!")
    print(f"   Text chunks: {stats['ingested']}")
    print(f"   Code blocks: {stats['code']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Total in DB: {collection.count()}")


def search_history(query: str, n_results: int = 10, content_type: str = None):
    """Search with optional type filter."""
    client = get_client()
    collection = get_collection(client)

    where_filter = {}
    if content_type:
        where_filter["type"] = content_type

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter if where_filter else None
    )

    print(f"\n🔍 Search results for: '{query}'")
    if content_type:
        print(f"   Filter: type={content_type}")
    print()

    if not results['documents'] or not results['documents'][0]:
        print("No results found.")
        return []

    output = []
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i] if results['metadatas'] else {}
        distance = results['distances'][0][i] if results['distances'] else 0

        print(f"--- Result {i + 1} (score: {1 - distance:.3f}) ---")
        print(f"📅 Date: {meta.get('date', 'Unknown')}")
        print(f"🏷️  Type: {meta.get('type', 'unknown')}")
        if meta.get('topics'):
            print(f"📌 Topics: {meta.get('topics')}")
        print(f"📄 {doc[:400]}...")
        print()

        output.append({
            "content": doc,
            "metadata": meta,
            "score": 1 - distance
        })

    return output


def deduplicate():
    """Remove near-duplicate entries."""
    client = get_client()
    collection = get_collection(client)

    print("🔄 Checking for duplicates...")

    result = collection.get()
    if not result['ids']:
        print("No documents to dedupe.")
        return

    # Group by similarity
    seen_hashes = {}
    duplicates = []

    for i, doc in enumerate(result['documents']):
        # Create a simple hash of first 200 chars
        doc_hash = hashlib.md5(doc[:200].encode()).hexdigest()

        if doc_hash in seen_hashes:
            duplicates.append(result['ids'][i])
        else:
            seen_hashes[doc_hash] = result['ids'][i]

    if duplicates:
        print(f"🗑️  Found {len(duplicates)} duplicates, removing...")
        collection.delete(ids=duplicates)
        print(f"✅ Removed {len(duplicates)} duplicates")
    else:
        print("✅ No duplicates found")


def extract_knowledge():
    """Extract and summarize key learnings from history."""
    client = get_client()
    collection = get_collection(client)

    # Search for learnings
    learning_queries = [
        "ошибка решение fix",
        "важно запомнить",
        "лучше использовать",
        "правильный способ",
    ]

    all_learnings = []

    for query in learning_queries:
        results = collection.query(
            query_texts=[query],
            n_results=20,
            where={"type": {"$in": ["learning", "error", "decision"]}}
        )

        if results['documents'] and results['documents'][0]:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                all_learnings.append({
                    "content": doc[:500],
                    "type": meta.get('type'),
                    "date": meta.get('date'),
                    "topics": meta.get('topics', '')
                })

    # Group by topic
    by_topic = defaultdict(list)
    for learning in all_learnings:
        topics = learning['topics'].split(',') if learning['topics'] else ['general']
        for topic in topics[:3]:
            by_topic[topic.strip()].append(learning)

    print("\n📚 Extracted Knowledge by Topic:\n")

    for topic, learnings in sorted(by_topic.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"### {topic.upper()} ({len(learnings)} items)")
        for l in learnings[:3]:
            print(f"  - [{l['type']}] {l['content'][:100]}...")
        print()


if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "scan":
        scan_chats()
    elif cmd == "ingest":
        limit = None
        force = "--force" in sys.argv
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        ingest_chats(limit=limit, force=force)
    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        content_type = None
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            content_type = sys.argv[idx + 1]
        search_history(query, content_type=content_type)
    elif cmd == "dedupe":
        deduplicate()
    elif cmd == "extract-knowledge":
        extract_knowledge()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)
