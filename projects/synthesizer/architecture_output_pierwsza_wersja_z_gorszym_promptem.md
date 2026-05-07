# 1. Analiza Domen i Encji

Jako doświadczony architekt oprogramowania, przeprowadzę analizę wymagań, identyfikując główne domeny (Bounded Contexts) oraz kluczowe encje domenowe, stosując zasady Domain-Driven Design (DDD).

### Wprowadzenie do Bounded Contexts

Bounded Contexts (Konteksty Ograniczone) to centralne pojęcie w DDD, które definiuje logiczne granice wokół spójnego zestawu funkcjonalności i języka wszechobecnego (Ubiquitous Language). W ramach każdego kontekstu, terminy domenowe mają jednoznaczne znaczenie. Pomaga to zarządzać złożonością, unikać dwuznaczności i projektować systemy w sposób modularny i skalowalny.

### Analiza Wymagań i Identyfikacja Bounded Contexts

Na podstawie dostarczonych wymagań, możemy zidentyfikować następujące główne Bounded Contexts:

1.  **Identity & Access Management (IAM)**
    *   **Opis:** Ten kontekst odpowiada za zarządzanie użytkownikami, specjalistami i administratorami, ich rolami oraz procesami uwierzytelniania i autoryzacji. Jest to domena odpowiedzialna za *kto* może wykonywać *jakie* operacje.
    *   **Ubiquitous Language:** User, Specialist, Admin, Role, Authentication, Authorization, Permissions.
    *   **Uzasadnienie:**
        *   Wymaga niezależnego zarządzania profilami użytkowników (User, Specialist, Admin).
        *   FR9 jasno definiuje różne poziomy dostępu do danych w zależności od roli.
        *   NFR3 wymaga uwierzytelnienia użytkownika.
    *   **Kluczowe Encje Domenowe:**
        *   `User`: Reprezentuje ogólnego użytkownika systemu, niezależnie od roli. Zawiera podstawowe dane do logowania i profilu.
        *   `SpecialistProfile`: Rozszerza `User` o specyficzne dane dla specjalisty (np. specjalizacja, link do konta użytkownika).
        *   `AdminProfile`: Rozszerza `User` o specyficzne dane dla administratora (link do konta użytkownika).
        *   `Role`: Określa uprawnienia (np. USER, SPECIALIST, ADMIN).
        *   `Permission`: Szczegółowe uprawnienia (np. CAN_BOOK_APPOINTMENT, CAN_MANAGE_SCHEDULE).

2.  **Scheduling & Availability**
    *   **Opis:** Ten kontekst zarządza grafikiem specjalistów oraz definicją i dostępnością terminów (slotów). Odpowiada za to, *kiedy* specjalista jest dostępny i *jakie* konkretne bloki czasowe są oferowane.
    *   **Ubiquitous Language:** Specialist Schedule, Time Slot, Availability, Blocked Slot.
    *   **Uzasadnienie:**
        *   FR1: Przeglądanie dostępnych terminów według specjalisty i daty.
        *   FR7: Specjalista zarządza swoim grafikiem (dodawanie/usuwanie wolnych terminów).
        *   FR11: Specjalista może oznaczyć slot jako niedostępny (BLOCKED).
        *   Gold: "slot trwa 30 minut", "jedna rezerwacja dotyczy jednego specjalisty i jednego slotu".
    *   **Kluczowe Encje Domenowe (Aggregate Roots):**
        *   `SpecialistSchedule`: Agregat dla grafiku konkretnego specjalisty. Może zawierać kolekcję `TimeSlot` lub zarządzać nimi poprzez ID. Jest to spójny zbiór dostępności specjalisty.
        *   `TimeSlot` (Value Object lub Encja w ramach `SpecialistSchedule`): Reprezentuje konkretny blok czasu oferowany przez specjalistę. Posiada:
            *   `Id` (unikalne dla slotu)
            *   `SpecialistId`
            *   `StartTime`
            *   `EndTime`
            *   `Duration` (np. 30 minut)
            *   `Status` (AVAILABLE, BLOCKED).

3.  **Appointment Management**
    *   **Opis:** To jest serce systemu, zarządzające procesem rezerwacji i anulowania wizyt. Odpowiada za *kto* rezerwuje *co*, *kiedy* i *na jakich zasadach*. Zawiera logikę biznesową dotyczącą konfliktów, limitów rezerwacji i statusów wizyt.
    *   **Ubiquitous Language:** Appointment, Reservation, Booking, Cancellation, Status (BOOKED, CANCELLED, COMPLETED), Booking Limit, Time Conflict, Double Booking.
    *   **Uzasadnienie:**
        *   FR2: Rezerwacja wizyty.
        *   FR3: Ograniczenie liczby rezerwacji na użytkownika.
        *   FR4: Brak podwójnej rezerwacji.
        *   FR5: Anulowanie wizyty z ograniczeniami czasowymi.
        *   FR8: Statusy wizyty.
        *   FR10: Konflikty czasowe dla użytkownika.
        *   AC1, AC2, AC3, AC4, AC6 definiują konkretne zachowania rezerwacji.
        *   Wymagania dotyczące spójności i współbieżności (FR13, NFR1) są kluczowe dla tej domeny.
    *   **Kluczowe Encje Domenowe (Aggregate Roots):**
        *   `Appointment`: Główny agregat. Reprezentuje potwierdzoną lub anulowaną wizytę. Posiada:
            *   `Id`
            *   `UserId`
            *   `SpecialistId`
            *   `TimeSlotId` (referencja do `TimeSlot` z `Scheduling & Availability`)
            *   `StartTime` (redundantne, ale ułatwia zapytania i zachowuje spójność historyczną w przypadku usunięcia slotu)
            *   `EndTime` (jw.)
            *   `Status` (BOOKED, CANCELLED, COMPLETED)
            *   `BookingTimestamp`
            *   `CancellationTimestamp` (jeśli anulowano)
            *   `AdminOverrideReason` (jeśli dotyczy)
        *   `UserBookingPolicy`: Encja lub serwis domenowy odpowiedzialny za egzekwowanie limitu rezerwacji dla danego użytkownika (FR3).
        *   `TimeOverlapPolicy`: Encja lub serwis domenowy odpowiedzialny za sprawdzanie konfliktów czasowych dla rezerwacji użytkownika (FR10).

