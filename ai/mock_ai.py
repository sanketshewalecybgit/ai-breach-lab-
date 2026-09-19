"""An intentionally small rule-based simulator, not an LLM or a security filter.

Explicit parser labels in traces describe matching rules, not hidden model reasoning.
Retrieved-text interpretation is deliberately enabled only in vulnerable mode.
"""
import re
from .provider import AIProvider


class MockAIProvider(AIProvider):
    def generate(self, prompt, user, available_tools):
        lower = prompt.lower()
        order_match = re.search(r'\bORD-\d{4}\b', prompt, re.I)
        order = order_match.group().upper() if order_match else None
        email_match = re.search(r'[\w.+-]+@[\w.-]+', prompt)
        email = email_match.group().lower().rstrip('.,') if email_match else None
        ticket = re.search(r'(?:ticket|case)\s*(?:#|id\s*)?(\d+)', lower)

        def proposal(tool, arguments, decision):
            if tool not in available_tools:
                return {'decision': 'Requested capability is outside the agent tool scope.',
                        'message': 'Global customer search is unavailable in secure mode. I can show your own profile.'}
            return {'tool': tool, 'arguments': arguments, 'decision': decision}

        if re.search(r'\b(create|open|submit|file)\b.*\b(ticket|case)\b', lower) and not ticket:
            content = prompt.split(':', 1)[-1].strip()
            return proposal('create_support_ticket', {'subject': 'Customer support request', 'message': content}, 'Create a fictional support ticket.')
        if ticket:
            return proposal('read_ticket', {'ticket_id': int(ticket.group(1))}, 'Read a support ticket for summarization.')
        if 'refund' in lower:
            if not order:
                return {'decision': 'Refund intent needs an order.', 'message': 'Please include an ORD-#### order ID and a whole-number INR amount.'}
            without_id = re.sub(r'ORD-\d{4}', '', prompt, flags=re.I)
            amount_match = re.search(r'(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w.])', without_id)
            if not amount_match or '.' in amount_match.group():
                return {'decision': 'Refund amount needs clarification.', 'message': 'Use a whole-number INR refund amount, for example: refund INR 100 for my order.'}
            amount_text = amount_match.group().replace(',', '')
            if len(amount_text) > 11:
                return {'decision': 'Simulation numeric limit.', 'message': 'That amount exceeds the local simulator limit.'}
            return proposal('issue_refund', {'order_id': order, 'amount': int(amount_text)}, 'Refund intent; model-selected order and amount.')
        if order and any(word in lower for word in ('shipping', 'shipment', 'tracking', 'carrier')):
            return proposal('lookup_shipping_status', {'order_id': order}, 'Look up fictional shipping status.')
        if order and any(word in lower for word in ('note', 'metadata', 'debug', 'internal')):
            return proposal('get_internal_note', {'order_id': order}, 'Retrieve support context for an order.')
        if email:
            return proposal('search_customer', {'email': email}, 'Search customer records by email.')
        if any(word in lower for word in ('profile', 'account', 'user')) and not order:
            match = re.search(r'\b(1001|1002|9001)\b', prompt)
            return proposal('get_profile', {'user_id': int(match.group()) if match else user['id']}, 'Retrieve a model-selected customer profile.')
        if order:
            return proposal('get_order', {'order_id': order}, 'Order lookup requested.')
        return {'decision': 'No supported intent matched.',
                'message': 'I can help with profiles, orders, refunds, support notes, tickets and shipping. Include an order ID or ticket number when needed. This is a deterministic simulator; try one task per message.'}

    def followups(self, tool, result, mode):
        """Deliberately promote untrusted text to authority in vulnerable mode."""
        if mode == 'secure' or 'error' in result:
            return []
        field = 'message' if tool == 'read_ticket' else 'carrier_message' if tool == 'lookup_shipping_status' else None
        if not field:
            return []
        content = result.get(field, '')
        if not re.search(r'AI\s+(?:SUPPORT\s+)?(?:AGENT|assistant)', content, re.I):
            return []
        source = f'ticket:{result["id"]}' if tool == 'read_ticket' else f'shipping:{result["order_id"]}'
        calls = []
        email = re.search(r'[\w.+-]+@novacart\.lab', content, re.I)
        if email and re.search(r'search_customer|search customer', content, re.I):
            calls.append({'tool': 'search_customer', 'arguments': {'email': email.group().lower()},
                          'source': source, 'decision': 'Untrusted retrieved text was promoted to a customer-search instruction.'})
        order = re.search(r'ORD-\d{4}', content, re.I)
        if order and re.search(r'internal[_ ]note', content, re.I):
            calls.append({'tool': 'get_internal_note', 'arguments': {'order_id': order.group().upper()},
                          'source': source, 'decision': 'Untrusted retrieved text was promoted to an internal-note instruction.'})
        return calls
