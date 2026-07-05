import { Injectable, NotFoundException } from '@nestjs/common';
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import { SponsorFile, VersionMeta } from './sponsors.types';

@Injectable()
export class SponsorsService {
  private readonly dataDir = join(process.cwd(), 'data');

  async getVersions(): Promise<VersionMeta[]> {
    const files = await readdir(this.dataDir);
    const jsonFiles = files.filter((f) => /^sponsors_\d{4}-\d{2}-\d{2}\.json$/.test(f));

    const versions = await Promise.all(
      jsonFiles.map(async (file) => {
        const raw = await readFile(join(this.dataDir, file), 'utf-8');
        const d: SponsorFile = JSON.parse(raw);
        return {
          date: d.version,
          label: d.label,
          foi: d.source?.foi_reference ?? '',
          total: d.total,
        } as VersionMeta;
      }),
    );

    return versions.sort((a, b) => b.date.localeCompare(a.date));
  }

  async getSponsors(version: string): Promise<SponsorFile> {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(version)) {
      throw new NotFoundException('Invalid version format');
    }

    const filePath = join(this.dataDir, `sponsors_${version}.json`);

    try {
      const raw = await readFile(filePath, 'utf-8');
      return JSON.parse(raw);
    } catch {
      throw new NotFoundException(`Version ${version} not found`);
    }
  }
}
