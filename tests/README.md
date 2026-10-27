# Тестовый набор проекта

---

## Запуск тестов

```powershell
# Запуск полного набора тестов
uv run pytest -q

# Запуск с отчетом о покрытии кода
uv run pytest --cov=src/app

# Запуск только интеграционных тестов
uv run pytest -m integration

# Запуск только модульных тестов
uv run pytest -m unit
```

---

## Иерархия фикстур (`conftest.py`)

- `tests/conftest.py` — глобальные зависимости: `now` (фиксированное время UTC), `forum_html` (HTML-фикстура),
  `make_comment` (фабрика доменных сущностей).
- `tests/unit/application/conftest.py` — легковесные in-memory фейки портов: `FakeCommentRepository`, `FakeForumParser`,
  фикстуры `fake_repo`, `repo`, `fake_parser_factory`.
- `tests/unit/infrastructure/conftest.py` — изоляция адаптеров БД: in-memory движок SQLite, фикстуры `session`,
  `sqlalchemy_repo`, `repo`.
- `tests/integration/conftest.py` — сквозное окружение: DI-контейнер Dishka `test_container`, ASGI-клиент `client` (
  `httpx.AsyncClient` с lifespan), фабрика кастомных клиентов `client_factory`.

---

## Реестр тестов по слоям и модулям

### 1. Интеграционный слой (`tests/integration/`)

#### `test_comments_crud.py` — Жизненный цикл комментариев (CRUD)

- `test_create_comment_success` — создание комментария через POST с проверкой HTTP 201, структуры ответа, `version=1` и
  `updated_at=None`.
- `test_create_comment_without_external_id` — создание комментария пользователем без привязки к внешнему ID форума (
  `external_id=None`).
- `test_create_comment_duplicate_natural_key_returns_409` — отклонение создания дубликата с совпадающей парой
  `(source_url, external_id)` с кодом HTTP 409 Conflict.
- `test_create_comment_same_external_id_different_sources` — успешное сохранение одинаковых `external_id`, принадлежащих
  разным `source_url`.
- `test_get_comment_by_id_success` — успешное получение сохраненного комментария по его UUID (HTTP 200).
- `test_get_comment_not_found_returns_404` — возврат HTTP 404 Not Found при запросе несуществующего идентификатора
  комментария.
- `test_get_comment_invalid_uuid_returns_422` — возврат HTTP 422 при передаче некорректной строки вместо UUID в
  path-параметре.
- `test_patch_comment_success` — частичное обновление текста через PATCH с инкрементом версии (`version=2`) и установкой
  `updated_at`.
- `test_put_comment_success` — полное обновление текста комментария через PUT с контролем версии.
- `test_update_comment_concurrency_conflict_returns_409` — защита от состояния гонки (OCC): возврат HTTP 409 при
  несовпадении `expected_version`.
- `test_update_comment_not_found_returns_404` — возврат HTTP 404 при попытке редактирования несуществующего комментария.
- `test_delete_comment_success` — удаление комментария через DELETE (HTTP 204) и проверка его последующей недоступности.
- `test_delete_comment_not_found_returns_404` — возврат HTTP 404 при попытке удаления несуществующего комментария.

#### `test_comments_query.py` — Выборка, фильтрация и пагинация

- `test_list_comments_pagination_pages` — постраничная навигация по списку комментариев с проверкой параметров `limit` и
  `offset`.
- `test_list_comments_filter_by_author` — фильтрация списка комментариев по автору (`?author=...`).
- `test_list_comments_filter_by_source_url` — фильтрация списка комментариев по URL источника (`?source_url=...`).
- `test_list_comments_filter_combined_author_and_source` — комбинированная фильтрация одновременно по автору и URL
  источника.
- `test_list_comments_empty_results` — возврат пустого списка (`items=[]`, `total=0`) при отсутствии совпадений по
  фильтрам.
