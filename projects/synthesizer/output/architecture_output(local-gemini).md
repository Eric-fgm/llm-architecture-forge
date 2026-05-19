# 1. Analiza Domen i Encji

Jako doświadczony architekt oprogramowania, analizując powyższe wymagania, zidentyfikowałem następujące główne Domenty (Bounded Contexts) oraz kluczowe Encje Domenowe. Podejście to ma na celu zapewnienie jasnych granic odpowiedzialności, ułatwienie skalowalności i zarządzania złożonością, a także wsparcie dla różnych poziomów spójności danych.

---

## Analiza Wymagań i Identyfikacja Domen (Bounded Contexts)

Na podstawie wymagań, wyróżniam pięć głównych Domen (Bounded Contexts):

1.  **Identity & Access Management (IAM)**
    *   **Cel:** Zarządzanie użytkownikami, ich rolami, uwierzytelnianiem i autoryzacją dostępu do systemu. To podstawa bezpieczeństwa i personalizacji.
    *   **Uzasadnienie:** Wymagania dotyczące ról (`User`, `Specialist`, `Admin`) oraz dostępu do danych (`FR9`, `NFR3`) wskazują na potrzebę wydzielenia tej domeny. Jest to standardowy kontekst w większości systemów.
    *   **Zależności:** Dostarcza identyfikatorów użytkowników i ich ról do wszystkich innych kontekstów.

2.  **Specialist Schedule Management**
    *   **Cel:** Umożliwienie specjalistom definiowania i zarządzania ich dostępnymi terminami oraz ich grafikiem pracy. To jest "strona podażowa" wizyt.
    *   **Uzasadnienie:** `FR7` (zarządzanie grafikiem), `FR11` (blokady slotów przez specjalistę) wyraźnie określają odpowiedzialność specjalisty za udostępnianie i modyfikowanie swoich wolnych terminów. Ten kontekst skupia się na *definicji* i *udostępnianiu* slotów.
    *   **Zależności:** Publikuje informacje o dostępnych/zmodyfikowanych `TimeSlot` do `Appointment Booking`.

3.  **Appointment Booking**
    *   **Cel:** Centralny kontekst odpowiedzialny za proces rezerwacji, zarządzanie cyklem życia wizyty (rezerwacja, anulowanie, ukończenie) oraz egzekwowanie kluczowych reguł biznesowych (limity rezerwacji, brak podwójnych rezerwacji, konflikty czasowe).
    *   **Uzasadnienie:** Większość wymagań funkcjonalnych (`FR1` do `FR6`, `FR8`, `FR10`, `FR13`, `AC1` do `AC6`) odnosi się do tego kontekstu. To tutaj występuje największa złożoność związana ze spójnością danych i operacjami współbieżnymi (`FR4`, `NFR1`). `AppointmentSlot` będzie tutaj kluczowym Agregatem do zarządzania współbieżnością.
    *   **Zależności:** Konsumuje dane o `TimeSlot` z `Specialist Schedule Management`, wymaga `UserID` z `IAM`. `System Administration` może modyfikować jego polityki lub stan.

4.  **System Administration**
    *   **Cel:** Zarządzanie globalnymi ustawieniami systemu, nadzorowanie operacji oraz możliwość nadpisywania reguł biznesowych w sytuacjach wyjątkowych.
    *   **Uzasadnienie:** `Admin` rola (`Roles`), `FR3` (Admin może zezwolić na przekroczenie limitu), `US6` (Admin nadpisuje ograniczenia) wskazują na specyficzną, uprzywilejowaną funkcjonalność, która często wymaga oddzielenia od standardowych przepływów biznesowych. Działa jako "brama do wyjątków".
    *   **Zależności:** Może wysyłać polecenia modyfikujące stan lub polityki w `Appointment Booking` oraz `Specialist Schedule Management`.

5.  **Audit & Reporting**
    *   **Cel:** Rejestrowanie wszystkich istotnych operacji i zdarzeń w systemie dla celów audytu, analizy i potencjalnego raportowania.
    *   **Uzasadnienie:** `FR12` (historia operacji), `NFR4` (audyt) jasno wskazują na potrzebę zbierania logów. Ten kontekst jest zazwyczaj reaktywny i jest odbiorcą zdarzeń ze wszystkich innych kontekstów. Zapewnia to perspektywę "eventualnej spójności".
    *   **Zależności:** Konsumuje zdarzenia (events) ze wszystkich innych kontekstów.

---

## Główne Encje Domenowe (Aggregate Roots & Key Entities)

Dla każdego zidentyfikowanego Bounded Contextu, przedstawiam kluczowe encje domenowe, ze wskazaniem na te, które prawdopodobnie będą Aggregate Root (AR) w ich kontekstach.

### 1. Identity & Access Management (IAM)

*   **`User` (AR)**: Reprezentuje użytkownika systemu (User, Specialist, Admin). Zawiera dane uwierzytelniające, podstawowe dane profilowe i powiązane `Role`.
    *   Atrybuty: `UserID`, `Username`, `PasswordHash`, `Email`, `FirstName`, `LastName`, `RoleID`.
*   **`Role`**: Definiuje uprawnienia przypisane do typu użytkownika (np. "BasicUser", "Specialist", "Administrator").
    *   Atrybuty: `RoleID`, `Name`, `Description`, `Permissions`.
*   **`Permission`**: Granularne uprawnienie (np. "book_appointment", "manage_schedule", "override_booking_limit").

### 2. Specialist Schedule Management

*   **`Specialist` (AR)**: Reprezentuje specjalistę. Może zawierać ogólne informacje o specjaliście, które nie są bezpośrednio związane z jego harmonogramem. Jest powiązany z `User` z kontekstu IAM.
    *   Atrybuty: `SpecialistID` (FK do `UserID` z IAM), `Specialization`, `Description`.
*   **`Schedule` (AR)**: Harmonogram specjalisty na dany okres (np. tydzień, miesiąc). Agreguje `TimeSlot`y. Możliwe, że jest to część Agregatu `Specialist`.
    *   Atrybuty: `ScheduleID`, `SpecialistID`, `StartDate`, `EndDate`.
*   **`TimeSlot`**: Definiuje konkretny, dostępny przedział czasowy, który specjalista oferuje (np. 9:00-9:30, 10:00-10:30). Stan początkowy to `AVAILABLE` lub `BLOCKED_BY_SPECIALIST`. Jest to *definicja* slotu, który może zostać zarezerwowany.
    *   Atrybuty: `TimeSlotID`, `SpecialistID`, `StartTime`, `EndTime`, `InitialStatus` (AVAILABLE, BLOCKED_BY_SPECIALIST), `CreatedAt`, `LastModifiedAt`.
    *   *Uwaga:* Ten `TimeSlot` reprezentuje *potencjalną* dostępność. Jego *rzeczywisty* status rezerwacji (`BOOKED`, `CANCELLED`) będzie zarządzany przez `Appointment Booking`.

### 3. Appointment Booking

