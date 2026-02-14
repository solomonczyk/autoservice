Структура базы данных (Database Schema)
Для поддержки мультифилиальности и временных слотов в календаре я спроектировал следующую схему:

Таблица: shops (Мастерские)
id: Primary Key.

name: Название филиала.

address: Адрес (для отображения в боте).

Таблица: clients (Клиенты)
id: Primary Key.

telegram_id: ID для связи через бот.

phone: Основной контакт для менеджера.

full_name: Имя клиента.

vehicle_info: Марка/модель авто (опционально).

Таблица: services (Услуги)
id: Primary Key.

name: Название (например, «Замена масла»).

duration_minutes: Длительность (важно для сетки календаря).

base_price: Ориентировочная стоимость.

Таблица: appointments (Записи — Сердце системы)
id: Primary Key.

shop_id: Foreign Key на shops.

client_id: Foreign Key на clients.

service_id: Foreign Key на services.

start_time: Начало записи (для почасового календаря).

end_time: Конец записи (рассчитывается автоматически).

status: Статус для канбан-доски (new, confirmed, in_progress, done, cancelled).