- `test_list_comments_invalid_limit_returns_422[-5]` — валидация отрицательного лимита (`limit=-5`) с возвратом HTTP
    422.
- `test_list_comments_invalid_limit_returns_422[0]` — валидация нулевого лимита (`limit=0`) с возвратом HTTP 422 (
  `ge=1`).
- `test_list_comments_invalid_limit_returns_422[101]` — валидация превышения максимального лимита (`limit=101`) с
  возвратом HTTP 422 (`le=100`).
- `test_list_comments_negative_offset_returns_422` — валидация отрицательного смещения (`offset=-1`) с возвратом HTTP
    422.

#### `test_comments_parse.py` — Парсинг веб-страниц форумов

- `test_parse_page_success_and_idempotency` — сбор постов по URL и проверка идемпотентности (повторный запуск не создает
  дубликатов).
- `test_parse_page_invalid_url_scheme_returns_422` — отклонение некорректной схемы протокола (`hts://` вместо
  `http/https`) с кодом HTTP 422.
- `test_parse_page_malformed_url_returns_422` — отклонение невалидной строки URL с кодом HTTP 422.
- `test_parse_page_empty_body_returns_422` — отклонение пустого тела JSON-запроса `{}` с кодом HTTP 422.
- `test_parse_page_forbids_extra_fields_returns_422` — отклонение неожиданных дополнительных полей в теле запроса (
  `extra="forbid"`).
- `test_parse_page_unreachable_upstream_returns_400` — трансляция ошибки внешнего форума (HTTP 500) в HTTP 400 Bad
  Request с пояснением.
- `test_parse_page_connection_failure_returns_502` — трансляция сетевого сбоя соединения (`ConnectError`) в HTTP 502 Bad
  Gateway.

#### `test_comments_validation.py` — Валидация входных данных и обработка ошибок

- `test_create_comment_empty_author_returns_422` — отклонение пустого имени автора при создании комментария (HTTP 422).
- `test_create_comment_whitespace_author_returns_422` — перехват имени из одних пробелов через `DomainError` и возврат
  HTTP 422.
- `test_create_comment_empty_text_returns_422` — отклонение пустого текста сообщения схемы создания (HTTP 422).
- `test_create_comment_whitespace_text_returns_422` — перехват текста из пробелов/табуляций через `DomainError` и
  возврат HTTP 422.
- `test_create_comment_oversized_author_returns_422` — отклонение имени автора, превышающего `MAX_USERNAME_LENGTH` (HTTP
  422).
- `test_create_comment_oversized_text_returns_422` — отклонение текста сообщения, превышающего
  `MAX_MESSAGE_TEXT_LENGTH` (HTTP 422).
- `test_create_comment_forbids_extra_field_returns_422` — запрет передачи незадекларированных полей в теле создания
  комментария.
- `test_update_comment_whitespace_text_returns_422` — отклонение пробельного текста при обновлении комментария через
  доменное исключение (HTTP 422).
- `test_update_comment_invalid_version_returns_422[0]` — отклонение нулевой ожидаемой версии (`expected_version=0`)
  схемы обновления (HTTP 422).
- `test_update_comment_invalid_version_returns_422[-1]` — отклонение отрицательной ожидаемой версии (
  `expected_version=-1`) (HTTP 422).
- `test_update_comment_invalid_version_returns_422[-99]` — отклонение произвольного отрицательного значения версии (HTTP
  422).
- `test_update_comment_forbids_extra_field_returns_422` — запрет передачи посторонних полей в payload обновления
  комментария (HTTP 422).

#### `test_di_container.py` — Dependency Injection

- `test_di_container_resolves_dependencies` — проверка корректного разрешения всего графа зависимостей через контейнер
  Dishka.

#### `test_health_and_root.py` — Служебные маршруты и документация

