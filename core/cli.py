import argparse
import json
from .rag_engine import RAGEngine


def main():
    parser = argparse.ArgumentParser(description="RAG local, sin frontend")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    args = parser.parse_args()
    engine = RAGEngine()
    output = engine.index() if args.command == "index" else engine.answer_question(args.question)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
