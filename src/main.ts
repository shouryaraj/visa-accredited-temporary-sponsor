import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.setGlobalPrefix('api');
  app.useStaticAssets(join(process.cwd(), 'public'));
  const port = process.env.PORT || 3000;
  await app.listen(port, '0.0.0.0');
  console.log(`Sponsor viewer running → http://localhost:${port}`);
}
bootstrap();
