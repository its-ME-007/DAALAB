import heapq
import time
from collections import Counter
from typing import Optional

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left: Optional[Node] = None
        self.right: Optional[Node] = None
    
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    """Build Huffman tree from input text"""
    if not text:
        return None
    
    # Count character frequencies
    freq = Counter(text)
    
    # Create leaf nodes
    heap = [Node(char, freq) for char, freq in freq.items()]
    heapq.heapify(heap)
    
    # Build tree by combining nodes
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        internal = Node(None, left.freq + right.freq)
        internal.left = left
        internal.right = right
        
        heapq.heappush(heap, internal)
    
    return heap[0] if heap else None

def generate_codes(root, code="", codes=None):
    """Generate Huffman codes for each character"""
    if codes is None:
        codes = {}
    
    if root is None:
        return codes
    
    # Leaf node
    if root.char is not None:
        codes[root.char] = code
        return codes
    
    # Traverse left (add 0)
    generate_codes(root.left, code + "0", codes)
    # Traverse right (add 1)
    generate_codes(root.right, code + "1", codes)
    
    return codes

def encode_text(text, codes):
    """Encode text using Huffman codes"""
    return ''.join(codes[char] for char in text)

def decode_text(encoded_text, root):
    """Decode text using Huffman tree"""
    if not encoded_text or root is None:
        return ""
    
    decoded = ""
    current = root
    
    for bit in encoded_text:
        if bit == '0':
            current = current.left
        else:
            current = current.right
        
        # If we reach a leaf node
        if current.char is not None:
            decoded += current.char
            current = root
    
    return decoded

def huffman_compression(text):
    """Complete Huffman compression process"""
    start_time = time.time()
    
    # Build Huffman tree
    root = build_huffman_tree(text)
    
    # Generate codes
    codes = generate_codes(root)
    
    # Encode text
    encoded = encode_text(text, codes)
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "original_text": text,
        "character_frequencies": dict(Counter(text)),
        "huffman_codes": codes,
        "encoded_text": encoded,
        "original_size": len(text) * 8,  # Assuming 8 bits per character
        "compressed_size": len(encoded),
        "compression_ratio": (1 - len(encoded) / (len(text) * 8)) * 100 if text else 0,
        "execution_time_ms": execution_time,
        "tree_root": root
    }

def huffman_decompression(encoded_text, root):
    """Complete Huffman decompression process"""
    start_time = time.time()
    
    decoded_text = decode_text(encoded_text, root)
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "encoded_text": encoded_text,
        "decoded_text": decoded_text,
        "execution_time_ms": execution_time
    } 