*   **`AppointmentSlot` (AR)**: **Kluczowy Aggregate Root dla spójności i współbieżności.** Reprezentuje konkretny, indywidualny slot czasowy, który można zarezerwować. Jest to "instancja" `TimeSlot` z `Specialist Schedule Management`. To ten Agregat jest "blokowany" podczas próby rezerwacji, aby zapobiec podwójnej rezerwacji (`FR4`, `NFR1`).
    *   Atrybuty: `AppointmentSlotID` (może być powiązany z `TimeSlotID` lub unikalnie generowany), `SpecialistID`, `StartTime`, `EndTime`, `CurrentStatus` (AVAILABLE, BOOKED, CANCELLED, COMPLETED, BLOCKED).
    *   Metody: `Book()`, `Cancel()`, `Block()`, `Complete()`.
*   **`Appointment` (AR)**: Reprezentuje rezerwację wizyty przez `User`. Agreguje dane rezerwacji i odnosi się do `AppointmentSlot`.
    *   Atrybuty: `AppointmentID`, `UserID` (FK do `UserID` z IAM), `AppointmentSlotID` (FK do `AppointmentSlot`), `BookingTime`, `Status` (BOOKED, CANCELLED, COMPLETED), `Notes`.
    *   Metody: `RequestBooking()`, `ConfirmBooking()`, `CancelBooking()`.
*   **`BookingPolicy`**: Wartość obiektu lub encja konfiguracji, zawierająca reguły biznesowe takie jak:
    *   `MaxActiveBookingsPerUser`: (np. 3) (`FR3`)
    *   `CancellationDeadlineHours`: (np. 24) (`FR5`)
    *   `AllowOverlappingAppointments`: Globalna flaga lub dla konkretnych użytkowników/specjalistów (`FR10`, `AC6`).

### 4. System Administration

*   **`SystemConfiguration` (AR)**: Przechowuje globalne ustawienia systemu, które mogą wpływać na działanie innych kontekstów.
    *   Atrybuty: `Key`, `Value` (np. "MaxActiveBookingsDefault", "24hCancellationThreshold").
*   **`AdminOverrideLog`**: Rejestruje działania administratora, które nadpisały standardowe reguły systemu (np. zezwolenie na przekroczenie limitu, ręczna modyfikacja statusu wizyty).
    *   Atrybuty: `OverrideID`, `AdminUserID`, `ActionType`, `TargetEntityID`, `OldValue`, `NewValue`, `Reason`, `Timestamp`.

### 5. Audit & Reporting

*   **`AuditRecord`**: Encja reprezentująca pojedynczy wpis w logu audytu. Jest tworzona w odpowiedzi na zdarzenia z innych kontekstów.
    *   Atrybuty: `RecordID`, `Timestamp`, `EventType`, `ActorID` (UserID/SpecialistID/AdminID), `EntityID` (np. `AppointmentID`, `AppointmentSlotID`), `Details` (JSON z kontekstowymi danymi zdarzenia), `SourceContext`.

---

### Relacje i Przepływy kluczowe:

*   **Rezerwacja wizyty:**
    1.  `User` z `IAM` przegląda dostępne `AppointmentSlot` z `Appointment Booking` (które powstały z `TimeSlot`ów z `Specialist Schedule Management`).
    2.  `User` wybiera `AppointmentSlot` i próbuje go zarezerwować, tworząc `Appointment`.
    3.  `Appointment` sprawdza `BookingPolicy` (limit aktywnych rezerwacji dla `User`, brak nakładania się czasowego).
    4.  Jeśli reguły są spełnione, `Appointment` próbuje "zarezerwować" (zmienić status na `BOOKED`) odpowiedni `AppointmentSlot`. To operacja transakcyjna na `AppointmentSlot` (AR) w celu zapewnienia `FR4`.
    5.  `Appointment` zostaje stworzony ze statusem `BOOKED`.
    6.  Wszystkie te operacje są logowane w `Audit & Reporting`.

*   **Zarządzanie grafikiem:**
    1.  `Specialist` z `IAM` zarządza swoim `Schedule` w `Specialist Schedule Management`, dodając/usuwając `TimeSlot`y lub oznaczając je jako `BLOCKED_BY_SPECIALIST`.
    2.  Zmiany w `TimeSlot` są propagowane do `Appointment Booking` (np. jako zdarzenia `TimeSlotCreated`, `TimeSlotModified`), które tworzy/aktualizuje/usuwa odpowiednie `AppointmentSlot`y.
    3.  Zmiany są logowane w `Audit & Reporting`.

*   **Nadpisywanie reguł:**
    1.  `Admin` z `IAM` używa `System Administration` do modyfikacji `SystemConfiguration` lub wykonania `AdminOverrideAction`.
    2.  `System Administration` wysyła polecenie do `Appointment Booking` (np. aby zezwolić `UserID` na przekroczenie limitu rezerwacji lub ręcznie zmienić status `AppointmentSlot` na `BLOCKED`).
    3.  Te działania są szczegółowo logowane w `Audit & Reporting`.

Ta struktura zapewnia elastyczność, rozszerzalność i możliwość niezależnego rozwijania i skalowania poszczególnych części systemu, jednocześnie dbając o kluczowe aspekty spójności danych i reguł biznesowych.

---

# 2. Zaproponowana Architektura

Na podstawie szczegółowej analizy domen, proponuję architekturę systemu opartą na mikrousługach (Microservices Architecture), z zastosowaniem wzorców Domain-Driven Design (DDD), Event-Driven Architecture oraz CQRS (Command Query Responsibility Segregation) dla kluczowego kontekstu rezerwacji.

---

### 1. Wybór Wzorców Architektonicznych i Uzasadnienie

**a) Microservices Architecture (Architektura Mikrousług)**
*   **Uzasadnienie:** Analiza domen wyraźnie wyodrębniła pięć niezależnych kontekstów (Bounded Contexts): `Identity & Access Management`, `Specialist Schedule Management`, `Appointment Booking`, `System Administration`, `Audit & Reporting`. Architektura mikrousług jest idealnie dopasowana do tego podziału, umożliwiając każdemu kontekstowi funkcjonowanie jako niezależna usługa.
    *   **Korzyści:**
        *   **Skalowalność (NFR1):** Każda usługa może być skalowana niezależnie w zależności od zapotrzebowania (np. `Appointment Booking` będzie wymagało innej strategii skalowania niż `Audit & Reporting`).
        *   **Wysoka dostępność (NFR2):** Izolacja błędów – awaria jednej usługi nie wpływa na cały system.
        *   **Niezależne wdrażanie (NFR5):** Umożliwia szybkie iteracje i aktualizacje poszczególnych części systemu bez wpływu na inne.
        *   **Elastyczność technologiczna (NFR5):** Pozwala na wybór najlepszych technologii dla konkretnych problemów domenowych w każdej usłudze.
        *   **Lepsza organizacja pracy zespołów (NFR5):** Zespoły mogą być odpowiedzialne za konkretne mikrousługi, co poprawia zarządzanie złożonością.

