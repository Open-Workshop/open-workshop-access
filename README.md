# open-workshop-access

Сервис расчёта прав доступа для Open Workshop.

Он не хранит собственное состояние сессии и не ходит напрямую в базы manager. Вместо этого сервис:

1. принимает запрос от `open-workshop-manager`,
2. проверяет сервисный токен в заголовке `x-token`,
3. по кукам `accessToken` и `refreshToken` запрашивает у manager доверенный статический контекст,
4. собирает и возвращает контракт прав для конкретной ручки.

Сервис нужен для того, чтобы логика принятия решений по доступу жила отдельно от основного manager-репозитория и возвращала единый, явный ответ с полями:

- `value`
- `reason`
- `reason_code`

## Что внутри

- HTTP API на `FastAPI`
- доверенный callback в manager для получения статичного контекста
- расчёт динамических прав:
  - mute
  - cooldown на смену никнейма
  - публикация модов
  - редактирование модов
  - управление авторами
  - удаление модов
  - доступ к закрытым данным профиля

## Как сервис авторизуется

Есть два разных токена, и у них разная роль:

- `ACCESS_SERVICE_TOKEN`
  Используется manager -> access. Передаётся в заголовке `x-token`.

- `ACCESS_CALLBACK_TOKEN`
  Используется access -> manager callback. Передаётся в заголовке `x-token`.

Пользовательские токены в body не передаются.

Пара сессионных токенов всегда едет как куки:

- `accessToken`
- `refreshToken`

Именно их access пробрасывает дальше в manager callback, когда нужно получить статичный контекст текущего пользователя.

## Переменные окружения

Сервис читает только переменные окружения.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `MANAGER_URL` | `http://127.0.0.1:7776/api/accounts` | Базовый URL manager для trusted callback |
| `ACCESS_SERVICE_TOKEN` | `""` | Токен, которым manager подписывает запросы в access |
| `ACCESS_CALLBACK_TOKEN` | `""` | Токен, которым access подписывает callback-запросы в manager |
| `REQUEST_TIMEOUT_SECONDS` | `30` | Таймаут callback-запроса к manager |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

## Установка

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Запуск

Пример локального запуска:

```bash
export MANAGER_URL="http://127.0.0.1:7776/api/accounts"
export ACCESS_SERVICE_TOKEN="dev-access-token"
export ACCESS_CALLBACK_TOKEN="dev-callback-token"

./venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8080 --reload
```

Swagger доступен по корню сервиса:

```text
GET /
```

## Контракт взаимодействия с manager

### Вход в access

Любой запрос в access должен содержать:

- заголовок `x-token: <ACCESS_SERVICE_TOKEN>`
- при пользовательском сценарии куки `accessToken` и `refreshToken`

### Callback в manager

Для получения статического контекста access вызывает manager:

```text
POST {MANAGER_URL}/access/callback/context
```

С этим запросом отправляются:

- заголовок `x-token: <ACCESS_CALLBACK_TOKEN>`
- куки `accessToken` и `refreshToken`, если они были в исходном запросе
- body только с нужными идентификаторами:
  - `user_id`
  - `mods_ids`

Это важно: access не тащит в body лишние поля “на всякий случай”.

## Ручки

Ниже перечислены основные endpoint-ы access и минимальные входные контракты.

### `POST /context`

Возвращает текущий статический контекст доступа.

Body:

```json
{
  "user_id": 15
}
```

`user_id` нужен только для статичных сценариев, когда manager хочет посчитать права для конкретного пользователя без текущей сессии.

### `PUT /mod`

Возвращает права на создание мода.

Body:

```json
{
  "without_author": false
}
```

### `POST /mod/{mod_id}`

Возвращает права для конкретного мода.

Body:

```json
{
  "author_id": 15,
  "mode": false
}
```

Эти поля нужны только для сценария изменения авторов мода.

### `POST /mods`

Пакетная проверка доступа к модам.

Body:

```json
{
  "user_id": 15,
  "mods_ids": [1, 2, 3],
  "edit": true
}
```

`user_id` используется в статичном сценарии, когда проверка идёт без пользовательских кук.

### `PATCH /tags`

Возвращает CRUD-права для тегов.

Body не требуется.

### `PATCH /genres`

Возвращает CRUD-права для жанров.

Body не требуется.

### `PUT /game`

Возвращает право на добавление игры.

Body не требуется.

### `POST /game/{game_id}`

Возвращает права на редактирование и удаление игры.

Body не требуется.

### `POST /profile/{profile_id}`

Возвращает права для профиля:

- просмотр скрытых метаданных
- редактирование никнейма
- редактирование описания
- редактирование аватара
- выдача мута
- редактирование прав
- голосование за репутацию
- комментарии
- реакции
- удаление собственного профиля

Body не требуется.

## Пример запроса

```bash
curl -X POST "http://127.0.0.1:8080/profile/7" \
  -H "x-token: dev-access-token" \
  -H "Content-Type: application/json" \
  -H "Cookie: accessToken=...; refreshToken=..." \
  -d '{}'
```

## Тесты

В репозитории есть endpoint-тесты ручек access:

- проверка `x-token`
- `context`
- `mod add`
- `mod`
- `mods`
- `tags`
- `genres`
- `game add`
- `game`
- `profile`

Тесты запускаются через стандартный `unittest`:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Дополнительно можно проверить синтаксис:

```bash
./venv/bin/python -m compileall -q src tests
```

## Что важно не ломать

- пользовательские токены передаются куками, а не через body
- access не должен знать про базы manager напрямую
- ручка должна возвращать свой явный контракт, а не выбрасывать решение наружу через исключения
- если право запрещено, причина должна возвращаться в `reason` и `reason_code`
