import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.rag import add_to_index

def process_pdf_to_rag(file_path: str, source_name: str):
    """
    Leest een PDF uit, splitst de tekst in chunks en voegt deze toe aan FAISS.
    """
    try:
        # 1. Controleer of het bestand bestaat
        if not os.path.exists(file_path):
            print(f"❌ Bestand niet gevonden: {file_path}")
            return 0

        # 2. Tekst extraheren uit PDF
        reader = PdfReader(file_path)
        full_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        if not full_text.strip():
            print(f"⚠️ Geen tekst gevonden in {source_name}. Is het een scan?")
            return 0

        # 3. Tekst splitsen in chunks (belangrijk voor AI context venster)
        # We gebruiken RecursiveCharacterTextSplitter voor slimme splitsingen op witregels/punten
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,      # Hoeveel tekens per blokje
            chunk_overlap=100,    # Overlap om context te behouden tussen blokjes
            length_function=len
        )
        
        chunks = text_splitter.split_text(full_text)

        # 4. Chunks toevoegen aan de FAISS index (via onze nieuwe rag.py functie)
        if chunks:
            add_to_index(chunks, source_name)
            print(f"✅ PDF Verwerkt: {source_name} ({len(chunks)} segmenten)")
            return len(chunks)
        
        return 0

    except Exception as e:
        print(f"❌ Fout bij verwerken PDF {source_name}: {str(e)}")
        return 0