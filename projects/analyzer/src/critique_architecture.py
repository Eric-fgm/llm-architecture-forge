import os

from dotenv import load_dotenv
from prompt_chain import GeminiClient, PromptChain


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("Błąd: Proszę ustawić prawidłowy klucz GEMINI_API_KEY w pliku .env")
        return

    # Krok 1: Wczytanie "celowo słabej architektury"
    print("Podaj ścieżke do słabej architektury:")
    weak_arch_path = input()

    if not os.path.exists(weak_arch_path):
        print(
            f"Błąd: Brak pliku {weak_arch_path}. Utwórz ten plik i wklej do niego słabą architekturę."
        )
        return

    with open(weak_arch_path, "r", encoding="utf-8") as f:
        weak_arch_text = f.read()

    client = GeminiClient(api_key=api_key, model="gemini-2.5-flash")
    chain = PromptChain(client)

    # Zadanie A3: Krytyka Architektury
    chain.add_step(
        prompt_template=(
            "Jesteś audytorem architektury oprogramowania. Przeanalizuj poniższy projekt (celowo słabą architekturę).\n"
            "Twoje zadania:\n"
            "1. Zidentyfikuj i wypisz główne problemy i antywzorce architektoniczne (np. brak separacji odpowiedzialności, problemy ze skalowalnością).\n"
            "2. Zaproponuj konkretne ulepszenia i poprawki dla każdego z problemów.\n\n"
            "Projekt architektury do analizy:\n{architecture}"
        ),
        output_key="critique_output",
    )

    print("Analizowanie architektury...")
    result = chain.run({"architecture": weak_arch_text})

    # Zapis do pliku
    output_file = "output/critique_output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Krytyka i Ulepszenia Architektury (Zadanie A3)\n\n")
        f.write(result.outputs["critique_output"])

    print(f"\nGotowe! Wynik analizy został zapisany w {output_file}")


if __name__ == "__main__":
    main()
