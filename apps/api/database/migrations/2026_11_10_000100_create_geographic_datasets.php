<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        DB::statement('CREATE EXTENSION IF NOT EXISTS postgis');

        Schema::create('geographic_datasets', function (Blueprint $table) {
            $table->id();
            $table->string('slug')->unique();
            $table->string('name');
            $table->string('publisher');
            $table->timestampsTz();
        });

        Schema::create('geographic_dataset_versions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('dataset_id')->constrained('geographic_datasets')->restrictOnDelete();
            $table->string('version');
            $table->text('source_url');
            $table->timestampTz('collected_at')->nullable();
            $table->text('license')->nullable();
            $table->string('checksum_sha256', 64)->nullable();
            $table->text('source_crs')->nullable();
            $table->timestampsTz();
            $table->unique(['dataset_id', 'version']);
        });

        DB::statement(<<<'SQL'
            ALTER TABLE geographic_dataset_versions
            ADD CONSTRAINT geographic_dataset_versions_sha256_check
            CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
            SQL);
    }

    public function down(): void
    {
        Schema::dropIfExists('geographic_dataset_versions');
        Schema::dropIfExists('geographic_datasets');
    }
};