4.  **Admin & Override Management**
    *   **Opis:** Ten kontekst umożliwia administratorom nadzorowanie systemu, konfigurowanie globalnych ograniczeń oraz, co kluczowe, *przekraczanie* lub *nadpisywanie* standardowych reguł biznesowych w uzasadnionych przypadkach.
    *   **Ubiquitous Language:** System Configuration, Override, Exception, Admin Decision.
    *   **Uzasadnienie:**
        *   Cel systemu: "dopuszczalne są wyjątki wynikające z decyzji administracyjnych".
        *   FR3: "Admin może w uzasadnionych przypadkach zezwolić na przekroczenie tego limitu."
        *   US6: "Jako admin chcę mieć możliwość nadpisania ograniczeń systemu w wyjątkowych sytuacjach."
    *   **Kluczowe Encje Domenowe:**
        *   `SystemConfiguration`: Przechowuje globalne ustawienia i domyślne limity (np. domyślny max. rezerwacji na użytkownika).
        *   `OverrideDecision`: Reprezentuje decyzję administratora o nadpisaniu konkretnego ograniczenia dla konkretnej encji (np. dla użytkownika, aby mógł mieć więcej niż 3 rezerwacje). Posiada:
            *   `Id`
            *   `AdminId`
            *   `TargetEntityId` (np. `UserId`, `AppointmentId`)
            *   `OverrideType` (np. BOOKING_LIMIT, TIME_CONFLICT)
            *   `Reason`
            *   `Timestamp`
            *   `ExpiresAt` (opcjonalnie, jeśli override jest tymczasowy)

5.  **Audit & Notifications**
    *   **Opis:** Ten kontekst jest odpowiedzialny za rejestrowanie wszystkich istotnych zdarzeń systemowych (rezerwacje, anulowania, błędy, akcje administratora) oraz za ewentualne wysyłanie powiadomień. Ma charakter "fire-and-forget", czyli nie blokuje operacji biznesowych.
    *   **Ubiquitous Language:** Audit Log, Event, Notification, History.
    *   **Uzasadnienie:**
        *   FR12: "System powinien rejestrować operacje takie jak rezerwacje, anulowania oraz błędy."
        *   NFR4: "System powinien rejestrować operacje wraz ze znacznikiem czasu."
    *   **Kluczowe Encje Domenowe:**
        *   `AuditEvent`: Reprezentuje pojedyncze zdarzenie, które zostało zarejestrowane. Posiada:
            *   `Id`
            *   `EventType` (np. APPOINTMENT_BOOKED, APPOINTMENT_CANCELLED, SLOT_BLOCKED, ADMIN_OVERRIDE)
            *   `EntityId` (referencja do encji, której dotyczy zdarzenie)
            *   `ActorId` (kto wykonał akcję, np. `UserId`, `SpecialistId`, `AdminId`)
            *   `Timestamp`
            *   `Details` (JSON lub inny format zawierający kontekstowe dane zdarzenia).
        *   `Notification`: Jeśli system ma wysyłać powiadomienia (np. email, SMS) o rezerwacji/anulowaniu, ta encja lub oddzielny agregat mógłby zarządzać stanem powiadomienia.

### Podsumowanie Bounded Contexts i Kluczowych Encji

| Bounded Context             | Cel                                                                | Kluczowe Encje Domenowe (Aggregate Roots / Encje)                                                      |
| :-------------------------- | :----------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------ |
| **Identity & Access Management** | Zarządzanie użytkownikami, rolami, uwierzytelnianiem i autoryzacją. | `User`, `SpecialistProfile`, `AdminProfile`, `Role`, `Permission`                                      |
| **Scheduling & Availability** | Definiowanie grafików specjalistów i zarządzanie dostępnymi slotami. | `SpecialistSchedule` (zawierający `TimeSlot` jako Value Object/Encję), `TimeSlot`                       |
| **Appointment Management**  | Proces rezerwacji, anulowania wizyt i egzekwowanie reguł biznesowych. | `Appointment`, `UserBookingPolicy`, `TimeOverlapPolicy`                                                 |
| **Admin & Override Management** | Konfiguracja systemu i zarządzanie wyjątkami/nadpisywaniem reguł.   | `SystemConfiguration`, `OverrideDecision`                                                               |
| **Audit & Notifications**   | Rejestrowanie zdarzeń systemowych i wysyłanie powiadomień.         | `AuditEvent`, `Notification` (jeśli powiadomienia są traktowane jako kluczowa encja do zarządzania) |

### Relacje Między Kontekstami

*   **IAM** dostarcza identyfikatorów (`UserId`, `SpecialistId`, `AdminId`) oraz informacji o rolach innym kontekstom.
*   **Scheduling & Availability** udostępnia `TimeSlot` do `Appointment Management`.
*   **Appointment Management** odwołuje się do `TimeSlotId` z `Scheduling & Availability` i do `UserId`/`SpecialistId` z `IAM`. Wysyła zdarzenia (`AppointmentBooked`, `AppointmentCancelled`) do `Audit & Notifications`. Konsultuje się z `Admin & Override Management` w sprawie wyjątków od reguł.
*   **Admin & Override Management** jest konsultowane przez `Appointment Management` w celu sprawdzenia, czy istnieją aktywne nadpisania reguł.
*   **Audit & Notifications** jest pasywnym odbiorcą zdarzeń ze wszystkich innych kontekstów.

### Dalsze Kroki (nie wymagane w zadaniu, ale wskazane w rzeczywistości)

