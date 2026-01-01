import re

def test_cleanup():
    input_text = """RESPONSE: നന്ദി! നിങ്ങളുടെ ഓർഡർ സ്ഥിരീകരിച്ചു. 
DATA: {'name': 'ഫാദി', 'address': 'കാസർഗോഡ്', 'cart': [{'id': 8, 'qty': 1, 'price': 20}]} 
COMMAND:CONFIRM_ORDER"""

    print(f"Original: {input_text}")
    
    clean_text = input_text.replace('RESPONSE:', '').strip()
    
    # AGGRESSIVE CLEANUP: Remove DATA and COMMAND blocks from spoken text
    # Note: re.DOTALL is important if DATA spans lines
    clean_text = re.sub(r'DATA:\s*\{.*?\}', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'COMMAND:\s*\w+', '', clean_text, flags=re.IGNORECASE)
    
    clean_text = clean_text.strip()
    
    print(f"\nCleaned: '{clean_text}'")
    
    if "DATA" in clean_text or "COMMAND" in clean_text or "{" in clean_text:
        print("\nFAIL: Metadata still present.")
    else:
        print("\nSUCCESS: Text is clean.")

if __name__ == "__main__":
    test_cleanup()
