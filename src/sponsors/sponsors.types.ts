export interface VersionMeta {
  date: string;
  label: string;
  foi: string;
  total: number;
}

export interface SponsorSource {
  agency: string;
  document: string;
  foi_reference: string;
  foi_act: string;
  license: string;
  license_url: string;
}

export interface SponsorFile {
  version: string;
  label: string;
  generated_at: string;
  source: SponsorSource;
  total: number;
  sponsors: string[];
}
