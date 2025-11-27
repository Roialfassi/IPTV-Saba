import { Request, Response, NextFunction } from 'express';
import { MovieService } from '../services/MovieService';

export class MovieController {
    constructor(private movieService: MovieService) { }

    getMovies = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { page, limit, groupTitle, year, sortBy, order } = req.query;

        const result = await this.movieService.getMovies(profileId, {
            page: page ? Number(page) : 1,
            limit: limit ? Number(limit) : 50,
            groupTitle: groupTitle as string,
            year: year ? Number(year) : undefined,
            sortBy: sortBy as 'name' | 'year' | 'date',
            order: order as 'asc' | 'desc',
        });

        res.status(200).json(result);
    };

    getMovieById = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, movieId } = req.params;
        const movie = await this.movieService.getMovieById(profileId, movieId);
        res.status(200).json(movie);
    };

    getMovieGroups = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const groups = await this.movieService.getMovieGroups(profileId);
        res.status(200).json({ groups });
    };

    getAvailableYears = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const years = await this.movieService.getAvailableYears(profileId);
        res.status(200).json({ years });
    };

    searchMovies = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { q, year, groupTitle } = req.query;

        const movies = await this.movieService.searchMovies(
            profileId,
            q as string,
            {
                year: year ? Number(year) : undefined,
                groupTitle: groupTitle as string,
            }
        );

        res.status(200).json({ movies, total: movies.length });
    };
}
