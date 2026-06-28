<<<<<<< HEAD
# MedServicePrice.kz — clean vanilla frontend + AI

Структура специально упрощена:

```text
backend/
frontend/
requirements.txt
.env.example
```

Фронтенд: обычные `index.html`, `app.js`, `styles.css`.
Backend: FastAPI + SQLAlchemy. По умолчанию используется SQLite.

## Запуск на Windows PowerShell

```powershell
cd C:\Users\user\Downloads\medprice_clean_ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --reload --port 8000
```

Открыть сайт:

```text
http://localhost:8000
```

## AI через ChatGPT API

Создай файл `.env` в корне проекта или в папке `backend`:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Если ключа нет или API временно недоступен, AI помощник автоматически переключится на локальные правила.

## Что изменено

- удалена админ-панель;
- база автоматически заполняется при запуске backend;
- упрощена структура папок: только `backend` и `frontend`;
- добавлен AI помощник по симптомам;
- новый светлый дизайн: белый фон + синий акцент;
- стандартные источники из ТЗ уже включены;
- 12 источников/клиник, весь справочник услуг, цены для всех комбинаций;
- `оак`, `ОАК`, `CBC` ищутся как `Общий анализ крови (ОАК)`.

## API

Swagger:

```text
http://localhost:8000/docs
```
=======
# 86_medicalsearch
>>>>>>> 4545854aa232d18d8a0cbf2212630cd61d1637c7