- `test_health_live_endpoint` — проверка liveness-пробы приложения (`GET /health/live` -> `{"status": "ok"}`).
- `test_health_ready_endpoint` — проверка readiness-пробы приложения (`GET /health/ready` -> `{"status": "ready"}`).
- `test_root_redirects_to_docs` — проверка автоматического редиректа с корня (`GET /`) на страницу документации
  Swagger (`/docs`).
- `test_docs_swagger_ui_endpoint` — проверка доступности интерактивной HTML-документации Swagger UI (`GET /docs`).
- `test_openapi_schema_endpoint` — проверка отдачи JSON-спецификации схемы OpenAPI (`GET /openapi.json`).

---

### 2. Прикладной слой (`tests/unit/application/`)

#### `test_commands.py` — Обработчики команд (Write Use Cases)

- `test_add_comment_success` — успешное выполнение команды `AddCommentCommand` с сохранением в репозиторий и возвратом
  DTO.
- `test_add_comment_without_external_id` — создание комментария без указания внешнего ID (`external_id=None`).
- `test_add_comment_already_exists_by_id` — выброс исключения `CommentAlreadyExistsError` при коллизии первичного ключа
  UUID.
- `test_add_comment_already_exists_by_source_and_external_id` — выброс `CommentAlreadyExistsError` при дублировании пары
  `(source_url, external_id)`.
- `test_update_comment_success` — успешное обновление текста комментария с изменением версии агрегата на +1.
- `test_update_comment_noop` — проверка no-op (идентичный текст не инкрементирует версию и не меняет `updated_at`).
- `test_update_comment_not_found` — выброс `CommentNotFoundError` при попытке обновления несуществующего комментария.
- `test_update_comment_concurrency_error` — выброс `ConcurrencyError` при несовпадении переданной версии с текущей
  версией агрегата.
- `test_delete_comment_success` — успешное удаление комментария по идентификатору через `DeleteCommentCommand`.
- `test_delete_comment_not_found` — выброс `CommentNotFoundError` при попытке удаления отсутствующего комментария.
- `test_parse_page_handler` — обработка парсинга страницы: вызов парсера, сохранение новых постов и обновление
  существующих.

#### `test_queries.py` — Обработчики запросов (Read Use Cases)

- `test_get_comment_query_success` — получение комментария по ID через `GetCommentQueryHandler` и маппинг в
  `CommentDTO`.
- `test_get_comment_query_not_found` — выброс `CommentNotFoundError` при запросе несуществующего комментария.
- `test_get_comments_query_with_filters_and_pagination` — выборка списка комментариев с фильтрацией по автору, источнику
  и параметрами пагинации.

---

### 3. Доменный слой (`tests/unit/domain/`)

#### `test_base_entities.py` — Базовые классы сущностей и инварианты

- `test_domain_model_immutability` — запрет прямого присвоения атрибутов объектам `DomainModel` (`frozen=True`).
- `test_domain_model_forbids_extra` — запрет передачи дополнительных необъявленных полей (`extra="forbid"`).
- `test_domain_model_copy_validates` — проверка обязательной валидации данных при вызове `model_copy(update=...)`.
- `test_domain_model_construct_forces_validation` — запрет обхода валидации через вызов `model_construct()`.
- `test_entity_requires_positive_id` — требование строго положительного целочисленного идентификатора сущности (
  `id > 0`).
- `test_entity_normalizes_created_at` — автоматическая нормализация часового пояса поля `created_at` к UTC.
- `test_entity_rejects_naive_created_at` — выброс `InvalidDomainTimestampError` при передаче naive datetime без
  таймзоны.
- `test_mutable_entity_initial_state` — проверка начального состояния изменяемой сущности (`updated_at is None`).
- `test_mutable_entity_apply_changes_advances_state` — обновление состояния сущности и выставление метки `updated_at`
  через `_apply_changes`.
- `test_mutable_entity_apply_changes_noop_returns_false` — возврат `False` и сохранение `updated_at=None` при передаче
  идентичных значений (no-op).
