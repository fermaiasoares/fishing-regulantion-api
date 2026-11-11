# Modelo geográfico

O banco registra a fonte e a versão de cada feição. `geographic_datasets` identifica o dataset e o publicador. `geographic_dataset_versions` registra a versão, a URL do artefato de origem e, quando disponíveis, a data de coleta, a licença, o CRS de origem e o SHA-256 do artefato. Correções ou atualizações da fonte entram como uma nova versão. O identificador da feição na fonte é único dentro da versão e da tabela. As chaves estrangeiras impedem excluir um dataset ou uma versão enquanto houver registros vinculados.

Bacias usam `MultiPolygon` e segmentos usam `MultiLineString`, ambos em WGS 84 (EPSG:4326) e com índices GiST. Uma futura ingestão deve verificar o CRS na fonte, rejeitar CRS ausente ou ambíguo, transformar a geometria com `ST_Transform` quando necessário e usar `ST_Multi` para normalizar as geometrias simples. `ST_SetSRID` apenas rotula coordenadas com um CRS já conhecido. O banco rejeita SRID ou tipo incorretos, geometrias inválidas ou vazias e coordenadas fora dos limites de WGS 84.

O serviço interno `App\Geography\HydrographicLookup::at` recebe latitude, longitude e o ID da versão. Na geometria, a ordem é longitude, latitude. A busca inclui a borda da bacia (`ST_Covers`) e a interseção exata com a linha do rio (`ST_Intersects`). Uma posição próxima de um rio pode não intersectar sua geometria. O retorno `geographic_match: false` indica ausência de feições correspondentes nessa versão e deixa a situação legal indeterminada.

O esquema foi preparado para Minas Gerais. A cobertura só será conhecida após a ingestão de fontes oficiais. Os testes usam geometrias sintéticas em transações. O rollback remove as tabelas da entrega na ordem inversa e preserva a extensão PostGIS, que pode servir a outros objetos do banco.
