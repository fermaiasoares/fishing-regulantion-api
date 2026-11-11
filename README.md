# Fishing Regulation API

API do MVP para consulta de regras de pesca. A primeira etapa prepara a infraestrutura e o modelo geográfico para Minas Gerais.

## Desenvolvimento

A API usa Laravel 13 e PHP 8.3 no Compose. Use Docker com o plugin Compose v2. Execute os comandos na raiz do repositório.

```sh
cp -n infrastructure/.env.example infrastructure/.env
cp -n apps/api/.env.example apps/api/.env
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml config --quiet
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml up -d --wait db redis
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml run --rm --no-deps api composer install
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml run --rm --no-deps api php artisan key:generate
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml run --rm --no-deps api php artisan migrate
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml up -d api
curl --fail http://localhost:8000/api/health
```

Edite a senha local em `infrastructure/.env` antes da primeira subida. Gere a chave do Laravel uma vez por ambiente. O Compose fornece as variáveis de conexão à API. O PostgreSQL habilita PostGIS na criação do volume. Para um banco existente, um administrador pode habilitar a extensão com `CREATE EXTENSION IF NOT EXISTS postgis;` no banco configurado.

`GET /up` verifica se o Laravel inicializa. `GET /api/health` verifica PostGIS e Redis e retorna HTTP 503 se uma das dependências falhar. Os detalhes ficam nos logs da aplicação. O Compose usa o servidor de desenvolvimento do Laravel.

## Testes e diagnóstico

O GitHub Actions usa um banco efêmero `fishing_test` e executa a validação do Compose, as migrations, uma consulta HTTP real e a suíte Laravel. Na aba **Checks** do PR, abra **Compose, PostGIS, Redis and Laravel** para ver o passo que falhou e os logs dos serviços. A aba **Actions** também lista execuções por branch e commit.

Para diagnóstico local, use `docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml ps` e `docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml logs api db redis`. Rode a suíte com `docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml exec -T api php artisan test` em um ambiente de testes isolado, com as migrations aplicadas.

## Geografia

Consulte a [modelagem geográfica](docs/geography.md) para o esquema de versionamento, a política de CRS e o significado dos resultados das consultas espaciais.
