# Architektura Systemu Rezerwacji Wizyt (Appointment Booking System)

Poniżej znajduje się pragmatyczny projekt architektury dla systemu rezerwacji. Został on podzielony na logiczne sekcje ułatwiające implementację i utrzymanie.

## 1. Podział na domeny (Bounded Contexts)

Rozbiliśmy system na niezależne obszary biznesowe, co ułatwi zarządzanie kodem i odpowiedzialnością.

* **Availability Context (Dostępność i Grafik):**
    * **Odpowiedzialność:** Zarządzanie czasem i grafikiem specjalistów.
    * **Główne encje:** `Specialist` (Specjalista), `Slot` (Termin). Zakładamy, że slot trwa standardowo 30 minut.
    * **Statusy Slotu:** `AVAILABLE` (dostępny) oraz `BLOCKED` (zablokowany przez specjalistę).
* **Booking Context (Rezerwacje):**
    * **Odpowiedzialność:** Obsługa procesu umawiania, przeglądania i anulowania wizyt przez użytkowników.
    * **Główne encje:** `Appointment` (Wizyta), `User` (Pacjent/Klient).
    * **Statusy Wizyty:** `BOOKED`, `CANCELLED`, `COMPLETED`.
* **Identity & Access Context (Użytkownicy i Uprawnienia):**
    * **Odpowiedzialność:** Uwierzytelnianie oraz autoryzacja ról w systemie (User, Specialist, Admin).
    * **Izolacja danych:** Użytkownik przegląda wyłącznie własne rezerwacje, specjalista wizyty przypisane do siebie, natomiast administrator ma pełny dostęp do wszystkich danych.
* **Audit Context (Audyt):**
    * **Odpowiedzialność:** Rejestrowanie kluczowych operacji (np. rezerwacji, anulowań, błędów) ze znacznikami czasu.

---

## 2. Architektura i Komunikacja

Najsensowniejszym wyborem dla tego projektu jest **Monolit Modułowy (Modular Monolith)**.

* **Dlaczego taki wybór?** System musi bezwzględnie zapewniać spójność danych i unikać podwójnych rezerwacji (double booking) pomimo występowania równoczesnych operacji. Oparcie całości na jednej relacyjnej bazie danych ułatwi realizację tego założenia. Jednocześnie podział na moduły wewnątrz jednej aplikacji pozwoli zrealizować wymóg wydajności (obsługa rezerwacji w czasie krótszym niż 1 sekunda) oraz umożliwi łatwe skalowanie w przypadku rosnącej liczby użytkowników i specjalistów.
* **Sposoby komunikacji:**
    * **Synchronicznie:** Poprzez wywołania wewnątrzprocesowe (np. wstrzykiwanie interfejsów). Rejestrując wizytę, moduł rezerwacji musi w czasie rzeczywistym zapytać o dostępność terminu.
    * **Asynchronicznie (Zdarzenia domenowe):** Za pomocą eventów publikowanych w pamięci. Przykładowo: anulowanie wizyty publikuje zdarzenie, na które reaguje moduł audytu logując operację, oraz moduł dostępności przywracając termin do puli wolnych slotów.

---

## 3. Gdzie obsłużyć logikę biznesową?

* **Reguły rezerwacji (limit i konflikty):** Domena rezerwacji weryfikuje zasady. Sprawdza, czy użytkownik ma obecnie nie więcej niż 3 aktywne rezerwacje oraz czy nie posiada innej wizyty w nakładającym się czasie.
* **Nadpisywanie uprawnień przez Admina:** Rola Admina umożliwia wysłanie żądania omijającego standardowe ramy systemu. Dzięki temu, w wyjątkowych, uzasadnionych przypadkach, może on np. zezwolić na przekroczenie limitu rezerwacji dla danego użytkownika.
* **Zarządzanie współbieżnością (Brak double bookingu):** Dokumentacja dopuszcza różne rozwiązania w tej kwestii i nie określa sztywnych mechanizmów. Doskonale sprawdzi się tu mechanizm **Blokady Optymistycznej (Optimistic Locking)** aplikowany bezpośrednio przy zapisie do bazy. Dzięki niemu równoczesne próby rezerwacji zakończą się sukcesem tylko dla jednej osoby, gwarantując spójny stan.
* **Zasady anulowania:** Logika ta przypisana jest do encji rezerwacji. Wizytę można anulować do 24 godzin przed zaplanowanym czasem, co automatycznie nadaje jej status `CANCELLED` i oddaje slot, chyba że został on wcześniej oznaczony jako niedostępny. Jeśli anulowanie odbywa się później (np. dokładnie 24 godziny przed), system odrzuca akcję lub prosi o dodatkową autoryzację.
* **Zarządzanie grafikiem:** Specjalista swobodnie operuje na swoim grafiku, tworząc i usuwając wolne terminy (jeśli nie są już zarezerwowane). Może też ręcznie zablokować slot (`BLOCKED`). W wyjątkowych sytuacjach dopuszcza się modyfikację terminu już zajętego.

---

## 4. Bazy danych i kluczowe API

Do zapewnienia pożądanej stabilności i czasów odpowiedzi poniżej sekundy wystarczy standardowa relacyjna baza danych ze zoptymalizowanymi indeksami.

**Zarys schematu:**
* `Slots`: `id`, `specialist_id` (INDEX), `start_time` (INDEX), `status`, `version` (potrzebne do obsługi Optimistic Lockingu).
* `Appointments`: `id`, `slot_id`, `user_id` (INDEX), `status`, `created_at`.
* `Audit_Logs`: `id`, `action_type`, `user_id`, `timestamp`. Szybka i prosta tabela pod zapisywanie logów audytowych.

**Najważniejsze Endpointy REST:**
* `GET /api/availability/slots?specialistId={id}&date={date}`
    * Pobiera aktualnie dostępne terminy na dany dzień dla konkretnego specjalisty, umożliwiając przeglądanie według daty.
* `POST /api/bookings/appointments`
    * Inicjuje proces rezerwacji na podstawie wybranego dostępnego terminu, dbając by status zmienił się na `BOOKED`.
* `PATCH /api/bookings/appointments/{id}/cancel`
    * Endpoint używany przez użytkownika do anulowania własnej wizyty, co w odpowiednim czasie zmienia status na `CANCELLED`.
* `POST` oraz `DELETE` na `/api/availability/specialists/{id}/slots`
    * Endpointy przeznaczone dla Specjalisty, ułatwiające zarządzanie udostępnianymi i zablokowanymi godzinami pracy.