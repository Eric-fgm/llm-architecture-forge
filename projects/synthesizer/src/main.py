import os
from dotenv import load_dotenv
from prompt_chain import GeminiClient, PromptChain
#from prompt_chain import OpenAIClient, PromptChain

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("Błąd: Proszę ustawić prawidłowy klucz GEMINI_API_KEY w pliku .env")
        return

    client = GeminiClient(api_key=api_key, model="gemini-2.5-flash")

    # Wczytanie wymagań
    with open("input_requirements.txt", "r", encoding="utf-8") as f:
        requirements_text = f.read()

    chain = PromptChain(client)
    
    # Krok 1: Analiza domen i encji
    chain.add_step(
        prompt_template=(
            "Jesteś doświadczonym architektem oprogramowania.\n"
            "Przeanalizuj poniższe wymagania biznesowe i zidentyfikuj główne domeny (Bounded Contexts) "
            "oraz najważniejsze encje domenowe.\n\n"
            "Wymagania:\n{requirements}"
        ),
        output_key="domains_analysis"
    )
    
    # Krok 2: Propozycja architektury, dobór wzorców (Task A2), mapowanie wymagań i diagram (Task A1)
    chain.add_step(
        prompt_template=(
            "Na podstawie poniższej analizy domen, zaproponuj architekturę systemu. "
            "1. Wybierz konkretne wzorce architektoniczne (np. Modular Monolith, Microservices, MVC, CQRS itp.) i UZASADNIJ swój wybór.\n"
            "2. Wypisz proponowane komponenty/serwisy, ich odpowiedzialności oraz sposób komunikacji między nimi.\n"
            "3. Wykonaj MAPOWANIE WYMAGAŃ na komponenty (np. wskaż, który komponent realizuje wymagania takie jak limit 3 rezerwacji, zapobieganie konfliktom, itp.).\n"
            "4. Wygeneruj tekstowy DIAGRAM ARCHITEKTURY używając formatu Mermaid.js (umieść go w bloku kodu ```mermaid ... ```), pokazujący komponenty i przepływ między nimi.\n\n"
            "Analiza domen:\n{domains_analysis}\n\n"
            "Pamiętaj, by uzasadniać podejmowane decyzje architektoniczne."
        ),
        output_key="architecture_design"
    )
    
    # Krok 3: API i dane
    chain.add_step(
        prompt_template=(
            "Biorąc pod uwagę poniższy projekt architektury, zaproponuj kluczowe endpointy API (np. RESTful) "
            "oraz ogólne struktury baz danych dla najważniejszych serwisów. Uwzględnij NFR dotyczące wydajności.\n\n"
            "Architektura:\n{architecture_design}"
        ),
        output_key="api_and_data"
    )

    print("Rozpoczęto analizę i generowanie architektury. To może potrwać kilkanaście sekund...")
    result = chain.run({"requirements": requirements_text})
    
    print("\nGotowe! Zapisywanie do pliku architecture_output.md...")
    
    # Zapis do pliku wynikowego
    with open("architecture_output.md", "w", encoding="utf-8") as f:
        f.write("# 1. Analiza Domen i Encji\n\n")
        f.write(result.outputs["domains_analysis"])
        f.write("\n\n---\n\n# 2. Zaproponowana Architektura\n\n")
        f.write(result.outputs["architecture_design"])
        f.write("\n\n---\n\n# 3. API i Modele Danych\n\n")
        f.write(result.outputs["api_and_data"])
        
    print("Zapisano pomyślnie. Sprawdź plik architecture_output.md.")

if __name__ == "__main__":
    main()