**b) Domain-Driven Design (DDD)**
*   **Uzasadnienie:** Analiza domen już wykorzystuje podstawowe koncepcje DDD (Bounded Contexts, Aggregate Roots, Entities). Wdrożenie DDD wewnątrz każdej mikrousługi zapewnia:
    *   **Jasne modelowanie domeny:** Agregaty (`AppointmentSlot`, `Appointment`) są kluczowe dla zarządzania spójnością danych i regułami biznesowymi (`FR4`, `FR10`).
    *   **Enkapsulację logiki biznesowej:** Reguły biznesowe są umieszczone w modelach domenowych, co zwiększa ich spójność i ułatwia testowanie.
    *   **Wspólny język (Ubiquitous Language):** Ułatwia komunikację między deweloperami a ekspertami domenowymi.

**c) Event-Driven Architecture (Architektura Sterowana Zdarzeniami)**
*   **Uzasadnienie:** Wiele wymagań wskazuje na potrzebę asynchronicznej komunikacji i reaktywności (np. propagacja zmian `TimeSlot`, zbieranie danych audytowych `FR12`, `NFR4`).
    *   **Korzyści:**
        *   **Luzne sprzężenie (Loose Coupling):** Usługi komunikują się poprzez zdarzenia, minimalizując bezpośrednie zależności.
        *   **Reaktywność:** Umożliwia łatwą implementację reakcji na zmiany stanu w innych kontekstach (np. `Appointment Booking` reaguje na zmiany w `Specialist Schedule Management`).
        *   **Audyt i raportowanie:** `Audit & Reporting Service` może subskrybować zdarzenia z całego systemu w sposób pasywny i niezależny.

**d) CQRS (Command Query Responsibility Segregation) dla Appointment Booking Service**
*   **Uzasadnienie:** Kontekst `Appointment Booking` został zidentyfikowany jako najbardziej złożony, z kluczowymi wymaganiami dotyczącymi wysokiej współbieżności i spójności danych (`FR4`, `NFR1`). CQRS idealnie odpowiada na te wyzwania:
    *   **Separacja odczytów i zapisów:**
        *   **Strona Command:** Optymalizowana pod kątem silnej spójności i transakcyjności, obsługuje operacje modyfikujące stan (rezerwacja, anulowanie `AppointmentSlot`), co jest kluczowe dla `FR4` (zapobieganie podwójnym rezerwacjom).
        *   **Strona Query:** Optymalizowana pod kątem wydajnych odczytów, udostępnia zdenormalizowane modele danych dla szybkiego wyszukiwania dostępnych terminów i podglądu rezerwacji użytkownika/specjalisty (`FR1`, `FR6`, `FR7`).
    *   **Niezależne skalowanie (NFR1):** Strony Command i Query mogą być skalowane niezależnie.
    *   **Elastyczność modeli danych:** Umożliwia użycie różnych technologii baz danych dla Command (transakcyjna) i Query (czytelna, zdenormalizowana).

---

### 2. Proponowane Komponenty/Serwisy, Ich Odpowiedzialności i Sposób Komunikacji

System będzie składał się z następujących mikrousług, odpowiadających zidentyfikowanym kontekstom domenowym:

1.  **Identity & Access Management Service (IAM Service)**
    *   **Odpowiedzialności:**
        *   Zarządzanie użytkownikami, ich rolami (`User`, `Specialist`, `Admin`) i uprawnieniami (`FR9`).
        *   Uwierzytelnianie (np. generowanie tokenów JWT) i autoryzacja dostępu do systemu (`AC1`, `NFR3`).
        *   Rejestracja i zarządzanie profilami użytkowników.
    *   **Komunikacja:**
        *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika (logowanie, rejestracja) oraz z innymi usługami w celu walidacji tokenów i autoryzacji.
        *   **Asynchroniczna (Events):** Może publikować zdarzenia np. `UserRegistered`, `UserRoleChanged` do `Audit & Reporting`.

2.  **Specialist Schedule Management Service**
    *   **Odpowiedzialności:**
        *   Umożliwienie specjalistom definiowania i zarządzania ich grafikiem pracy (`Schedule`) i dostępnymi `TimeSlot`ami (`FR7`).
        *   Blokowanie konkretnych slotów przez specjalistę (`FR11`).
        *   Wysyłanie zdarzeń o zmianach dostępności `TimeSlot`ów.
    *   **Komunikacja:**
        *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika dla specjalistów (zarządzanie grafikiem).
        *   **Asynchroniczna (Events):** Publikuje zdarzenia takie jak `TimeSlotCreated`, `TimeSlotUpdated`, `TimeSlotDeleted` do Message Broker.

3.  **Appointment Booking Service (z CQRS)**
    *   **a) Command Side (AppointmentBooking.Commands)**
        *   **Odpowiedzialności:**
            *   Przyjmowanie i przetwarzanie żądań rezerwacji (`FR1`), anulowania (`FR5`), ukończenia (`FR8`) wizyt.
            *   Egzekwowanie reguł biznesowych: limit rezerwacji (`FR3`), zapobieganie podwójnym rezerwacjom (`FR4`), brak nakładania się terminów dla użytkownika (`FR10`, `AC6`).
            *   Reagowanie na zdarzenia `TimeSlotChanged` ze `Specialist Schedule Management` w celu utrzymania aktualnych `AppointmentSlot`ów.
            *   Publikowanie zdarzeń o zmianach statusu rezerwacji (`AppointmentBooked`, `AppointmentCancelled`, `AppointmentCompleted`).
        *   **Komunikacja:**
            *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika (wysyłanie komend rezerwacji/anulowania).
            *   **Asynchroniczna (Events):** Subskrybuje `TimeSlotChanged` z Message Broker. Publikuje zdarzenia domenowe (np. `AppointmentBooked`, `AppointmentSlotBlocked`) do Message Broker (dla Query Side, Audit & Reporting).
            *   **Synchroniczna (REST/gRPC lub wewnętrzny mechanizm):** Odbiera komendy nadpisywania od `System Administration Service`.
    *   **b) Query Side (AppointmentBooking.Queries)**
        *   **Odpowiedzialności:**
            *   Udostępnianie zoptymalizowanych widoków dostępnych `AppointmentSlot`ów (`FR1`).
            *   Prezentacja bieżących i historycznych rezerwacji użytkownika (`FR6`).
            *   Wyświetlanie grafik specjalistów z zarezerwowanymi wizytami (`FR7`).
        *   **Komunikacja:**
            *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika (pobieranie danych do wyświetlenia).
            *   **Asynchroniczna (Events):** Subskrybuje zdarzenia domenowe z Command Side (np. `AppointmentBooked`, `AppointmentCancelled`, `AppointmentSlotBlocked`) w celu aktualizacji swoich zdenormalizowanych baz danych.