*   **Definicja interfejsów:** Zdefiniowanie API dla każdego kontekstu.
*   **Agregaty i zdarzenia domenowe:** Pogłębiona analiza wewnątrz każdego kontekstu, aby zidentyfikować agregaty i zdarzenia domenowe, które będą służyć do komunikacji i zapewnienia spójności.
*   **Mapowanie kontekstów:** Zrozumienie, w jaki sposób konteksty wchodzą w interakcje (np. poprzez Anti-Corruption Layer, Shared Kernel, Customer/Supplier).
*   **Mechanizmy współbieżności:** Szczegółowe zaprojektowanie strategii obsługi równoczesnych operacji (np. optymistyczne/pesymistyczne blokady, kolejki zdarzeń).

Ta struktura zapewnia solidne podstawy do dalszego projektowania systemu, umożliwiając niezależny rozwój, testowanie i skalowanie poszczególnych komponentów.

---

# 2. Zaproponowana Architektura

Na podstawie przeprowadzonej analizy domen, która jasno zidentyfikowała Bounded Contexts, najbardziej odpowiednią architekturą systemu wydaje się być **architektura mikroserwisowa**. Pozwoli ona na niezależne rozwijanie, wdrażanie i skalowanie poszczególnych domen biznesowych, co jest kluczowe dla złożonych systemów z różnymi wymaganiami dotyczącymi wydajności i niezawodności poszczególnych części. Alternatywnie, dla mniejszych zespołów lub początkowych faz projektu, można rozważyć **modułowy monolit**, który jednak na dłuższą metę może ewoluować w kierunku mikroserwisów. W tej propozycji skupię się na architekturze mikroserwisowej, ponieważ naturalnie wynika ona z podziału na Bounded Contexts.

---

### 1. Proponowana Architektura Systemu: Mikroserwisy

Każdy z zidentyfikowanych Bounded Contexts zostanie zaimplementowany jako niezależny mikroserwis, zarządzający własnymi danymi i logiką biznesową. To podejście promuje luźne powiązanie (loose coupling) i wysoką spójność (high cohesion) w ramach każdego serwisu.

### 2. Proponowane Komponenty/Serwisy, Ich Odpowiedzialności i Komunikacja

Poniżej przedstawiono szczegóły dla każdego mikroserwisu:

#### 1. Identity Service (IAM)
*   **Odpowiedzialności:**
    *   Zarządzanie kontami użytkowników (User, Specialist, Admin) - CRUD.
    *   Zarządzanie rolami i uprawnieniami (Role, Permission).
    *   Uwierzytelnianie (authentication) użytkowników (logowanie, generowanie tokenów JWT/OAuth).
    *   Autoryzacja (authorization) - weryfikacja uprawnień dla żądań.
    *   Dostarczanie podstawowych informacji o użytkownikach (ID, rola).
*   **Baza Danych:** Własna baza danych (np. PostgreSQL), zawierająca tabele `Users`, `SpecialistProfiles`, `AdminProfiles`, `Roles`, `Permissions`.
*   **API:** REST API.
*   **Komunikacja z innymi serwisami:**
    *   **Synchroniczna (REST/gRPC):**
        *   **API Gateway/Inne Serwisy:** Walidacja tokenów, pobieranie szczegółów użytkownika/roli do autoryzacji.
        *   **Scheduling Service, Appointment Service, Admin Override Service:** Mogą zapytać o podstawowe dane użytkownika (np. czy dany ID to specjalista) lub weryfikować uprawnienia dla złożonych operacji.
    *   **Asynchroniczna (Wydarzenia - Message Broker):**
        *   Publikacja zdarzeń: `UserRegisteredEvent`, `SpecialistProfileUpdatedEvent`, `UserRoleChangedEvent`.
        *   **Audit & Notification Service:** Subskrybuje zdarzenia w celu rejestracji zmian i wysyłki powiadomień.

#### 2. Scheduling Service (Scheduling & Availability)
*   **Odpowiedzialności:**
    *   Zarządzanie grafikami specjalistów (`SpecialistSchedule`) - CRUD.
    *   Definiowanie i zarządzanie slotami czasowymi (`TimeSlot`) w ramach grafiku specjalisty (dodawanie, usuwanie, zmiana statusu na `AVAILABLE`, `BLOCKED`).
    *   Udostęnianie API do wyszukiwania dostępnych slotów (wg. specjalisty, daty).
    *   Zapewnienie spójności danych dotyczących grafiku specjalisty.
*   **Baza Danych:** Własna baza danych (np. PostgreSQL), zawierająca tabele `SpecialistSchedules`, `TimeSlots`.
*   **API:** REST API.
*   **Komunikacja z innymi serwisami:**
    *   **Synchroniczna (REST/gRPC):**
        *   **Appointment Service:**
            *   **Query:** Pobiera listę dostępnych `TimeSlot` dla danego specjalisty i daty.
            *   **Command:** Aktualizuje status `TimeSlot` na `PENDING_BOOKING` (po próbie rezerwacji) lub `BOOKED` (po potwierdzeniu rezerwacji) / `AVAILABLE` (po anulowaniu rezerwacji). Zapewnia to atomowość operacji na poziomie slotu.
    *   **Asynchroniczna (Wydarzenia - Message Broker):**
        *   Publikacja zdarzeń: `TimeSlotBlockedEvent`, `TimeSlotAvailableEvent`, `SpecialistScheduleUpdatedEvent`.
        *   **Audit & Notification Service:** Subskrybuje zdarzenia.

#### 3. Appointment Service (Appointment Management)
*   **Odpowiedzialności:**
    *   Zarządzanie rezerwacjami wizyt (`Appointment`) - rezerwacja, anulowanie, zmiana statusu (`BOOKED`, `CANCELLED`, `COMPLETED`).
    *   Implementacja logiki biznesowej:
        *   Weryfikacja dostępności slotu (`Scheduling Service`).
        *   Sprawdzanie limitu rezerwacji dla użytkownika (FR3), z konsultacją `Admin Override Service`.
        *   Sprawdzanie konfliktów czasowych dla rezerwującego użytkownika (FR10).
        *   Egzekwowanie zasad anulowania wizyt (FR5).
        *   Zapobieganie podwójnej rezerwacji (`FR4`, FR13, NFR1) - użycie blokad optymistycznych/pesymistycznych.
    *   Obsługa transakcji rezerwacji/anulowania jako agregatu domenowego.
