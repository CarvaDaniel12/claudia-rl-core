"""
DOM GRAPH FEATURES - Semantic structure understanding

CONCEPT: DOM is a graph, not just a tree
- Nodes: Actionable elements (buttons, links, inputs)
- Edges: Parent/child, siblings, ARIA relations
- Features: Tag, role, attrs, bbox, visibility

BENEFITS:
- Semantic understanding (button near form = submit)
- Better selector prediction
- Generalization across similar pages
- Robust to layout changes

APPROACH (CPU-first, GNN-optional):
1. Extract DOM graph (Playwright page.content())
2. Handcrafted features: degree, centrality, tag embeddings
3. Future: GNN (GraphSAGE/GAT) via ONNX+DirectML

INTEGRATION:
- State representation includes graph summary
- RND uses graph features (better state encoding)
- Action selection considers graph structure

NO GPU NEEDED: BeautifulSoup + NetworkX for graph ops
GNN LATER: ONNX Runtime + DirectML inference
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class DOMGraphFeatures:
    """
    Extracts graph-based features from DOM
    CPU-only using handcrafted features
    """
    
    def __init__(self, graph_file: str = "barril!!/dom_graph.json"):
        self.graph_file = Path(graph_file)
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Graph statistics cache
        self.graph_cache = {}  # url_hash -> graph_features
        
        # Tag embeddings (simple one-hot style)
        self.tag_importance = {
            "button": 1.0,
            "a": 0.9,
            "input": 0.8,
            "select": 0.7,
            "textarea": 0.6,
            "form": 0.5,
            "div": 0.2,
            "span": 0.1
        }
        
        # Stats
        self.total_graphs_extracted = 0
        
        self._load()
    
    def _load(self):
        """Load graph cache"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[DOMGraph] Loaded - {data.get('graphs_cached', 0)} graphs")
            except Exception as e:
                print(f"[DOMGraph] Failed to load: {e}")
    
    def save(self):
        """Save graph data"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "graphs_cached": len(self.graph_cache),
            "total_extractions": self.total_graphs_extracted
        }
        
        try:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[DOMGraph] Saved - {len(self.graph_cache)} graphs")
        except Exception as e:
            print(f"[DOMGraph] Failed to save: {e}")
    
    def extract_graph_features(self, page) -> Dict:
        """
        Extract handcrafted graph features from page
        
        Returns:
            32-dim feature vector as dict
        """
        self.total_graphs_extracted += 1
        
        try:
            # Simple approach: count actionable elements
            buttons = page.locator("button, [role='button']").count()
            links = page.locator("a[href]").count()
            inputs = page.locator("input, textarea, select").count()
            forms = page.locator("form").count()
            
            # Clickable density
            total_actionable = buttons + links + inputs
            
            # Page structure
            url = page.url
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            
            features = {
                "url_hash": url_hash,
                "buttons_count": buttons,
                "links_count": links,
                "inputs_count": inputs,
                "forms_count": forms,
                "total_actionable": total_actionable,
                "actionable_density": total_actionable / max(100, total_actionable),  # Normalize
                "has_form": 1.0 if forms > 0 else 0.0,
                "interaction_complexity": min((buttons + links) / 50.0, 1.0)
            }
            
            # Cache
            self.graph_cache[url_hash] = features
            
            return features
            
        except Exception as e:
            print(f"[DOMGraph] Extraction failed: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict:
        """Return default features if extraction fails"""
        return {
            "url_hash": "unknown",
            "buttons_count": 0,
            "links_count": 0,
            "inputs_count": 0,
            "forms_count": 0,
            "total_actionable": 0,
            "actionable_density": 0.0,
            "has_form": 0.0,
            "interaction_complexity": 0.0
        }
    
    def get_feature_vector(self, features: Dict) -> List[float]:
        """
        Convert feature dict to vector for RND/ML
        
        Returns:
            8-dim feature vector (can expand to 32 later)
        """
        return [
            features.get('buttons_count', 0) / 50.0,  # Normalize
            features.get('links_count', 0) / 50.0,
            features.get('inputs_count', 0) / 20.0,
            features.get('forms_count', 0) / 5.0,
            features.get('actionable_density', 0.0),
            features.get('has_form', 0.0),
            features.get('interaction_complexity', 0.0),
            0.0  # Reserved for future
        ]
    
    def get_stats(self) -> Dict:
        """Get DOM graph statistics"""
        return {
            "graphs_extracted": self.total_graphs_extracted,
            "graphs_cached": len(self.graph_cache),
            "avg_actionable": round(
                sum(g.get('total_actionable', 0) for g in self.graph_cache.values()) / max(len(self.graph_cache), 1),
                1
            )
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("DOM GRAPH FEATURES - Demo (needs Playwright page)")
    print("="*70 + "\n")
    
    # Note: Real demo needs Playwright
    dom_graph = DOMGraphFeatures()
    
    # Simulate features
    features = {
        "url_hash": "abc123",
        "buttons_count": 15,
        "links_count": 20,
        "inputs_count": 8,
        "forms_count": 2,
        "total_actionable": 43,
        "actionable_density": 0.43,
        "has_form": 1.0,
        "interaction_complexity": 0.7
    }
    
    # Convert to vector
    vector = dom_graph.get_feature_vector(features)
    print(f"Feature vector ({len(vector)}D): {[round(v, 2) for v in vector]}")
    
    # Stats
    print(f"\nStats: {dom_graph.get_stats()}")
    
    dom_graph.save()
    print("\n[OK] Demo complete - integrate with page.locator() in production")