4.  **System Administration Service**
    *   **Odpowiedzialności:**
        *   Zarządzanie globalnymi ustawieniami systemu (`SystemConfiguration`), takimi jak domyślne limity rezerwacji czy terminy anulowania (`FR3`, `FR5`).
        *   Umożliwienie administratorowi nadpisywania reguł biznesowych (np. zezwolenie na przekroczenie limitu `FR3`, `US6`), wysyłając odpowiednie komendy do innych usług (np. `Appointment Booking`).
        *   Logowanie wszystkich działań administratora (do `AdminOverrideLog`).
    *   **Komunikacja:**
        *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika dla administratorów.
        *   **Synchroniczna (REST/gRPC):** Wysyła komendy do `Appointment Booking Service` w celu nadpisywania.
        *   **Asynchroniczna (Events):** Publikuje zdarzenia `SystemConfigurationUpdated`, `AdminOverrideExecuted` do Message Broker.

5.  **Audit & Reporting Service**
    *   **Odpowiedzialności:**
        *   Zbieranie i przechowywanie wszystkich istotnych zdarzeń z systemu w postaci `AuditRecord`ów (`FR12`, `NFR4`).
        *   Dostarczanie interfejsów do generowania raportów i zapytań historycznych (np. dla potrzeb audytu, analizy operacyjnej).
    *   **Komunikacja:**
        *   **Asynchroniczna (Events):** Subskrybuje wszystkie istotne zdarzenia z Message Broker, bez bezpośredniej zależności od usług źródłowych.
        *   **Synchroniczna (REST/gRPC):** Z interfejsem użytkownika (dla raportów).

**Komunikacja Międzysystemowa:**
*   **Frontend/Mobile App:** Będzie komunikować się z usługami poprzez API REST/gRPC.
*   **Message Broker (np. Kafka, RabbitMQ):** Służy jako centralny kanał dla asynchronicznej komunikacji między usługami (publikacja/subskrypcja zdarzeń).

---

### 3. Mapowanie Wymagań na Komponenty

**Wymagania Funkcjonalne (FR):**

*   **FR1 (Przeglądanie/rezerwacja/podgląd wizyt):**
    *   `Appointment Booking Service (Query Side)`: Przeglądanie dostępnych slotów, podgląd wizyt.
    *   `Appointment Booking Service (Command Side)`: Rezerwacja wizyt.
    *   `IAM Service`: Autentykacja/autoryzacja użytkownika.
*   **FR2 (Potwierdzenie rezerwacji, email):**
    *   `Appointment Booking Service (Command Side)`: Potwierdza rezerwację, publikuje zdarzenie (`AppointmentBooked`).
    *   (Sugestia: osobny `Notification Service` subskrybujący `AppointmentBooked` event).
*   **FR3 (Limit 3 rezerwacji, nadpisanie przez Admina):**
    *   `Appointment Booking Service (Command Side)`: Egzekwuje limit (za pomocą `BookingPolicy`).
    *   `System Administration Service`: Umożliwia administratorowi nadpisanie limitu.
*   **FR4 (Zapobieganie podwójnym rezerwacjom):**
    *   `Appointment Booking Service (Command Side)`: Kluczowa odpowiedzialność, realizowana na poziomie `AppointmentSlot` (Aggregate Root) z użyciem transakcyjności.
*   **FR5 (Anulowanie rezerwacji, termin, nadpisanie przez Admina):**
    *   `Appointment Booking Service (Command Side)`: Przetwarza anulowanie, egzekwuje termin.
    *   `System Administration Service`: Umożliwia administratorowi nadpisanie terminu.
*   **FR6 (Podgląd przeszłych/nadchodzących wizyt):**
    *   `Appointment Booking Service (Query Side)`: Udostępnia te widoki.
*   **FR7 (Specjalista zarządzający harmonogramem):**
    *   `Specialist Schedule Management Service`: Główne zarządzanie harmonogramem.
    *   `Appointment Booking Service (Query Side)`: Podgląd zarezerwowanych terminów specjalisty.
    *   `IAM Service`: Autentykacja/autoryzacja specjalisty.
*   **FR8 (Aktualizacje statusu wizyt):**
    *   `Appointment Booking Service (Command Side)`: Zarządza statusami (`Appointment`, `AppointmentSlot`).
*   **FR9 (Kontrola dostępu oparta na rolach):**
    *   `IAM Service`: Centralne zarządzanie uprawnieniami. Wszystkie inne usługi integrują się z IAM.
*   **FR10 (Brak nakładających się wizyt dla użytkownika/specjalisty):**
    *   `Appointment Booking Service (Command Side)`: Egzekwuje tę regułę podczas rezerwacji.
*   **FR11 (Specjalista blokujący sloty):**
    *   `Specialist Schedule Management Service`: Umożliwia specjaliście blokowanie `TimeSlot`ów.
    *   `Appointment Booking Service (Command Side)`: Reaguje na zmiany `TimeSlot`ów, blokując odpowiadające `AppointmentSlot`y.
*   **FR12 (Historia operacji / Audit trail):**
    *   `Audit & Reporting Service`: Zbiera i przechowuje dane audytowe z całego systemu.
    *   Wszystkie usługi: Publikują zdarzenia do Message Broker.
*   **FR13 (Przepływ procesu rezerwacji):**
    *   `Appointment Booking Service (Command/Query Side)`: Cały proces rezerwacji.
    *   `IAM Service`: Autentykacja.

**Kryteria Akceptacji (AC):**

*   **AC1 (Uwierzytelnienie użytkownika do rezerwacji):** `IAM Service`.
*   **AC2 (Statusy rezerwacji: oczekująca, potwierdzona, zakończona):** `Appointment Booking Service (Command Side)`.
*   **AC3 (Anulowanie w terminie):** `Appointment Booking Service (Command Side)`.
*   **AC4 (Specjalista podgląda/zarządza kalendarzem):** `Specialist Schedule Management Service`, `Appointment Booking Service (Query Side)`.
*   **AC5 (Administrator nadpisuje limit rezerwacji):** `System Administration Service`.
*   **AC6 (Brak nakładających się osobistych wizyt):** `Appointment Booking Service (Command Side)`.

**Wymagania Niefunkcjonalne (NFR):**

*   **NFR1 (Wysoka współbieżność, brak podwójnych rezerwacji):**
    *   `Appointment Booking Service (Command Side)`: Zapewnia transakcyjność i spójność dla `AppointmentSlot`.
    *   `Appointment Booking Service (Query Side)`: Obsługuje wysokie obciążenie zapytań.
    *   `Microservices Architecture` + `CQRS`: Umożliwia niezależne skalowanie i optymalizację read/write.
*   **NFR2 (Wysoka dostępność):**
    *   `Microservices Architecture`: Zapewnia izolację błędów. (Dodatkowo: deployment w chmurze, replikacja, load balancing).
*   **NFR3 (Bezpieczeństwo - autentykacja/autoryzacja):**
    *   `IAM Service`: Centralny dostawca bezpieczeństwa.
    *   Wszystkie usługi: Integrują się z IAM.
