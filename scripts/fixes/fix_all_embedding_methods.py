#!/usr/bin/env python3
"""
Fix all embedding methods to handle dict format from ModelManager
"""
import re
from pathlib import Path

def fix_embedding_method(file_path: Path, model_var_name: str, embedding_size: int = 768):
    """Fix an embedding method to handle dict format."""
    
    content = file_path.read_text()
    
    # Pattern to find the embedding method
    pattern = rf'(def _get_query_embedding\(self, query: str\) -> np\.ndarray:.*?try:)(.*?)(return embedding.*?except Exception as e:.*?return np\.zeros\({embedding_size}\))'
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"❌ No embedding method found in {file_path}")
        return False
    
    # Create the new implementation
    new_impl = f'''
            # Handle model format - could be direct model or dict from ModelManager
            model = self.{model_var_name}
            tokenizer = None
            
            if isinstance(self.{model_var_name}, dict):
                model = self.{model_var_name}.get('model')
                tokenizer = self.{model_var_name}.get('tokenizer')
            
            # Use the model's encode method (standard for sentence-transformers)
            if hasattr(model, 'encode'):
                embedding = model.encode(query, convert_to_numpy=True)
            elif hasattr(model, 'embed'):
                embedding = model.embed([query])[0]
            elif tokenizer is not None:
                # Use transformers model with tokenizer from ModelManager
                import torch
                inputs = tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            else:
                # Fallback for direct transformer models (legacy)
                inputs = self.{model_var_name}.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.{model_var_name}(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            '''
    
    # Replace the old implementation
    new_content = content[:match.start(2)] + new_impl + content[match.start(3):]
    
    # Write back
    file_path.write_text(new_content)
    print(f"✅ Fixed embedding method in {file_path}")
    return True

def main():
    """Fix all embedding methods."""
    base_path = Path("src/components/query_processors/analyzers/ml_views")
    
    # Files to fix (excluding technical and linguistic which are already done)
    fixes = [
        ("task_complexity_view.py", "_deberta_model", 768),
        ("computational_complexity_view.py", "_t5_model", 512),  # T5 has different size
    ]
    
    for filename, model_var, size in fixes:
        file_path = base_path / filename
        if file_path.exists():
            fix_embedding_method(file_path, model_var, size)
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    main()