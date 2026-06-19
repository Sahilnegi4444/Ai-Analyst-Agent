import os
import glob
from sentence_transformers import SentenceTransformer

print("HF cache directory:")
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
print(cache_dir)
if os.path.exists(cache_dir):
    print("Files in cache:")
    for path in glob.glob(os.path.join(cache_dir, "**/*"), recursive=True):
        if os.path.isfile(path):
            print(" -", path)
else:
    print("Cache dir does not exist.")

try:
    print("\nTrying to see if CrossEncoder can be imported...")
    from sentence_transformers import CrossEncoder
    print("CrossEncoder imported successfully.")
except Exception as e:
    print("CrossEncoder import failed:", e)
