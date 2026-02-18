import os
import json
import asyncio
import re
from llama_parse import LlamaParse 
from llama_index.core import SimpleDirectoryReader
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.core.factories import Factories
from src.core.config import Config

class InsuranceIngestor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.llm = Factories.get_llm()
        self.embeddings = Factories.get_embedding_model()
        self.vector_db = Chroma(
            persist_directory=Config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        # 최신 LlamaParse 설정
        self.parser = LlamaParse(
            result_type="markdown",
            num_workers=8,
            language="ko"
        )

    async def parse_pdf(self):
        print(f"📄 Llama Cloud를 통한 고성능 파싱 시작: {self.pdf_path}")
        file_extractor = {".pdf": self.parser}
        documents = SimpleDirectoryReader(
            input_files=[self.pdf_path],
            file_extractor=file_extractor
        ).load_data()
        return "\n\n".join([doc.text for doc in documents])

    async def process_and_store(self):
        # 1. PDF 파싱
        full_markdown = await self.parse_pdf()
        
        # [주의] 전체 텍스트가 너무 길면 Gemini 컨텍스트 한계를 넘을 수 있습니다.
        # 텍스트가 3만자 이상일 경우, 보통약관/특별약관 섹션을 물리적으로 나눠서 호출하는 것이 안전합니다.
        
        prompt = f"""
        당신은 보험 약관 분석가입니다. 다음 마크다운 텍스트에서 '보통약관'과 '특별약관'을 분리하세요.
        반드시 모든 특별약관의 제목과 내용을 누락 없이 추출해야 합니다.
        
        결과는 반드시 JSON 형식으로만 응답하세요:
        {{
            "common": "보통약관 내용",
            "special": [ {{ "name": "담보명", "content": "내용" }} ]
        }}
        
        텍스트: {full_markdown[:30000]}  # 일단 3만자까지만 안전하게 전달
        """
        
        print("🤖 Gemini가 섹션을 분석 중입니다...")
        response = self.llm.invoke(prompt)
        
        # 2. JSON 안전 파싱 로직
        content = response.content
        # JSON 블록 추출
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
            print("❌ JSON 형태를 찾을 수 없습니다. 원본 응답 확인:")
            print(content)
            return

        json_str = json_match.group()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            # 마크다운 기호 제거 후 재시도
            try:
                clean_json = re.sub(r"```json|```", "", json_str).strip()
                data = json.loads(clean_json)
            except:
                print("❌ 재시도 실패. 원본 응답 상위 500자:")
                print(content[:500])
                return

        all_vector_docs = []
        backend_sync_data = []
        PRODUCT_ID = 10 

        # 3. 보통약관 처리 (ID: 100)
        common_id = 100
        common_name = "무배당 한화 BigPlus 재산종합보험 보통약관"
        all_vector_docs.append(Document(
            page_content=data.get('common', '내용 없음'),
            metadata={
                "product_id": PRODUCT_ID,
                "coverage_id": common_id,
                "category": "COMMON_TERMS",
                "name": common_name
            }
        ))
        backend_sync_data.append({
            "product_id": PRODUCT_ID,
            "coverage_id": common_id,
            "name": common_name,
            "category": "COMMON_TERMS"
        })

        # 4. 특별약관 처리 (최대 20개 제한)
        current_id = 101
        special_items = data.get('special', [])
        
        if len(special_items) > 20:
            print(f"⚠️ 탐지된 특별약관이 {len(special_items)}개입니다. 상위 20개만 처리합니다.")
            special_items = special_items[:20]

        for item in special_items:
            all_vector_docs.append(Document(
                page_content=item.get('content', '내용 없음'),
                metadata={
                    "product_id": PRODUCT_ID,
                    "coverage_id": current_id,
                    "category": "SPECIAL_TERMS",
                    "name": item.get('name', '알 수 없는 담보')
                }
            ))
            backend_sync_data.append({
                "product_id": PRODUCT_ID,
                "coverage_id": current_id,
                "name": item.get('name', '알 수 없는 담보'),
                "category": "SPECIAL_TERMS"
            })
            current_id += 1

        # 5. Vector DB 저장
        print(f"📦 ChromaDB에 {len(all_vector_docs)}개 섹션 저장 중...")
        self.vector_db.add_documents(all_vector_docs)

        # 6. 백엔드 동기화용 JSON 저장
        data_dir = "src/data" # 경로 수정 (src/data 에 저장되도록)
        os.makedirs(data_dir, exist_ok=True)
        sync_file = os.path.join(data_dir, "backend_sync_insurance.json")
        
        with open(sync_file, "w", encoding="utf-8") as f:
            json.dump(backend_sync_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 완료! 저장된 문서 수: {len(all_vector_docs)} (보통 1 + 특별 {len(special_items)})")
        print(f"📁 백엔드 동기화 파일 생성됨: {sync_file}")

if __name__ == "__main__":
    PDF_PATH = "src/data/HHBigPlusLiving.pdf" 
    if not os.path.exists(PDF_PATH):
        print(f"❌ 파일을 찾을 수 없습니다: {PDF_PATH}")
    else:
        ingestor = InsuranceIngestor(PDF_PATH)
        asyncio.run(ingestor.process_and_store())