- `test_mutable_entity_normalizes_updated_at_to_utc` — нормализация временной метки `updated_at` к часовому поясу UTC.
- `test_mutable_entity_rejects_naive_updated_at` — отклонение naive datetime при вызове `_apply_changes`.
- `test_mutable_entity_rejects_updated_at_preceding_created_at` — запрет выставления `updated_at` раньше даты создания
  `created_at`.
- `test_mutable_entity_rejects_updated_at_preceding_current_updated_at` — запрет отката метки времени назад относительно
  текущего `updated_at`.
- `test_versioned_mutable_entity_increments_version` — автоматический инкремент поля `version` на +1 при каждом успешном
  изменении.
- `test_versioned_mutable_entity_noop_preserves_version` — неизменность версии агрегата при отсутствии реальных
  изменений в данных.
- `test_versioned_mutable_entity_atomic_rollback_on_invalid_change` — атомарный откат состояния к исходному при ошибке
  валидации изменений.
- `test_mutable_entity_rejects_id_mutation` — выброс `EntityIdentityImmutableError` при попытке изменить идентификатор
  `id`.
- `test_mutable_entity_rejects_created_at_mutation` — выброс `EntityIdentityImmutableError` при попытке изменить дату
  создания `created_at`.

#### `test_clock.py` — Доменные часы и работа со временем

- `test_utc_now_returns_timezone_aware_utc_datetime` — генерация текущего времени строго с часовым поясом UTC (
  `tzinfo is UTC`).
- `test_ensure_utc_defaults_to_now_when_none` — возврат текущего времени UTC при передаче значения `None`.
- `test_ensure_utc_converts_timezone_aware_to_utc` — конвертация даты с произвольным смещением пояса к единому UTC.
- `test_ensure_utc_rejects_naive_datetime` — выброс `InvalidDomainTimestampError` при попытке нормализации naive
  datetime.

#### `test_comment.py` — Агрегат комментария (`Comment`)

- `test_comment_create_and_properties` — корректная инициализация агрегата со всеми свойствами, `version=1` и
  `updated_at=None`.
- `test_comment_create_with_explicit_uuid` — создание агрегата с явно переданным пользовательским UUID.
- `test_comment_create_with_none_external_id` — создание агрегата без внешнего ID (`external_id=None`).
- `test_comment_create_with_string_external_ids` — автоматическое приведение числовой строки к `int` и сохранение
  строкового ID при наличии букв.
- `test_comment_create_with_value_objects` — создание сущности путем прямой передачи готовых Value Objects `Username` и
  `MessageText`.
- `test_comment_edit_text_success` — успешное редактирование текста комментария с продвижением версии на 2.
- `test_comment_edit_text_noop` — неизменность версии и времени при передаче текста, идентичного текущему.
- `test_comment_edit_text_invalid_rollback` — откат текста к исходному при ошибке валидации нового текста и выброс
  `InvalidMessageTextError`.
- `test_comment_edit_text_with_message_text_vo` — обновление текста агрегата при передаче экземпляра `MessageText`.
- `test_comment_immutability` — запрет прямого изменения полей агрегата в обход бизнес-методов (`frozen=True`).

#### `test_value_objects.py` — Объекты-значения (`Username`, `MessageText`)

- `test_username_valid` — создание валидного объекта `Username`, проверка тримминга пробелов, хеширования и строкового
  представления.
- `test_username_rejects_empty_or_whitespace[empty]` — отклонение пустой строки имени пользователя (`""`).
- `test_username_rejects_empty_or_whitespace[spaces]` — отклонение имени пользователя, состоящего только из пробелов.
- `test_username_rejects_empty_or_whitespace[tab]` — отклонение имени пользователя из символов табуляции.
- `test_username_rejects_empty_or_whitespace[newline]` — отклонение имени пользователя из символа перевода строки.
- `test_username_rejects_empty_or_whitespace[mixed_whitespace]` — отклонение имени пользователя из смеси пробельных
  символов.
