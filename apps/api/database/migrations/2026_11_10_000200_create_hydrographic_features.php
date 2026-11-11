<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        foreach (['hydrographic_basins' => 'MultiPolygon', 'river_segments' => 'MultiLineString'] as $name => $geometryType) {
            Schema::create($name, function (Blueprint $table) {
                $table->id();
                $table->foreignId('dataset_version_id')
                    ->constrained('geographic_dataset_versions')->restrictOnDelete();
                $table->string('source_feature_id');
                $table->string('name')->nullable();
                $table->timestampsTz();
                $table->unique(['dataset_version_id', 'source_feature_id']);
            });

            DB::statement(<<<SQL
                ALTER TABLE {$name}
                ADD COLUMN geometry geometry({$geometryType}, 4326) NOT NULL,
                ADD CONSTRAINT {$name}_geometry_check
                CHECK (
                    ST_IsValid(geometry) AND NOT ST_IsEmpty(geometry)
                    AND ST_XMin(geometry) >= -180 AND ST_XMax(geometry) <= 180
                    AND ST_YMin(geometry) >= -90 AND ST_YMax(geometry) <= 90
                )
                SQL);

            DB::statement("CREATE INDEX {$name}_geometry_gist ON {$name} USING GIST (geometry)");
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('river_segments');
        Schema::dropIfExists('hydrographic_basins');
    }
};
