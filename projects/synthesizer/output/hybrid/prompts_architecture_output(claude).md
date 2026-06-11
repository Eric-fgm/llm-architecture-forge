# Prompty do korekty: architecture_output(claude).md

---

## Prompt 1 – Po analizie domen i encji

Masz pięć dobrze zdefiniowanych Bounded Contexts, ale zastanów się, czy Administration i Notification to nie jest trochę przesadzone jak na system tej skali. Notification jako osobna domena z własnym modelem danych i Event Busem to rozwiązanie typowe dla systemów dużo bardziej złożonych. Zgodnie z YAGNI — w systemie rezerwacji wizyt powiadomienia mogą być prostą funkcją wywoływaną po zakończeniu transakcji rezerwacji, bez potrzeby osobnego kontekstu domenowego. Podobnie Administration z wyjątkami konfliktów wydaje się zbyt ciężka — te reguły mogą być konfiguracją przechowywaną w Booking Service lub prostej tabeli systemowej.

---

## Prompt 2 – Po zaproponowaniu komponentów i ich komunikacji

Proponujesz Outbox Pattern, Redis Cache, zewnętrzny IdP (Keycloak/Auth0) i CQRS we wszystkich modułach. To dużo infrastruktury dla systemu rezerwacji wizyt. Rozważ uproszczenie: czy CQRS jest naprawdę potrzebny w Availability Module skoro logika tam jest prosta CRUD? Czy zewnętrzny IdP jest konieczny skoro wymagania mówią tylko o rolach USER/SPECIALIST/ADMIN? Skupmy się na tym, co jest core: Booking Service z transakcyjną rezerwacją, Schedule Service z zarządzaniem slotami, Audit Service z logowaniem operacji i User/Access Service z prostą kontrolą ról. Uprość architekturę do tego co naprawdę potrzebne.

---

## Prompt 3 – Po wygenerowaniu API i struktury danych

Twój model danych jest bardzo rozbudowany — osobne schematy per moduł, partycjonowanie tabeli audit_logs, tabela outbox, osobne tabele specializations i specialist_specializations. Część z tego ma sens, ale schemat `availability` z oddzielną tabelą `schedules` jako Aggregate Root i `time_slots` jako osobna tabela to niekoniecznie najlepsze podejście — w Gold Architecture Slot jest encją samą w sobie (specialist_id, start_time, end_time, status), bez pośredniej tabeli Schedule. Uprość model: usuń tabelę schedules jako pośrednika, niech Slot bezpośrednio należy do specjalisty. Upewnij się też, że tabela Booking ma pole `created_at` i status zawęża się do BOOKED/CANCELLED, a status COMPLETED przynależy do Slotu.
