# Prompty do korekty: architecture_output(gpt).md

---

## Prompt 1 – Po analizie domen i encji

Wyodrębniłeś sześć domen, a jedną z nich jest osobny Appointment Management obok Schedule Management i Booking Management — to niepotrzebne rozdrobnienie. Wizyta/Slot to encja zarządzana przez Schedule Context, a jej rezerwacja przez Booking Context. Scalenie appointment i scheduling w jeden kontekst Schedule, który zarządza slotami (ich tworzeniem, blokowaniem i statusami), znacząco upraszcza model bez utraty czytelności. Dodatkowo, Configuration & Rules Management to trochę zbyt duży twór jako samodzielna domena — w mniejszych systemach reguły rezerwacji mogą być zwykłą konfiguracją odczytywaną przez Booking Service.

---

## Prompt 2 – Po zaproponowaniu komponentów i ich komunikacji

Twoje mapowanie wymagań na komponenty jest zbyt ogólne. Przykładowo, "Limit 3 aktywnych rezerwacji" jest przypisany do Booking Module — ale jak dokładnie to działa? Booking Service powinien przed zapisem rezerwacji: (1) sprawdzić dostępność slotu przez Schedule Service, (2) sprawdzić liczbę aktywnych rezerwacji użytkownika, (3) sprawdzić, czy nowa wizyta nie nakłada się czasowo z istniejącymi. Opisz ten przepływ explicite jako sekwencję kroków. Diagram komunikacji też powinien pokazywać, że Booking → Schedule to wywołanie synchroniczne, a Booking → Audit to zapis po zakończeniu operacji.

---

## Prompt 3 – Po wygenerowaniu API i struktury danych

W projekcie API brakuje kilku kluczowych endpointów: `GET /bookings/my` (lista moich rezerwacji), `PATCH /slots/{id}/block` (blokowanie slotu przez specjalistę) i `GET /audit-log` (dla admina). W strukturze bazy danych tabela Appointments/Slots nie ma statusu `BLOCKED` — dodaj go, bo specjalista musi móc zablokować slot niezależnie od rezerwacji. Tabela Reservation/Booking powinna mieć pole `created_at`. Upewnij się też, że anulowanie rezerwacji przez specjalistę przywraca slot do AVAILABLE, a nie do BLOCKED — chyba że slot był wcześniej zablokowany, wtedy powinien wrócić do BLOCKED. Opisz tę logikę.
