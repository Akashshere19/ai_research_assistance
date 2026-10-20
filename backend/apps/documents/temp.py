from services import extract_document_content

text = extract_document_content(
    "/home/akash/ai_research_assistance/backend/media/rag_documents/2026/10/Spaceo_M1_Technical_Specification_Government_Tender_jfZcWcY.docx",
    "docx",
)

print(text[:2000])