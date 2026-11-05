"""CLI entry point. Trusted demo identity comes only from local configuration."""
import argparse
import json
import os
import sys
from pathlib import Path
from .agent import Agent, DEFAULT_MODEL
from .demo import DemoAgent
from .policies import Policies
from .store import Store
from .tools import Tools


def positive_int(text):
    value=int(text)
    if value<1:
        raise argparse.ArgumentTypeError('customer ID must be positive')
    return value


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Emporio da Musica support-agent prototype')
    parser.add_argument('--mode',choices=['demo','openai'],default='demo')
    parser.add_argument('--model',default=os.environ.get('OPENAI_MODEL',DEFAULT_MODEL))
    parser.add_argument('--data-dir',type=Path,default=Path.cwd()/'data')
    parser.add_argument('--customer-id',type=positive_int,help='Trusted local fictional-customer context; not production authentication')
    parser.add_argument('--message',help='Answer one message and exit')
    parser.add_argument('--trace',action='store_true',help='Print tool names and minimized results locally')
    args=parser.parse_args()
    client=None
    if args.mode=='openai':
        if not os.environ.get('OPENAI_API_KEY'):
            parser.error('Set OPENAI_API_KEY in your environment, or use --mode demo.')
        try:
            from openai import OpenAI
        except ImportError:
            parser.error('Install the live dependency: python -m pip install -r requirements-live.txt')
        client=OpenAI(timeout=25.0,max_retries=0)
    store=None
    try:
        store=Store(args.data_dir)
        tools=Tools(store,Policies(args.data_dir),args.customer_id)
        agent=DemoAgent(tools) if args.mode=='demo' else Agent(tools,client,args.model)
        print('DEMO MODE - deterministic patterns, no LLM or network calls.' if args.mode=='demo'
              else f'OPENAI MODE - {args.model}; tool results use the supplied static snapshot.')
        if args.customer_id:
            print(f'Fictional customer session: {args.customer_id}. This CLI flag is not real authentication.')
        def answer(text):
            result=agent.reply(text)
            print(result.answer)
            if args.trace:
                print(json.dumps(result.trace,ensure_ascii=False,indent=2))
            return 1 if result.error else 0
        if args.message is not None:
            return answer(args.message)
        print('Type /reset to clear conversation memory or /quit to exit.')
        while True:
            try:
                text=input('You> ')
            except (EOFError,KeyboardInterrupt):
                print()
                return 0
            if text.strip()=='/quit': return 0
            if text.strip()=='/reset':
                agent.reset()
                print('Conversation memory cleared.')
                continue
            answer(text)
    except (OSError,ValueError,KeyError) as exc:
        print(f'Cannot load the project data ({type(exc).__name__}). Run from the repository root or use --data-dir with the complete supplied data folder.',file=sys.stderr)
        return 2
    finally:
        if store is not None: store.close()


if __name__=='__main__':
    raise SystemExit(main())
