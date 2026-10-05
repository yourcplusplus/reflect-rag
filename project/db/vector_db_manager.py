import config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

class VectorDbManager:
    RETRIEVAL_MODES = {
        "hybrid": RetrievalMode.HYBRID,
        "sparse": RetrievalMode.SPARSE,
        "dense": RetrievalMode.DENSE,
    }

    __client: QdrantClient
    __dense_embeddings: HuggingFaceEmbeddings
    __sparse_embeddings: FastEmbedSparse
    def __init__(self):
        self.__client = QdrantClient(path=config.QDRANT_DB_PATH)
        self.__dense_embeddings = HuggingFaceEmbeddings(model_name=config.DENSE_MODEL)
        self.__sparse_embeddings = FastEmbedSparse(model_name=config.SPARSE_MODEL)

    def _dense_vector_size(self):
        return len(self.__dense_embeddings.embed_query("test"))

    @staticmethod
    def _collection_vector_size(collection_info):
        vectors_config = collection_info.config.params.vectors
        if hasattr(vectors_config, "size"):
            return vectors_config.size
        if isinstance(vectors_config, dict) and vectors_config:
            first_vector = next(iter(vectors_config.values()))
            return getattr(first_vector, "size", None)
        return None

    def create_collection(self, collection_name):
        expected_size = self._dense_vector_size()
        if not self.__client.collection_exists(collection_name):
            print(f"Creating collection: {collection_name}...")
            self.__client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(size=expected_size, distance=qmodels.Distance.COSINE),
                sparse_vectors_config={config.SPARSE_VECTOR_NAME: qmodels.SparseVectorParams()},
            )
            print(f"✓ Collection created: {collection_name}")
        else:
            collection_info = self.__client.get_collection(collection_name)
            existing_size = self._collection_vector_size(collection_info)
            if existing_size and existing_size != expected_size:
                raise ValueError(
                    f"Qdrant collection '{collection_name}' has dense vector size "
                    f"{existing_size}, but '{config.DENSE_MODEL}' produces size "
                    f"{expected_size}. Clear and re-index the collection after "
                    "changing embedding models."
                )
            print(f"✓ Collection already exists: {collection_name}")

    def delete_collection(self, collection_name):
        try:
            if self.__client.collection_exists(collection_name):
                print(f"Removing existing Qdrant collection: {collection_name}")
                self.__client.delete_collection(collection_name)
        except Exception as e:
            raise RuntimeError(f"Unable to delete Qdrant collection '{collection_name}'.") from e

    def get_collection(self, collection_name, retrieval_mode=None):
        """Build a QdrantVectorStore view over the collection.

        retrieval_mode (a key of RETRIEVAL_MODES) overrides
        config.DEFAULT_RETRIEVAL_MODE so ablation variants such as a
        pure-vector V0 reuse the same client, collection, and embeddings
        instead of needing a separate retrieval path.
        """
        mode_name = (retrieval_mode or config.DEFAULT_RETRIEVAL_MODE).lower()
        if mode_name not in self.RETRIEVAL_MODES:
            raise ValueError(
                f"Unknown retrieval mode {mode_name!r}; expected one of {sorted(self.RETRIEVAL_MODES)}"
            )
        uses_sparse = mode_name != "dense"
        view_kwargs = dict(
            client=self.__client,
            collection_name=collection_name,
            embedding=self.__dense_embeddings,
            retrieval_mode=self.RETRIEVAL_MODES[mode_name],
        )
        if uses_sparse:
            view_kwargs["sparse_embedding"] = self.__sparse_embeddings
            view_kwargs["sparse_vector_name"] = config.SPARSE_VECTOR_NAME
        try:
            return QdrantVectorStore(**view_kwargs)
        except Exception as e:
            raise RuntimeError(f"Unable to initialize Qdrant collection '{collection_name}'.") from e

    def get_dense_collection(self, collection_name):
        """Pure-vector view: no BM25 sparse signals. The reranker is not
        part of the store at all (it lives in the search tool), so a dense
        view bypasses both by construction."""
        return self.get_collection(collection_name, retrieval_mode="dense")
