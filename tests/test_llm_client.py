from src.services.llm_client import get_llm_client


def test_llm():
    llm = get_llm_client()

    prompt = "Say hello in one short sentence."

    print("\n--- OLLAMA TEST ---")
    resp_local = llm.generate(prompt, llm_type="ollama")
    print(resp_local)

    print("\n--- API TEST ---")
    resp_api = llm.generate(prompt, llm_type="api")
    print(resp_api)


if __name__ == "__main__":
    test_llm()