*   **Baza Danych:** Własna baza danych (np. PostgreSQL), zawierająca tabele `Appointments`, `UserBookingPolicies`, `TimeOverlapPolicies`.
*   **API:** REST API.
*   **Komunikacja z innymi serwisami:**
    *   **Synchroniczna (REST/gRPC):**
        *   **Scheduling Service:**
            *   **Query:** `GET /slots?specialistId={id}&date={date}` (sprawdzenie dostępności).
            *   **Command:** `PUT /slots/{id}/status` (zmień status slotu na `PENDING_BOOKING` / `BOOKED` / `AVAILABLE`). Wymaga obsługi transakcji rozproszonych lub wzorca Saga.
        *   **Admin Override Service:** `GET /overrides?userId={id}&type=BOOKING_LIMIT` (sprawdzenie, czy jest aktywne nadpisanie limitu).
        *   **Identity Service:** Opcjonalnie do pobrania danych o User/Specialist, jeśli nie są wystarczające z tokena lub cachowane.
    *   **Asynchroniczna (Wydarzenia - Message Broker):**
        *   Publikacja zdarzeń: `AppointmentBookedEvent`, `AppointmentCancelledEvent`, `AppointmentCompletedEvent`.
        *   **Audit & Notification Service:** Subskrybuje te zdarzenia.

#### 4. Admin Override Service (Admin & Override Management)
*   **Odpowiedzialności:**
    *   Zarządzanie konfiguracją systemu (`SystemConfiguration`) - np. domyślne limity rezerwacji.
    *   Zarządzanie decyzjami administratora o nadpisaniu reguł (`OverrideDecision`) - CRUD.
    *   Dostarczanie API do weryfikacji aktywnych nadpisań.
    *   Zapewnienie, że tylko autoryzowani administratorzy mogą zarządzać nadpisaniami (autoryzacja przez Identity Service).
*   **Baza Danych:** Własna baza danych (np. PostgreSQL), zawierająca tabele `SystemConfigurations`, `OverrideDecisions`.
*   **API:** REST API.
*   **Komunikacja z innymi serwisami:**
    *   **Synchroniczna (REST/gRPC):**
        *   **Appointment Service:** `GET /overrides?userId={id}&type=BOOKING_LIMIT` (sprawdzenie aktywnych nadpisań).
    *   **Asynchroniczna (Wydarzenia - Message Broker):**
        *   Publikacja zdarzeń: `OverrideDecisionCreatedEvent`, `OverrideDecisionUpdatedEvent`.
        *   **Audit & Notification Service:** Subskrybuje zdarzenia.

#### 5. Audit & Notification Service (Audit & Notifications)
*   **Odpowiedzialności:**
    *   Rejestrowanie wszystkich istotnych zdarzeń systemowych (`AuditEvent`) pochodzących z innych serwisów.
    *   Przechowywanie logów audytu ze znacznikiem czasu.
    *   Zarządzanie i wysyłanie powiadomień (np. e-mail, SMS) na podstawie zarejestrowanych zdarzeń.
    *   Dostarczanie API do przeglądania logów audytu (dla administratorów).
*   **Baza Danych:** Własna baza danych (np. MongoDB dla elastyczności schematu logów, lub PostgreSQL dla strukturyzowanych `AuditEvents` i `Notifications`).
*   **API:** REST API (głównie do pobierania logów, może być dla statusu wysłanych powiadomień).
*   **Komunikacja z innymi serwisami:**
    *   **Asynchroniczna (Wydarzenia - Message Broker):**
        *   **Subskrybuje zdarzenia od wszystkich innych serwisów:** `UserRegisteredEvent`, `SpecialistProfileUpdatedEvent`, `AppointmentBookedEvent`, `AppointmentCancelledEvent`, `TimeSlotBlockedEvent`, `OverrideDecisionCreatedEvent` itd.
        *   Działa w modelu "fire-and-forget" - nie blokuje operacji biznesowych innych serwisów.

### 3. Schemat Komunikacji Między Serwisami

*   **Synchroniczna (Request/Response):**
    *   Używana, gdy serwis potrzebuje natychmiastowej odpowiedzi z innego serwisu do kontynuowania swojej operacji (np. `Appointment Service` pyta `Scheduling Service` o dostępność slotu lub `Admin Override Service` o aktywny override).
    *   Realizowana za pomocą **REST API** lub **gRPC**.
*   **Asynchroniczna (Event-Driven):**
    *   Używana dla zdarzeń, które nie wymagają natychmiastowej odpowiedzi i mogą być przetwarzane w tle, często przez wiele serwisów jednocześnie (np. `Appointment Service` publikuje `AppointmentBookedEvent`, na które reaguje `Audit & Notification Service`).
    *   Realizowana za pomocą **Message Broker** (np. Apache Kafka, RabbitMQ). Zapewnia to odporność na awarie i elastyczność.

### 4. Wspólne Komponenty Infrastrukturalne

*   **API Gateway:** Pojedynczy punkt wejścia dla wszystkich zewnętrznych klientów. Odpowiada za routing żądań do odpowiednich mikroserwisów, wstępną autoryzację i uwierzytelnianie (delegując do Identity Service), rate limiting, transformację protokołów.
*   **Service Discovery:** Mechanizm pozwalający serwisom odnajdywać się nawzajem (np. Eureka, Consul, Kubernetes DNS).
*   **Message Broker:** Centralna platforma do asynchronicznej komunikacji między serwisami (np. Apache Kafka lub RabbitMQ).
*   **Monitoring i Logging:** Zcentralizowany system do zbierania logów (np. ELK Stack, Grafana Loki) i metryk (Prometheus, Grafana) z wszystkich serwisów.
*   **CI/CD Pipeline:** Zautomatyzowany proces do budowania, testowania i wdrażania każdego mikroserwisu niezależnie.
*   **Container Orchestration:** Platforma do zarządzania kontenerami (np. Kubernetes), zapewniająca skalowanie, wysoką dostępność i automatyczne odzyskiwanie po awariach.

