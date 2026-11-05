"""Small bilingual lexical retrieval index with original PDF page evidence."""
import json
import re
from pathlib import Path
from pypdf import PdfReader
from .store import normalize

STOP = set('a an the is are do does can i my me you your for of to in on and or what how when where qual como o os a as de da do e eu'.split())


class Policies:
    def __init__(self, data_dir: Path):
        data_dir = Path(data_dir)
        self.entries = json.loads((data_dir / 'policy_index.json').read_text(encoding='utf-8'))
        self.pages = [' '.join(p.extract_text().split()) for p in PdfReader(data_dir/'store_policies.pdf').pages]

    def search(self, query: str) -> dict:
        if not isinstance(query,str) or not 1 <= len(query.strip()) <= 300:
            raise ValueError('Policy query must contain 1 to 300 characters.')
        words = set(re.findall(r'[a-z0-9]+', normalize(query))) - STOP
        scored = []
        for entry in self.entries:
            keys = set(normalize(' '.join(entry['keywords'])).split())
            score = len(words & keys)
            if score:
                hit = {k:v for k,v in entry.items() if k != 'keywords'}
                hit['original_text'] = '\n'.join(f'Page {p}: {self.pages[p-1]}' for p in entry['pages'])
                hit['source'] = 'store_policies.pdf, pages ' + ', '.join(map(str, entry['pages']))
                scored.append((score,hit))
        scored.sort(key=lambda item:-item[0])
        return {'matches':[hit for _,hit in scored[:2]],
                'version':'Store manual v2.1, June 2025; fictional challenge policy, not legal advice.'}