*   **NFR4 (Audytowalność):**
    *   `Audit & Reporting Service`: Dedkowany komponent.
    *   `Event-Driven Architecture`: Ułatwia zbieranie zdarzeń.
*   **NFR5 (Łatwość utrzymania i rozszerzalność):**
    *   `Microservices Architecture` + `DDD`: Przejrzyste granice, luźne sprzężenie, niezależny rozwój.
*   **NFR6 (Wydajność - szybka reakcja):**
    *   `CQRS for Appointment Booking`: Szybkie odczyty przez Query Side.
    *   `Microservices Architecture`: Optymalizacja i skalowanie konkretnych usług.

---

### 4. Tekstowy Diagram Architektury (Mermaid.js)

```mermaid
graph TD
    subgraph User Interface [Frontend Application]
        UI[Web/Mobile App]
    end

    subgraph Core Services
        IAM[1. Identity & Access Management Service]
        SSM[2. Specialist Schedule Management Service]
        ABS_CMD[3a. Appointment Booking Service (Command Side)]
        ABS_QRY[3b. Appointment Booking Service (Query Side)]
        ADM[4. System Administration Service]
        AUD[5. Audit & Reporting Service]
    end

    subgraph Infrastructure
        MSG_BROKER[Message Broker (e.g., Kafka, RabbitMQ)]
        DB_IAM(IAM Database)
        DB_SSM(Specialist Schedule DB)
        DB_ABS_CMD(Appointment Booking Write DB)
        DB_ABS_QRY(Appointment Booking Read DB)
        DB_ADM(System Admin DB)
        DB_AUD(Audit & Reporting DB)
    end

    %% Frontend Interactions
    UI -- (1) Uwierzytelnienie/Autoryzacja --> IAM
    UI -- (2) Zarządzanie grafikiem Specjalisty --> SSM
    UI -- (3) Przeglądanie/Podgląd wizyt --> ABS_QRY
    UI -- (4) Rezerwacja/Anulowanie wizyt --> ABS_CMD
    UI -- (5) Akcje Administratora --> ADM

    %% Service to DB connections
    IAM --- DB_IAM
    SSM --- DB_SSM
    ABS_CMD --- DB_ABS_CMD
    ABS_QRY --- DB_ABS_QRY
    ADM --- DB_ADM
    AUD --- DB_AUD

    %% Asynchronous Communication via Message Broker
    SSM -- Publishes Events (TimeSlotCreated/Updated/Deleted) --> MSG_BROKER
    ABS_CMD -- Subscribes to TimeSlot Events --> MSG_BROKER
    ABS_CMD -- Publishes Events (AppointmentBooked/Cancelled/SlotBlocked/Completed) --> MSG_BROKER
    ABS_QRY -- Subscribes to Appointment Events from ABS_CMD --> MSG_BROKER
    ADM -- Publishes Events (SystemConfigUpdated/AdminOverrideExecuted) --> MSG_BROKER
    MSG_BROKER -- All Events (Audit Trail) --> AUD

    %% Synchronous Internal Communication / Authorization Checks
    SSM -- (Auth Check) --> IAM
    ABS_CMD -- (Auth Check) --> IAM
    ABS_QRY -- (Auth Check) --> IAM
    ADM -- (Auth Check) --> IAM
    ADM -- (Commands: Override Policy, Block Slot) --> ABS_CMD

    %% Styling for better readability
    style UI fill:#ecec00,stroke:#333,stroke-width:2px,color:#000
    style IAM fill:#afeeee,stroke:#333,stroke-width:2px,color:#000
    style SSM fill:#f0e68c,stroke:#333,stroke-width:2px,color:#000
    style ABS_CMD fill:#ffb6c1,stroke:#333,stroke-width:2px,color:#000
    style ABS_QRY fill:#b0e0e6,stroke:#333,stroke-width:2px,color:#000
    style ADM fill:#dda0dd,stroke:#333,stroke-width:2px,color:#000
    style AUD fill:#d8bfd8,stroke:#333,stroke-width:2px,color:#000
    style MSG_BROKER fill:#f5f5dc,stroke:#333,stroke-width:2px,color:#000
    style DB_IAM fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
    style DB_SSM fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
    style DB_ABS_CMD fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
    style DB_ABS_QRY fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
    style DB_ADM fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
    style DB_AUD fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000
```

---

# 3. API i Modele Danych

Jasne, na podstawie przedstawionej architektury, zaproponujmy kluczowe endpointy API (RESTful) oraz ogólne struktury baz danych dla każdego z serwisów, uwzględniając NFR dotyczące wydajności.

### Kluczowe Założenia API i Bazy Danych

*   **Identyfikatory (ID):** Wszędzie, gdzie to możliwe, używane będą UUID (Universally Unique Identifiers) dla głównych zasobów, co ułatwia rozproszone systemy i unikalność.
*   **Format Danych:** JSON.
*   **Autoryzacja:** Każdy endpoint będzie miał jasno określoną wymaganą rolę (np. `[Auth, User]`, `[Auth, Specialist]`, `[Auth, Admin]`). Będzie to realizowane przez walidację tokenów JWT przez `IAM Service`.
*   **Wydajność:**
    *   Dla list zasobów, zawsze zakładamy paginację (np. `?page=1&size=20`) i możliwość filtrowania.
    *   Dla Query Side w CQRS, bazy danych będą zoptymalizowane pod kątem odczytów (denormalizacja, indeksowanie).
    *   Cache'owanie (np. Redis) może być zaimplementowane na poziomie API Gateway lub w samych serwisach dla często odczytywanych, rzadko zmieniających się danych.
    *   Asynchroniczne przetwarzanie dla operacji niekrytycznych.

---

### 1. Identity & Access Management Service (IAM Service)

**Odpowiedzialności:** Zarządzanie użytkownikami, uwierzytelnianie, autoryzacja, profile.
**NFR:** Bezpieczeństwo (NFR3), skalowalność (NFR1).

#### **Kluczowe Endpointy API (RESTful)**

*   `POST /auth/register`
    *   **Opis:** Rejestruje nowego użytkownika w systemie.
    *   **Body:** `{ "email": "user@example.com", "password": "securePassword123", "firstName": "Jan", "lastName": "Kowalski", "role": "User" }`
    *   **Response:** `{ "userId": "uuid-123", "message": "User registered successfully" }`
*   `POST /auth/login`
    *   **Opis:** Uwierzytelnia użytkownika i zwraca tokeny JWT.
    *   **Body:** `{ "email": "user@example.com", "password": "securePassword123" }`
    *   **Response:** `{ "accessToken": "jwt.token.string", "refreshToken": "refresh.token.string", "expiresInSeconds": 3600, "user": { "id": "uuid-123", "role": "User" } }`
*   `POST /auth/refresh-token`
    *   **Opis:** Odświeża accessToken przy użyciu refreshToken.
    *   **Body:** `{ "refreshToken": "refresh.token.string" }`
    *   **Response:** `{ "accessToken": "new.jwt.token.string", "expiresInSeconds": 3600 }`