### 5. Zalety Proponowanej Architektury

*   **Skalowalność:** Każdy serwis może być skalowany niezależnie, w zależności od jego obciążenia.
*   **Odporność:** Awaria jednego serwisu nie musi wpływać na cały system.
*   **Niezależny rozwój i wdrażanie:** Zespoły mogą pracować nad różnymi serwisami bez wzajemnego blokowania się.
*   **Elastyczność technologiczna:** Pozwala na użycie różnych technologii i języków programowania dla różnych serwisów, jeśli jest to uzasadnione.
*   **Wsparcie dla DDD:** Bezpośrednie mapowanie Bounded Contexts na mikroserwisy ułatwia zarządzanie złożonością domenową.

### 6. Wyzwania

*   **Złożoność operacyjna:** Zarządzanie wieloma serwisami, ich bazami danych i komunikacją jest bardziej skomplikowane niż w monolicie.
*   **Rozproszone transakcje:** Operacje obejmujące wiele serwisów (np. rezerwacja, która zmienia status slotu w `Scheduling Service` i tworzy `Appointment` w `Appointment Service`) wymagają wzorców takich jak Saga.
*   **Spójność danych:** Zapewnienie ostatecznej spójności (eventual consistency) i radzenie sobie z nią w interfejsach użytkownika.

Ta architektura stanowi solidną podstawę do budowy skalowalnego i łatwego w utrzymaniu systemu, w pełni wykorzystując potencjał analizy Domain-Driven Design.

---

# 3. API i Modele Danych

Fantastyczna analiza architektury! Podział na mikroserwisy zgodnie z Bounded Contexts jest solidnym fundamentem. Poniżej przedstawiam propozycję kluczowych endpointów API (RESTful) i ogólne struktury baz danych dla każdego serwisu, uwzględniając NFR dotyczące wydajności.

---

## Proponowane Endpointy API (RESTful) i Struktury Baz Danych

### 1. Identity Service (IAM)

*   **Cel wydajnościowy:** Szybka autentykacja i autoryzacja, niskie opóźnienia przy pobieraniu podstawowych danych użytkowników.
*   **Technologia DB:** PostgreSQL (ze względu na silne relacje, ACID i dojrzałość).

#### Kluczowe Endpointy API:

*   **Użytkownicy (Users):**
    *   `POST /auth/register`
        *   **Body:** `{ "email": "...", "password": "...", "role": "USER", "firstName": "...", "lastName": "..." }`
        *   **Opis:** Rejestracja nowego użytkownika.
    *   `POST /auth/login`
        *   **Body:** `{ "email": "...", "password": "..." }`
        *   **Response:** `{ "accessToken": "...", "refreshToken": "...", "userId": "...", "role": "..." }`
        *   **Opis:** Uwierzytelnianie, generowanie tokenów JWT.
    *   `POST /auth/refresh-token`
        *   **Body:** `{ "refreshToken": "..." }`
        *   **Response:** `{ "accessToken": "...", "refreshToken": "..." }`
        *   **Opis:** Odświeżanie tokena dostępu.
    *   `GET /users/{userId}`
        *   **Response:** `{ "id": "...", "email": "...", "firstName": "...", "lastName": "...", "role": "...", "status": "..." }`
        *   **Opis:** Pobieranie podstawowych danych użytkownika. Może być używane wewnętrznie przez inne serwisy.
    *   `PUT /users/{userId}`
        *   **Body:** `{ "firstName": "...", "lastName": "...", "email": "..." }`
        *   **Opis:** Aktualizacja danych użytkownika.
    *   `PUT /users/{userId}/password`
        *   **Body:** `{ "oldPassword": "...", "newPassword": "..." }`
        *   **Opis:** Zmiana hasła użytkownika.
    *   `PUT /users/{userId}/role`
        *   **Body:** `{ "roleId": "..." }`
        *   **Opis:** Zmiana roli użytkownika (wymaga uprawnień administratora).
    *   `POST /specialists`
        *   **Body:** `{ "userId": "...", "bio": "...", "specialty": "..." }`
        *   **Opis:** Tworzenie profilu specjalisty (lub `PUT /users/{userId}/specialist-profile` jeśli profile są ściśle powiązane z użytkownikiem).
    *   `GET /specialists/{specialistId}`
        *   **Response:** `{ "userId": "...", "bio": "...", "specialty": "...", "contactInfo": "..." }`
        *   **Opis:** Pobieranie profilu specjalisty.

#### Ogólne Struktury Baz Danych:

*   **`users`**
    *   `id` (UUID, PK)
    *   `email` (VARCHAR, UNIQUE, NOT NULL, INDEXED) - do szybkiego logowania.
    *   `password_hash` (VARCHAR, NOT NULL)
    *   `first_name` (VARCHAR, NOT NULL)
    *   `last_name` (VARCHAR, NOT NULL)
    *   `role_id` (UUID, FK do `roles.id`, INDEXED)
    *   `status` (VARCHAR, np. 'ACTIVE', 'INACTIVE', 'BLOCKED')
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `updated_at` (TIMESTAMP, NOT NULL)
*   **`roles`**
    *   `id` (UUID, PK)
    *   `name` (VARCHAR, UNIQUE, NOT NULL, np. 'USER', 'SPECIALIST', 'ADMIN')
*   **`permissions`**
    *   `id` (UUID, PK)
    *   `name` (VARCHAR, UNIQUE, NOT NULL, np. 'CAN_BOOK_APPOINTMENT', 'CAN_MANAGE_SCHEDULE')
*   **`role_permissions`** (tabela pośrednicząca)
    *   `role_id` (UUID, FK do `roles.id`)
    *   `permission_id` (UUID, FK do `permissions.id`)
    *   (PK: `role_id`, `permission_id`)
