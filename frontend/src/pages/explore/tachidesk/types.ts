export interface Source {
  id: string;
  name: string;
  lang: string;
}

export interface Manga {
  id: string;
  title: string;
  thumbnailUrl: string;
}

export interface Chapter {
  id: string;
  name: string;
  chapterNumber: number;
}

export interface Extension {
  pkgName: string;
  name: string;
  versionName: string;
  isInstalled: boolean;
  hasUpdate: boolean;
  lang: string;
  iconUrl: string;
  isNsfw: boolean;
  isObsolete: boolean;
}

export type ExtensionAction = 'install' | 'uninstall' | 'update';
