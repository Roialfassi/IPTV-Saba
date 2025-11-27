import { PrismaClient } from '@prisma/client';

export abstract class BaseRepository<T> {
    protected abstract prisma: PrismaClient;
    protected abstract model: any;

    async findById(id: string): Promise<T | null> {
        return this.model.findUnique({ where: { id } });
    }

    async findAll(skip?: number, take?: number): Promise<T[]> {
        return this.model.findMany({ skip, take });
    }

    async create(data: any): Promise<T> {
        return this.model.create({ data });
    }

    async update(id: string, data: any): Promise<T> {
        return this.model.update({
            where: { id },
            data,
        });
    }

    async delete(id: string): Promise<T> {
        return this.model.delete({ where: { id } });
    }

    async count(): Promise<number> {
        return this.model.count();
    }
}
