import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import channelRoutes from './routes/channel.routes';
import movieRoutes from './routes/movie.routes';
import seriesRoutes from './routes/series.routes';
import profileRoutes from './routes/profile.routes';
import favoritesRoutes from './routes/favorites.routes';
import historyRoutes from './routes/history.routes';
import downloadRoutes from './routes/download.routes';
import searchRoutes from './routes/search.routes';
import settingsRoutes from './routes/settings.routes';
import { errorHandler } from './middleware/errorHandler.middleware';
import { env } from './config/environment';
import { logger } from './utils/logger';

const app = express();

// Middleware
app.use(helmet());
app.use(cors({ origin: env.CORS_ORIGIN }));
app.use(compression());
app.use(express.json());

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
    logger.http(`${req.method} ${req.url}`);
    next();
});

// Health check
app.get('/health', (req: Request, res: Response) => {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API Routes
app.use('/api/v1', channelRoutes);
app.use('/api/v1', movieRoutes);
app.use('/api/v1', seriesRoutes);
app.use('/api/v1', profileRoutes);
app.use('/api/v1/profiles/:profileId/favorites', favoritesRoutes);
app.use('/api/v1/profiles/:profileId/history', historyRoutes);
app.use('/api/v1/profiles/:profileId/search', searchRoutes);
app.use('/api/v1/profiles/:profileId/settings', settingsRoutes);
app.use('/api/v1', downloadRoutes);

app.use(errorHandler);
import { db } from './repositories';

export const startServer = async () => {
    try {
        // Enable WAL mode for SQLite to improve concurrency
        await db.$queryRawUnsafe('PRAGMA journal_mode = WAL;');
        logger.info('SQLite WAL mode enabled');

        app.listen(env.PORT, () => {
            logger.info(`Server running on port ${env.PORT} in ${env.NODE_ENV} mode`);
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
};

if (require.main === module) {
    startServer();
}

export default app;
