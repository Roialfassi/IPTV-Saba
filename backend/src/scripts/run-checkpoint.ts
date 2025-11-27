#!/usr/bin/env node

import { PrismaClient } from '@prisma/client';
import { HealthCheckService } from '../health/HealthCheckService';

const prisma = new PrismaClient();

async function runCheckpoint() {
    console.log('🔍 Starting System Checkpoint...\n');

    const healthCheck = new HealthCheckService(prisma);
    const result = await healthCheck.performFullHealthCheck();

    console.log(`Overall Status: ${getStatusEmoji(result.status)} ${result.status.toUpperCase()}`);
    console.log(`Timestamp: ${result.timestamp}`);
    console.log(`Version: ${result.version}\n`);

    console.log('Detailed Results:\n');
    console.log('─'.repeat(80));

    for (const [name, check] of Object.entries(result.checks)) {
        console.log(`\n${getStatusEmoji(check.status)} ${name}`);
        console.log(`   Status: ${check.status}`);
        console.log(`   Message: ${check.message}`);
        console.log(`   Duration: ${check.duration}ms`);

        if (check.details) {
            console.log(`   Details: ${JSON.stringify(check.details, null, 2)}`);
        }
    }

    console.log('\n' + '─'.repeat(80));

    if (result.status === 'healthy') {
        console.log('\n✅ All systems operational!');
        process.exit(0);
    } else if (result.status === 'degraded') {
        console.log('\n⚠️  System is degraded but operational');
        process.exit(0);
    } else {
        console.log('\n❌ System is unhealthy');
        process.exit(1);
    }
}

function getStatusEmoji(status: string): string {
    switch (status) {
        case 'pass':
        case 'healthy':
            return '✅';
        case 'warn':
        case 'degraded':
            return '⚠️ ';
        case 'fail':
        case 'unhealthy':
            return '❌';
        default:
            return '⚪';
    }
}

runCheckpoint()
    .catch((error) => {
        console.error('❌ Checkpoint failed:', error);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