- `test_username_rejects_non_string` — выброс `InvalidUsernameError` при валидации нестрокового типа данных.
- `test_username_rejects_too_long` — отклонение имени пользователя, длина которого превышает `MAX_USERNAME_LENGTH`.
- `test_message_text_valid` — валидация текста сообщения, проверка тримминга пробелов и нормализации `\r\n` в `\n`.
- `test_message_text_nfc_normalization` — каноническая Unicode-нормализация (NFC) составных символов с диакритикой.
- `test_message_text_rejects_empty_or_whitespace[empty]` — отклонение пустого текста сообщения (`""`).
- `test_message_text_rejects_empty_or_whitespace[spaces]` — отклонение текста из одних пробелов.
- `test_message_text_rejects_empty_or_whitespace[tab]` — отклонение текста из символов табуляции.
- `test_message_text_rejects_empty_or_whitespace[crlf]` — отклонение текста из пустых переводов строк `\n\r`.
- `test_message_text_rejects_empty_or_whitespace[mixed_whitespace]` — отклонение текста из смеси пробелов, переносов и
  табуляций.
- `test_message_text_rejects_non_string` — выброс `InvalidMessageTextError` при валидации нестрокового значения текста.
- `test_message_text_rejects_too_long` — отклонение текста, длина которого превышает `MAX_MESSAGE_TEXT_LENGTH`.

---

### 4. Входной слой (`tests/unit/entrypoints/http/`)

#### `test_schemas.py` — Валидация HTTP-схем DTO

- `test_add_comment_request_valid` — создание валидной схемы `AddCommentRequest` со всеми заполненными полями.
- `test_add_comment_request_defaults` — проверка значений по умолчанию в `AddCommentRequest` (`source_url=""`,
  `external_id=None`).
- `test_add_comment_request_rejects_empty_fields` — валидация запрета пустых строк в полях `author` и `text`.
- `test_add_comment_request_rejects_oversized_fields` — валидация превышения максимальных допустимых длин автора и
  текста.
- `test_add_comment_request_forbids_extra_fields` — запрет передачи посторонних ключей в JSON-объекте
  `AddCommentRequest`.
- `test_update_comment_request_valid` — корректная инициализация схемы `UpdateCommentRequest`.
- `test_update_comment_request_rejects_invalid_version` — валидация ожидаемой версии (`expected_version <= 0`).
- `test_update_comment_request_forbids_extra_fields` — запрет передачи лишних полей в схеме `UpdateCommentRequest`.
- `test_parse_page_request_valid` — валидация корректного HTTP/HTTPS URL в схеме `ParsePageRequest`.
- `test_parse_page_request_rejects_invalid_url` — отклонение невалидных URL и протоколов (`ftp://`).
- `test_comment_response_from_domain` — фабричный метод `CommentResponse.from_domain` для формирования схемы ответа из
  сущности.

---

### 5. Инфраструктурный слой (`tests/unit/infrastructure/`)

#### `test_soup_parser.py` — Парсер веб-страниц форумов и лент

- `test_parse_html_fixture` — извлечение комментариев из типовой HTML-страницы форума по селекторам.
- `test_parse_page_with_mock_transport` — интеграция `BeautifulSoupForumParser` с клиентом HTTP через
  `httpx.MockTransport`.
- `test_parse_html_skips_invalid_elements` — пропуск некорректных элементов DOM (без ID, без автора, пустой контент).
- `test_parse_html_empty_string` — возврат пустого списка при передаче пустой строки HTML.
- `test_parse_page_raises_on_http_status_error[404-400-404]` — выброс `ForumFetchError` со статусом 400 и апстримом 404
  при ответе сервера Not Found.
- `test_parse_page_raises_on_http_status_error[403-400-403]` — выброс `ForumFetchError` со статусом 400 и апстримом 403
  при Forbidden.
- `test_parse_page_raises_on_http_status_error[500-400-500]` — выброс `ForumFetchError` со статусом 400 и апстримом 500
  при внутренней ошибке форума.