*   **`specialist_profiles`**
    *   `user_id` (UUID, PK, FK do `users.id`) - 1:1 relacja
    *   `bio` (TEXT)
    *   `specialty` (VARCHAR)
    *   `contact_info` (JSONB, np. `{ "phone": "...", "email": "..." }`)
    *   `average_rating` (NUMERIC) - może być też zaciągane z innego serwisu
*   **`admin_profiles`**
    *   `user_id` (UUID, PK, FK do `users.id`)
    *   `admin_level` (VARCHAR, np. 'SUPER_ADMIN', 'MODERATOR')

### 2. Scheduling Service (Scheduling & Availability)

*   **Cel wydajnościowy:** Szybkie wyszukiwanie dostępnych slotów, atomowe aktualizacje statusów slotów.
*   **Technologia DB:** PostgreSQL (dla transakcji i zapytań geoprzestrzennych/czasowych, jeśli byłyby wymagane).

#### Kluczowe Endpointy API:

*   **Grafiki Specjalistów (Specialist Schedules):**
    *   `POST /schedules`
        *   **Body:** `{ "specialistId": "...", "startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD", "defaultSlotDurationMinutes": 30 }`
        *   **Opis:** Tworzenie nowego grafiku.
    *   `GET /schedules/{specialistId}`
        *   **Response:** `{ "id": "...", "specialistId": "...", "startDate": "...", "endDate": "...", "timeSlots": [...] }`
        *   **Opis:** Pobieranie grafiku specjalisty wraz ze slotami.
*   **Sloty Czasowe (Time Slots):**
    *   `GET /slots?specialistId={specialistId}&date={YYYY-MM-DD}`
        *   **Response:** `[{ "id": "...", "startTime": "...", "endTime": "...", "status": "..." }]`
        *   **Opis:** Wyszukiwanie dostępnych slotów dla danego specjalisty i daty. (Kluczowy endpoint dla `Appointment Service`).
    *   `POST /slots`
        *   **Body:** `{ "scheduleId": "...", "startTime": "YYYY-MM-DDTHH:MM:SSZ", "endTime": "YYYY-MM-DDTHH:MM:SSZ", "status": "AVAILABLE" }`
        *   **Opis:** Dodawanie pojedynczego slotu.
    *   `PATCH /slots/{slotId}/status`
        *   **Body:** `{ "newStatus": "PENDING_BOOKING" | "BOOKED" | "AVAILABLE" | "BLOCKED" }`, opcjonalnie `{"version": 1}` dla optymistycznej blokady.
        *   **Opis:** Atomowa zmiana statusu slotu (np. przez `Appointment Service`). Kluczowe dla `FR4`, `FR13`, `NFR1`. Zapewnienie atomowości na poziomie DB (np. `UPDATE ... WHERE status='AVAILABLE' AND version={version}`).
    *   `PUT /slots/{slotId}`
        *   **Body:** `{ "startTime": "...", "endTime": "...", "status": "..." }`
        *   **Opis:** Pełna aktualizacja slotu (np. przez specjalistę).

#### Ogólne Struktury Baz Danych:

*   **`specialist_schedules`**
    *   `id` (UUID, PK)
    *   `specialist_id` (UUID, NOT NULL, INDEXED) - Id specjalisty z Identity Service
    *   `start_date` (DATE, NOT NULL)
    *   `end_date` (DATE, NOT NULL)
    *   `default_slot_duration_minutes` (INTEGER)
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `updated_at` (TIMESTAMP, NOT NULL)
*   **`time_slots`**
    *   `id` (UUID, PK)
    *   `schedule_id` (UUID, FK do `specialist_schedules.id`, INDEXED)
    *   `specialist_id` (UUID, NOT NULL, INDEXED) - Denormalizacja dla szybszych zapytań
    *   `start_time` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)
    *   `end_time` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)
    *   `status` (VARCHAR, ENUM: 'AVAILABLE', 'BLOCKED', 'PENDING_BOOKING', 'BOOKED', NOT NULL, INDEXED)
    *   `version` (INTEGER, NOT NULL) - Do optymistycznej blokady, szczególnie dla `PATCH /slots/{slotId}/status`.
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `updated_at` (TIMESTAMP, NOT NULL)
    *   **Indeksy dla wydajności:**
        *   `CREATE INDEX idx_slots_specialist_date ON time_slots (specialist_id, start_time, status) WHERE status = 'AVAILABLE';`
        *   `CREATE UNIQUE INDEX idx_slots_specialist_time_unique ON time_slots (specialist_id, start_time) WHERE status IN ('PENDING_BOOKING', 'BOOKED');` (zapobiega podwójnej rezerwacji).

### 3. Appointment Service (Appointment Management)

*   **Cel wydajnościowy:** Szybkie tworzenie i anulowanie rezerwacji, unikanie konfliktów i podwójnych rezerwacji (NFR1, FR4, FR13).
*   **Technologia DB:** PostgreSQL (dla transakcyjności i silnej spójności).

#### Kluczowe Endpointy API:

*   **Rezerwacje (Appointments):**
    *   `POST /appointments`
        *   **Body:** `{ "userId": "...", "specialistId": "...", "slotId": "..." }`
        *   **Opis:** Rezerwacja wizyty. Wymaga komunikacji z `Scheduling Service` (sprawdzenie dostępności, zmiana statusu slotu na `PENDING_BOOKING` -> `BOOKED`). Może wymagać wzorca Saga.
    *   `GET /appointments/{appointmentId}`
        *   **Response:** `{ "id": "...", "userId": "...", "specialistId": "...", "slotId": "...", "startTime": "...", "endTime": "...", "status": "..." }`
        *   **Opis:** Pobieranie szczegółów rezerwacji.
    *   `GET /appointments?userId={userId}&status={status}`
        *   **Response:** `[{ ... }]`
        *   **Opis:** Pobieranie listy rezerwacji dla danego użytkownika/specjalisty z filtrowaniem po statusie.
    *   `PATCH /appointments/{appointmentId}/cancel`
        *   **Body:** `{ "reason": "...", "userId": "..." }`
        *   **Opis:** Anulowanie rezerwacji. Wymaga aktualizacji statusu slotu w `Scheduling Service` na `AVAILABLE` i sprawdzenia reguł anulowania (FR5).
    *   `PATCH /appointments/{appointmentId}/complete`
        *   **Opis:** Oznaczanie rezerwacji jako zakończonej (tylko dla specjalisty/admina).

