from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conversation = [
    {
        "role": "system",
        "content": (
            "Du er ZynoX, en smart, rolig og hjelpsom AI-agent. "
            "Du hjelper brukeren med idéer, struktur, læring, prosjektbygging og fremdrift. "
            "Svar tydelig, konkret og vennlig."
        )
    }
]

def ask_zynox(user_input: str) -> str:
    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=conversation,
        temperature=0.7
    )

    answer = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": answer})
    return answer

def main():
    print("=== ZynoX Agent v0.2 Memory Mode ===")
    print("Skriv 'exit' for å avslutte.\n")

    while True:
        user_input = input("Du: ")

        if user_input.lower() in ["exit", "quit", "q"]:
            print("ZynoX: Farvel.")
            break

        try:
            answer = ask_zynox(user_input)
            print(f"ZynoX: {answer}\n")
        except Exception as e:
            print(f"Feil: {e}\n")

if __name__ == "__main__":
    main()