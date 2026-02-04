export interface ApiEnvelope<T> {
  data: T[];
  meta: {
    request_id: string;
    total?: number;
    page?: number;
    page_size?: number;
  };
  links: {
    self: string;
    next?: string | null;
    prev?: string | null;
  };
  // seu backend pode retornar objetos; vamos normalizar pra string[] no client
  errors: string[];
}

export interface Film {
  id: number;
  title: string;
  url: string;

  episode_id?: number;
  opening_crawl?: string;
  director?: string;
  producer?: string;
  release_date?: string;
}

export interface Person {
  id: number;
  name: string;
  url: string;

  height?: string;
  mass?: string;
  hair_color?: string;
  skin_color?: string;
  eye_color?: string;
  birth_year?: string;
  gender?: string;
}

export interface Planet {
  id: number;
  name: string;
  url: string;

  rotation_period?: string;
  orbital_period?: string;
  diameter?: string;
  climate?: string;
  gravity?: string;
  terrain?: string;
  surface_water?: string;
  population?: string;
}

export interface Starship {
  id: number;
  name: string;
  url: string;

  model?: string;
  manufacturer?: string;
  cost_in_credits?: string;
  length?: string;
  max_atmosphering_speed?: string;
  crew?: string;
  passengers?: string;
  cargo_capacity?: string;
  consumables?: string;
  hyperdrive_rating?: string;
  MGLT?: string;
  starship_class?: string;
}

export interface RelatedItem {
  id: number;
  name: string;
}

export type Resource = Film | Person | Planet | Starship;
export type ResourceType = "films" | "people" | "planets" | "starships";