#### Ogólne Struktury Baz Danych:

*   **`appointments`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, NOT NULL, INDEXED) - Id użytkownika z Identity Service
    *   `specialist_id` (UUID, NOT NULL, INDEXED) - Id specjalisty z Identity Service
    *   `slot_id` (UUID, NOT NULL, UNIQUE, INDEXED) - Id slotu z Scheduling Service. Zapewnia unikalność rezerwacji dla danego slotu.
    *   `start_time` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED) - Denormalizacja dla szybszych zapytań
    *   `end_time` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED) - Denormalizacja
    *   `status` (VARCHAR, ENUM: 'PENDING', 'BOOKED', 'CANCELLED', 'COMPLETED', NOT NULL, INDEXED)
    *   `cancellation_reason` (TEXT)
    *   `booked_at` (TIMESTAMP, NOT NULL)
    *   `cancelled_at` (TIMESTAMP)
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `updated_at` (TIMESTAMP, NOT NULL)
    *   **Indeksy dla wydajności:**
        *   `CREATE INDEX idx_appointments_user_status ON appointments (user_id, status);`
        *   `CREATE INDEX idx_appointments_specialist_status ON appointments (specialist_id, status);`
        *   `CREATE INDEX idx_appointments_user_time ON appointments (user_id, start_time, end_time);` (do sprawdzania konfliktów czasowych FR10).
*   **`user_booking_policies`**
    *   `user_id` (UUID, PK, FK do `Identity Service.users.id`)
    *   `max_concurrent_appointments` (INTEGER, NOT NULL)
    *   `max_appointments_per_day` (INTEGER, NOT NULL)
    *   `max_appointments_per_week` (INTEGER, NOT NULL)
*   **`cancellation_rules`**
    *   `id` (UUID, PK)
    *   `min_hours_before_cancellation` (INTEGER, NOT NULL)
    *   `penalty_percentage` (NUMERIC(5,2))
    *   `effective_from` (TIMESTAMP)
    *   `effective_to` (TIMESTAMP)

### 4. Admin Override Service (Admin & Override Management)

*   **Cel wydajnościowy:** Szybkie pobieranie aktywnych nadpisań.
*   **Technologia DB:** PostgreSQL (dla transakcyjności i spójności danych konfiguracyjnych).

#### Kluczowe Endpointy API:

*   **Konfiguracja Systemu (System Configurations):**
    *   `GET /config/{key}`
        *   **Response:** `{ "key": "...", "value": "..." }`
        *   **Opis:** Pobieranie wartości konfiguracyjnej. Może być cachowane.
    *   `PUT /config/{key}`
        *   **Body:** `{ "value": "..." }`
        *   **Opis:** Aktualizacja wartości konfiguracyjnej (wymaga uprawnień admina).
*   **Decyzje o Nadpisaniu (Override Decisions):**
    *   `GET /overrides?userId={userId}&type={type}`
        *   **Response:** `[{ "id": "...", "userId": "...", "overrideType": "...", "value": "...", "isActive": true }]`
        *   **Opis:** Pobieranie aktywnych nadpisań dla danego użytkownika i typu (np. dla `Appointment Service` do `FR3`). Kluczowy endpoint dla innych serwisów.
    *   `POST /overrides`
        *   **Body:** `{ "userId": "...", "overrideType": "BOOKING_LIMIT", "value": 5, "reason": "...", "adminId": "...", "expiresAt": "..." }`
        *   **Opis:** Tworzenie nowej decyzji o nadpisaniu.
    *   `DELETE /overrides/{overrideId}`
        *   **Opis:** Usuwanie decyzji o nadpisaniu.

#### Ogólne Struktury Baz Danych:

*   **`system_configurations`**
    *   `key` (VARCHAR, PK)
    *   `value` (TEXT, NOT NULL)
    *   `description` (TEXT)
    *   `updated_at` (TIMESTAMP, NOT NULL)
*   **`override_decisions`**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, NOT NULL, INDEXED) - Id użytkownika z Identity Service
    *   `override_type` (VARCHAR, ENUM: 'BOOKING_LIMIT', 'CANCELLATION_FEE', NOT NULL, INDEXED)
    *   `value` (TEXT, NOT NULL) - Wartość nadpisania (np. "5" dla limitu, "false" dla zwolnienia z opłaty)
    *   `reason` (TEXT)
    *   `admin_id` (UUID, FK do `Identity Service.users.id`)
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `expires_at` (TIMESTAMP, INDEXED) - Kiedy nadpisanie przestaje być aktywne.
    *   `is_active` (BOOLEAN, GENERATED ALWAYS AS (expires_at IS NULL OR expires_at > NOW()) STORED) - Kolumna wirtualna/indeksowana dla szybkiego filtrowania.
    *   **Indeksy dla wydajności:**
        *   `CREATE INDEX idx_overrides_user_type_active ON override_decisions (user_id, override_type) WHERE is_active = true;`

### 5. Audit & Notification Service

*   **Cel wydajnościowy:** Wysoka przepustowość zapisu (logi), elastyczność schematu danych, szybkie pobieranie logów.
*   **Technologia DB:** MongoDB (dla `audit_events` ze względu na elastyczny schemat i wysoką skalowalność zapisu), PostgreSQL (dla `notifications` ze względu na bardziej strukturyzowane dane i potrzebę transakcji wewnętrznych np. przy śledzeniu statusu wysyłki).

#### Kluczowe Endpointy API:

*   **Logi Audytu (Audit Logs):**
    *   `GET /audit-logs?userId={userId}&eventType={type}&startDate={date}&endDate={date}&page={page}&size={size}`
        *   **Response:** `[{ "id": "...", "eventType": "...", "entityType": "...", "entityId": "...", "userId": "...", "timestamp": "...", "details": {} }]`
        *   **Opis:** Pobieranie i filtrowanie logów audytu.
