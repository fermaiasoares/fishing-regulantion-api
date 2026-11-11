<?php

namespace Tests\Feature;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use RuntimeException;
use Tests\TestCase;

class HealthTest extends TestCase
{
    public function test_application_boots(): void
    {
        $this->get('/up')->assertOk();
    }

    public function test_postgis_and_redis_are_reachable(): void
    {
        $this->getJson('/api/health')
            ->assertOk()
            ->assertExactJson(['status' => 'ok']);
    }

    public function test_postgis_failure_returns_unavailable_without_connection_details(): void
    {
        DB::shouldReceive('selectOne')->once()->with('SELECT PostGIS_Version()')
            ->andThrow(new RuntimeException('Internal database details'));

        $this->getJson('/api/health')
            ->assertServiceUnavailable()
            ->assertExactJson(['status' => 'unavailable']);
    }

    public function test_redis_failure_returns_unavailable_without_connection_details(): void
    {
        Redis::shouldReceive('connection')->once()
            ->andThrow(new RuntimeException('Internal Redis details'));

        $this->getJson('/api/health')
            ->assertServiceUnavailable()
            ->assertExactJson(['status' => 'unavailable']);
    }
}
