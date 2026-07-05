import { Module } from '@nestjs/common';
import { SponsorsModule } from './sponsors/sponsors.module';

@Module({
  imports: [SponsorsModule],
})
export class AppModule {}