- `test_parse_page_raises_on_request_error` — выброс `ForumFetchError` со статусом 502 при сетевом сбое подключения (
  `ConnectError`).
- `test_parse_xml_rss_feed` — парсинг RSS/XML ленты комментариев и автоопределение сущностей.
- `test_parse_4pda_html_structure` — парсинг структуры веток комментариев форума 4PDA.
- `test_parse_page_default_client` — запуск парсинга страницы при инициализации парсера с дефолтным клиентом (
  `client=None`).
- `test_parse_page_follows_rss_auto_discovery` — обнаружение тега `<link rel="alternate" ...>` и переход на
  автодискавери RSS-ленты.
- `test_parse_page_cyclic_rss_redirect_protection` — защита от зацикливания при перекрестных ссылках страниц друг на
  друга.
- `test_parse_html_logs_malformed_comment` — логирование предупреждения и пропуск постов с поврежденными или аномальными
  данными.
- `test_parse_html_alphanumeric_external_id` — извлечение строковых буквенно-цифровых идентификаторов постов (например,
  Lobsters).
- `test_parse_html_ignores_author_inside_quote` — исключение автора цитируемого сообщения и выборка реального автора
  ответа.
- `test_parse_html_truncates_oversized_text` — безопасное усечение сверхдлинных текстов с добавлением суффикса
  `... [truncated]`.
- `test_parse_lor_html_structure` — парсинг структуры топиков и постов форума Linux.org.ru (LOR).
- `test_parse_html_ignores_sidebar_and_news_articles` — игнорирование боковых колонок, тизеров и новостных блоков вне
  контейнера комментариев.
- `test_parse_page_fallback_client_on_403` — повторная попытка запроса через резервный SSL-клиент при получении
  блокировки 403.

#### `test_sqlalchemy_repo.py` — Репозиторий SQLAlchemy (SQLite)

- `test_repo_add_and_get_by_id` — сохранение сущности в БД через `add` и получение через `get_by_id`.
- `test_repo_exists_by_id` — проверка существования записи по идентификатору через `exists_by_id`.
- `test_repo_get_by_id_not_found` — возврат `None` при попытке чтения отсутствующего идентификатора.
- `test_repo_find_by_source_and_external_id` — поиск записи по естественному составному ключу
  `(source_url, external_id)`.
- `test_repo_unique_constraint_source_external_id` — срабатывание уникального индекса БД и выброс
  `CommentAlreadyExistsError` при дубликате.
- `test_repo_same_external_id_different_sources` — возможность сохранения записей с одинаковым `external_id` из
  различных источников.
- `test_repo_get_by_author` — выборка всех комментариев указанного автора с сортировкой по времени создания.
- `test_repo_update` — обновление текста комментария в БД с сохранением новой версии агрегата.
- `test_repo_delete` — удаление записи из таблицы и возврат флага успешности (`True`/`False`).
- `test_repo_multiple_none_external_ids_allowed` — поддержка нескольких записей с `external_id=None` в пределах одного
  `source_url`.
- `test_repo_update_concurrency_error` — выброс `ConcurrencyError` при обновлении с несовпадающей версией строки.
- `test_repo_find_by_source_and_external_ids` — пакетная загрузка словаря комментариев по списку внешних ID.
- `test_repo_get_paginated` — постраничная выборка записей с сортировкой, `limit`, `offset` и фильтрами.
- `test_repo_get_by_source_url` — выборка всех комментариев для конкретного URL источника.
- `test_repo_get_by_id_for_update` — выполнение выборки записи с блокировкой строки `with_for_update()`.
- `test_repo_find_by_source_and_external_ids_empty` — возврат пустого словаря `{}` при передаче пустого списка
  идентификаторов.
- `test_mapper_handles_integer_external_id` — корректный маппинг целочисленного ID из столбца БД в доменное поле
  `external_id`.
