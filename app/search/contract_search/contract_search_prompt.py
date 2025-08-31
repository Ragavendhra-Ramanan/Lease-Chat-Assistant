CONTRACT_SEARCH_PROMPT = """ 
Answer based on Contract data:
Provide only factual answer based on User Question and Given Answer.
Also Explain to user about the Answer.
Do not provide the detail of column 'Preferred Customer'

Rule:
- The output should always be formatted in markdown with  points.

\nContext: {context}\n\nUser Question: {query}\nAnswer:
"""