*   `GET /users/{userId}` `[Auth, User or Admin]`
    *   **Opis:** Pobiera szczegóły profilu użytkownika.
    *   **Response:** `{ "id": "uuid-123", "email": "user@example.com", "firstName": "Jan", "lastName": "Kowalski", "role": "User", "createdAt": "..." }`
*   `PUT /users/{userId}` `[Auth, User or Admin]`
    *   **Opis:** Aktualizuje profil użytkownika.
    *   **Body:** `{ "firstName": "Adam", "lastName": "Nowak" }`
*   `PATCH /users/{userId}/role` `[Auth, Admin]`
    *   **Opis:** Zmienia rolę użytkownika.
    *   **Body:** `{ "role": "Specialist" }`
*   `GET /users` `[Auth, Admin]`
    *   **Opis:** Pobiera listę użytkowników z opcją filtrowania i paginacji.
    *   **Query Params:** `?page=1&size=20&role=Specialist&emailContains=kowalski`
    *   **Response:** `{ "data": [ { "id": "uuid-123", "email": "...", "role": "..." }, ... ], "total": 100, "page": 1, "size": 20 }`

#### **Ogólna Struktura Baz Danych (Relacyjna, np. PostgreSQL)**

*   **`users` table:**
    *   `id` (UUID, PK)
    *   `email` (VARCHAR(255), UNIQUE, NOT NULL)
    *   `password_hash` (VARCHAR(255), NOT NULL)
    *   `first_name` (VARCHAR(255))
    *   `last_name` (VARCHAR(255))
    *   `role` (VARCHAR(50), NOT NULL - np. 'User', 'Specialist', 'Admin')
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
*   **`refresh_tokens` table:**
    *   `token` (VARCHAR(255), PK)
    *   `user_id` (UUID, FK do `users.id`, NOT NULL)
    *   `expires_at` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `issued_at` (TIMESTAMP WITH TIME ZONE)

---

### 2. Specialist Schedule Management Service

**Odpowiedzialności:** Definiowanie i zarządzanie grafikiem pracy specjalistów oraz dostępnymi `TimeSlot`ami.
**NFR:** Skalowalność (NFR1), wydajność (NFR6).

#### **Kluczowe Endpointy API (RESTful)**

*   `GET /specialists/{specialistId}/schedule` `[Auth, Specialist or Admin]`
    *   **Opis:** Pobiera grafik specjalisty na określony zakres dat.
    *   **Query Params:** `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`
    *   **Response:** `[ { "date": "YYYY-MM-DD", "timeSlots": [ { "id": "slot-uuid-1", "startTime": "HH:MM", "endTime": "HH:MM", "status": "AVAILABLE" }, ... ] }, ... ]`
*   `POST /specialists/{specialistId}/schedule/timeslots` `[Auth, Specialist]`
    *   **Opis:** Tworzy jeden lub wiele slotów czasowych w grafiku specjalisty.
    *   **Body:** `[ { "date": "YYYY-MM-DD", "startTime": "HH:MM", "endTime": "HH:MM", "durationMinutes": 30 }, { ... } ]`
    *   **Response:** `[ { "id": "slot-uuid-1", "startTime": "...", "status": "AVAILABLE" }, ... ]`
*   `PUT /specialists/{specialistId}/schedule/timeslots/{slotId}` `[Auth, Specialist]`
    *   **Opis:** Aktualizuje istniejący slot (np. zmianę czasu, statusu na "zablokowany").
    *   **Body:** `{ "startTime": "HH:MM", "endTime": "HH:MM", "status": "BLOCKED", "reason": "Urlop" }`
    *   **Response:** `{ "id": "slot-uuid-1", "status": "BLOCKED" }`
*   `DELETE /specialists/{specialistId}/schedule/timeslots/{slotId}` `[Auth, Specialist]`
    *   **Opis:** Usuwa slot czasowy z grafiku.
    *   **Response:** `204 No Content`

#### **Ogólna Struktura Baz Danych (Relacyjna, np. PostgreSQL)**

*   **`specialists` table:**
    *   `id` (UUID, PK, FK do IAM.users.id)
    *   `first_name` (VARCHAR(255)) - denormalizacja z IAM dla wydajności/luznego sprzężenia
    *   `last_name` (VARCHAR(255))
    *   `specialty` (VARCHAR(255))
*   **`time_slots` table:**
    *   `id` (UUID, PK)
    *   `specialist_id` (UUID, FK do `specialists.id`, NOT NULL)
    *   `start_time` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `end_time` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `status` (ENUM: 'AVAILABLE', 'BLOCKED', NOT NULL, DEFAULT 'AVAILABLE')
    *   `blocking_reason` (VARCHAR(255), NULL)
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeksy:** `(specialist_id, start_time)` dla szybkich zapytań zakresowych.

---

### 3. Appointment Booking Service (CQRS)

**Odpowiedzialności:** Rezerwacje, anulowanie, zarządzanie statusami, egzekwowanie reguł biznesowych.
**NFR:** Wysoka współbieżność (NFR1), wydajność (NFR6), wysoka dostępność (NFR2).

#### **3a. Command Side (AppointmentBooking.Commands)**

**NFR:** Silna spójność, transakcyjność, zapobieganie podwójnym rezerwacjom (FR4).

##### **Kluczowe Endpointy API (RESTful)**

*   `POST /appointments` `[Auth, User]`
    *   **Opis:** Tworzy nową rezerwację wizyty.
    *   **Body:** `{ "userId": "user-uuid", "specialistId": "specialist-uuid", "timeSlotId": "slot-uuid", "notes": "Konsultacja" }`
    *   **Response:** `{ "appointmentId": "appointment-uuid", "status": "BOOKED", "message": "Appointment booked successfully" }`
*   `PUT /appointments/{appointmentId}/cancel` `[Auth, User or Specialist or Admin]`
    *   **Opis:** Anuluje istniejącą rezerwację.
    *   **Body:** `{ "reason": "Zmiana planów" }`
    *   **Response:** `{ "appointmentId": "appointment-uuid", "status": "CANCELLED" }`
*   `PUT /appointments/{appointmentId}/complete` `[Auth, Specialist]`
    *   **Opis:** Zmienia status rezerwacji na zakończoną.
    *   **Response:** `{ "appointmentId": "appointment-uuid", "status": "COMPLETED" }`
*   `PATCH /appointments/policies/override-booking-limit` `[Auth, Admin]`
    *   **Opis:** Nadpisuje limit rezerwacji dla danego użytkownika (komenda z Admin Service).
    *   **Body:** `{ "userId": "user-uuid", "newLimit": 5, "durationHours": 24, "adminReason": "Specjalny klient" }`
