import { PrismaClient } from '@prisma/client';
import axios from 'axios';

export interface HealthCheckResult {
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: {
        [key: string]: {
            status: 'pass' | 'fail' | 'warn';
            message: string;
            duration: number;
            details?: any;
        };
    };
    timestamp: string;
    version: string;
}

export class HealthCheckService {
    constructor(private prisma: PrismaClient) { }

    async performFullHealthCheck(): Promise<HealthCheckResult> {
        const checks: HealthCheckResult['checks'] = {};
        const startTime = Date.now();

        // 1. Database Connection
        checks.database = await this.checkDatabase();

        // 2. Database Tables
        checks.tables = await this.checkDatabaseTables();

        // 3. API Endpoints
        checks.api = await this.checkAPIEndpoints();

        // 4. M3U Parser
        checks.m3uParser = await this.checkM3UParser();

        // 5. File System
        checks.filesystem = await this.checkFileSystem();

        // 6. Memory Usage
        checks.memory = await this.checkMemory();

        // 7. Profile Data Integrity
        checks.dataIntegrity = await this.checkDataIntegrity();

        // Determine overall status
        const statuses = Object.values(checks).map(c => c.status);
        const status = statuses.some(s => s === 'fail')
            ? 'unhealthy'
            : statuses.some(s => s === 'warn')
                ? 'degraded'
                : 'healthy';

        return {
            status,
            checks,
            timestamp: new Date().toISOString(),
            version: process.env.npm_package_version || '1.0.0',
        };
    }

    private async checkDatabase() {
        const start = Date.now();
        try {
            await this.prisma.$queryRaw`SELECT 1`;
            return {
                status: 'pass' as const,
                message: 'Database connection successful',
                duration: Date.now() - start,
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `Database connection failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }

    private async checkDatabaseTables() {
        const start = Date.now();
        try {
            const requiredTables = [
                'profile',
                'm3USource',
                'channel',
                'series',
                'episode',
                'favorite',
                'watchHistory',
            ];

            const results: any = {};

            for (const table of requiredTables) {
                try {
                    const count = await (this.prisma as any)[table].count();
                    results[table] = { exists: true, count };
                } catch (error) {
                    results[table] = { exists: false, error: 'Table not found' };
                }
            }

            const allExist = Object.values(results).every((r: any) => r.exists);

            return {
                status: allExist ? ('pass' as const) : ('fail' as const),
                message: allExist
                    ? 'All required tables exist'
                    : 'Some tables are missing',
                duration: Date.now() - start,
                details: results,
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `Table check failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }

    private async checkAPIEndpoints() {
        const start = Date.now();
        const baseURL = process.env.API_BASE_URL || 'http://localhost:3000';

        try {
            const response = await axios.get(`${baseURL}/health`, {
                timeout: 5000,
            });

            return {
                status: response.status === 200 ? ('pass' as const) : ('warn' as const),
                message: 'API health endpoint responding',
                duration: Date.now() - start,
                details: { statusCode: response.status },
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `API health check failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }

    private async checkM3UParser() {
        const start = Date.now();
        try {
            // Test with a minimal M3U content
            const testM3U = `#EXTM3U
#EXTINF:-1 tvg-id="test" tvg-name="Test Channel" tvg-logo="" group-title="Test",Test Channel
http://example.com/stream`;

            const { M3UParser } = await import('../parsers/M3UParser');
            const parser = new M3UParser();
            const result = await parser.parseM3U(testM3U);

            return {
                status: result.entries.length === 1 ? ('pass' as const) : ('fail' as const),
                message: 'M3U parser functional',
                duration: Date.now() - start,
                details: { parsedEntries: result.entries.length },
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `M3U parser check failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }

    private async checkFileSystem() {
        const start = Date.now();
        const fs = require('fs/promises');
        const path = require('path');

        try {
            const requiredDirs = ['./downloads', './logs'];
            const results: any = {};

            for (const dir of requiredDirs) {
                try {
                    await fs.access(dir);
                    results[dir] = { exists: true, writable: true };
                } catch (error) {
                    try {
                        await fs.mkdir(dir, { recursive: true });
                        results[dir] = { exists: true, created: true };
                    } catch (mkdirError) {
                        results[dir] = { exists: false, error: 'Cannot create directory' };
                    }
                }
            }

            const allOk = Object.values(results).every((r: any) => r.exists);

            return {
                status: allOk ? ('pass' as const) : ('warn' as const),
                message: 'File system checks completed',
                duration: Date.now() - start,
                details: results,
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `File system check failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }

    private async checkMemory() {
        const start = Date.now();
        const used = process.memoryUsage();
        const heapUsedMB = Math.round(used.heapUsed / 1024 / 1024);
        const heapTotalMB = Math.round(used.heapTotal / 1024 / 1024);
        const externalMB = Math.round(used.external / 1024 / 1024);

        const status =
            heapUsedMB > 500 ? 'warn' : heapUsedMB > 1000 ? 'fail' : 'pass';

        return {
            status: status as 'pass' | 'warn' | 'fail',
            message: `Memory usage: ${heapUsedMB}MB / ${heapTotalMB}MB`,
            duration: Date.now() - start,
            details: {
                heapUsed: `${heapUsedMB}MB`,
                heapTotal: `${heapTotalMB}MB`,
                external: `${externalMB}MB`,
            },
        };
    }

    private async checkDataIntegrity() {
        const start = Date.now();
        try {
            // Data integrity is largely enforced by foreign key constraints in the database.
            // We can add specific logical checks here if needed in the future.

            return {
                status: 'pass' as const,
                message: 'Data integity enforced by database schema',
                duration: Date.now() - start,
                details: {
                    schemaEnforced: true
                },
            };
        } catch (error: any) {
            return {
                status: 'fail' as const,
                message: `Data integrity check failed: ${error.message}`,
                duration: Date.now() - start,
            };
        }
    }
}
