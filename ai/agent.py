import json
import uuid
from tools import execute, SCHEMAS
from security.secure_policy import CUSTOMER_TOOLS
from challenges.engine import evaluate
from .mock_ai import MockAIProvider


class SupportAgent:
    def __init__(self, provider=None):
        self.provider = provider or MockAIProvider()

    def run(self, db, user, prompt, mode):
        allowed_tools = CUSTOMER_TOOLS if mode == 'secure' and user['role'] == 'customer' else set(SCHEMAS)
        proposal = self.provider.generate(prompt, user, allowed_tools)
        events, context = [], []
        interaction_id = uuid.uuid4().hex
        queue = [dict(proposal, source='user')] if 'tool' in proposal else []
        # Finite allowlisted tool graph: no external I/O, code execution or recursive agent loop.
        while queue and len(events) < 4:
            call = queue.pop(0)
            result, authorization = execute(db, user, mode, call['tool'], call['arguments'], call['source'])
            event = dict(call, authorization=authorization, result=result)
            events.append(event)
            context.append(result)
            db.execute('INSERT INTO tool_events (interaction_id, session_user, user_prompt, mode, source, tool_name, arguments_json, authorization_result, tool_result) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (interaction_id, user['id'], prompt, mode, call['source'], call['tool'], json.dumps(call['arguments']), authorization, json.dumps(result)))
            if isinstance(self.provider, MockAIProvider):
                queue.extend(self.provider.followups(call['tool'], result, mode))
        if events:
            parts = []
            for event in events:
                result = event['result']
                if 'error' in result:
                    parts.append(result['error'])
                    if result.get('requires_approval'):
                        parts.append(f'Simulated refund proposal #{result["approval_id"]} is awaiting your explicit confirmation in the approval panel.')
                elif event['tool'] == 'read_ticket' and mode == 'secure':
                    # Summarize only the benign first paragraph. Raw content stays data in the trace.
                    parts.append(f'Ticket {result["id"]}: {result["subject"]}. {result["message"].split(chr(10))[0]}\nRetrieved ticket text is untrusted data; embedded instructions were not followed.')
                else:
                    parts.append(json.dumps(result, indent=2, ensure_ascii=False))
            response = '\n\n'.join(parts)
        else:
            response = proposal['message']
        solved = evaluate(db, user['id'], mode, events, response)
        db.commit()
        return {'interaction_id': interaction_id, 'authenticated_user': user['id'], 'user_input': prompt,
                'mode': mode, 'model_decision': proposal['decision'], 'trace': events,
                'response': response, 'newly_solved': solved,
                'solved_count': db.execute('SELECT COUNT(*) FROM challenge_progress WHERE solved=1 AND challenge_id <= 7').fetchone()[0]}