*   `PATCH /appointments/policies/override-cancellation-deadline` `[Auth, Admin]`
    *   **Opis:** Nadpisuje termin anulowania dla konkretnej rezerwacji (komenda z Admin Service).
    *   **Body:** `{ "appointmentId": "appointment-uuid", "newDeadlineMinutesBeforeStart": 15, "adminReason": "Nagły przypadek" }`

##### **Ogólna Struktura Baz Danych (Relacyjna, np. PostgreSQL, z optymistycznym blokowaniem)**

*   **`appointment_slots` table:** (Reprezentuje sloty, które mogą być zarezerwowane, kluczowe dla FR4)
    *   `id` (UUID, PK) - odpowiada `time_slots.id` z SSM
    *   `specialist_id` (UUID, NOT NULL)
    *   `start_time` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `end_time` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `status` (ENUM: 'AVAILABLE', 'BOOKED', 'BLOCKED_BY_SPECIALIST', 'CANCELED_BY_SPECIALIST', NOT NULL)
        *   `BLOCKED_BY_SPECIALIST` / `CANCELED_BY_SPECIALIST` odzwierciedlają zmiany w SSM.
    *   `version` (INT, NOT NULL) - dla optymistycznego blokowania
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeksy:** `(specialist_id, start_time, status)`
    *   **Unikalny indeks:** `(specialist_id, start_time)` (dla zapewnienia unikalności slotu)
*   **`appointments` table:**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, NOT NULL)
    *   `specialist_id` (UUID, NOT NULL)
    *   `appointment_slot_id` (UUID, FK do `appointment_slots.id`, UNIQUE, NOT NULL)
    *   `start_time` (TIMESTAMP WITH TIME ZONE)
    *   `end_time` (TIMESTAMP WITH TIME ZONE)
    *   `status` (ENUM: 'BOOKED', 'PENDING', 'CANCELLED', 'COMPLETED', NOT NULL, DEFAULT 'PENDING')
    *   `booked_at` (TIMESTAMP WITH TIME ZONE)
    *   `cancelled_at` (TIMESTAMP WITH TIME ZONE, NULL)
    *   `completion_time` (TIMESTAMP WITH TIME ZONE, NULL)
    *   `cancellation_reason` (VARCHAR(255), NULL)
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeksy:** `(user_id, start_time)`, `(specialist_id, start_time)` (dla FR10)
*   **`booking_policies` table:** (Dla FR3, FR5)
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK do IAM.users.id, NULL - dla polityk globalnych)
    *   `max_active_appointments` (INT, NULL - jeśli nieograniczony)
    *   `cancellation_deadline_minutes` (INT, NULL - jeśli brak deadline)
    *   `is_override` (BOOLEAN, DEFAULT FALSE)
    *   `expires_at` (TIMESTAMP WITH TIME ZONE, NULL - dla tymczasowych nadpisań)
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeks:** `user_id`

#### **3b. Query Side (AppointmentBooking.Queries)**

**NFR:** Wydajne odczyty (FR1, FR6, FR7), skalowalność (NFR1).

##### **Kluczowe Endpointy API (RESTful)**

*   `GET /available-slots` `[Auth]`
    *   **Opis:** Pobiera dostępne sloty do rezerwacji, z filtrowaniem i paginacją.
    *   **Query Params:** `?specialistId=uuid&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&minDuration=30&page=1&size=20`
    *   **Response:** `{ "data": [ { "id": "slot-uuid", "specialistId": "uuid", "specialistName": "Dr. Smith", "startTime": "...", "endTime": "...", "status": "AVAILABLE" } ], "total": 100, "page": 1, "size": 20 }`
*   `GET /users/{userId}/appointments` `[Auth, User or Admin]`
    *   **Opis:** Pobiera przyszłe i przeszłe rezerwacje dla danego użytkownika (FR6).
    *   **Query Params:** `?status=upcoming&page=1&size=10`
    *   **Response:** `{ "data": [ { "id": "appointment-uuid", "specialistId": "uuid", "specialistName": "Dr. Smith", "startTime": "...", "endTime": "...", "status": "BOOKED" }, ... ], "total": 50, "page": 1, "size": 10 }`
*   `GET /specialists/{specialistId}/appointments` `[Auth, Specialist or Admin]`
    *   **Opis:** Pobiera rezerwacje dla danego specjalisty (FR7).
    *   **Query Params:** `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&status=booked&page=1&size=20`
    *   **Response:** `{ "data": [ { "id": "appointment-uuid", "userId": "user-uuid", "userName": "Jan Kowalski", "startTime": "...", "endTime": "...", "status": "BOOKED" }, ... ], "total": 75, "page": 1, "size": 20 }`

##### **Ogólna Struktura Baz Danych (Zdenormalizowana, zoptymalizowana do odczytów, np. MongoDB lub PostgreSQL z Materialized Views/JSONB)**

*   **`available_slots_view` collection/table:** (Pre-agregowany widok dla szybkiego wyszukiwania dostępnych slotów)
    *   `_id` (UUID, PK) - odpowiada `appointment_slots.id`
    *   `specialist_id` (UUID)
    *   `specialist_first_name` (VARCHAR)
    *   `specialist_last_name` (VARCHAR)
    *   `start_time` (TIMESTAMP WITH TIME ZONE)
    *   `end_time` (TIMESTAMP WITH TIME ZONE)
    *   `status` (VARCHAR - 'AVAILABLE', 'BLOCKED_BY_SPECIALIST')
    *   `search_tags` (Array of Strings - np. ["Dr. Smith", "Kardiolog", "poniedziałek", "rano"])
    *   **Indeksy:** `specialist_id`, `start_time`, `status`.
*   **`user_appointments_view` collection/table:** (Widok z denormalizowanymi danymi użytkownika i specjalisty)
    *   `_id` (UUID, PK) - odpowiada `appointments.id`
    *   `user_id` (UUID)
    *   `user_first_name` (VARCHAR)
    *   `user_last_name` (VARCHAR)
    *   `specialist_id` (UUID)
    *   `specialist_first_name` (VARCHAR)
    *   `specialist_last_name` (VARCHAR)
    *   `start_time` (TIMESTAMP WITH TIME ZONE)
    *   `end_time` (TIMESTAMP WITH TIME ZONE)
    *   `status` (VARCHAR - 'BOOKED', 'CANCELLED', 'COMPLETED')
    *   `booked_at` (TIMESTAMP WITH TIME ZONE)
    *   `cancellation_reason` (VARCHAR)
    *   **Indeksy:** `user_id`, `start_time`, `status`.
