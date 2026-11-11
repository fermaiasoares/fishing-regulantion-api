# Ingestão hidrográfica

A primeira etapa baixa o arquivo oficial da BHB250 (edição 2021, nível 2) e registra o SHA-256 dos bytes recebidos. O nível 2 é o menor arquivo vetorial publicado pelo IBGE e serve para validar o fluxo inicial. A granularidade para o MVP de Minas Gerais será avaliada com as feições carregadas.

## Aquisição do IBGE

Com Python 3.11 ou superior, execute da raiz do repositório:

```bash
mkdir -p /tmp/fishing-geo
python3 services/geo-ingestion/acquire_ibge.py /tmp/fishing-geo/bacias.zip \
  > /tmp/fishing-geo/bacias.json
```

Guarde o ZIP e o JSON juntos. O JSON registra URL, edição, horário de coleta em UTC, tamanho e SHA-256. Use `--expected-sha256` com o valor registrado para verificar outra coleta. O script valida a estrutura do ZIP, mantém o arquivo anterior se o download ou a validação falharem e retorna código de saída diferente de zero.

A [documentação técnica da BHB250](https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/bacias_e_divisoes_hidrograficas_do_brasil/2021/Bacias_Hidrograficas_do_Brasil_BHB250/vetores/Documentacao_Tecnica_BHB250.pdf) informa EPSG:4674, a chave `id` e o nome `nome_bacia`. A leitura vetorial deverá conferir o CRS declarado no arquivo e a unicidade da chave antes de transformar para EPSG:4326.

## Trechos da ANA

A [camada de trechos da BHO6](https://portal1.snirh.gov.br/server/rest/services/Hosted/main_geoft_bho6_trecho_drenagem/FeatureServer/0) publica polilinhas em EPSG:4674 e aceita paginação. A próxima etapa precisa verificar o identificador de origem e a edição da amostra antes de fixar o contrato de aquisição. Para as duas fontes, o recorte piloto deverá selecionar feições que interceptam a malha oficial de Minas Gerais, preservando a geometria de origem das feições selecionadas.

## Testes

```bash
cd services/geo-ingestion
python3 -m unittest discover -s tests -v
```

Os testes usam um ZIP local para verificar a coleta de metadados e o tratamento de erros. A validação das geometrias e a publicação no PostGIS são acompanhadas na [issue #4](https://github.com/fermaiasoares/fishing-regulation-api/issues/4).

## Validação com fontes oficiais no GitHub Actions

O workflow **Official hydrography sources** roda em PRs que alteram o serviço ou o workflow e pode ser disparado manualmente quando estiver disponível na branch padrão. Ele verifica o ZIP oficial do IBGE e consulta até dez trechos da BHO6 em um retângulo no entorno de Caratinga (MG).

O resumo registra URL, horário, SHA-256, CRS e contagem de registros para cada coleta. O artefato `official-hydrography-evidence` contém os relatórios e a resposta da ANA. A contagem do IBGE é do arquivo nacional de nível 2. A checagem verifica a integridade dos downloads, os componentes do shapefile e as polilinhas da amostra. A carga no PostGIS é acompanhada na issue #4.
