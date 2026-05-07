# Krytyka i Ulepszenia Architektury (Zadanie A3)

Jako audytor przeanalizowałem dostarczony projekt "Systemu Rezerwacji Wizyt". Projekt ten stanowi podręcznikowy przykład antywzorców architektonicznych. Poniżej znajduje się diagnoza głównych problemów oraz zestawienie konkretnych rekomendacji naprawczych.

## 1. Zidentyfikowane Problemy i Antywzorce Architektoniczne

1. **Antywzorzec "Shared Database" (Wspólna Baza Danych w Mikroserwisach):** 
   - *Problem:* Projekt wymusza architekturę rozproszoną, ale wszystkie usługi dzielą tę samą instancję bazy danych MongoDB. Taki projekt łamie całkowicie wzorzec "Database-per-Service". Skutkuje to twardym sprzężeniem (tight coupling) – zmiana schematu dokumentów lub awaria bazy zatrzyma cały system.

2. **Antywzorzec "God Object / Monolithic Gateway" (Front API Service):**
   - *Problem:* Ustanowienie "pojedynczego serwisu odpowiedzialnego za wszystko" jako bramy dla klienta prowadzi do stworzenia rozrastającego się monolitycznego wąskiego gardła (bottleneck), który ciężko skalować.

3. **Nieprawidłowa komunikacja z bazą (Booking Service):**
   - *Problem:* Komunikacja serwisu bezpośrednio z "interfejsem bazy danych za pomocą zapytań HTTP" uchodzi za fatalną praktykę pod względem wydajności, bezpieczeństwa i hermetyzacji. Bazy powinny być odpytywane poprzez dedykowane sterowniki i po bezpiecznym protokole.

4. **Nieskalowalne i zasobożerne zarządzanie stanem (Availability Service):**
   - *Problem:* Serwis operujący w nieskończonej pętli `while(true)` nieprzerwanie skanującej bazę danych to tzw. "Busy Waiting". Skutkuje to ogromnym, bezużytecznym obciążeniem bazy i procesora (CPU) i całkowitym brakiem skalowalności operacyjnej.

5. **Wadliwy mechanizm audytu i centralny plik (Audit Service):**
   - *Problem:* Polling (odpytywanie co 5 sekund po HTTP) to nieefektywny sposób śledzenia zmian. Co więcej, zapisywanie audytu jako płaskiego tekstu w pojedynczym pliku `logs.txt` naraża system na tzw. blokady dostępu do pliku (file locks) przy wysokim natężeniu ruchu i uniemożliwia proste przeszukiwanie logów w przyszłości.

6. **Złe umiejscowienie reguł biznesowych i fatalne UX (Limity asynchroniczne):**
   - *Problem:* Sprawdzanie twardego limitu "maksymalnie 3 rezerwacje" dopiero nocą za pomocą batch jobs sprawia, że klient widzi sukces rezerwacji, a rano otrzymuje powiadomienie o jej usunięciu. To bardzo zła praktyka projektowania doświadczeń użytkownika (UX) i obsługi integralności.

7. **Brak czytelnej obsługi błędów konfliktów (Double Booking):**
   - *Problem:* Zwracanie niesprecyzowanego statusu `500 Internal Server Error` wskutek naturalnego i spodziewanego problemu na warstwie danych (podwójna rezerwacja) to antywzorzec obsługi błędów w API.

---

## 2. Zaproponowane Ulepszenia i Poprawki

1. **Decyzja strategiczna - Zmiana na Modular Monolith lub Database-per-service:**
   - Należy zrezygnować z narzutu mikroserwisów dla tak małej skali i wdrożyć architekturę **Modular Monolith** wykorzystującą bazę relacyjną (PostgreSQL/MySQL), w której z łatwością zabezpieczymy transakcje. Jeśli mikroserwisy są wymogiem absolutnym, każda usługa (np. Booking) **musi** posiadać własną, logiczną bazę danych, a synchronizacja powinna odbywać się w sposób asynchroniczny.

2. **Wdrożenie prawdziwego API Gateway:**
   - Serwis "Front API Service" należy zastąpić standardowym komponentem "API Gateway" (np. Kong, Ocelot, Spring Cloud Gateway), który będzie odpowiadał wyłącznie za *routing*, autoryzację, obsługę tokenów i *rate limiting*, nie ingerując w procesy domenowe.

3. **Event-Driven Architecture (Architektura oparta na zdarzeniach):**
   - Należy wyeliminować *Availability Service* z jego pętlą while oraz odpytywanie po HTTP (polling) z *Audit Service*. Zamiast tego należy w pełni wykorzystać kolejkę Kafka. *Booking Service* po zakończeniu rezerwacji emituje zdarzenie (Event) np. `BookingCreatedEvent`. Pozostałe serwisy stają się konsumentami podłączonymi do Kafki (Publish-Subscribe Pattern) i aktualizują się tylko wtedy, gdy faktycznie coś się wydarzy.

4. **Wprowadzenie dedykowanego stosu do Logowania:**
   - Zapis do płaskiego pliku `logs.txt` zastąpić zewnętrznym, profesjonalnym rozwiązaniem, takim jak ELK Stack (Elasticsearch, Logstash, Kibana) lub Grafana Loki, co umożliwi scentralizowane gromadzenie, agregację i wyszukiwanie incydentów na żywo.

5. **Synchroniczna walidacja kluczowych reguł:**
   - Limit 3 rezerwacji musi być sprawdzany w sposób **synchroniczny** w *Booking Service* natychmiast po otrzymaniu żądania API od klienta. Jeśli użytkownik ma 3 aktywne wizyty, API od razu odrzuca prośbę.

6. **Właściwa reakcja API na "Double Booking":**
   - Użyć blokowania optymistycznego (Optimistic Locking) w bazie danych lub systemów blokad (np. w Redis) przed zapisem. Gdy wystąpi Double Booking, serwer powinien przechwycić konflikt i kulturalnie poinformować klienta, zwracając status **HTTP 409 Conflict** wraz z wiadomością o treści "Ten termin jest już zarezerwowany, odśwież widok i wybierz inny".
