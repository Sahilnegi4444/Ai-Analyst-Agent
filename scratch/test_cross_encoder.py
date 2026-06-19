import os
# Force offline modes
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

try:
    from sentence_transformers import CrossEncoder
    print("Loading CrossEncoder...")
    model = CrossEncoder("cross-encoder/nli-deberta-v3-base")
    print("CrossEncoder loaded successfully!")
    
    query = "What is the policy on inventory reordering?"
    docs = [
        "The inventory reordering procedure requires checking current stock levels weekly.",
        "Supplier SLA penalty is 2% of transaction amount.",
        "Marketing campaigns are scheduled for holidays."
    ]
    
    pairs = [[query, doc] for doc in docs]
    scores = model.predict(pairs)
    print("Scores:", scores)
except Exception as e:
    print("Error loading CrossEncoder:", e)
