from src.core.factories import Factories

def test_gemini_api():
    llm = Factories.get_llm()
    prompt = "안녕하세요? 오늘 날씨 어때요?"

    try:
        response = llm.invoke(prompt)
        print("✅ Gemini API 응답:", response.content)
    except Exception as e:
        print("❌ Gemini API 호출 실패:", e)

if __name__ == "__main__":
    test_gemini_api()
