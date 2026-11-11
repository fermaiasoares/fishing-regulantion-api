<?php

namespace App\Geography;

use Illuminate\Support\Facades\DB;
use InvalidArgumentException;

final class HydrographicLookup
{
    public function at(float $latitude, float $longitude, int $datasetVersionId): array
    {
        if (! is_finite($latitude) || $latitude < -90 || $latitude > 90
            || ! is_finite($longitude) || $longitude < -180 || $longitude > 180) {
            throw new InvalidArgumentException('Latitude or longitude outside WGS 84 bounds.');
        }

        $matches = DB::select(<<<'SQL'
            WITH location AS (SELECT ST_SetSRID(ST_MakePoint(?, ?), 4326) AS point)
            SELECT 'basin' AS feature_type, b.id, b.source_feature_id, b.name
            FROM hydrographic_basins AS b CROSS JOIN location
            WHERE b.dataset_version_id = ? AND ST_Covers(b.geometry, location.point)
            UNION ALL
            SELECT 'river_segment', r.id, r.source_feature_id, r.name
            FROM river_segments AS r CROSS JOIN location
            WHERE r.dataset_version_id = ? AND ST_Intersects(r.geometry, location.point)
            ORDER BY feature_type, id
            SQL, [$longitude, $latitude, $datasetVersionId, $datasetVersionId]);

        return [
            'dataset_version_id' => $datasetVersionId,
            'geographic_match' => $matches !== [],
            'basins' => array_values(array_filter($matches, fn ($match) => $match->feature_type === 'basin')),
            'river_segments' => array_values(array_filter($matches, fn ($match) => $match->feature_type === 'river_segment')),
        ];
    }
}
