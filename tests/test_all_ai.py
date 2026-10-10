import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from localmind.llm import (
    is_llm_available, 
    generate,
    answer_question, 
    summarize_document, 
    compare_documents, 
    analyze_csv, 
    plan_file_operations
)

print('--- TESTING LLM AVAILABILITY ---')
avail, msg = is_llm_available()
print(f'Available: {avail}, Message: {msg}')

if not avail:
    print('EXITING: LLM not available.')
    sys.exit(1)

print('\n--- TESTING GENERATE ---')
try:
    resp = generate('Say the word OK')
    print(f'Generate success! Response length: {len(resp)}')
except Exception as e:
    print(f'Generate failed: {e}')

print('\n--- TESTING ASK ---')
try:
    chunks = [{'content': 'The secret code is 42.', 'filename': 'secret.txt', 'file_path': '/secret.txt', 'chunk_id': 1}]
    resp = answer_question('What is the secret code?', chunks)
    print(f'Ask success! Response snippet: {resp[:50]}...')
except Exception as e:
    print(f'Ask failed: {e}')

print('\n--- TESTING SUMMARIZE ---')
try:
    resp = summarize_document('This is a test document about artificial intelligence. AI is good.', 'doc.txt')
    print(f'Summarize success! Response snippet: {resp[:50]}...')
except Exception as e:
    print(f'Summarize failed: {e}')

print('\n--- TESTING COMPARE ---')
try:
    resp = compare_documents('Apples are red.', 'doc1.txt', 'Bananas are yellow.', 'doc2.txt')
    print(f'Compare success! Response snippet: {resp[:50]}...')
except Exception as e:
    print(f'Compare failed: {e}')

print('\n--- TESTING CSV ---')
try:
    csv_content = 'name,age\nAlice,30\nBob,25'
    resp = analyze_csv(csv_content, 'data.csv', 'Who is the oldest?')
    print(f'CSV success! Response snippet: {resp[:50]}...')
except Exception as e:
    print(f'CSV failed: {e}')

print('\n--- TESTING FILE OPS ---')
try:
    idx = [{'filepath': 'C:/docs/file.txt', 'filename': 'file.txt'}]
    auth = ['C:/docs']
    ops, errs = plan_file_operations('Move file.txt to C:/docs/archive', idx, auth)
    print(f'File Ops success! Ops: {ops}, Errors: {errs}')
except Exception as e:
    print(f'File Ops failed: {e}')