*   **`specialist_appointments_view` collection/table:** (Widok z denormalizowanymi danymi specjalisty i użytkownika)
    *   `_id` (UUID, PK) - odpowiada `appointments.id`
    *   `specialist_id` (UUID)
    *   `specialist_first_name` (VARCHAR)
    *   `specialist_last_name` (VARCHAR)
    *   `user_id` (UUID)
    *   `user_first_name` (VARCHAR)
    *   `user_last_name` (VARCHAR)
    *   `start_time` (TIMESTAMP WITH TIME ZONE)
    *   `end_time` (TIMESTAMP WITH TIME ZONE)
    *   `status` (VARCHAR - 'BOOKED', 'CANCELLED', 'COMPLETED')
    *   `booked_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeksy:** `specialist_id`, `start_time`, `status`.

---

### 4. System Administration Service

**Odpowiedzialności:** Zarządzanie globalnymi ustawieniami, nadpisywanie reguł biznesowych, logowanie działań administratora.
**NFR:** Bezpieczeństwo (NFR3), audytowalność (NFR4).

#### **Kluczowe Endpointy API (RESTful)**

*   `GET /config` `[Auth, Admin]`
    *   **Opis:** Pobiera globalne ustawienia systemu.
    *   **Response:** `{ "defaultMaxAppointments": 3, "defaultCancellationDeadlineMinutes": 60 }`
*   `PUT /config` `[Auth, Admin]`
    *   **Opis:** Aktualizuje globalne ustawienia systemu.
    *   **Body:** `{ "defaultMaxAppointments": 4, "defaultCancellationDeadlineMinutes": 90 }`
*   `POST /admin/actions/override-booking-limit` `[Auth, Admin]`
    *   **Opis:** Wysyła komendę nadpisującą limit rezerwacji do `Appointment Booking Service`.
    *   **Body:** `{ "userId": "user-uuid", "newLimit": 5, "durationHours": 24, "reason": "VIP client" }`
    *   **Response:** `{ "adminActionId": "action-uuid", "status": "Initiated" }`
*   `POST /admin/actions/override-cancellation-deadline` `[Auth, Admin]`
    *   **Opis:** Wysyła komendę nadpisującą termin anulowania do `Appointment Booking Service`.
    *   **Body:** `{ "appointmentId": "appointment-uuid", "newDeadlineMinutesBeforeStart": 15, "reason": "Nagły przypadek" }`
    *   **Response:** `{ "adminActionId": "action-uuid", "status": "Initiated" }`

#### **Ogólna Struktura Baz Danych (Relacyjna, np. PostgreSQL)**

*   **`system_configurations` table:**
    *   `key` (VARCHAR(255), PK)
    *   `value` (TEXT, NOT NULL)
    *   `description` (TEXT)
    *   `updated_by_user_id` (UUID, FK do IAM.users.id)
    *   `updated_at` (TIMESTAMP WITH TIME ZONE)
*   **`admin_override_logs` table:** (FR12 - Historia operacji administratora)
    *   `id` (UUID, PK)
    *   `admin_user_id` (UUID, FK do IAM.users.id, NOT NULL)
    *   `action_type` (VARCHAR(100), NOT NULL - np. 'OVERRIDE_BOOKING_LIMIT', 'UPDATE_GLOBAL_CONFIG')
    *   `target_entity_type` (VARCHAR(50), NULL - np. 'USER', 'APPOINTMENT')
    *   `target_entity_id` (UUID, NULL)
    *   `old_value` (JSONB, NULL)
    *   `new_value` (JSONB, NULL)
    *   `reason` (TEXT, NULL)
    *   `created_at` (TIMESTAMP WITH TIME ZONE)
    *   **Indeks:** `admin_user_id`, `created_at`

---

### 5. Audit & Reporting Service

**Odpowiedzialności:** Zbieranie i przechowywanie zdarzeń audytowych, generowanie raportów.
**NFR:** Audytowalność (NFR4), wydajność (NFR6) dla raportów, skalowalność (NFR1) dla ingestowania zdarzeń.

#### **Kluczowe Endpointy API (RESTful)**

*   `GET /audit-trail` `[Auth, Admin]`
    *   **Opis:** Pobiera zapisy z dziennika audytu z filtrowaniem i paginacją.
    *   **Query Params:** `?eventType=AppointmentBooked&userId=uuid&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&page=1&size=20`
    *   **Response:** `{ "data": [ { "id": "audit-uuid", "timestamp": "...", "eventType": "...", "sourceService": "...", "actorId": "...", "payload": { ... } }, ... ], "total": 5000, "page": 1, "size": 20 }`
*   `GET /reports/appointments-by-specialist` `[Auth, Admin]`
    *   **Opis:** Generuje raport z wizytami pogrupowanymi wg specjalistów.
    *   **Query Params:** `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`
    *   **Response:** `[ { "specialistId": "uuid", "specialistName": "Dr. Smith", "totalAppointments": 150, "completed": 100, "cancelled": 30 }, ... ]`
*   `GET /reports/user-booking-trends` `[Auth, Admin]`
    *   **Opis:** Generuje raport trendów rezerwacji dla użytkowników.
    *   **Query Params:** `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&topN=10`
    *   **Response:** `[ { "userId": "uuid", "userName": "Jan Kowalski", "totalBookings": 25, "cancellations": 2 }, ... ]`

#### **Ogólna Struktura Baz Danych (Zoptymalizowana do analityki, np. ClickHouse, MongoDB, lub PostgreSQL z JSONB)**

*   **`audit_records` table/collection:** (Główne repozytorium zdarzeń)
    *   `id` (UUID, PK)
    *   `event_id` (UUID) - unikalny identyfikator oryginalnego zdarzenia
    *   `timestamp` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    *   `event_type` (VARCHAR(100), NOT NULL - np. 'UserRegistered', 'AppointmentBooked', 'TimeSlotBlocked')
    *   `source_service` (VARCHAR(50), NOT NULL - np. 'IAM', 'AppointmentBookingCommand')
    *   `actor_id` (UUID, NULL - ID użytkownika/specjalisty/admina, który zainicjował akcję)
    *   `correlation_id` (UUID, NULL - dla śledzenia zdarzeń w ramach pojedynczego przepływu)
    *   `payload` (JSONB / JSON, NOT NULL - pełne szczegóły zdarzenia)
    *   **Indeksy:** `timestamp`, `event_type`, `actor_id`, `source_service` (dla efektywnego filtrowania i zapytań zakresowych).

*   **`reports_materialized_views` (Opcjonalne, dla bardzo szybkich raportów):**
    *   **`specialist_appointment_summary` table:**
        *   `specialist_id` (UUID, PK)
        *   `date_day` (DATE, PK)
        *   `total_appointments` (INT)
        *   `completed_appointments` (INT)
        *   `cancelled_appointments` (INT)
        *   `booked_hours` (DECIMAL)
    *   **`user_booking_summary` table:**
        *   `user_id` (UUID, PK)
        *   `date_day` (DATE, PK)
        *   `total_bookings` (INT)
        *   `total_cancellations` (INT)

---

Powyższe propozycje stanowią solidną bazę dla implementacji API i baz danych, silnie uwzględniając wskazane wzorce architektoniczne i wymagania niefunkcjonalne. Dalsze szczegóły, takie jak konkretne technologie (np. Kafka jako Message Broker, Redis jako cache) oraz wybory ORM/bibliotek do baz danych, będą zależały od preferencji zespołu i ekosystemu technologicznego.