<?php

namespace Tests\Feature;

use App\Geography\HydrographicLookup;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use InvalidArgumentException;
use Tests\TestCase;

class HydrographicLookupTest extends TestCase
{
    use DatabaseTransactions;

    public function test_it_matches_basins_and_rivers_in_the_selected_version(): void
    {
        [$version, $otherVersion] = $this->createVersions();
        $this->insertBasin($version, 'basin-1');
        $this->insertBasin($otherVersion, 'other-version');
        DB::insert(
            'INSERT INTO river_segments (dataset_version_id, source_feature_id, geometry)
             VALUES (?, ?, ST_GeomFromText(?, 4326))',
            [$version, 'segment-1', 'MULTILINESTRING((10 23, 14 23))'],
        );

        $lookup = new HydrographicLookup;
        $result = $lookup->at(23, 12, $version);
        $this->assertTrue($result['geographic_match']);
        $this->assertSame($version, $result['dataset_version_id']);
        $this->assertSame(['basin-1'], array_column($result['basins'], 'source_feature_id'));
        $this->assertSame(['segment-1'], array_column($result['river_segments'], 'source_feature_id'));

        $boundary = $lookup->at(22, 10, $version);
        $this->assertSame(['basin-1'], array_column($boundary['basins'], 'source_feature_id'));
        $this->assertSame([], $boundary['river_segments']);
    }

    public function test_a_point_outside_the_dataset_has_no_geographic_match(): void
    {
        [$version] = $this->createVersions();
        $this->insertBasin($version, 'basin-1');

        $this->assertSame([
            'dataset_version_id' => $version,
            'geographic_match' => false,
            'basins' => [],
            'river_segments' => [],
        ], (new HydrographicLookup)->at(25, 12, $version));
    }

    public function test_it_rejects_invalid_coordinates_before_querying(): void
    {
        $this->expectException(InvalidArgumentException::class);

        (new HydrographicLookup)->at(NAN, 12, 1);
    }

    public function test_the_database_rejects_the_wrong_srid(): void
    {
        [$version] = $this->createVersions();

        $this->expectException(QueryException::class);
        $this->expectExceptionMessage('SRID');

        $this->insertBasin($version, 'wrong-srid', 3857);
    }

    private function createVersions(): array
    {
        $dataset = DB::table('geographic_datasets')->insertGetId([
            'slug' => 'test-fixture',
            'name' => 'Synthetic test fixture',
            'publisher' => 'Automated test',
        ]);

        return array_map(fn ($version) => DB::table('geographic_dataset_versions')->insertGetId([
            'dataset_id' => $dataset,
            'version' => $version,
            'source_url' => 'https://example.invalid/test-fixture',
            'source_crs' => 'EPSG:4326',
        ]), ['1', '2']);
    }

    private function insertBasin(int $version, string $featureId, int $srid = 4326): void
    {
        DB::insert(
            'INSERT INTO hydrographic_basins (dataset_version_id, source_feature_id, geometry)
             VALUES (?, ?, ST_GeomFromText(?, ?))',
            [$version, $featureId, 'MULTIPOLYGON(((10 22, 14 22, 14 24, 10 24, 10 22)))', $srid],
        );
    }
}
