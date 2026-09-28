"""Ollama embeddings plus local Ollama or hosted Groq generation. No web search."""
import json
import httpx


class ProviderError(RuntimeError):
    pass


class AI:
    def __init__(self, settings):
        self.s = settings

    def _post(self, url, payload, headers=None):
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=self.s.timeout)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            msg = {401: 'API key rejected. Check GROQ_API_KEY.', 429: 'AI rate limit reached. Wait and retry.',
                   404: 'AI model or endpoint unavailable. Check model names and pull the Ollama models.'}.get(
                       code, f'AI service returned HTTP {code}. Check the server configuration.')
            raise ProviderError(msg) from exc
        except (httpx.RequestError, ValueError, ImportError) as exc:
            raise ProviderError('AI service unavailable or timed out. Start Ollama and check your connection/model setup.') from exc

    def embed(self, texts):
        if self.s.provider == 'evidence':
            raise ProviderError('Evidence-only mode does not provide semantic embeddings.')
        result = []
        for start in range(0, len(texts), 16):
            data = self._post(self.s.ollama_url.rstrip('/') + '/api/embed',
                              {'model': self.s.embedding_model, 'input': texts[start:start+16], 'truncate': False, 'keep_alive': '30m'})
            vectors = data.get('embeddings', [])
            if len(vectors) != len(texts[start:start+16]):
                raise ProviderError('Embedding service returned an incomplete batch.')
            result.extend(vectors)
        return result

    def generate(self, system, payload):
        if self.s.provider == 'evidence':
            raise ProviderError('Evidence-only mode has no AI generation. Select Ollama or Groq in .env for the submission.')
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': json.dumps(payload)}]
        if self.s.provider == 'groq':
            if not self.s.groq_key:
                raise ProviderError('GROQ_API_KEY is missing. Add it to .env and restart the server, or use Ollama.')
            data = self._post('https://api.groq.com/openai/v1/chat/completions',
                              {'model': self.s.groq_model, 'messages': messages, 'temperature': 0,
                               'response_format': {'type': 'json_object'}, 'max_completion_tokens': 2500},
                              {'Authorization': 'Bearer ' + self.s.groq_key})
            try:
                text = data['choices'][0]['message']['content']
            except (KeyError, IndexError, TypeError) as exc:
                raise ProviderError('Unexpected response from the AI service.') from exc
        elif self.s.provider == 'ollama':
            data = self._post(self.s.ollama_url.rstrip('/') + '/api/chat',
                              {'model': self.s.chat_model, 'messages': messages, 'format': 'json', 'stream': False,
                               'keep_alive': '30m',
                               'options': {'temperature': 0, 'seed': 42, 'num_ctx': 8192, 'num_predict': 1200}})
            text = data.get('message', {}).get('content', '')
        else:
            raise ProviderError('AI_PROVIDER must be ollama, groq or evidence.')
        try:
            result = json.loads(text)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except (ValueError, TypeError) as exc:
            raise ProviderError('AI returned invalid structured output. Retry or use a stronger configured model.') from exc