*   **Powiadomienia (Notifications):**
    *   `GET /notifications?userId={userId}&status={status}&type={type}`
        *   **Response:** `[{ "id": "...", "userId": "...", "type": "EMAIL", "status": "SENT", "subject": "...", "sentAt": "..." }]`
        *   **Opis:** Pobieranie statusu wysłanych powiadomień.

#### Ogólne Struktury Baz Danych:

*   **MongoDB: `audit_events` collection**
    *   `_id` (ObjectId, PK)
    *   `event_type` (STRING, e.g., 'APPOINTMENT_BOOKED', 'USER_REGISTERED', INDEXED)
    *   `entity_type` (STRING, e.g., 'APPOINTMENT', 'USER', 'TIME_SLOT', INDEXED)
    *   `entity_id` (UUID, ID of the affected entity, INDEXED)
    *   `user_id` (UUID, ID of the user who initiated the event, INDEXED)
    *   `timestamp` (ISODate, NOT NULL, INDEXED)
    *   `details` (DOCUMENT, JSON object z dowolnymi szczegółami zdarzenia)
    *   `source_service` (STRING, nazwa serwisu, który wygenerował zdarzenie)
    *   **Indeksy dla wydajności (MongoDB):**
        *   `{ timestamp: -1 }` (dla najnowszych logów).
        *   `{ user_id: 1, timestamp: -1 }` (dla logów użytkownika).
        *   `{ entity_type: 1, entity_id: 1, timestamp: -1 }` (dla logów związanych z konkretnym obiektem).
*   **PostgreSQL: `notifications` table**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, NOT NULL, INDEXED) - Adresat powiadomienia
    *   `type` (VARCHAR, ENUM: 'EMAIL', 'SMS', 'IN_APP', NOT NULL)
    *   `subject` (TEXT)
    *   `body` (TEXT, NOT NULL)
    *   `status` (VARCHAR, ENUM: 'PENDING', 'SENT', 'FAILED', 'READ', NOT NULL, INDEXED)
    *   `sent_at` (TIMESTAMP)
    *   `attempts` (INTEGER, domyślnie 0)
    *   `last_attempt_at` (TIMESTAMP)
    *   `error_message` (TEXT)
    *   `created_at` (TIMESTAMP, NOT NULL)
    *   `updated_at` (TIMESTAMP, NOT NULL)
    *   **Indeksy dla wydajności:**
        *   `CREATE INDEX idx_notifications_user_status ON notifications (user_id, status);`
        *   `CREATE INDEX idx_notifications_created_at ON notifications (created_at);` (do czyszczenia starych powiadomień).

---

### API Gateway (Wspólny Komponent Infrastrukturalny)

Choć nie jest to mikroserwis, jest kluczowe dla zarządzania API:

*   **Odpowiedzialności:**
    *   **Autentykacja i autoryzacja:** Zintegrowany z `Identity Service`. Wszystkie zewnętrzne żądania najpierw przechodzą walidację tokena JWT. Następnie kontekst użytkownika (ID, role, uprawnienia) jest przekazywany do mikroserwisu docelowego (np. jako nagłówki).
    *   **Routing:** Przekierowanie żądań do odpowiednich mikroserwisów.
    *   **Rate Limiting:** Ograniczanie liczby żądań.
    *   **Logging i Monitoring:** Podstawowe zbieranie metryk i logów.

*   **Kluczowe "Endpointy" (w sensie routingu):**
    *   `GET /api/v1/users/{userId}` -> `Identity Service`
    *   `POST /api/v1/auth/login` -> `Identity Service`
    *   `GET /api/v1/specialists/{specialistId}/slots` -> `Scheduling Service`
    *   `POST /api/v1/appointments` -> `Appointment Service`
    *   `GET /api/v1/admin/overrides` -> `Admin Override Service`
    *   `GET /api/v1/audit-logs` -> `Audit & Notification Service`

---

### Uwagi dotyczące wydajności (NFR) w ogólnym kontekście:

1.  **Indeksowanie:** Każda propozycja bazy danych uwzględnia kluczowe indeksy na polach, które będą często używane w zapytaniach `WHERE` i `JOIN`.
2.  **Denormalizacja:** W kilku miejscach (`time_slots.specialist_id`, `appointments.start_time`, `appointments.end_time`) wprowadzono denormalizację, aby uniknąć kosztownych złączeń z innymi tabelami lub serwisami, przyspieszając najczęściej wykonywane zapytania.
3.  **Blokady Optymistyczne/Pesymistyczne:** `Scheduling Service` (`time_slots.version`) jest zaprojektowany z myślą o optymistycznej blokadzie, co jest kluczowe dla zapobiegania podwójnej rezerwacji i problemów `FR4`, `FR13`, `NFR1`.
4.  **Asynchroniczność:** Wykorzystanie brokera wiadomości (Kafka/RabbitMQ) do zdarzeń minimalizuje wzajemne blokowanie się serwisów i pozwala na niezależne przetwarzanie w tle (np. `Audit & Notification Service`).
5.  **Cache:** Dla często odczytywanych danych (np. konfiguracja z `Admin Override Service`, podstawowe dane użytkownika z `Identity Service`) można rozważyć warstwę cache (Redis, Memcached) w ramach serwisu lub na poziomie API Gateway.
6.  **Paginacja i Filtrowanie:** Wszystkie endpointy listujące zasoby (np. `/appointments`, `/audit-logs`) powinny wspierać paginację (`page`, `size`) i filtrowanie, aby unikać pobierania zbyt dużych zestawów danych.
7.  **Architektura Serwisu:** Mikroserwisy pozwalają na niezależne skalowanie każdego komponentu. Np. `Audit & Notification Service` może być skalowany horyzontalnie, aby obsłużyć dużą liczbę zdarzeń.

Ta propozycja stanowi kompleksowy zestaw endpointów i struktur baz danych, który powinien dobrze współgrać z przedstawioną architekturą mikroserwisową i spełnić wymagania wydajnościowe.