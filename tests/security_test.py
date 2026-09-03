from utils.helpers import sanitize_text

malicious = '<script>alert(1)</script><div onclick="evil()">Click</div>'

print('Original:', malicious)
print('Sanitized:', sanitize_text(malicious))

# Demonstrate usage in a simulated card value
card_value = sanitize_text(malicious)
print('\nSimulated KPI card value (should show escaped HTML):')
print(card_value)
