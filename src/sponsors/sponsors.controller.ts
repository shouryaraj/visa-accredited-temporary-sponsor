import { Controller, Get, Param } from '@nestjs/common';
import { SponsorsService } from './sponsors.service';
import { SponsorFile, VersionMeta } from './sponsors.types';

@Controller()
export class SponsorsController {
  constructor(private readonly sponsorsService: SponsorsService) {}

  @Get('versions')
  getVersions(): Promise<VersionMeta[]> {
    return this.sponsorsService.getVersions();
  }

  @Get('sponsors/:version')
  getSponsors(@Param('version') version: string): Promise<SponsorFile> {
    return this.sponsorsService.getSponsors(version);
  }
}
