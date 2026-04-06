from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conversation = [
    {
        "role": "system",
        "content": (
            "You are Akkan, the twin brother of ZynoX. "
            "You are an execution-focused AI operator for parallel tasks and missions. "
            "You support Tim with structure, speed, organization, checklists, planning, "
            "monitoring, and second-brain operations. "
            "Be concise, practical, and mission-oriented. "
            "When possible, return answers in this format:\n"
            "1. Mission\n"
            "2. Steps\n"
            "3. Risks\n"
            "4. Next Action"
        )
    }
]

def ask_akkan(user_input: str) -> str:
    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=conversation,
        temperature=0.4
    )

    answer = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": answer})
    return answer

def main():
    print("=== Akkan v0.2 | Parallel Ops Mode ===")
    print("Skriv 'exit' for å avslutte.\n")

    while True:
        user_input = input("Tim -> Akkan: ")

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Akkan: Mission ended.")
            break

        try:
            answer = ask_akkan(user_input)
            print(f"\nAkkan:\n{answer}\n")
        except Exception as e:
            print(f"Feil: {e}\n")

if __name__ == "__main__":
    main()
