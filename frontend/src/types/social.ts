import type { components } from './api';

export type CreativeFusion = Omit<
  components['schemas']['CreativeFusion'],
  'image_url' | 'creator_name' | 'is_liked' | 'created_at'
> & {
  image_url?: string;
  creator_name?: string;
  is_liked?: boolean;
  created_at?: string;
};

export type ClubEvent = Omit<
  components['schemas']['ClubEvent'],
  'is_participant' | 'participants_count' | 'event_date'
> & {
  event_date: string;
  is_participant?: boolean;
  participants_count?: number;
};

export type DiscoveryClub = Omit<
  components['schemas']['DiscoveryClub'],
  'image_url' | 'is_private' | 'events'
> & {
  image_url?: string;
  is_private: boolean;
  events: ClubEvent[];
  is_member?: boolean;
};

export interface ClubMembership {
  id: number;
  user: number;
  username: string;
  role: 'member' | 'admin' | 'owner';
  joined_at: string;
}

export interface ChatMessage {
  user: string;
  text: string;
  timestamp?: number;
}
