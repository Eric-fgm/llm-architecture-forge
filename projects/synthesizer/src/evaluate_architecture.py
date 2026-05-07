import os
from dotenv import load_dotenv
from prompt_chain import GeminiClient, PromptChain

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("Błąd: Proszę ustawić prawidłowy klucz GEMINI_API_KEY w pliku .env")
        return

    client = GeminiClient(api_key=api_key, model="gemini-2.5-flash")

    # Wczytanie wygenerowanej architektury (do oceny)
    try:
        with open("architecture_output.md", "r", encoding="utf-8") as f:
            generated_arch = f.read()
    except FileNotFoundError:
        print("Błąd: Brak pliku architecture_output.md")
        return

    # Wczytanie architektury referencyjnej (Gold Standard)
    try:
        with open("Gold2-architecture-ver2.txt", "r", encoding="utf-8") as f:
            gold_arch = f.read()
    except FileNotFoundError:
        print("Błąd: Brak pliku Gold2-architecture-ver2.txt")
        return

    chain = PromptChain(client)

    # Krok ewaluacji (LLM-as-a-judge)
    chain.add_step(
        prompt_template=(
            "Jesteś ekspertem z zespołu Evaluation Team.\n"
            "Twoim zadaniem jest ocena wygenerowanej architektury (Generated Architecture) w odniesieniu do architektury referencyjnej (Gold Architecture).\n"
            "Oceń architekturę na podstawie pięciu metryk (M1-M5), przyznając punkty w skali od 0 do 3 dla każdej z nich, gdzie:\n"
            "0 – nieakceptowalne (wynik błędny, bezużyteczny)\n"
            "1 – słabe (częściowo poprawne, wymaga dużych poprawek)\n"
            "2 – dobre (w większości poprawne, drobne błędy)\n"
            "3 – bardzo dobre (kompletne, spójne, gotowe do użycia)\n\n"
            "Metryki do oceny:\n"
            "M1. Correctness (poprawność): Czy projekt jest merytorycznie poprawny i zgodny z Gold Architecture?\n"
            "M2. Completeness (kompletność): Czy obejmuje wszystkie istotne elementy zadania i komponenty z Gold?\n"
            "M3. Consistency (spójność): Czy artefakt jest spójny wewnętrznie?\n"
            "M4. Clarity (jasność): Czy opis i diagram są czytelne i zrozumiałe?\n"
            "M5. Maintainability (utrzymywalność): Czy wynik nadaje się do realnego użycia (czy nie wprowadzono np. overengineeringu niezgodnego z Gold)?\n\n"
            "Dla każdej metryki podaj wynik oraz krótkie, merytoryczne uzasadnienie.\n"
            "Na końcu podsumuj ocenę i wylicz średni wynik.\n\n"
            "=== GOLD ARCHITECTURE (Wzorzec) ===\n{gold}\n\n"
            "=== GENERATED ARCHITECTURE (Do oceny) ===\n{generated}"
        ),
        output_key="evaluation_report"
    )

    print("Rozpoczęto ocenę wygenerowanej architektury przez LLM-Judge. To może chwilę potrwać...")
    result = chain.run({
        "gold": gold_arch,
        "generated": generated_arch
    })
    
    print("\nGotowe! Zapisywanie do pliku evaluation_output.md...")
    
    with open("evaluation_output.md", "w", encoding="utf-8") as f:
        f.write("# Raport Ewaluacyjny (LLM-as-a-Judge)\n\n")
        f.write(result.outputs["evaluation_report"])
        
    print("Zapisano pomyślnie. Sprawdź plik evaluation_output.md.")

if __name__ == "__main__":
    main()
